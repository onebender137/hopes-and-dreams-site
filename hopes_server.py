#!/usr/bin/env python3
"""
Hopes Bot Server — SSE-based HTTP server for the Hopes Bot APK app.

Architecture (mirrors danny-push):
  Pixel app (Kotlin, SSE) <-> hopes_server (Python, :8767 tailnet) <-> Hopes Bot

Endpoints:
  POST /command  — receive a command (e.g., "/draft <topic>"). Calls the
                   Telegram bot's command handler, captures responses.
  GET  /sub      — SSE stream; replays last N messages on connect, then live.
  POST /pub      — publish a message (server->client).
  GET  /history  — history of commands + responses.

Token auth: single shared token (query param), stored in token.txt (0600).

This server runs in the same process as the Hopes Bot (started in
run_telegram_bot()), so it can access the Telegram bot's command handlers
directly.
"""

import asyncio
import json
import os
import queue
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# --- Config ---
BASE = Path(__file__).parent
TOKEN_FILE = BASE / "hopes_token.txt"
HISTORY_FILE = BASE / "hopes_history.jsonl"
PORT = 8767
HOST = "0.0.0.0"  # bind to all interfaces (tailnet access)

# --- State ---
subs: list = []  # subscriber queues (outbound SSE)
history: list = []  # command + response history
_lock = threading.Lock()


def load_token() -> str:
    """Load or generate the shared token."""
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    tok = secrets.token_urlsafe(24)
    TOKEN_FILE.write_text(tok + "\n")
    os.chmod(TOKEN_FILE, 0o600)
    return tok


TOKEN = load_token()


def load_history():
    """Load history from disk."""
    global history
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        history.append(json.loads(line))
        except Exception:
            pass


def save_history_entry(entry: dict):
    """Append a history entry to disk."""
    try:
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def publish(payload: dict):
    """Publish a message to all subscribers (SSE)."""
    # Convert to the format the app expects (title, body, id, ts, session)
    app_payload = {
        "title": payload.get("title", "hopes-bot"),
        "body": payload.get("text", payload.get("body", "")),
        "id": payload.get("id", int(time.time() * 1000)),
        "ts": payload.get("ts", time.time()),
        "session": payload.get("session", "main"),
    }
    # Preserve any extra fields (e.g., type, photo, command)
    for key in payload:
        if key not in app_payload:
            app_payload[key] = payload[key]
    
    with _lock:
        history.append(app_payload)
        for q in subs:
            try:
                q.put(app_payload)
            except Exception:
                pass
    # Also save to history
    save_history_entry(app_payload)


def broadcast(payload: dict):
    """Transient SSE event; never persisted to history."""
    with _lock:
        for q in subs:
            try:
                q.put(payload)
            except Exception:
                pass


# --- Fake Telegram objects (to capture responses) ---

class FakeMessage:
    """Fake Telegram message that captures responses instead of sending to Telegram."""
    
    def __init__(self, publish_fn):
        self._publish = publish_fn
        self.chat_id = "hopes_app"
    
    async def reply_text(self, text, **kwargs):
        self._publish({"type": "text", "text": text, "ts": time.time()})
    
    async def reply_photo(self, photo, caption=None, **kwargs):
        # photo is a file object or path
        if hasattr(photo, 'name'):
            photo_ref = photo.name
        elif isinstance(photo, (str, Path)):
            photo_ref = str(photo)
        else:
            photo_ref = "unknown"
        self._publish({"type": "photo", "photo": photo_ref, "caption": caption, "ts": time.time()})
    
    async def reply_video(self, video, caption=None, **kwargs):
        if hasattr(video, 'name'):
            video_ref = video.name
        elif isinstance(video, (str, Path)):
            video_ref = str(video)
        else:
            video_ref = "unknown"
        self._publish({"type": "video", "video": video_ref, "caption": caption, "ts": time.time()})
    
    async def reply_document(self, document, caption=None, **kwargs):
        if hasattr(document, 'name'):
            doc_ref = document.name
        elif isinstance(document, (str, Path)):
            doc_ref = str(document)
        else:
            doc_ref = "unknown"
        self._publish({"type": "document", "document": doc_ref, "caption": caption, "ts": time.time()})


class FakeUpdate:
    """Fake Telegram update that captures responses."""
    
    def __init__(self, publish_fn):
        self.message = FakeMessage(publish_fn)
        # Use the actual admin ID from Config (so @restricted decorator passes)
        try:
            from config import Config
            admin_id = str(Config.ADMIN_TELEGRAM_ID)
        except Exception:
            admin_id = "6834628238"
        self.effective_chat = type("FakeChat", (), {"id": "hopes_app", "type": "private"})()
        self.effective_user = type("FakeUser", (), {"id": admin_id, "first_name": "Cory", "username": "cory"})()


class FakeBot:
    """Fake Telegram bot for send_chat_action, etc."""
    
    async def send_chat_action(self, chat_id, action):
        pass  # no-op
    
    async def send_message(self, chat_id, text, **kwargs):
        pass  # no-op


class FakeContext:
    """Fake Telegram context with args + bot."""
    
    def __init__(self, args: list, bot=None):
        self.args = args
        self.bot = bot or FakeBot()
        self.job_queue = None
        self.job = None


# --- Command dispatcher ---

# Telegram bot instance (set when the server starts)
_tg_bot = None


def set_telegram_bot(tg_bot):
    """Set the Telegram bot instance (called when the server starts)."""
    global _tg_bot
    _tg_bot = tg_bot


def dispatch_command(command: str) -> list:
    """
    Dispatch a command to the Telegram bot's command handler.
    
    Args:
        command: The command string (e.g., "/draft <topic>").
    
    Returns:
        List of response payloads (captured from the fake update).
    """
    if not _tg_bot:
        return [{"type": "text", "text": "⚠️ Telegram bot not initialized.", "ts": time.time()}]
    
    # Parse the command
    parts = command.strip().split(maxsplit=1)
    cmd_name = parts[0].lstrip("/") if parts else ""
    args = parts[1].split() if len(parts) > 1 else []
    
    # Map command name to handler method
    handler_map = {
        "draft": "draft_post_cmd",
        "confirm": "confirm_post",
        "post": "post_immediate",
        "force_post": "force_post_direct",
        "regen_img": "regen_img_cmd",
        "cancel": "cancel_draft_cmd",
        "video": "generate_video",
        "confirm_video": "confirm_video_cmd",
        "reroll_video": "reroll_video_cmd",
        "edit_video": "edit_video_cmd",
        "cancel_video": "cancel_video_cmd",
        "schedule": "schedule_topic_cmd",
        "schedule_day": "schedule_day_cmd",
        "upcoming": "upcoming_cmd",
        "unschedule": "unschedule_cmd",
        "clear_day": "clear_day_cmd",
        "themes": "themes_cmd",
        "theme_day": "theme_day_cmd",
        "theme_week": "theme_week_cmd",
        "confirm_theme": "confirm_theme_cmd",
        "cancel_theme": "cancel_theme_cmd",
        "research": "search_research",
        "news": "search_news",
        "affiliate": "search_affiliate",
        "status": "get_status",
        "debug": "get_debug_log",
        "test_uplink": "test_uplink",
        "sync": "trigger_sync",
        "fix_git": "repair_git",
        "pulse": "get_pulse",
        "check": "trigger_check",
        "index": "rebuild_index_cmd",
        "help": "help_cmd",
        "clear": "clear_memory",
        "start": "start",
    }
    
    method_name = handler_map.get(cmd_name)
    if not method_name:
        # If it's not a known command, treat it as chat
        return [{"type": "text", "text": f"⚠️ Unknown command: /{cmd_name}. Use /help for a list.", "ts": time.time()}]
    
    handler = getattr(_tg_bot, method_name, None)
    if not handler:
        return [{"type": "text", "text": f"⚠️ Handler not found: {method_name}", "ts": time.time()}]
    
    # Create fake update + context
    responses = []
    
    def publish_fn(payload):
        # Convert to the format the app expects (title, body, id, ts, session)
        app_payload = {
            "title": payload.get("title", "hopes-bot"),
            "body": payload.get("text", payload.get("body", "")),
            "id": payload.get("id", int(time.time() * 1000)),
            "ts": payload.get("ts", time.time()),
            "session": payload.get("session", "main"),
        }
        # Preserve any extra fields (e.g., type, photo, command)
        for key in payload:
            if key not in app_payload:
                app_payload[key] = payload[key]
        
        responses.append(app_payload)
        # Also broadcast to SSE subscribers in real-time
        broadcast(app_payload)
    
    update = FakeUpdate(publish_fn)
    context = FakeContext(args)
    
    # Call the handler (async)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handler(update, context))
        loop.close()
    except Exception as e:
        responses.append({"type": "text", "text": f"⚠️ Error: {str(e)}", "ts": time.time()})
    
    return responses


# --- HTTP Handler ---

class HopesHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # quiet
    
    def _token_ok(self) -> bool:
        """Check token auth (query param)."""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        token = qs.get("token", [""])[0]
        return token == TOKEN
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/sub":
            if not self._token_ok():
                self.send_error(401, "Unauthorized")
                return
            self._handle_sub()
        elif path == "/history":
            if not self._token_ok():
                self.send_error(401, "Unauthorized")
                return
            self._handle_history()
        elif path == "/health":
            # Health check (no auth)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "port": PORT}).encode())
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/command":
            if not self._token_ok():
                self.send_error(401, "Unauthorized")
                return
            self._handle_command()
        elif path == "/pub":
            if not self._token_ok():
                self.send_error(401, "Unauthorized")
                return
            self._handle_pub()
        else:
            self.send_error(404, "Not Found")
    
    def _handle_sub(self):
        """SSE stream: replays last N messages, then live."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        
        # Create a queue for this subscriber
        q = queue.Queue()
        with _lock:
            subs.append(q)
        
        try:
            # Replay last 50 messages (with event name "replay")
            for entry in history[-50:]:
                data = json.dumps(entry)
                self.wfile.write(f"event: replay\ndata: {data}\n\n".encode())
                self.wfile.flush()
            
            # Live stream
            last_ping = time.time()
            while True:
                try:
                    payload = q.get(timeout=25)
                    data = json.dumps(payload)
                    self.wfile.write(f"event: message\ndata: {data}\n\n".encode())
                    self.wfile.flush()
                    last_ping = time.time()
                except queue.Empty:
                    if time.time() - last_ping >= 25:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                        last_ping = time.time()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _lock:
                if q in subs:
                    subs.remove(q)
    
    def _handle_history(self):
        """Return history of commands + responses."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(history[-100:]).encode())
    
    def _handle_command(self):
        """Receive a command, dispatch it, capture responses."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else ""
        
        if not body:
            self.send_error(400, "Empty command")
            return
        
        # Save the command to history
        command_entry = {"type": "command", "command": body, "ts": time.time()}
        with _lock:
            history.append(command_entry)
        save_history_entry(command_entry)
        
        # Dispatch the command
        responses = dispatch_command(body)
        
        # Save the responses to history
        for r in responses:
            with _lock:
                history.append(r)
            save_history_entry(r)
        
        # Send back the responses
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"responses": responses}).encode())
    
    def _handle_pub(self):
        """Publish a message (server->client)."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else ""
        
        if not body:
            self.send_error(400, "Empty message")
            return
        
        publish({"type": "text", "text": body, "ts": time.time()})
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())


def start_server():
    """Start the Hopes Bot server (in a separate thread)."""
    load_history()
    
    server = ThreadingHTTPServer((HOST, PORT), HopesHandler)
    
    def run():
        print(f"[HOPES_SERVER] Started on {HOST}:{PORT} (token: {TOKEN[:8]}...)")
        server.serve_forever()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print(f"[HOPES_SERVER] Thread started (PID {os.getpid()})")
    return server


if __name__ == "__main__":
    # Standalone mode (for testing)
    load_history()
    server = ThreadingHTTPServer((HOST, PORT), HopesHandler)
    print(f"[HOPES_SERVER] Standalone mode on {HOST}:{PORT}")
    server.serve_forever()

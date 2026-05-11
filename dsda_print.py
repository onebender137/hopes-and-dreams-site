"""
dsda_print.py — Tag-aware print wrapper that double-publishes to the DSDA bus.

Drop-in replacement for `print()` in DSDA bots. Behavior:
  1. Still prints to stdout EXACTLY like the built-in print(). Zero visible change.
  2. Also publishes to the DSDA event bus (Postgres on beast via Tailscale).

Tag parsing:
  Looks for [TAG] or "EXECUTIVE EXECUTION ERROR" style prefixes and routes
  to the appropriate severity. Falls back to P3 (silent) if no tag detected.

Usage:
  from dsda_print import dsda_print as print  # alias-import to shadow built-in
  # ...or use it explicitly:
  from dsda_print import dsda_print
  dsda_print(f"[BRAINSTORM] generated topic: {topic}")
  dsda_print(f"EXECUTIVE EXECUTION CRITICAL FAILURE: {e}")

Failures in the bus layer are SILENTLY swallowed — your bot never crashes
because the CEO bus is down. The local print() always happens first.
"""

import re
import sys
from datetime import datetime, timezone

# Import the bus library. If it's not available, dsda_print degrades
# gracefully to a plain print() so the calling bot never breaks.
try:
    from dsda_bus import log_event
    _BUS_AVAILABLE = True
except Exception as _bus_import_err:
    _BUS_AVAILABLE = False
    _bus_import_error_msg = str(_bus_import_err)


# --- Tag → (severity, category) mapping ----------------------------------
#
# Rules of thumb:
#   P0 = wake Bender up (critical failure, money risk, public breakage)
#   P1 = morning digest (errors, retries, content flagged)
#   P2 = weekly report (trends, noise)
#   P3 = silent (verbose dev info)

# Exact-phrase matches checked first (highest priority)
PHRASE_RULES = [
    # (substring to match in lower-case, severity, category)
    ("critical failure",         "P0", "critical"),
    ("execution error",          "P1", "error"),
    ("api call failed",          "P1", "error"),
    ("posted successfully",      "P1", "post_success"),
    ("transmission uplink",      "P2", "uplink"),
    ("masterclass posted",       "P1", "post_success"),
]

# Bracket tag → (severity, category)
TAG_RULES = {
    "SANITIZER":     ("P2", "sanitizer"),
    "THEME":         ("P3", "theme"),
    "COOLDOWN":      ("P3", "cooldown"),
    "CHAT MEMORY":   ("P3", "chat_memory"),
    "BRAINSTORM":    ("P2", "brainstorm"),
    "DATA LAYER":    ("P1", "data_layer"),
    "HEARTBEAT":     ("heartbeat", "alive"),
}

# Default bot identifier — override per-call if needed.
DEFAULT_BOT_ID = "hopes_bot"

_TAG_RE = re.compile(r"\[([A-Z][A-Z _]+)\]")


def _classify(msg: str):
    """Return (severity, category) tuple for a given message."""
    lower = msg.lower()

    # Phrase rules win — check first.
    for needle, sev, cat in PHRASE_RULES:
        if needle in lower:
            return sev, cat

    # Then bracket tags.
    m = _TAG_RE.search(msg)
    if m:
        tag = m.group(1).strip()
        if tag in TAG_RULES:
            return TAG_RULES[tag]
        # Unknown tag — log it as P3 with the tag as category.
        return "P3", tag.lower().replace(" ", "_")

    # No tag, no phrase → P3 silent.
    return "P3", "uncategorized"


def dsda_print(*args, sep=" ", end="\n", file=None, flush=False,
               bot_id=None, severity=None, category=None, payload_extra=None):
    """
    Print as normal, then publish to the DSDA bus.

    Extra kwargs for explicit control:
        bot_id        — override DEFAULT_BOT_ID
        severity      — force severity (P0/P1/P2/P3/heartbeat)
        category      — force category
        payload_extra — dict merged into the bus payload
    """
    # 1. Always print to stdout first (so visibility is never lost)
    msg = sep.join(str(a) for a in args)
    print(msg, end=end, file=file or sys.stdout, flush=flush)

    # 2. Try to publish to the bus. Never raise.
    if not _BUS_AVAILABLE:
        return

    try:
        sev, cat = _classify(msg)
        if severity:
            sev = severity
        if category:
            cat = category

        payload = {"message": msg.strip()}
        if payload_extra:
            payload.update(payload_extra)

        log_event(
            bot_id or DEFAULT_BOT_ID,
            sev,
            cat,
            payload,
            raise_on_error=False,
        )
    except Exception:
        # Absolute last-resort safety net. Bus problems must never break the bot.
        pass


# --- Heartbeat helper ----------------------------------------------------

def heartbeat(bot_id=None):
    """One-line heartbeat call for the scheduler. Safe to call always."""
    if not _BUS_AVAILABLE:
        return
    try:
        log_event(
            bot_id or DEFAULT_BOT_ID,
            "heartbeat",
            "alive",
            {"ts": datetime.now(timezone.utc).isoformat()},
            raise_on_error=False,
        )
    except Exception:
        pass


# --- CLI self-test -------------------------------------------------------

if __name__ == "__main__":
    print("dsda_print self-test")
    print(f"  Bus available: {_BUS_AVAILABLE}")
    if not _BUS_AVAILABLE:
        print(f"  Reason: {_bus_import_error_msg}")
        sys.exit(1)

    test_lines = [
        "[BRAINSTORM] LLM generated 3 candidate topics",
        "[SANITIZER] REJECTED — topic too long",
        "EXECUTIVE EXECUTION CRITICAL FAILURE: simulated test crash",
        "Syndicate Masterclass posted successfully at test time!",
        "[COOLDOWN] 'magnesium' in same cluster — blocking.",
        "random uncategorized log line",
    ]
    for line in test_lines:
        sev, cat = _classify(line)
        print(f"  [{sev:9s} {cat:18s}] would log: {line}")
        dsda_print(line, bot_id="dsda_print_test")
    print("  ✓ Self-test complete. Check events table.")
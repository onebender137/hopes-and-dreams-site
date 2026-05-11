"""
dsda_bus.py — DSDA Empire Event Bus

The single library every bot in the DSDA empire imports to report status,
errors, heartbeats, and events to the central Postgres database on the beast.

Connection is over Tailscale mesh, TLS-encrypted, password-authenticated.

Usage:
    from dsda_bus import log_event, heartbeat

    # Severity tiers: P0 (pager), P1 (daily), P2 (weekly), P3 (silent)
    log_event("hopes_researcher", "P1", "post", {"title": "...", "url": "..."})
    log_event("clamps_main", "P0", "error", {"error": "API timeout", "retry": 3})

    # Heartbeat — call every ~5 minutes from each bot
    heartbeat("hopes_researcher")

Configuration:
    Set environment variables (or edit DEFAULTS below):
        DSDA_DB_HOST     — Tailscale IP of the beast (default: 100.95.48.7)
        DSDA_DB_NAME     — database name (default: dsda)
        DSDA_DB_USER     — username (default: dsda_bus)
        DSDA_DB_PASSWORD — password (REQUIRED, no default)
"""

import os
import json
import logging
from datetime import datetime, timezone
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import Json

# --- Config ---------------------------------------------------------------

DEFAULTS = {
    "host": "100.95.48.7",
    "dbname": "dsda",
    "user": "dsda_bus",
    "port": 5432,
}

def _get_config():
    return {
        "host": os.environ.get("DSDA_DB_HOST", DEFAULTS["host"]),
        "dbname": os.environ.get("DSDA_DB_NAME", DEFAULTS["dbname"]),
        "user": os.environ.get("DSDA_DB_USER", DEFAULTS["user"]),
        "password": os.environ.get("DSDA_DB_PASSWORD"),
        "port": int(os.environ.get("DSDA_DB_PORT", DEFAULTS["port"])),
        "connect_timeout": 5,
        "sslmode": "require",
    }

VALID_SEVERITIES = {"P0", "P1", "P2", "P3", "heartbeat"}

# --- Internal logger (so bus failures don't crash the calling bot) -------

_logger = logging.getLogger("dsda_bus")
if not _logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[dsda_bus] %(levelname)s: %(message)s"))
    _logger.addHandler(_h)
    _logger.setLevel(logging.WARNING)

# --- Connection helper ---------------------------------------------------

@contextmanager
def _connect():
    """Open a short-lived connection. Auto-closes on exit/error."""
    cfg = _get_config()
    if not cfg["password"]:
        raise RuntimeError(
            "DSDA_DB_PASSWORD not set. Export it before running the bot."
        )
    conn = psycopg2.connect(**cfg)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# --- Public API -----------------------------------------------------------

def log_event(bot_id, severity, category, payload=None, raise_on_error=False):
    """
    Log an event to the DSDA bus.

    Args:
        bot_id (str): Identifier for the bot (e.g. "hopes_researcher", "clamps_main").
        severity (str): One of P0, P1, P2, P3, heartbeat.
        category (str): Free-form tag (e.g. "post", "error", "trade", "alive").
        payload (dict|None): Arbitrary JSON-serializable data.
        raise_on_error (bool): If True, exceptions propagate. If False (default),
                               failures are logged and swallowed so the bot
                               keeps running even if the bus is down.

    Returns:
        bool: True if logged, False if failed (when raise_on_error=False).
    """
    if severity not in VALID_SEVERITIES:
        msg = f"Invalid severity {severity!r}. Must be one of {VALID_SEVERITIES}."
        if raise_on_error:
            raise ValueError(msg)
        _logger.error(msg)
        return False

    payload = payload or {}

    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO events (bot_id, severity, category, payload)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (bot_id, severity, category, Json(payload)),
                )
        return True
    except Exception as e:
        if raise_on_error:
            raise
        _logger.warning(f"Failed to log event ({bot_id}/{severity}/{category}): {e}")
        return False


def heartbeat(bot_id):
    """Convenience: log a heartbeat. Call every ~5 minutes from each bot."""
    return log_event(bot_id, "heartbeat", "alive", {"ts": datetime.now(timezone.utc).isoformat()})


# --- CLI test mode --------------------------------------------------------

if __name__ == "__main__":
    """
    Run `python dsda_bus.py` to send a test event and verify connectivity.
    """
    import sys
    print("DSDA bus — connectivity test")
    print(f"  Host: {_get_config()['host']}")
    print(f"  User: {_get_config()['user']}")

    if not _get_config()["password"]:
        print("  ERROR: DSDA_DB_PASSWORD env var not set.")
        sys.exit(1)

    ok = log_event(
        "dsda_bus_test",
        "P3",
        "test",
        {"message": "connectivity check from " + os.uname().nodename if hasattr(os, "uname") else "unknown"},
        raise_on_error=True,
    )
    if ok:
        print("  ✓ Test event written successfully.")
    else:
        print("  ✗ Test event failed.")
        sys.exit(1)

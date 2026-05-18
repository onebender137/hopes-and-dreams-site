"""Add empire_stats.json emitter to hopes_bot.
- New method: _write_empire_stats_json (writes + commits + pushes)
- New scheduled job: every 15min in existing APScheduler
Idempotent: aborts if already patched."""
from pathlib import Path
import sys

src = Path("bot.py")
content = src.read_text(encoding="utf-8")
original = content

if "_write_empire_stats_json" in content:
    print("❌ Already patched. Aborting.")
    sys.exit(1)

# --- EDIT 1: Inject the new method before _git_push_changes ---
ANCHOR_1 = "    def _git_push_changes(self, commit_message):"
METHOD = '''    def _write_empire_stats_json(self):
        """Write public empire_stats.json from DSDA bus telemetry, then commit + push."""
        import json
        from datetime import datetime, timezone, timedelta
        from pathlib import Path as _Path

        try:
            from dsda_bus import get_last_heartbeats, get_event_counts_since
        except Exception:
            return False

        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        try:
            heartbeats = get_last_heartbeats()
        except Exception:
            heartbeats = {}

        def _age_sec(t):
            if t is None:
                return 999999
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            return (now - t).total_seconds()

        active_bots = sum(1 for v in heartbeats.values() if _age_sec(v) < 600)

        try:
            counts_7d = get_event_counts_since(seven_days_ago)
        except Exception:
            counts_7d = {}

        bus_events_total = sum(counts_7d.values()) if counts_7d else 0
        heartbeat_events = sum(v for (b, s), v in counts_7d.items() if s == "heartbeat") if counts_7d else 0
        expected = len(heartbeats) * 2016 if heartbeats else 0
        integrity = round(min(100.0, (heartbeat_events / expected * 100) if expected else 0), 1)

        try:
            articles_7d = sum(
                1 for f in _Path("articles").glob("*.html")
                if f.name != "template.html" and (now.timestamp() - f.stat().st_mtime) < 604800
            )
        except Exception:
            articles_7d = 0

        stats = {
            "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "empire": {
                "articles_published_7d": articles_7d,
                "bus_events_total_7d": bus_events_total,
                "active_bots": active_bots,
                "heartbeat_integrity_pct": integrity
            },
            "next_update_in_minutes": 15
        }

        try:
            with open("empire_stats.json", "w") as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"[empire_stats] write failed: {e}")
            return False

        try:
            self._git_push_changes("data: update empire_stats.json")
        except Exception as e:
            print(f"[empire_stats] git push failed: {e}")
            return False
        return True

'''
assert content.count(ANCHOR_1) == 1, "ANCHOR_1 (def _git_push_changes) not unique"
content = content.replace(ANCHOR_1, METHOD + ANCHOR_1, 1)

# --- EDIT 2: Add scheduler job after the DSDA heartbeat job ---
# Find the DSDA heartbeat block and inject after it
ANCHOR_2 = "# DSDA bus heartbeat — every 5 minutes"
if ANCHOR_2 not in content:
    print(f"⚠️  Anchor 2 ({ANCHOR_2!r}) not found verbatim — inspecting variations")
    sys.exit(1)

# Find the location of the DSDA heartbeat scheduler.add_job block
idx_anchor = content.find(ANCHOR_2)
# Find the next "scheduler.add_job(" after that
idx_addjob = content.find("scheduler.add_job(", idx_anchor)
if idx_addjob < 0:
    print("⚠️  Could not find scheduler.add_job after DSDA heartbeat anchor")
    sys.exit(1)

# Find the closing ) of that add_job call - walk parens
depth = 0
i = idx_addjob
while i < len(content):
    c = content[i]
    if c == "(":
        depth += 1
    elif c == ")":
        depth -= 1
        if depth == 0:
            i += 1
            break
    i += 1

# i now points to char after the closing paren of DSDA heartbeat add_job
EMPIRE_JOB = '''

    # Empire stats JSON — every 15 minutes (public telemetry for intel.html vitals widget)
    from datetime import timedelta as _td
    scheduler.add_job(
        hopes_and_dreams_bot._write_empire_stats_json,
        "interval",
        minutes=15,
        next_run_time=datetime.now() + _td(seconds=30),
        id="empire_stats_writer",
        misfire_grace_time=300,
        replace_existing=True
    )'''

content = content[:i] + EMPIRE_JOB + content[i:]

backup = Path("bot.py.bak-before-empirestats-20260517")
backup.write_text(original, encoding="utf-8")
src.write_text(content, encoding="utf-8")

print(f"PATCH APPLIED")
print(f"  Backup: {backup.name}")
print(f"  Old: {len(original)} bytes")
print(f"  New: {len(content)} bytes")
print(f"  Delta: +{len(content) - len(original)}")

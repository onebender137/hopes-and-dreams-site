#!/usr/bin/env python3
"""event_watcher.py — hourly watcher for the empire event layer.

Pulls the newest `new` + `article_worthy=1` event, rate-limits to
max 1 event-article/day, and routes by section:
  - sovereign -> sovereign_writer.py <event_id>  (publish to tech/)
  - syndicate -> insert into scheduled_topics for the next open slot

Idempotent: a second run the same hour is a no-op (the event's status
has already moved off `new`).
"""
import sqlite3, datetime, os, subprocess, sys

SITE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(SITE, "syndicate_memory.db")
SLOTS = ["07:00", "12:00", "15:00"]
VENV_PY = sys.executable  # use the running interpreter (system python has markdown)


def find_next_open_slot(c, now):
    """Earliest (date, slot) in the future with no scheduled topic yet.
    Looks up to a week ahead. Returns (date, slot) or (None, None)."""
    for day_offset in range(0, 8):
        d = (now + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for slot in SLOTS:
            slot_dt = datetime.datetime.strptime(f"{d} {slot}", "%Y-%m-%d %H:%M")
            if slot_dt <= now:
                continue  # slot already passed
            sched = c.execute(
                "SELECT COUNT(*) FROM scheduled_topics WHERE scheduled_date=? AND slot=?",
                (d, slot)).fetchone()[0]
            if sched == 0:
                return d, slot
    return None, None


def main():
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    c = sqlite3.connect(DB)
    try:
        # 1. Newest new + worthy event (FIFO by ts)
        row = c.execute(
            "SELECT id, title, summary, tags, section FROM empire_events "
            "WHERE status='new' AND article_worthy=1 ORDER BY ts ASC LIMIT 1").fetchone()
        if not row:
            print("no new worthy events")
            return
        eid, title, summary, tags, section = row

        # 2. Rate limit: max 1 event-article/day
        today_count = c.execute(
            "SELECT COUNT(*) FROM empire_events WHERE date=? AND status IN ('written','queued')",
            (date,)).fetchone()[0]
        if today_count >= 1:
            print(f"rate limit: {today_count} event-article(s) today; leaving {eid} new")
            return

        # 3. Route by section
        if section == "sovereign":
            r = subprocess.run(
                [VENV_PY, os.path.join(SITE, "sovereign_writer.py"), str(eid)],
                capture_output=True, text=True, timeout=900)
            print(r.stdout)
            if r.returncode != 0:
                print(f"sovereign_writer failed (rc={r.returncode}): {r.stderr}")
                return
            href = ""
            for line in r.stdout.splitlines():
                if line.startswith("HREF:"):
                    href = line.split("HREF:", 1)[1].strip()
            c.execute("UPDATE empire_events SET status='written', article_href=? WHERE id=?",
                      (href, eid))
            c.commit()
            print(f"event {eid} written, href={href}")
        else:  # syndicate
            d, slot = find_next_open_slot(c, now)
            if not slot:
                print(f"no open slot within a week; leaving {eid} new")
                return
            c.execute(
                "INSERT OR IGNORE INTO scheduled_topics (scheduled_date, slot, topic, status) "
                "VALUES (?,?,?, 'pending')", (d, slot, title))
            c.execute("UPDATE empire_events SET status='queued' WHERE id=?", (eid,))
            c.commit()
            print(f"event {eid} queued for {d} {slot}: {title}")
    finally:
        c.close()


if __name__ == "__main__":
    main()

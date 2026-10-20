#!/usr/bin/env python3
"""log_event.py — log an empire event to the event layer.

Danny calls this over SSH when he finishes something significant.
Idempotent on (ts, title) — re-running the same call is a no-op.

    python3 log_event.py \
      --title "Debloated the Fire TV, built a custom remote" \
      --summary "Ran dumbtv on the AFTTI43, fixed the DNS-filter VPN, ..." \
      --tags build,infra \
      --section sovereign \
      --worthy 1
"""
import argparse, sqlite3, datetime, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "syndicate_memory.db")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--tags", default="")
    ap.add_argument("--section", default="syndicate", choices=["syndicate", "sovereign"])
    ap.add_argument("--source", default="danny", choices=["danny", "git", "chat"])
    ap.add_argument("--worthy", type=int, default=1, choices=[0, 1])
    args = ap.parse_args()

    now = datetime.datetime.now()
    ts = now.isoformat()
    date = now.strftime("%Y-%m-%d")
    c = sqlite3.connect(DB)
    try:
        cur = c.execute("SELECT id FROM empire_events WHERE title=?", (args.title,))
        if cur.fetchone():
            print(f"already logged (idempotent no-op): {args.title}")
            return
        c.execute(
            "INSERT INTO empire_events (ts, date, title, summary, tags, section, source, article_worthy, status) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (ts, date, args.title, args.summary, args.tags, args.section, args.source, args.worthy, "new"))
        c.commit()
        new_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"logged event {new_id}: {args.title} (section={args.section}, worthy={args.worthy})")
    finally:
        c.close()


if __name__ == "__main__":
    main()

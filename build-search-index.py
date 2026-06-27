#!/usr/bin/env python3
"""
build-search-index.py  —  Syndicate Intel Search index builder
Dream Syndicate Digital Assets // hopes-and-dreams.ca

Reads transmissions.json (the authoritative published list) and, for every entry,
pulls the article body text out of its HTML, producing search-index.json:

    [ { "href": ..., "title": ..., "date": ..., "body": "<stripped article text>" }, ... ]

intel-search.js lazy-loads this file the first time someone focuses the search box,
so the page stays light and only searchers pay the download.

RUN from the repo root in your deploy/seal step, BEFORE `git push`:
    python3 build-search-index.py

Zero dependencies (stdlib only). Idempotent — safe to run every publish.
"""
import json, os, re, sys
from html import unescape

SRC = "transmissions.json"
OUT = "search-index.json"
BODY_CAP = 7000  # max chars of body text per article (safety bound; most are smaller)

# article body lives inside <article class="article-container"> ... </article>
ARTICLE_RE = re.compile(
    r'<article[^>]*class="[^"]*article-container[^"]*"[^>]*>(.*?)</article>',
    re.S | re.I,
)
# stop before related-links / nav / newsletter boilerplate if it sits inside the article
CUT_RE = re.compile(r'<[^>]*class="[^"]*(?:article-nav|related|newsletter|share)[^"]*"', re.I)
SCRIPT_STYLE_RE = re.compile(r'<(script|style)\b.*?</\1>', re.S | re.I)
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'\s+')


def extract_body(html_text):
    m = ARTICLE_RE.search(html_text)
    inner = m.group(1) if m else html_text
    cut = CUT_RE.search(inner)
    if cut:
        inner = inner[:cut.start()]
    inner = SCRIPT_STYLE_RE.sub(' ', inner)
    text = TAG_RE.sub(' ', inner)
    text = unescape(text)
    text = WS_RE.sub(' ', text).strip()
    return text[:BODY_CAP]


def main():
    if not os.path.exists(SRC):
        sys.exit(f"ERROR: {SRC} not found. Run from the repo root.")
    entries = json.load(open(SRC, encoding="utf-8"))

    out, missing, empty = [], 0, 0
    for e in entries:
        href = (e.get("href") or "").strip()
        title = (e.get("title") or "").strip()
        date = (e.get("date") or "").strip()
        if not href or not title:
            continue
        body = ""
        if os.path.exists(href):
            try:
                body = extract_body(open(href, encoding="utf-8").read())
            except Exception as ex:
                print(f"  warn: {href}: {ex}", file=sys.stderr)
        else:
            missing += 1
        if not body:
            empty += 1
        out.append({"href": href, "title": title, "date": date, "body": body})

    # compact JSON (no spaces) to keep the file small
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(OUT)
    print(f"{OUT}: {len(out)} entries, {size/1024:.0f} KB "
          f"(~{size*0.32/1024:.0f} KB gzipped over the wire)")
    if missing:
        print(f"  note: {missing} article file(s) referenced in {SRC} not found on disk")
    if empty:
        print(f"  note: {empty} entr(y/ies) ended up with empty body text")


if __name__ == "__main__":
    main()

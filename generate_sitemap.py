#!/usr/bin/env python3
"""
generate_sitemap.py  —  Build sitemap.xml for hopes-and-dreams.ca

Scans articles/*.html and a fixed list of core pages, emits a valid
sitemaps.org 0.9 sitemap. Idempotent: run any time, it overwrites sitemap.xml.

lastmod sources (most-accurate-available, no lying about freshness):
  - articles : the YYYY-MM-DD date embedded in the filename (the publish date).
               Falls back to git last-commit date, then file mtime.
  - core     : git last-commit date (accurate even on a fresh checkout).
               Falls back to file mtime, then today.

The XML is parse-validated before anything is written to disk, so a malformed
sitemap can never overwrite a good one.

Place this at the repo root and run:  python3 generate_sitemap.py
Stretch: have the Hopes bot call it right after it publishes an article.
"""

import os
import re
import sys
import subprocess
import datetime
import xml.etree.ElementTree as ET

BASE = "https://hopes-and-dreams.ca"
ROOT = os.path.dirname(os.path.abspath(__file__))      # script lives at repo root
ARTICLES_DIR = os.path.join(ROOT, "articles")
OUT = os.path.join(ROOT, "sitemap.xml")

# Explicit allow-list. Utility pages (404, template, hotspot-dev, google-verify)
# are intentionally absent so they never get sitemapped.
CORE_PAGES = [
    ("/",                  "1.0"),
    ("/cipher.html",       "0.9"),
    ("/shop.html",         "0.8"),
    ("/optimization.html", "0.8"),
    ("/intel.html",        "0.8"),
    ("/about.html",        "0.7"),
    ("/privacy.html",      "0.5"),
    ("/alpha-gpc-uridine-stack.html", "0.8"),
]
ARTICLE_PRIORITY = "0.6"

TODAY = datetime.date.today().isoformat()
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def git_date(abspath):
    """Last commit date (YYYY-MM-DD) for a file, or None if unavailable."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", abspath],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        d = out.stdout.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            return d
    except Exception:
        pass
    return None


def mtime_date(abspath):
    try:
        return datetime.date.fromtimestamp(os.path.getmtime(abspath)).isoformat()
    except OSError:
        return TODAY


def core_lastmod(path):
    full = os.path.join(ROOT, "index.html" if path == "/" else path.lstrip("/"))
    return git_date(full) or mtime_date(full)


def article_lastmod(abspath, fname):
    m = DATE_RE.match(fname)
    if m:
        try:
            datetime.date.fromisoformat(m.group(1))
            return m.group(1)
        except ValueError:
            pass
    return git_date(abspath) or mtime_date(abspath)


def build_tree():
    ET.register_namespace("", NS)
    urlset = ET.Element(f"{{{NS}}}urlset")

    def add(loc, lastmod, priority):
        u = ET.SubElement(urlset, f"{{{NS}}}url")
        ET.SubElement(u, f"{{{NS}}}loc").text = loc
        ET.SubElement(u, f"{{{NS}}}lastmod").text = lastmod
        ET.SubElement(u, f"{{{NS}}}priority").text = priority

    for path, pri in CORE_PAGES:
        add(BASE + path, core_lastmod(path), pri)

    articles = []
    if os.path.isdir(ARTICLES_DIR):
        for f in os.listdir(ARTICLES_DIR):
            if f.endswith(".html"):
                articles.append(f)
    articles.sort(reverse=True)   # date-prefixed -> newest first
    for f in articles:
        add(f"{BASE}/articles/{f}", article_lastmod(os.path.join(ARTICLES_DIR, f), f), ARTICLE_PRIORITY)

    return urlset, len(CORE_PAGES), len(articles)


def main():
    urlset, n_core, n_art = build_tree()
    ET.indent(urlset, space="  ")
    body = ET.tostring(urlset, encoding="unicode")
    doc = '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"

    # Validate before writing — a broken sitemap must never clobber a good one.
    try:
        ET.fromstring(doc)
    except ET.ParseError as e:
        sys.exit(f"ABORT: generated XML failed to parse ({e}). sitemap.xml untouched.")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)

    print(f"sitemap.xml written -> {OUT}")
    print(f"  {n_core + n_art} URLs total  ({n_core} core + {n_art} articles)")


if __name__ == "__main__":
    main()

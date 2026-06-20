"""Patch — adds 'The Cipher' to nav (before Intel Hub) and footer (after Tools)
across every page that has the Syndicate nav/footer. Handles both root pages
(cipher.html) and article pages (../cipher.html). Idempotent: safe to re-run."""
import re
from pathlib import Path

SKIP = {"cipher.html", "template.html", "hotspot-dev.html"}

# Match the Intel Hub nav link, capturing its indentation and any ../ prefix.
NAV_RE = re.compile(
    r'(?P<indent>[ \t]*)<a (?:class="[^"]*" )?href="(?P<pre>(?:\.\./)?)intel\.html">Intel Hub</a>'
)
# Match the Tools footer link (links to optimization.html, label "Tools").
FOOT_RE = re.compile(
    r'(?P<indent>[ \t]*)<a href="(?P<pre>(?:\.\./)?)optimization\.html">Tools</a>\s*\|'
)

def slice_block(html, open_tag, close_tag):
    s = html.find(open_tag)
    if s == -1:
        return None
    e = html.find(close_tag, s)
    if e == -1:
        return None
    return s, e + len(close_tag)

def patch_nav(html):
    span = slice_block(html, "<nav>", "</nav>")
    if not span:
        return html, False
    s, e = span
    block = html[s:e]
    if "cipher.html" in block:
        return html, False
    m = NAV_RE.search(block)
    if not m:
        return html, False
    ins = f'{m.group("indent")}<a href="{m.group("pre")}cipher.html">Cipher</a>\n'
    new_block = block[:m.start()] + ins + block[m.start():]
    return html[:s] + new_block + html[e:], True

def patch_footer(html):
    span = slice_block(html, "<footer>", "</footer>")
    if not span:
        return html, False
    s, e = span
    block = html[s:e]
    if "cipher.html" in block:
        return html, False
    m = FOOT_RE.search(block)
    if not m:
        return html, False
    add = f'\n{m.group("indent")}<a href="{m.group("pre")}cipher.html">Cipher</a> |'
    new_block = block[:m.end()] + add + block[m.end():]
    return html[:s] + new_block + html[e:], True

def targets():
    files = [p for p in Path(".").glob("*.html") if p.name not in SKIP]
    files += [p for p in Path("articles").glob("*.html")] if Path("articles").is_dir() else []
    return sorted(files)

stats = {"nav": 0, "footer": 0, "files": 0}
for f in targets():
    original = f.read_text(encoding="utf-8")
    html = original
    html, n = patch_nav(html)
    html, ft = patch_footer(html)
    if html != original:
        f.write_text(html, encoding="utf-8")
        stats["files"] += 1
        stats["nav"] += int(n)
        stats["footer"] += int(ft)
        print(f"  ✅ {f}  (nav={n}, footer={ft})")

print("\n--- SUMMARY ---")
print(f"  Nav links added:    {stats['nav']}")
print(f"  Footer links added: {stats['footer']}")
print(f"  Files changed:      {stats['files']}")

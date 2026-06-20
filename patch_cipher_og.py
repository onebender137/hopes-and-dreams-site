#!/usr/bin/env python3
"""Patch — repoint cipher.html's og:image + twitter:image to cipher-og.png.
Idempotent: safe to re-run. Touches only those two meta tags in cipher.html."""
from pathlib import Path

f = Path("cipher.html")
html = f.read_text(encoding="utf-8")

OLD = 'content="https://hopes-and-dreams.ca/topper.png"'
NEW = 'content="https://hopes-and-dreams.ca/cipher-og.png"'

# Only swap within the og:image / twitter:image meta lines.
changed = 0
out = []
for line in html.splitlines(keepends=True):
    if ('og:image' in line or 'twitter:image' in line) and OLD in line:
        line = line.replace(OLD, NEW)
        changed += 1
    out.append(line)

if changed:
    f.write_text("".join(out), encoding="utf-8")
    print(f"  Repointed {changed} meta image tag(s) -> cipher-og.png")
else:
    print("  Nothing to change (already pointing at cipher-og.png).")

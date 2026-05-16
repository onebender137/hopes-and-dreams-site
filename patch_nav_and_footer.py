"""Patch nav (add Merch) and footer (upgrade to new) across template + all articles.
Idempotent: safe to re-run. Reports which files changed."""
from pathlib import Path
import sys

# --- ANCHORS ---
NAV_ANCHOR = '''            <a href="../intel.html">Intel Hub</a>
            <a href="../about.html">About</a>'''

NAV_REPLACEMENT = '''            <a href="../intel.html">Intel Hub</a>
            <a href="https://merch.hopes-and-dreams.ca" target="_blank" rel="noopener noreferrer">Merch</a>
            <a href="../about.html">About</a>'''

FOOTER_ANCHOR = '''        <footer>
            <p>&copy; 2026 Dream Syndicate Digital Assets. All Rights Reserved.</p>
        </footer>'''

FOOTER_REPLACEMENT = '''        <footer>
            <p>&copy; 2026 Dream Syndicate Digital Assets. All Rights Reserved.</p>
            <p>
                <a href="https://www.facebook.com/profile.php?id=61581034972328" target="_blank" rel="noopener noreferrer">Connect on Facebook</a> |
                <a href="https://merch.hopes-and-dreams.ca" target="_blank" rel="noopener noreferrer">Merch</a> |
                <a href="../intel.html">Intel Hub</a> |
                <a href="../optimization.html">Tools</a> |
                <a href="../privacy.html">Privacy Policy</a> |
                <a href="../about.html">Contact Us</a>
            </p>
            <p style="font-size: 0.7rem; color: var(--text-dim); margin-top: 10px;">Location: Saint John, New Brunswick, Canada</p>
        </footer>'''

# Skip these files
SKIP = {"placeholder.txt"}

# --- COLLECT TARGETS ---
articles_dir = Path("articles")
targets = []
for f in sorted(articles_dir.iterdir()):
    if f.name in SKIP:
        continue
    if f.suffix != ".html":
        continue
    targets.append(f)

print(f"Found {len(targets)} HTML files to inspect\n")

# --- PATCH ---
stats = {"nav_patched": 0, "nav_skipped": 0, "footer_patched": 0, "footer_skipped": 0, "untouched": []}

for f in targets:
    original = f.read_text(encoding="utf-8")
    content = original
    nav_changed = False
    footer_changed = False

    # Nav patch (idempotent — only patch if merch link absent in nav)
    if "merch.hopes-and-dreams.ca" not in content[:content.find("</nav>") + 10] if "</nav>" in content else False:
        if NAV_ANCHOR in content:
            content = content.replace(NAV_ANCHOR, NAV_REPLACEMENT, 1)
            nav_changed = True
            stats["nav_patched"] += 1
        else:
            stats["nav_skipped"] += 1
    else:
        stats["nav_skipped"] += 1

    # Footer patch (idempotent — only if old minimal footer present)
    if FOOTER_ANCHOR in content:
        content = content.replace(FOOTER_ANCHOR, FOOTER_REPLACEMENT, 1)
        footer_changed = True
        stats["footer_patched"] += 1
    else:
        stats["footer_skipped"] += 1

    if content != original:
        f.write_text(content, encoding="utf-8")
        flags = []
        if nav_changed: flags.append("NAV")
        if footer_changed: flags.append("FOOTER")
        print(f"  ✅ {f.name}  [{'+'.join(flags)}]")
    else:
        stats["untouched"].append(f.name)

print(f"\n--- SUMMARY ---")
print(f"  Nav patched:    {stats['nav_patched']}")
print(f"  Nav skipped:    {stats['nav_skipped']}  (already had merch or no anchor match)")
print(f"  Footer patched: {stats['footer_patched']}")
print(f"  Footer skipped: {stats['footer_skipped']}  (already upgraded or no anchor match)")
print(f"  Files untouched: {len(stats['untouched'])}")

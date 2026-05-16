"""Patch v2 — handles 2025 articles with flat indent + different footer copyright.
Idempotent: safe to re-run alongside v1."""
from pathlib import Path

# --- ANCHORS (FLAT INDENT, old branding) ---
NAV_ANCHOR_FLAT = '''<a href="../intel.html">Intel Hub</a>
<a href="../about.html">About</a>'''

NAV_REPLACEMENT_FLAT = '''<a href="../intel.html">Intel Hub</a>
<a href="https://merch.hopes-and-dreams.ca" target="_blank" rel="noopener noreferrer">Merch</a>
<a href="../about.html">About</a>'''

FOOTER_ANCHOR_FLAT = '''<footer>
<p>© 2026 Hopes and Dreams. All Rights Reserved.</p>
</footer>'''

FOOTER_REPLACEMENT_FLAT = '''<footer>
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

SKIP = {"placeholder.txt"}

articles_dir = Path("articles")
targets = [f for f in sorted(articles_dir.iterdir())
           if f.suffix == ".html" and f.name not in SKIP]

print(f"Inspecting {len(targets)} HTML files (will only touch flat-indent ones)\n")

stats = {"nav_patched": 0, "footer_patched": 0, "files_changed": 0}

for f in targets:
    original = f.read_text(encoding="utf-8")
    content = original

    if NAV_ANCHOR_FLAT in content and "merch.hopes-and-dreams.ca" not in content[:content.find("</nav>") + 10]:
        content = content.replace(NAV_ANCHOR_FLAT, NAV_REPLACEMENT_FLAT, 1)
        stats["nav_patched"] += 1

    if FOOTER_ANCHOR_FLAT in content:
        content = content.replace(FOOTER_ANCHOR_FLAT, FOOTER_REPLACEMENT_FLAT, 1)
        stats["footer_patched"] += 1

    if content != original:
        f.write_text(content, encoding="utf-8")
        stats["files_changed"] += 1
        print(f"  ✅ {f.name}")

print(f"\n--- SUMMARY ---")
print(f"  Nav patched:    {stats['nav_patched']}")
print(f"  Footer patched: {stats['footer_patched']}")
print(f"  Files changed:  {stats['files_changed']}")

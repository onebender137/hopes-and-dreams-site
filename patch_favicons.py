"""Add favicon links to all HTML files (root + articles).
Idempotent: skips files that already have favicon links."""
from pathlib import Path

FAVICON_BLOCK_ROOT = '''    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="favicon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
'''

FAVICON_BLOCK_ARTICLE = '''    <link rel="icon" type="image/x-icon" href="../favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="../favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../favicon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="../apple-touch-icon.png">
'''

# Anchor: insert AFTER first <link rel="stylesheet" ... style.css">
# Use two anchor patterns since intel.html and template.html use different style
ROOT_ANCHORS = [
    '<link href="style.css" rel="stylesheet"/>\n',
    '<link href="style.css" rel="stylesheet">\n',
    '<link rel="stylesheet" href="style.css">\n',
]

ARTICLE_ANCHORS = [
    '<link rel="stylesheet" href="../style.css">\n',
    '<link href="../style.css" rel="stylesheet"/>\n',
    '<link href="../style.css" rel="stylesheet">\n',
]

def patch_file(path: Path, block: str, anchors: list) -> str:
    """Returns 'patched', 'skipped' (already has favicon), or 'no_anchor'."""
    content = path.read_text(encoding="utf-8")
    if "favicon.ico" in content:
        return "skipped"
    for anchor in anchors:
        if anchor in content:
            new_content = content.replace(anchor, anchor + block, 1)
            path.write_text(new_content, encoding="utf-8")
            return "patched"
    return "no_anchor"

# --- ROOT FILES ---
root_files = [
    "index.html", "intel.html", "transmissions.html",
    "optimization.html", "shop.html", "about.html", "privacy.html",
]

print("=== ROOT FILES ===")
for fname in root_files:
    p = Path(fname)
    if not p.exists():
        print(f"  ⏭️  {fname} (not found)")
        continue
    result = patch_file(p, FAVICON_BLOCK_ROOT, ROOT_ANCHORS)
    icon = {"patched": "✅", "skipped": "⏭️ ", "no_anchor": "❌"}[result]
    print(f"  {icon} {fname}  [{result}]")

# --- ARTICLE FILES ---
print("\n=== ARTICLES + TEMPLATE ===")
articles_dir = Path("articles")
stats = {"patched": 0, "skipped": 0, "no_anchor": []}

for f in sorted(articles_dir.iterdir()):
    if f.suffix != ".html":
        continue
    result = patch_file(f, FAVICON_BLOCK_ARTICLE, ARTICLE_ANCHORS)
    if result == "patched":
        stats["patched"] += 1
    elif result == "skipped":
        stats["skipped"] += 1
    else:
        stats["no_anchor"].append(f.name)

print(f"  ✅ Patched:     {stats['patched']}")
print(f"  ⏭️  Skipped:     {stats['skipped']}  (already had favicon)")
print(f"  ❌ No anchor:  {len(stats['no_anchor'])}")
if stats["no_anchor"]:
    print(f"     Files needing manual review:")
    for n in stats["no_anchor"][:5]:
        print(f"       - {n}")

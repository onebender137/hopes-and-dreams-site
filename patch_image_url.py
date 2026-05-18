"""Add image_url to transmissions.json entries.
- Modifies _update_transmissions_json in bot.py to extract article-img src
- Backfills existing 97 articles' entries with their image_url
- Falls back to media/fallback.jpg for articles without article-img class
Idempotent: aborts if already patched."""
from pathlib import Path
import json
import re
import sys

# === PART 1: Patch bot.py ===
bot_src = Path("bot.py")
bot_content = bot_src.read_text(encoding="utf-8")

if "image_url" in bot_content and "_update_transmissions_json" in bot_content[bot_content.find("image_url"):bot_content.find("_update_transmissions_json", bot_content.find("image_url"))+50] if "image_url" in bot_content else False:
    pass  # might already be patched

PATCH_MARKER = '"image_url":'
if PATCH_MARKER in bot_content:
    print("⚠️  Bot already has image_url field — skipping bot.py patch")
else:
    OLD_INSERT = '''            transmissions.insert(0, {
                "href": f"articles/{filename}",
                "title": clean_topic,
                "date": clean_date
            })'''
    NEW_INSERT = '''            # Extract image_url from the article we just wrote
            image_url = "media/fallback.jpg"
            try:
                article_path = f"articles/{filename}"
                if os.path.exists(article_path):
                    with open(article_path, 'r', encoding='utf-8') as af:
                        article_html = af.read()
                    img_match = re.search(r'<img\\s+src="([^"]+)"[^>]*class="article-img"', article_html)
                    if not img_match:
                        img_match = re.search(r'<img\\s+[^>]*class="article-img"[^>]*src="([^"]+)"', article_html)
                    if img_match:
                        raw_src = img_match.group(1).strip()
                        # Normalize ../media/... to media/...
                        image_url = raw_src.lstrip('./').replace('../', '')
            except Exception as _e:
                pass  # fallback already set
            transmissions.insert(0, {
                "href": f"articles/{filename}",
                "title": clean_topic,
                "date": clean_date,
                "image_url": image_url
            })'''
    assert bot_content.count(OLD_INSERT) == 1, "OLD_INSERT not unique in bot.py"
    bot_content = bot_content.replace(OLD_INSERT, NEW_INSERT, 1)
    Path("bot.py.bak-before-image-url-20260518").write_text(bot_src.read_text(encoding="utf-8"), encoding="utf-8")
    bot_src.write_text(bot_content, encoding="utf-8")
    print("✅ bot.py patched (image_url extraction + fallback)")

# === PART 2: Backfill existing transmissions.json ===
json_path = Path("transmissions.json")
data = json.loads(json_path.read_text())

img_pattern_1 = re.compile(r'<img\s+src="([^"]+)"[^>]*class="article-img"')
img_pattern_2 = re.compile(r'<img\s+[^>]*class="article-img"[^>]*src="([^"]+)"')

fallback = "media/fallback.jpg"
updated = 0
fallback_count = 0

for entry in data:
    href = entry.get("href", "")
    article_file = Path(href)
    image_url = fallback
    if article_file.exists():
        try:
            html = article_file.read_text(encoding="utf-8")
            m = img_pattern_1.search(html) or img_pattern_2.search(html)
            if m:
                raw = m.group(1).strip()
                # Normalize ../media/... to media/...
                image_url = raw.lstrip('./').replace('../', '')
            else:
                fallback_count += 1
        except Exception as e:
            print(f"  ⚠️  failed to read {article_file}: {e}")
            fallback_count += 1
    else:
        fallback_count += 1
    entry["image_url"] = image_url
    updated += 1

# Backup before write
Path("transmissions.json.bak-before-image-url-20260518").write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
json_path.write_text(json.dumps(data, indent=4))

print(f"✅ transmissions.json backfilled")
print(f"   Total entries: {updated}")
print(f"   Using fallback: {fallback_count}")
print(f"   With real images: {updated - fallback_count}")

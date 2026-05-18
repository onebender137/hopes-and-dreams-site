"""Add thumbnail images to MATCHED_TRANSMISSIONS list in intel.html.
- CSS for .mini-scanned-thumb
- Adjust .mini-scanned-link spacing/text-max-width to accommodate thumb
- JS: inject <img> using article.image_url (fallback to media/fallback.jpg)
Idempotent: aborts if already patched."""
from pathlib import Path
import sys

src = Path("intel.html")
content = src.read_text(encoding="utf-8")
original = content

if "mini-scanned-thumb" in content:
    print("❌ Already patched. Aborting.")
    sys.exit(1)

# === EDIT 1: Add new CSS for thumbnails + adjust the link rule ===
OLD_CSS = '''        .mini-scanned-link {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 14px;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.85rem;
            color: var(--text-main);
            transition: all 0.2s ease;
        }
        .mini-scanned-link:hover { border-color: var(--neon-blue); background: rgba(56, 189, 248, 0.04); }
        .mini-scanned-link span { text-transform: capitalize; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 78%; text-align: left; min-width: 0; }
        .mini-scanned-link .mini-date { font-family: 'Courier New', Courier, monospace; font-size: 0.72rem; color: var(--text-dim); }'''

NEW_CSS = '''        .mini-scanned-link {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 14px 8px 8px;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.85rem;
            color: var(--text-main);
            transition: all 0.2s ease;
        }
        .mini-scanned-link:hover { border-color: var(--neon-blue); background: rgba(56, 189, 248, 0.04); }
        .mini-scanned-link:hover .mini-scanned-thumb { box-shadow: 0 0 8px rgba(56, 189, 248, 0.4); }
        .mini-scanned-thumb {
            width: 44px;
            height: 44px;
            object-fit: cover;
            border-radius: 6px;
            flex-shrink: 0;
            background: rgba(0,0,0,0.3);
            transition: box-shadow 0.2s ease;
        }
        .mini-scanned-text {
            flex: 1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            min-width: 0;
        }
        .mini-scanned-link .mini-title { text-transform: capitalize; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0; text-align: left; }
        .mini-scanned-link .mini-date { font-family: 'Courier New', Courier, monospace; font-size: 0.72rem; color: var(--text-dim); flex-shrink: 0; }'''

assert content.count(OLD_CSS) == 1, "OLD_CSS not unique"
content = content.replace(OLD_CSS, NEW_CSS, 1)

# === EDIT 2: Modify the JS that builds each link ===
OLD_JS = '''                        const linkNode = document.createElement('a');
                        linkNode.href = article.href;
                        linkNode.className = "mini-scanned-link";
                        linkNode.innerHTML = `
                            <span>${article.title}</span>
                            <span class=\\"mini-date\\">${article.date}</span>
                        `;
                        scannedFeed.appendChild(linkNode);'''

NEW_JS = '''                        const linkNode = document.createElement('a');
                        linkNode.href = article.href;
                        linkNode.className = "mini-scanned-link";
                        const thumbSrc = article.image_url || 'media/fallback.jpg';
                        linkNode.innerHTML = `
                            <img class="mini-scanned-thumb" src="${thumbSrc}" alt="" loading="lazy" onerror="this.src='media/fallback.jpg'">
                            <span class="mini-scanned-text">
                                <span class="mini-title">${article.title}</span>
                                <span class="mini-date">${article.date}</span>
                            </span>
                        `;
                        scannedFeed.appendChild(linkNode);'''

assert content.count(OLD_JS) == 1, "OLD_JS not unique"
content = content.replace(OLD_JS, NEW_JS, 1)

Path("intel.html.bak-before-thumbs-20260518").write_text(original, encoding="utf-8")
src.write_text(content, encoding="utf-8")

print("PATCH APPLIED")
print(f"  Old: {len(original)} bytes")
print(f"  New: {len(content)} bytes")
print(f"  Delta: +{len(content) - len(original)}")

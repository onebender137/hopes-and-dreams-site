"""Make video_creator.py resilient to long scripts + bolden intro title.
Idempotent: aborts if already patched."""
from pathlib import Path
import sys

src = Path("video_creator.py")
content = src.read_text(encoding="utf-8")
original = content

if "MAX_PARAGRAPH_CHARS" in content:
    print("❌ Already patched. Aborting.")
    sys.exit(1)

OLD_CHUNK = '''            # Split text by paragraphs to avoid memory crashes
            paragraphs = [p.strip() for p in text.split('\\n') if p.strip()]'''

NEW_CHUNK = '''            # Split into paragraphs, then further chunk any long paragraph.
            # ImageMagick caption: builds one tall image per clip — long paragraphs
            # exceed policy.xml width/height limits.
            MAX_PARAGRAPH_CHARS = 600
            raw_paragraphs = [p.strip() for p in text.split('\\n') if p.strip()]
            paragraphs = []
            for p in raw_paragraphs:
                if len(p) <= MAX_PARAGRAPH_CHARS:
                    paragraphs.append(p)
                    continue
                sentences = re.split(r'(?<=[.!?])\\s+', p)
                buf = ""
                for sent in sentences:
                    if len(buf) + len(sent) + 1 <= MAX_PARAGRAPH_CHARS:
                        buf = (buf + " " + sent).strip() if buf else sent
                    else:
                        if buf:
                            paragraphs.append(buf)
                        while len(sent) > MAX_PARAGRAPH_CHARS:
                            paragraphs.append(sent[:MAX_PARAGRAPH_CHARS])
                            sent = sent[MAX_PARAGRAPH_CHARS:]
                        buf = sent
                if buf:
                    paragraphs.append(buf)'''

assert content.count(OLD_CHUNK) == 1, "OLD_CHUNK anchor not unique"
content = content.replace(OLD_CHUNK, NEW_CHUNK, 1)

OLD_TITLE = '''            intro_title = TextClip(
                clean_title, 
                fontsize=75, 
                color='white', 
                font='Arial-Bold', 
                stroke_color='black',  
                stroke_width=4,
                method='caption', 
                size=(920, None), 
                align='center'
            )'''

NEW_TITLE = '''            intro_title = TextClip(
                clean_title, 
                fontsize=92, 
                color='white', 
                font='Arial-Bold', 
                stroke_color='black',  
                stroke_width=7,
                method='caption', 
                size=(960, None), 
                align='center'
            )'''

assert content.count(OLD_TITLE) == 1, "OLD_TITLE anchor not unique"
content = content.replace(OLD_TITLE, NEW_TITLE, 1)

Path("video_creator.py.bak-before-robust-20260518").write_text(original, encoding="utf-8")
src.write_text(content, encoding="utf-8")

print("PATCH APPLIED")
print(f"  Old: {len(original)} bytes")
print(f"  New: {len(content)} bytes")
print(f"  Delta: +{len(content) - len(original)}")

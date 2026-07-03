#!/usr/bin/env python3
"""
tech_publish.py — publish a generated tech-article .md into the live site (BRAND-MATCHED).

Run from the SITE REPO root (venv active — needs the `markdown` lib):
    python3 tech_publish.py --md ~/claude_export/tech_articles/<slug>.md
    # then: git add tech/ tech_transmissions.json && commit && push

Writes tech/<slug>.html + upserts tech_transmissions.json.

The tech pages now INHERIT the brand: they link ../style.css (brand navy/blue/gold palette,
Inter font, header/nav/footer, light-dark toggle) and add only a small tech-content layer
(SYS_// headers, code blocks) built entirely from the brand CSS variables so it flips with
the theme. Sovereign Tech reads as a DIVISION of the empire, not a different website.
"""
import os, re, sys, json, argparse, datetime
import markdown

CLEAN_PATTERNS = [
    r'(?im)^#{1,5}\s*step\s*\d+\s*:\s*(correct|fix|remove|removed)\b.*(indentation|redundant|your script|the script).*$',
    r'(?im)^.*correct the indentation error.*$',
    r'(?im)^.*redundant\s+`?OLLAMA_BASE_URL`?\s+definition.*$',
    r'(?im)^#{1,5}\s*step\s*\d+\s*:\s*$',
]

NAV = [
    ("Home", "../index.html"), ("Shop", "../shop.html"), ("Optimization", "../optimization.html"),
    ("Cipher", "../cipher.html"), ("Intel Hub", "../intel.html"),
    ("Sovereign Tech", "../sovereign.html"),
    ("Merch", "https://merch.hopes-and-dreams.ca"), ("About", "../about.html"),
    ("Privacy", "../privacy.html"),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Hopes and Dreams</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../style.css">
<style>
  .tech-log {{ max-width:820px; margin:0 auto; padding:30px 22px 80px; counter-reset:stepcount; }}
  .tech-back {{ font-family:'Courier New',monospace; font-size:0.85rem; display:inline-block; margin-bottom:20px; color:var(--neon-blue); }}
  .tech-tagline {{ font-family:'Courier New',monospace; color:var(--neon-blue); font-size:0.72rem;
    letter-spacing:3px; text-transform:uppercase; margin-bottom:8px; opacity:0.85; }}
  .tech-log h1 {{ font-size:2.2rem; line-height:1.15; margin:0 0 22px; color:var(--text-main);
    text-shadow:0 0 22px rgba(56,189,248,0.25); }}
  .tech-log h2 {{ font-family:'Courier New',monospace; color:var(--neon-blue); text-transform:uppercase;
    letter-spacing:1px; font-size:1.15rem; margin:40px 0 12px; padding-top:18px;
    border-top:1px solid rgba(148,163,184,0.18); }}
  .tech-log h2::before {{ content:"SYS_// "; color:var(--neon-gold); opacity:0.9; }}
  .tech-log h3 {{ color:var(--neon-gold); font-size:1rem; margin:24px 0 8px; }}
  .tech-log h3.step::before {{ counter-increment:stepcount; content:"Step " counter(stepcount) " // ";
    color:var(--neon-blue); font-family:'Courier New',monospace; }}
  .tech-log p {{ margin:0 0 16px; color:var(--text-main); line-height:1.7; }}
  .tech-log a {{ color:var(--neon-blue); }}
  .tech-log ul, .tech-log ol {{ padding-left:22px; color:var(--text-main); }}
  .tech-log li {{ margin-bottom:8px; line-height:1.6; }}
  .tech-log code {{ font-family:'Courier New',monospace; background:rgba(56,189,248,0.1);
    color:var(--neon-blue); padding:2px 6px; border-radius:4px; font-size:0.9em; }}
  .tech-log pre {{ background:var(--card-bg); border:1px solid rgba(56,189,248,0.2);
    border-left:3px solid var(--neon-blue); border-radius:6px; padding:16px 18px; overflow-x:auto;
    margin:0 0 20px; }}
  .tech-log pre code {{ background:none; padding:0; color:var(--text-main); font-size:0.85rem; line-height:1.55; }}
  .tech-signoff {{ margin-top:44px; padding-top:20px; border-top:1px solid rgba(148,163,184,0.18);
    font-family:'Courier New',monospace; color:var(--neon-gold); letter-spacing:1px; font-size:0.9rem; }}
</style>
</head>
<body>
  <div id="scroll-progress"></div>
  <button id="theme-toggle" class="theme-toggle-pill" aria-label="Toggle between dark and light mode">&#9728;&#65039; LIGHT MODE</button>
  <header>
    <div class="logo-wrap">
      <a href="../index.html"><img src="../topper.png" alt="Hopes and Dreams Syndicate Neuro-Optimization"></a>
    </div>
    <nav>{nav}</nav>
  </header>

  <main class="tech-log">
    <a class="tech-back" href="../sovereign.html">&lt;&lt; back to build logs</a>
    <div class="tech-tagline">SYS_OUTPUT // BUILD_LOG DECODED</div>
    <h1>{title}</h1>
    {body}
    <div class="tech-signoff">// Do your own research. Don't be a statistic.</div>
  </main>

  <footer>
    <p>&copy; {year} Dream Syndicate Digital Assets. All Rights Reserved.</p>
    <p>
      <a href="https://www.facebook.com/profile.php?id=61581034972328" target="_blank" rel="noopener noreferrer">Connect on Facebook</a> |
      <a href="https://merch.hopes-and-dreams.ca" target="_blank" rel="noopener noreferrer">Merch</a> |
      <a href="../intel.html">Intel Hub</a> |
      <a href="../sovereign.html">Sovereign Tech</a> |
      <a href="../privacy.html">Privacy Policy</a> |
      <a href="../about.html">Contact Us</a>
    </p>
    <p style="font-size:0.7rem; color:var(--text-dim); margin-top:10px;">Location: Saint John, New Brunswick, Canada</p>
  </footer>
  <script src="../script.js" defer></script>
</body>
</html>
"""


def auto_clean(md):
    removed = []
    for pat in CLEAN_PATTERNS:
        for m in re.findall(pat, md):
            removed.append(m if isinstance(m, str) else " ".join(x for x in m if x))
        md = re.sub(pat, "", md)
    return re.sub(r"\n{3,}", "\n\n", md).strip(), [r.strip() for r in removed if r and r.strip()]


# Grounding keeps real commands verbatim (good) but also real identifiers (bad — that's
# publishing your own coordinates). Swap personal infra tokens for generic placeholders so
# the reader substitutes their own. Runs automatically on every publish. Order: specific first.
REDACT_RULES = [
    (r'https?://github\.com/onebender137/([A-Za-z0-9._-]+?)(\.git)?\b',
     r'https://github.com/your-username/\1\2', "repo URL"),
    (r'\bgithub\.com/onebender137\b', r'github.com/your-username', "github path"),
    (r'\bonebender137\b', r'your-username', "GitHub handle"),
    (r'\bcoryr@bigboy\b', r'user@host', "shell prompt"),
    (r'\bbender@\w+\b', r'user@host', "shell prompt"),
    (r'100\.108\.37\.25', r'<TAILNET_IP>', "tailnet IP"),
    (r'100\.123\.157\.7', r'<TAILNET_IP>', "tailnet IP"),
    (r'\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b', r'<TAILNET_IP>', "tailnet IP"),
    (r'192\.168\.\d{1,3}\.\d{1,3}', r'<LAN_IP>', "LAN IP"),
    (r'EnvironmentFile=-?/home/\w+/', r'EnvironmentFile=-/home/user/', "systemd env path"),
    (r'/home/coryr\b', r'/home/user', "home path"),
    (r'/home/bender\b', r'/home/user', "home path"),
]


def redact(text):
    hits = []
    for pat, repl, label in REDACT_RULES:
        text, n = re.subn(pat, repl, text)
        if n:
            hits.append((label, n))
    return text, hits


def extract_title(md):
    # prefer a proper H1 heading
    m = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
    if m:
        return m.group(1).strip().strip("*"), md.replace(m.group(0), "", 1).strip()
    # fallback: the model sometimes bolds the title instead of using #  ( **Title** )
    m = re.search(r"^\s*\*\*(.+?)\*\*\s*$", md, re.MULTILINE)
    if m:
        return m.group(1).strip(), md.replace(m.group(0), "", 1).strip()
    return "Sovereign Tech Build Log", md


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)[:60] or "article"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--siterepo", default=os.getcwd())
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--image", default="")
    args = ap.parse_args()

    path = os.path.expanduser(args.md)
    if not os.path.exists(path):
        sys.exit(f"ABORT: {path} not found.")
    repo = os.path.expanduser(args.siterepo)
    if not os.path.isdir(os.path.join(repo, "articles")):
        sys.exit(f"ABORT: {repo} doesn't look like the site repo (no articles/). Use --siterepo.")

    raw = open(path, encoding="utf-8").read()
    cleaned, removed = auto_clean(raw)
    if removed:
        print("[auto-clean] stripped transcript seams (verify these were junk):")
        for r in removed:
            print(f"    - {r[:100]}")
    else:
        print("[auto-clean] nothing matched.")

    cleaned, redactions = redact(cleaned)
    if redactions:
        print("[redact] scrubbed personal identifiers -> placeholders:")
        for label, n in redactions:
            print(f"    - {label}: {n}x")
    else:
        print("[redact] no personal identifiers found.")

    title, body_md = extract_title(cleaned)
    body_html = markdown.markdown(body_md, extensions=["fenced_code", "tables", "sane_lists"])
    body_html = re.sub(r'<h3>Step\s+\d+\s*:\s*(.*?)</h3>', r'<h3 class="step">\1</h3>', body_html)
    body_html = re.sub(r"<p>\s*Do your own research\.?\s*Don't be a statistic\.?\s*</p>", "",
                       body_html, flags=re.I)

    nav_html = " ".join(
        (f'<a class="active" href="{href}">{label}</a>' if label == "Sovereign Tech"
         else f'<a href="{href}">{label}</a>')
        for label, href in NAV
    )
    desc = re.sub(r"<[^>]+>", "", body_html)[:150].replace('"', "'") + "..."
    html = TEMPLATE.format(title=title, desc=desc, nav=nav_html, body=body_html,
                           year=datetime.date.today().year)

    slug = slugify(os.path.basename(path).replace(".md", ""))
    techdir = os.path.join(repo, "tech")
    os.makedirs(techdir, exist_ok=True)
    outpath = os.path.join(techdir, slug + ".html")
    open(outpath, "w", encoding="utf-8").write(html)

    href = f"tech/{slug}.html"
    mpath = os.path.join(repo, "tech_transmissions.json")
    entries = json.load(open(mpath)) if os.path.exists(mpath) else []
    entries = [e for e in entries if e.get("href") != href]
    entries.insert(0, {"href": href, "title": title, "date": args.date, "image_url": args.image})
    json.dump(entries, open(mpath, "w"), indent=2)

    print(f"\n[published] {outpath}")
    print(f"[manifest ] {mpath}  ({len(entries)} tech article(s))")
    print(f"  next: git add tech/ tech_transmissions.json && git commit && push")


if __name__ == "__main__":
    main()

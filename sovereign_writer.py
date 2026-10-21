#!/usr/bin/env python3
"""sovereign_writer.py — write + publish a sovereign build-log article.

Input: event_id. Builds a build-log prompt, calls the 35b (no-think),
generates a header image (tech_image.py), publishes via tech_publish.py,
git commits + pushes. Prints `HREF: <url>` on the last line for the
watcher to capture.
"""
import sqlite3, datetime, os, sys, re, subprocess, json, urllib.request

SITE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(SITE, "syndicate_memory.db")
BASE = "http://100.123.157.7:11434"
MODEL = "huihui_ai/qwen3.6-abliterated:35b"
SITE_DOMAIN = "https://hopes-and-dreams.ca"

BUILD_LOG_SYSTEM = (
    "You are the Sovereign Tech writer for Hopes and Dreams. You write first-person "
    "build logs about infrastructure and systems you actually built. Plain English, "
    "not overly technical. You link to repos where relevant and give platform-specific "
    "directions. Gritty, insider, confident. No AI tells, no disclaimers, no marketing "
    "fluff. The article body uses plain text with section labels in CAPS on their own "
    "line (no markdown headers, no bold, no lists Never include any secrets: no API tokens, keys, passwords, bearer strings, IP addresses, hostnames, or credentials. If a detail would expose a secret, describe it generically instead (e.g. 'a bearer token', not the actual value).). End the article with exactly: "
    "'Do your own research. Don't be a statistic.'"
)


def slugify(s):
    # must match tech_publish.py's slugify exactly
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)[:60] or "article"



def sanitize(text):
    """Redact high-confidence secret patterns before publishing (fail-safe)."""
    # sk- style keys (OpenAI / Together / etc.)
    text = re.sub(r'\bsk-[A-Za-z0-9]{8,}\b', '[REDACTED]', text)
    # Bearer <token>
    text = re.sub(r'(?i)Bearer\s+[A-Za-z0-9_\-]{8,}', 'Bearer [REDACTED]', text)
    # password= / token= / api_key= / secret=  value
    text = re.sub(r'(?i)\b(password|passwd|token|api[_-]?key|secret)\s*[=:]\s*\S+',
                  r'\1=[REDACTED]', text)
    # Tailscale CGNAT / tailnet IPs (100.64.0.0/10)
    text = re.sub(r'\b100\.(6[4-9]|[7-9]\d|1[0-2]\d)\.\d{1,3}\.\d{1,3}\b',
                  '[REDACTED-IP]', text)
    # High-entropy mixed-case alphanumeric (tokens/keys): 16+ alnum chars w/ upper+lower+digit
    def _he(m):
        t = m.group()
        a = [c for c in t if c.isalnum()]
        if len(a) >= 16 and any(c.isupper() for c in a) and any(c.islower() for c in a) and any(c.isdigit() for c in a):
            return "[REDACTED]"
        return t
    text = re.sub(r"\b[A-Za-z0-9][A-Za-z0-9-]*[A-Za-z0-9]\b", _he, text)
    return text

def gen_markdown(title, summary, tags):
    prompt = (
        f"Write a Sovereign Tech build-log article.\n\n"
        f"TITLE: {title}\n\n"
        f"WHAT I BUILT (the seed — expand on this, first person):\n{summary}\n\n"
        f"TAGS: {tags}\n\n"
        "Start with a single H1 line: '# ' followed by the title, then a blank line.\n"
        "Then write the build log body: what I did, why, how, what it took, what's next.\n"
        "Plain English, first person, not overly technical. Link to repos where relevant.\n"
        "Use plain text with section labels in CAPS on their own line (no markdown headers).\n"
        "End with exactly: 'Do your own research. Don't be a statistic.'"
    )
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": BUILD_LOG_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": False,
        "options": {"num_ctx": 8192},
    }
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=900))
    msg = d.get("message", {})
    return msg.get("content", "") if isinstance(msg, dict) else str(msg)


def gen_image(title, content, slug):
    """Generate a header image via tech_image.py. Returns the image path or ''."""
    r = subprocess.run(
        [sys.executable, os.path.join(SITE, "tech_image.py"),
         "--title", title, "--content", content, "--slug", slug],
        capture_output=True, text=True, timeout=900)
    print(r.stdout)
    if r.returncode != 0:
        print(f"image gen failed (non-fatal): {r.stderr}")
        return ""
    for line in r.stdout.splitlines():
        if line.startswith("IMAGE_PATH:"):
            return line.split("IMAGE_PATH:", 1)[1].strip()
    return ""


def main():
    if len(sys.argv) < 2:
        print("usage: sovereign_writer.py <event_id>")
        sys.exit(1)
    eid = sys.argv[1]
    c = sqlite3.connect(DB)
    row = c.execute("SELECT title, summary, tags FROM empire_events WHERE id=?", (eid,)).fetchone()
    c.close()
    if not row:
        print(f"event {eid} not found")
        sys.exit(1)
    title, summary, tags = row

    md = gen_markdown(title, summary, tags)
    md = sanitize(md)
    if not md or len(md) < 200:
        print(f"generation too short ({len(md)} chars), aborting")
        sys.exit(1)

    # Name the file <slug>.md (tech_publish derives the slug from the filename)
    slug = slugify(title)
    md_path = os.path.join(SITE, "tech_articles", f"{slug}.md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w") as f:
        f.write(md)

    # Generate the header image (non-fatal — article publishes even if image fails)
    image_path = gen_image(title, md, slug)

    date = datetime.date.today().isoformat()
    publish_cmd = [sys.executable, os.path.join(SITE, "tech_publish.py"),
                   "--md", md_path, "--date", date]
    if image_path:
        # tech_publish stores the image URL in the manifest; use the relative site path
        rel_image = os.path.relpath(image_path, SITE)
        publish_cmd += ["--image", f"{SITE_DOMAIN}/{rel_image}"]
    r = subprocess.run(publish_cmd, capture_output=True, text=True, timeout=300, cwd=SITE)
    print(r.stdout)
    if r.returncode != 0:
        print(f"tech_publish failed: {r.stderr}")
        sys.exit(1)

    # Git commit + push (include the image if generated)
    git_add = ["git", "add", "tech/", "tech_transmissions.json"]
    if image_path:
        git_add += [os.path.relpath(image_path, SITE)]
    subprocess.run(git_add, cwd=SITE, capture_output=True)
    commit = subprocess.run(["git", "commit", "-m", f"sovereign: {title}"],
                            cwd=SITE, capture_output=True, text=True)
    if commit.returncode != 0 and "nothing to commit" not in commit.stdout:
        print(f"git commit issue: {commit.stdout} {commit.stderr}")
    push = subprocess.run(["git", "push"], cwd=SITE, capture_output=True, text=True)
    print(push.stdout)
    if push.returncode != 0:
        print(f"git push failed: {push.stderr}")
        sys.exit(1)

    href = f"{SITE_DOMAIN}/tech/{slug}.html"
    print(f"HREF: {href}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# ============================================================================
# build-supplements-index.py
# Dream Syndicate Digital Assets // hopes-and-dreams.ca
#
# Derives supplements.json from the ALREADY-DEPLOYED search-index.json.
# No raw-article rescan: search-index.json already holds {href,title,date,body}
# for every article, so we just grep bodies for each compound's terms.
#
#   python3 build-supplements-index.py
#   python3 build-supplements-index.py --index search-index.json --out supplements.json
#
# OUTPUT schema (what supplement-search.js expects):
#   [{ "name", "what", "dose", "shop", "aliases":[...], "articles":[{href,title,date}] }]
# ============================================================================

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# SEED CATALOG  ---  THIS IS YOURS, BENDER.
#   name    : display name (Title Case)
#   aliases : every spelling/form to grep for (lowercase). name is auto-added.
#   what    : one-line "what it does" for the profile card
#   dose    : profile-card dose line
#   shop    : link target (shop.html#anchor, or "" to hide the ACQUIRE button)
#
#   !! DOSES BELOW ARE COMMON-RANGE PLACEHOLDERS. Verify each against your own
#      articles / Stack Review before you commit. You propose, you own it. !!
# ---------------------------------------------------------------------------
SEED = [
    {"name": "Magnesium",
     "aliases": ["magnesium glycinate", "mag glycinate", "magnesium l-threonate",
                 "magnesium threonate", "magnesium bisglycinate", "magnesium citrate"],
     "what": "Cofactor in 300+ enzymatic reactions. Supports sleep depth, muscle recovery, and nervous-system downregulation.",
     "dose": "200-400 mg elemental, evening",
     "shop": "shop.html"},

    {"name": "L-Theanine",
     "aliases": ["theanine", "l theanine"],
     "what": "Amino acid from green tea. Smooths caffeine's edge, promotes calm-focus without sedation.",
     "dose": "100-200 mg, often 2:1 with caffeine",
     "shop": "shop.html"},

    {"name": "Ashwagandha",
     "aliases": ["withania", "ksm-66", "ksm 66", "sensoril"],
     "what": "Adaptogen. Blunts cortisol response to stress; studied for anxiety and recovery.",
     "dose": "300-600 mg standardized extract, daily",
     "shop": "shop.html"},

    {"name": "Creatine",
     "aliases": ["creatine monohydrate", "creatine hcl"],
     "what": "Cellular energy buffer. Strength/power output plus emerging cognitive and mood support.",
     "dose": "3-5 g daily, timing-agnostic",
     "shop": "shop.html"},

    {"name": "Omega-3",
     "aliases": ["fish oil", "epa", "dha", "epa/dha", "krill oil"],
     "what": "EPA/DHA fatty acids. Anti-inflammatory, cardiovascular, and neuronal membrane support.",
     "dose": "1-2 g combined EPA+DHA daily",
     "shop": "shop.html"},

    {"name": "Vitamin D3",
     "aliases": ["vitamin d", "cholecalciferol", "d3", "d3/k2", "vitamin d3"],
     "what": "Hormone-precursor vitamin. Immune, bone, and mood function; pairs with K2.",
     "dose": "2000-5000 IU daily, with fat",
     "shop": "shop.html"},

    {"name": "Rhodiola Rosea",
     "aliases": ["rhodiola", "rosavins", "salidroside"],
     "what": "Adaptogen for fatigue resistance and mental stamina under load.",
     "dose": "200-400 mg (3% rosavins), morning",
     "shop": "shop.html"},

    {"name": "Lion's Mane",
     "aliases": ["lions mane", "lion's mane", "hericium", "hericium erinaceus"],
     "what": "Mushroom studied for nerve-growth-factor support and cognitive maintenance.",
     "dose": "500-1000 mg extract, daily",
     "shop": "shop.html"},

    {"name": "Caffeine",
     "aliases": ["coffee", "caffeine anhydrous"],
     "what": "Adenosine antagonist. Acute alertness and output; best stacked with L-theanine.",
     "dose": "50-200 mg, watch the half-life",
     "shop": "shop.html"},

    {"name": "Alpha-GPC",
     "aliases": ["alpha gpc", "glycerophosphocholine", "choline"],
     "what": "Choline source for acetylcholine synthesis. Focus and mind-muscle signalling.",
     "dose": "300-600 mg daily",
     "shop": "shop.html"},

    {"name": "Bacopa Monnieri",
     "aliases": ["bacopa", "bacosides", "brahmi"],
     "what": "Ayurvedic nootropic. Memory consolidation over 8-12 week horizons.",
     "dose": "300 mg (50% bacosides), daily",
     "shop": "shop.html"},

    {"name": "NAC",
     "aliases": ["n-acetylcysteine", "n acetylcysteine", "acetylcysteine"],
     "what": "Glutathione precursor. Antioxidant support and glutamate modulation.",
     "dose": "600-1200 mg daily",
     "shop": "shop.html"},

    {"name": "CoQ10",
     "aliases": ["coenzyme q10", "ubiquinol", "ubiquinone", "coq-10"],
     "what": "Mitochondrial electron-transport cofactor. Cellular energy and cardiovascular support.",
     "dose": "100-200 mg (ubiquinol), with fat",
     "shop": "shop.html"},

    {"name": "Zinc",
     "aliases": ["zinc picolinate", "zinc bisglycinate"],
     "what": "Trace mineral for immune function, testosterone, and enzymatic activity.",
     "dose": "15-30 mg daily, away from other minerals",
     "shop": "shop.html"},

    {"name": "Melatonin",
     "aliases": ["melatonin"],
     "what": "Circadian signalling hormone. Sleep-onset timing, not a sedative.",
     "dose": "0.3-1 mg, ~1 hr before bed",
     "shop": "shop.html"},

    {"name": "Taurine",
     "aliases": ["taurine"],
     "what": "Conditionally-essential amino acid. Cardiovascular, mitochondrial, calming support.",
     "dose": "1-2 g daily",
     "shop": "shop.html"},

    {"name": "Glycine",
     "aliases": ["glycine"],
     "what": "Inhibitory amino acid. Lowers core temp for sleep onset; collagen substrate.",
     "dose": "3 g before bed",
     "shop": "shop.html"},

    {"name": "L-Tyrosine",
     "aliases": ["tyrosine", "l tyrosine", "n-acetyl-l-tyrosine", "nalt"],
     "what": "Dopamine precursor. Cognitive performance under acute stress/sleep debt.",
     "dose": "500-2000 mg, empty stomach",
     "shop": "shop.html"},
]


def word_re(term):
    """Boundary-aware matcher so 'zinc' doesn't hit 'zincography', etc.
    Falls back to loose contains for multi-word/hyphen terms where \b is flaky."""
    esc = re.escape(term)
    return re.compile(r'(?<![a-z0-9])' + esc + r'(?![a-z0-9])', re.IGNORECASE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="search-index.json",
                    help="source full-text index (default: search-index.json)")
    ap.add_argument("--out", default="supplements.json",
                    help="output file (default: supplements.json)")
    ap.add_argument("--keep-empty", action="store_true",
                    help="keep compounds with zero article matches (default: drop them)")
    args = ap.parse_args()

    idx_path = Path(args.index)
    if not idx_path.exists():
        sys.exit(f"[!] {idx_path} not found. Run this from the repo root where "
                 f"search-index.json lives, or pass --index.")

    try:
        articles = json.loads(idx_path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"[!] failed to parse {idx_path}: {e}")

    if not isinstance(articles, list):
        sys.exit(f"[!] {idx_path} is not a JSON array of articles.")

    # pre-lower each article's haystack once
    haystacks = []
    for a in articles:
        if not isinstance(a, dict):
            continue
        body = (a.get("body", "") or "") + " " + (a.get("title", "") or "")
        haystacks.append((a, body.lower()))

    out = []
    empties = []
    for c in SEED:
        terms = [c["name"].lower()] + [t.lower() for t in c.get("aliases", [])]
        patterns = [word_re(t) for t in terms]
        seen = set()
        matches = []
        for a, hay in haystacks:
            if any(p.search(hay) for p in patterns):
                href = (a.get("href", "") or "").strip()
                if not href or href in seen:
                    continue
                seen.add(href)
                matches.append({
                    "href": href,
                    "title": (a.get("title", "") or "").strip(),
                    "date": (a.get("date", "") or "").strip(),
                })
        matches.sort(key=lambda m: m["date"], reverse=True)

        if not matches and not args.keep_empty:
            empties.append(c["name"])
            continue

        out.append({
            "name": c["name"],
            "what": c.get("what", ""),
            "dose": c.get("dose", ""),
            "shop": c.get("shop", ""),
            "aliases": c.get("aliases", []),
            "articles": matches,
        })

    out.sort(key=lambda x: x["name"].lower())
    Path(args.out).write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---- report ----
    print(f"[ok] wrote {args.out}  ({len(out)} compounds)")
    print(f"     scanned {len(haystacks)} articles from {idx_path}")
    print()
    print("     coverage:")
    for c in sorted(out, key=lambda x: -len(x["articles"])):
        print(f"       {len(c['articles']):>3}  {c['name']}")
    if empties:
        print()
        print(f"     [!] {len(empties)} seeded compound(s) matched ZERO articles "
              f"(dropped; use --keep-empty to keep as profile-only):")
        print("         " + ", ".join(empties))
        print("         -> check the alias spellings against how you write them in articles.")


if __name__ == "__main__":
    main()

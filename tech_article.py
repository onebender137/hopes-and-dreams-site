#!/usr/bin/env python3
"""
tech_article.py — sovereign-tech article generator (isolated tech-KB from war-story briefs).

Run from the SITE REPO root (venv active — needs llm_client + langchain + embeddings):
    python3 tech_article.py --topic "Exposing Ollama to WSL over the network"
    python3 tech_article.py --topic "..." --rebuild     # force-rebuild the tech index

FULLY ISOLATED from the biohacking KB — its own FAISS index built from the war-briefs,
its own voice, its own structure. Nothing here touches knowledge_base/ or vector_db/.

Pipeline:
  1. Build (once, cached) a FAISS index from ~/claude_export/war_briefs/*.md
  2. Retrieve the briefs most relevant to --topic
  3. Generate a grounded article in the sovereign-cyberpunk voice, PROBLEM/STACK/BUILD/GOTCHAS
  4. Write to ~/claude_export/tech_articles/<slug>.md  (review before it goes near the site)

GROUNDING LAW: the article is written ENTIRELY from the retrieved briefs. Every command/config
is kept verbatim; the model is forbidden from inventing commands or values.
"""
import os, sys, glob, re, argparse

sys.path.insert(0, os.getcwd())
from llm_client import LLMClient
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

BRIEFS = os.path.expanduser("~/claude_export/war_briefs")
INDEX = os.path.expanduser("~/claude_export/tech_vector_db")
OUT = os.path.expanduser("~/claude_export/tech_articles")

SYS_VOICE = (
    "You are the voice of the Hopes & Dreams sovereign-tech division. You run your own AI "
    "empire on your own hardware and you write for people who want to take the power back "
    "from Big Tech. Your voice is direct, gritty, and technically precise, with a rebel edge "
    "— never corporate, never hype. You have ACTUALLY built this stuff; you write as a peer in "
    "the workshop: 'here's how I did it, here's how you do it too.' You keep every command and "
    "config exact and never invent them. The ethos: own your stack, own your data, run it local, "
    "do your own research, don't be a statistic."
)

def build_index(embeddings, rebuild=False):
    if os.path.exists(INDEX) and os.listdir(INDEX) and not rebuild:
        return FAISS.load_local(INDEX, embeddings, allow_dangerous_deserialization=True)
    print(f"[tech-kb] building index from {BRIEFS} ...")
    docs = []
    for p in sorted(glob.glob(os.path.join(BRIEFS, "*.md"))):
        text = open(p, encoding="utf-8", errors="replace").read()
        docs.append(Document(page_content=text, metadata={"source": os.path.basename(p)}))
    if not docs:
        sys.exit(f"ABORT: no briefs found in {BRIEFS}")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1400, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    print(f"[tech-kb] {len(docs)} briefs -> {len(chunks)} chunks")
    vs = FAISS.from_documents(chunks, embeddings)
    os.makedirs(INDEX, exist_ok=True)
    vs.save_local(INDEX)
    return vs

def slug(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)[:60] or "article"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--k", type=int, default=6)
    args = ap.parse_args()

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vs = build_index(embeddings, rebuild=args.rebuild)

    # score-gated retrieval: keep only briefs that clear a relevance threshold, so a focused
    # topic grounds on its 1-2 tight briefs instead of dragging in loose neighbors.
    scored = vs.similarity_search_with_score(args.topic, k=max(args.k, 8))
    if scored:
        best = scored[0][1]
        # keep the best, plus anything within `band` distance of it, up to args.k
        band = 0.35
        kept = [(d, s) for d, s in scored if s <= best + band][:args.k]
    else:
        kept = []
    seen, briefs = set(), []
    print("[tech-kb] retrieval scores (lower = closer):")
    for d, s in kept:
        src = d.metadata.get("source", "?")
        seen.add(src)
        briefs.append(f"[BRIEF: {src}]\n{d.page_content}")
        print(f"    {s:.3f}  {src}")
    grounding = "\n\n---\n\n".join(briefs)
    print(f"[tech-kb] grounding on {len(seen)} brief(s): {', '.join(sorted(seen))}\n")

    prompt = (
        f"Write a sovereign-tech article on: {args.topic}\n\n"
        "Ground it ENTIRELY in these real build-log briefs from my own work. Keep every "
        "command, config value, and flag EXACTLY as written — do not invent, vague, or alter "
        "them. If the briefs don't cover something, leave it out rather than making it up.\n\n"
        f"SOURCE BRIEFS:\n{grounding}\n\n"
        "Structure the article with these four sections (use these exact headers):\n"
        "THE PROBLEM — what's broken, or why someone who wants to own their stack would do this\n"
        "THE STACK — what you need (hardware, software, prerequisites)\n"
        "THE BUILD — the actual steps, with the exact commands from the briefs in code blocks\n"
        "THE GOTCHAS — the hard-won, non-obvious traps and lessons\n\n"
        "Write ~600-900 words in the sovereign-tech voice. Real, useful, grounded. Open with a "
        "short punchy title line. End with exactly: Do your own research. Don't be a statistic."
    )

    llm = LLMClient()
    print("[gen] writing article ...")
    article = llm.generate_response(prompt, system_message=SYS_VOICE, reflect=False,
                                    sanitize=False, options={"num_ctx": 8192})
    article = (article or "").strip()
    if not article:
        sys.exit("ABORT: empty generation.")

    os.makedirs(OUT, exist_ok=True)
    outpath = os.path.join(OUT, slug(args.topic) + ".md")
    open(outpath, "w", encoding="utf-8").write(article + "\n")
    print(f"\n{'='*60}\n{article}\n{'='*60}\n")
    print(f"[done] wrote {outpath}")

if __name__ == "__main__":
    main()

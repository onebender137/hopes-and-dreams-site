# "Hopes and Dreams" Syndicate Syndicate Bot

This is a fully autonomous brand management system for the "Hopes and Dreams" Syndicate. It integrates Facebook, Telegram, and a local Ollama LLM (`dolphin-llama3:8b`) to manage a Business Page and build a biohacking empire.

## The "Big Dog" Syndicate Upgrade
This version implements an **Agentic Workflow** with the following pillars:
- **RAG (Retrieval-Augmented Generation):** Indexes PDFs and transcripts in `/knowledge_base` using FAISS to ground the bot's intelligence in *your* specific data.
- **PubMed Integration:** Fetches real clinical data using `metapub` to provide science-heavy "Masterclass" content.
- **ReAct/Reflect Logic:** The bot self-corrects its drafts, purging marketing fluff and clichés before you ever see them.
- **YouTube Pipeline:** Automated voiceover generation (Edge-TTS) and video production (MoviePy) to prepare for a faceless YouTube presence.
- **Monetization:** Automatic Amazon Affiliate link generation for discussed supplements.

## Project Structure
- `/knowledge_base`: Drop your PDFs, transcripts, and research here.
- `knowledge_client.py`: Manages the local RAG vector store.
- `llm_client.py`: Handles the Syndicate Persona and Reflection logic.
- `fb_client.py`: Facebook Page API client.
- `telegram_bot.py`: The secure "Syndicate Intel Hub" for remote control.
- `bot.py`: The main autonomous monitor and scheduler (7:00 AM ADT).
- `research_client.py`: PubMed/NCBI science researcher.
- `news_client.py`: Biohacking RSS news desk.
- `affiliate_client.py`: Amazon PAAPI monetization client.
- `video_creator.py`: TTS and Video production engine.

## Setup Instructions
1. **Knowledge Base**: Place your PDFs or `.txt` files in the `/knowledge_base` folder.
2. **Indexing**: Run `python bot.py --index` to build your local intelligence index.
3. **Credentials**: Copy `.env.template` to `.env` and fill in your keys (FB, Telegram, Amazon).
4. **Run the Syndicate**:
   ```bash
   python bot.py --run
   ```

## Telegram Commands (Admin Only)
- `/draft [topic]` - Generate a Syndicate Masterclass draft grounded in RAG + Science.
- `/post [topic]` - IMMEDIATELY post a Masterclass to Facebook.
- `/research [topic]` - Deep-dive into PubMed studies.
- `/video [topic]` - Generate a voiceover script and video file for social media.
- `/pulse` - Analyze community sentiment and trending topics.
- `/index` - Update the knowledge base index after adding new files.
- `/affiliate [keyword]` - Fetch Amazon products and affiliate links.
- `/news` - Get the latest biohacking news roundup.

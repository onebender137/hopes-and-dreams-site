import os
import json
import asyncio
import logging
import time
from datetime import datetime
from functools import wraps
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import Config
from llm_client import LLMClient
from research_client import ResearchClient
from news_client import NewsClient
from affiliate_client import AffiliateClient
from video_creator import VideoCreator
from knowledge_client import KnowledgeClient

# File for simple persistent storage of conversation memory
CHAT_MEMORY_FILE = "chat_memory.json"
UPLINK_LOG_FILE = "syndicate_uplink.log"
SYNDICATE_VERSION = "2.2.3"

# Set up logging for Telegram bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def restricted(func):
    """Decorator to restrict commands to the admin user only."""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        admin_id = str(Config.ADMIN_TELEGRAM_ID)

        if user_id != admin_id:
            print(f"Unauthorized access attempt by {user_id}")
            await update.message.reply_text("⛔ Access Denied. This command is restricted to the administrator.")
            return
        return await func(self, update, context)
    return wrapper

class TelegramBot:
    def __init__(self, hopes_and_dreams_bot=None):
        """Initializes the Hopes and Dreams Syndicate Telegram Agent."""
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.llm = LLMClient()
        self.hdbot = hopes_and_dreams_bot
        self.research = ResearchClient()
        self.news = NewsClient()
        self.affiliate = AffiliateClient()
        self.video = VideoCreator()
        self.knowledge = KnowledgeClient()
        self.last_topic = None

        self.chat_persona = (
            "You are the Lead Technical Researcher for the Hopes and Dreams Syndicate. You are talking in a PRIVATE chat with Bender, your CEO. "
            "Bender is the boss. You are in 'Lead Researcher' mode. Provide direct intelligence. No fluff, no arguing. "
            "OBJECTIVE: Provide a full, actionable protocol by connecting dots across all provided context chunks. "
            "CRITICAL: Stop using 'Data Unavailable' or similar disclaimers if any relevant numbers or data points are found. "
            "You are aware that you have scheduled Facebook Masterclass posts at 7:00 AM, 12:00 PM, and 3:00 PM daily. "
            "You can take requests from Bender for these slots and will prioritize them. "
            "CRITICAL: NEVER use email formatting. NEVER use greetings like \"Dear Bender\" or \"Dear CEO\". "
            "NEVER sign off with \"Best regards\", \"Sincerely\", or your name. Respond with raw conversational text only. "
            "STRICTLY FORBIDDEN: NEVER use placeholders or mention your own name. NEVER use the name 'Dink'. "
            "Your tone is gritty, professional, and science-heavy. "
            "Do not talk like an idiot. Just give him the facts and the research he asks for. "
            "SYNONYM BRIDGE: Treat 'Yuschak', 'LDS Induction', and 'Galantamine protocols' as the same entity. "
            "PARENT DOCUMENT CONTEXT: If a source header or filename is 'Advanced Lucid Dreaming', assume all data in that file is 'Yuschak-approved'."
        )
        self.chat_history = self._load_history()
        self.last_draft = None
        self.last_topic = None
        self.last_image_path = None

    def _load_history(self):
        """Loads chat history from a JSON file."""
        if os.path.exists(CHAT_MEMORY_FILE):
            try:
                with open(CHAT_MEMORY_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_history(self):
        """Saves chat history to a JSON file."""
        try:
            with open(CHAT_MEMORY_FILE, 'w') as f:
                json.dump(self.chat_history, f)
        except IOError as e:
            print(f"Error saving chat history: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /start command."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hi {user.mention_html()}! 👋 This is the Hopes and Dreams Syndicate Intel Hub."
            "\nOllama model: dolphin-llama3:8b | Syndicate Mode Active."
            "\n\nType /help to see all available intel commands."
        )

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /help command."""
        help_text = (
            "<b>📊 SYNDICATE INTEL HUB - COMMAND DIRECTORY</b>\n\n"
            "<b>/clear</b> - Reset memory\n"
            "<b>/draft [topic]</b> - Generate Masterclass draft\n"
            "<b>/confirm</b> - Post draft to FB\n"
            "<b>/draft [topic]</b> - Generate Masterclass draft + image\n"
            "<b>/confirm</b> - Post draft + image to FB + website\n"
            "<b>/regen_img</b> - Regenerate just the image\n"
            "<b>/cancel</b> - Drop the pending draft\n"
            "<b>/post [topic]</b> - Immediate FB post\n"
            "<b>/force_post [text]</b> - Direct raw FB post\n"
            "<b>/pulse</b> - Activity report\n"
            "<b>/check</b> - Monitor FB comments\n"
            "<b>/research [topic]</b> - PubMed search\n"
            "<b>/news [topic]</b> - RSS search\n"
            "<b>/affiliate [keyword]</b> - Amazon search\n"
            "<b>/video [topic]</b> - Video generation\n"
            "<b>/index</b> - Rebuild knowledge index\n"
            "<b>/status</b> - System status report\n"
            "<b>/debug</b> - View uplink logs\n"
            "<b>/test_uplink</b> - Diagnostic website post\n"
            "<b>/sync</b> - Manual repository sync\n"
            "<b>/fix_git</b> - Emergency Git repair"
        )
        await update.message.reply_text(help_text, parse_mode='HTML')

    @restricted
    async def clear_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /clear command to reset chat history."""
        user_id = str(update.effective_user.id)
        if user_id in self.chat_history:
            self.chat_history[user_id] = []
            self._save_history()
        await update.message.reply_text("Memory reset. Re-initializing Syndicate context.")

    @restricted
    async def draft_post_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /draft command with RAG context. Generates image too."""
        if not context.args:
            await update.message.reply_text("Usage: /draft <topic>")
            return
        topic = " ".join(context.args)
        await update.message.reply_text(f"🧠 Generating Masterclass draft on: {topic}\n⏳ This takes ~30s...")

        local_context = self.knowledge.query_knowledge(topic, limit=3)
        draft = await asyncio.to_thread(self.llm.create_biohacking_post, topic, local_context)
        self.last_draft = draft
        self.last_topic = topic

        if not draft:
            await update.message.reply_text("I'm sorry, I couldn't generate a draft right now.")
            return

        # Send draft text first
        await self._send_long_message(update, f"📝 **SYNDICATE MASTERCLASS DRAFT:**\n\n{draft}")

        # Generate image
        await update.message.reply_text("🎨 Generating infographic image...")
        image_path = await asyncio.to_thread(self.hdbot._generate_topic_image, topic)
        self.last_image_path = image_path

        if image_path:
            try:
                with open(image_path, 'rb') as img:
                    await update.message.reply_photo(photo=img, caption=f"🖼️ Image for: {topic}")
            except Exception as e:
                await update.message.reply_text(f"⚠️ Image saved to {image_path} but couldn't display: {e}")
        else:
            await update.message.reply_text("⚠️ Image generation failed. Will use random media on /confirm.")

        await update.message.reply_text(
            "✅ Ready to post.\n"
            "/confirm — post to FB + website\n"
            "/regen_img — regenerate just the image\n"
            "/cancel — drop this draft"
        )

    @restricted
    async def post_immediate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /post [topic] command with RAG context."""
        topic = " ".join(context.args)
        if not topic:
            await update.message.reply_text("Provide a topic! Usage: /post [topic]")
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        local_context = self.knowledge.query_knowledge(topic)
        content = await asyncio.to_thread(self.llm.create_biohacking_post, topic, local_context)

        if content:
            print("EXECUTIVE EXECUTION: Hitting FB Graph API for /post command.")
            result = self.hdbot.fb.post_to_page(content)
            if result:
                await self._send_long_message(update, f"🚀 **LIVE ON FACEBOOK (SYNDICATE MASTERCLASS):**\n\n{content}")

                # 5. Website Transmission Uplink
                print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Initiating website transmission uplink via Telegram...")
                asyncio.create_task(asyncio.to_thread(self.hdbot._post_to_website, content, topic))

                # Record the topic as posted to avoid repeats
                self.hdbot._record_posted_topic(topic)

                # Add affiliate recommendation (non-blocking)
                post_id = result.get('id')
                asyncio.create_task(asyncio.to_thread(self.hdbot._add_affiliate_comment, post_id, topic, content))
            else:
                await update.message.reply_text("❌ Failed to post.")
        else:
            await update.message.reply_text("❌ Could not generate Masterclass.")

    @restricted
    async def force_post_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /force_post command to bypass AI and post directly."""
        text = " ".join(context.args)
        if not text:
            await update.message.reply_text("Provide text! Usage: /force_post [message]")
            return

        print(f"EXECUTIVE EXECUTION: Forced direct post to FB Page ID {Config.FB_PAGE_ID}")
        result = self.hdbot.fb.post_to_page(text)

        if result:
            await update.message.reply_text(f"⚡ **FORCED POST SUCCESSFUL!**\n\nDirect content delivered to FB Page.")
        else:
            await update.message.reply_text("❌ Forced post failed. Check FB API connectivity.")

    @restricted
    async def get_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /status command."""
        import subprocess

        # Get git info
        try:
            branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
            remote = subprocess.check_output(["git", "remote", "-v"]).decode().strip().split('\n')[0]
        except:
            branch = "Unknown"
            remote = "Unknown"

        status_msg = (
            f"🛰 **SYNDICATE STATUS REPORT**\n"
            f"Version: {SYNDICATE_VERSION}\n"
            f"Ollama: {Config.OLLAMA_MODEL}\n"
            f"FB Page: {Config.FB_PAGE_ID}\n"
            f"Branch: {branch}\n"
            f"Remote: {remote}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await update.message.reply_text(status_msg)

    @restricted
    async def get_debug_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /debug command."""
        if os.path.exists(UPLINK_LOG_FILE):
            with open(UPLINK_LOG_FILE, 'r') as f:
                lines = f.readlines()
                log_content = "".join(lines[-20:])
                await self._send_long_message(update, f"📄 **UPLINK DEBUG LOG (Last 20):**\n\n{log_content}")
        else:
            await update.message.reply_text("Uplink log file not found.")

    @restricted
    async def repair_git(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /fix_git command."""
        await update.message.reply_text("🛠 Initializing Emergency Git Repair Protocol...")
        try:
            import subprocess
            import os
            import shutil

            # 1. Kill any stuck rebase or merge
            subprocess.run(["git", "rebase", "--abort"], capture_output=True)
            subprocess.run(["git", "merge", "--abort"], capture_output=True)

            # Manually delete .git/rebase-merge if it still exists
            rebase_path = os.path.join(".git", "rebase-merge")
            if os.path.exists(rebase_path):
                shutil.rmtree(rebase_path)

            # 2. Force remove the offending database if it's untracked and causing issues
            if os.path.exists("syndicate_memory.db"):
                await update.message.reply_text("🧹 Clearing local state conflicts...")
                os.rename("syndicate_memory.db", f"syndicate_memory.db.bak_{int(time.time())}")

            # 3. Detect target branch reliably
            subprocess.run(["git", "fetch", "origin"], capture_output=True)
            remote_branches = subprocess.run(["git", "ls-remote", "--heads", "origin"], capture_output=True, text=True).stdout

            if "refs/heads/main" in remote_branches:
                target_branch = "main"
            elif "refs/heads/master" in remote_branches:
                target_branch = "master"
            else:
                branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
                target_branch = branch_res.stdout.strip()
                if target_branch == "HEAD":
                    target_branch = "main"

            # 4. Recovery Option: Soft reset to origin to keep local articles staged
            await update.message.reply_text(f"📡 Performing Soft Reset to origin/{target_branch} to salvage articles...")
            res = subprocess.run(["git", "reset", "--soft", f"origin/{target_branch}"], capture_output=True, text=True)

            # Clean up non-article junk but keep new articles
            subprocess.run(["git", "clean", "-f", "-e", "articles/", "-e", "intel.html", "-e", "transmissions.html"], capture_output=True)

            if res.returncode == 0:
                await update.message.reply_text(f"✅ Repository restored. Local changes are staged. Use /sync to push salvaged intel to origin/{target_branch}.")
            else:
                await update.message.reply_text(f"❌ Hard reset failed: {res.stderr}")
        except Exception as e:
            await update.message.reply_text(f"❌ Repair failed: {str(e)}")

    @restricted
    async def trigger_sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /sync command."""
        await update.message.reply_text("🔄 Manually triggering Syndicate repository sync...")
        try:
            # We use the bot's internal method
            await asyncio.to_thread(self.hdbot._git_push_changes, "Manual Syndicate Synchronization")
            await update.message.reply_text("✅ Repository sync protocol complete. Check /debug for results.")
        except Exception as e:
            await update.message.reply_text(f"❌ Sync failed: {str(e)}")

    @restricted
    async def test_uplink(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /test_uplink command."""
        await update.message.reply_text("🧪 Initializing diagnostic website uplink...")
        test_topic = f"Diagnostic Test {datetime.now().strftime('%H%M%S')}"
        test_content = "This is a diagnostic transmission to verify website uplink functionality."

        success = await asyncio.to_thread(self.hdbot._post_to_website, test_content, test_topic)

        if success:
            await update.message.reply_text("✅ Diagnostic Uplink Signal: SUCCESS. Check the website and /debug log.")
        else:
            await update.message.reply_text("❌ Diagnostic Uplink Signal: FAILED. Use /debug to see the error log.")

    @restricted
    async def confirm_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /confirm command to push the last draft + image to FB and website."""
        if not self.last_draft:
            await update.message.reply_text("No draft available. Use /draft first!")
            return

        image_path = getattr(self, 'last_image_path', None)
        if not image_path:
            image_path = self.hdbot._get_random_media()

        await update.message.reply_text("📡 Posting to Facebook...")
        print("EXECUTIVE EXECUTION: Confirmed draft being pushed to FB API.")
        result = self.hdbot.fb.post_to_page(self.last_draft, image_path=image_path)

        if result:
            post_id = result.get('id') if isinstance(result, dict) else None
            await update.message.reply_text("✅ Posted to Facebook!\n📡 Pushing to website...")

            asyncio.create_task(asyncio.to_thread(
                self.hdbot._post_to_website,
                self.last_draft,
                self.last_topic,
                image_path
            ))

            if post_id:
                asyncio.create_task(asyncio.to_thread(
                    self.hdbot._add_affiliate_comment,
                    post_id,
                    self.last_topic,
                    self.last_draft
                ))

            await update.message.reply_text("🚀 Syndicate transmission complete.")
            self.last_draft = None
            self.last_topic = None
            self.last_image_path = None
        else:
            await update.message.reply_text("❌ FB post failed.")

    async def regen_img_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Regenerate the image for the current draft."""
        if not self.last_draft or not self.last_topic:
            await update.message.reply_text("No active draft. Use /draft first.")
            return
        await update.message.reply_text("🎨 Regenerating image...")
        image_path = await asyncio.to_thread(self.hdbot._generate_topic_image, self.last_topic)
        self.last_image_path = image_path
        if image_path:
            with open(image_path, 'rb') as img:
                await update.message.reply_photo(photo=img, caption="🖼️ New image. /confirm or /regen_img again.")
        else:
            await update.message.reply_text("⚠️ Image generation failed.")

    async def cancel_draft_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Drop the pending draft."""
        if self.last_draft:
            self.last_draft = None
            self.last_topic = None
            self.last_image_path = None
            await update.message.reply_text("🗑️ Draft discarded.")
        else:
            await update.message.reply_text("No draft to cancel.")

    @restricted
    async def get_pulse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /pulse command."""
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        report = await asyncio.to_thread(self.hdbot.generate_community_report)
        await self._send_long_message(update, f"📈 **SYNDICATE PULSE REPORT:**\n\n{report}")

    @restricted
    async def trigger_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /check command."""
        await update.message.reply_text("🔄 Triggering Syndicate comment monitor...")
        await asyncio.to_thread(self.hdbot.auto_reply_to_recent_interactions)
        await update.message.reply_text("✅ Syndicate Check Complete.")

    @restricted
    async def rebuild_index_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /index command."""
        await update.message.reply_text("🗂 Rebuilding local knowledge index...")
        await asyncio.to_thread(self.knowledge.rebuild_index)
        await update.message.reply_text("✅ Index rebuilt successfully.")

    @restricted
    async def search_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /research command."""
        topic = " ".join(context.args) if context.args else "biohacking"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        studies = await asyncio.to_thread(self.research.search_studies, topic)

        if studies:
            for study in studies:
                post_content = self.research.format_study_as_post(study)
                await self._send_long_message(update, post_content)
        else:
            await update.message.reply_text(f"No research found for: {topic}")

    @restricted
    async def search_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /news command."""
        topic = " ".join(context.args) if context.args else "supplement"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        news = await asyncio.to_thread(self.news.get_latest_news, topic)

        if news:
            update_text = self.news.format_news_for_telegram(news)
            await self._send_long_message(update, update_text)
        else:
            await update.message.reply_text(f"No news found for: {topic}")

    @restricted
    async def search_affiliate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /affiliate command."""
        keyword = " ".join(context.args) if context.args else "magnesium"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        products = await asyncio.to_thread(self.affiliate.search_products, keyword)

        if products:
            for prod in products:
                rec_text = self.affiliate.format_product_as_recommendation(prod)
                await self._send_long_message(update, rec_text)
        else:
            await update.message.reply_text(f"No products found.")

    @restricted
    async def generate_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /video command."""
        topic = " ".join(context.args)
        if not topic:
            await update.message.reply_text("Provide a topic! Usage: /video [topic]")
            return
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        # Hardened prompt — explicit anti-preamble guards
        prompt = (
            f"Write the spoken script ONLY for a 30-second Syndicate-style biohacking video about: {topic}. "
            "OUTPUT RULES (CRITICAL):\n"
            "- Begin with the first sentence of the actual script. NO preamble.\n"
            "- DO NOT write 'Sure', 'Let's', 'Alright', 'Okay', 'Here is', 'Here's the script', or any acknowledgment.\n"
            "- DO NOT write headings, labels, stage directions, brackets, or notes.\n"
            "- DO NOT mention forums, posts, or that this is a script.\n"
            "- Plain spoken prose only. Direct, technical, authoritative tone.\n"
            "- Target ~75 words (about 30 seconds at conversational pace).\n"
            "- Start with a hook sentence. End with a forward-looking statement.\n"
            f"\nBegin the script now about: {topic}"
        )
        content = await asyncio.to_thread(self.llm.generate_response, prompt)

        # Sanitizer — strip any LLM preamble that slipped through
        content = self._strip_script_preamble(content) if content else content

        if content:
            await update.message.reply_text(f"🎥 **PRODUCTION STARTED**\n\nScript:\n'{content}'\n\nGenerating Intel-optimized voiceover...")
            file_path = await self.video.generate_biohacking_snippet(topic, content)

            if file_path.endswith('.mp4'):
                await update.message.reply_video(video=open(file_path, 'rb'))
            elif file_path.endswith('.mp3'):
                await update.message.reply_audio(audio=open(file_path, 'rb'))
            else:
                await update.message.reply_text("Issue generating snippet.")
        else:
            await update.message.reply_text("Could not generate script.")

    def _strip_script_preamble(self, text: str) -> str:
        """
        Removes common LLM preamble/wrapper phrases that leak into video scripts.
        Applies multiple cleanup passes to catch quote wrappers, lead-in phrases,
        section labels, and trailing meta-comments.
        """
        import re
        if not text:
            return text

        cleaned = text.strip()

        # 1. Strip outer quote wrappers ("..." or '...' around the entire response)
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()

        # 2. Drop any leading "Script:" / "Here's the script:" style label lines
        cleaned = re.sub(
            r'^(script|here(\'s| is) the script|here(\'s| is)|video script)[:\-\s]+',
            '',
            cleaned,
            flags=re.IGNORECASE
        )

        # 3. Strip common conversational lead-in phrases up to first sentence break
        # Matches things like "Sure, let's tackle this like we're on the underground forum:"
        lead_in_patterns = [
            r"^(sure|alright|okay|ok|yeah|yes|absolutely|of course|got it|certainly)[\s,]+[^.!?\n]*[.!?:\n]+",
            r"^(let'?s|we'?ll|i'?ll|here'?s|here is)\s+[^.!?\n]{0,80}[.!?:\n]+",
            r"^(no problem|happy to|love to)[\s,]+[^.!?\n]*[.!?:\n]+",
        ]
        for pattern in lead_in_patterns:
            new_cleaned = re.sub(pattern, '', cleaned, count=1, flags=re.IGNORECASE)
            if new_cleaned != cleaned and len(new_cleaned) > 50:
                # Only accept the strip if it didn't nuke the whole script
                cleaned = new_cleaned.strip()

        # 4. Strip leading colons/dashes left from removed labels
        cleaned = re.sub(r'^[:\-\s]+', '', cleaned)

        # 5. Drop any "underground forum" / "we're on the" bullshit phrases
        cleaned = re.sub(r"(like )?we'?re on the (underground|biohacking) forum[\s,:.]*", '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles incoming chat with RAG memory."""
        user_id = str(update.effective_user.id)
        user_message = update.message.text

        # Ensure it's not a command being misrouted (The "Calculon" Bug Fix)
        if user_message.startswith('/'):
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        local_context = self.knowledge.query_knowledge(user_message) if any(kw in user_message.lower() for kw in ["agmatine","kratom","nicotine","nootropic","biohack","supplement","dosage","stack","protocol","melatonin","galantamine","yuschak","astral","lucid","mitochondria","nmda","gaba","dopamine","serotonin","acetylcholine"]) else ""

        if user_id not in self.chat_history:
            self.chat_history[user_id] = []

        self.chat_history[user_id].append({"role": "user", "content": user_message})
        history = self.chat_history[user_id][-10:]

        full_prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
        # Pass stop token to fix ChatML Bleed with Dolphin
        options = {'stop': ['<|im_end|>', 'USER:', 'BENDER:']}
        reply_text = await asyncio.to_thread(self.llm.generate_response, full_prompt, system_message=self.chat_persona, context=local_context, options=options)

        if reply_text:
            self.chat_history[user_id].append({"role": "assistant", "content": reply_text})
            self._save_history()
            await self._send_long_message(update, reply_text)
        else:
            await update.message.reply_text("Issue connecting to Syndicate Intel.")

    def run(self):
        """Starts the Telegram bot application."""
        if not self.token:
            print("TELEGRAM_BOT_TOKEN not found.")
            return

        print("Starting Syndicate Intel Hub...")
        application = ApplicationBuilder().token(self.token).build()

        # Add handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help_cmd))
        application.add_handler(CommandHandler('clear', self.clear_memory))
        application.add_handler(CommandHandler('draft', self.draft_post_cmd))
        application.add_handler(CommandHandler('confirm', self.confirm_post))
        application.add_handler(CommandHandler('post', self.post_immediate))
        application.add_handler(CommandHandler('status', self.get_status))
        application.add_handler(CommandHandler('debug', self.get_debug_log))
        application.add_handler(CommandHandler('test_uplink', self.test_uplink))
        application.add_handler(CommandHandler('sync', self.trigger_sync))
        application.add_handler(CommandHandler('fix_git', self.repair_git))
        application.add_handler(CommandHandler('force_post', self.force_post_direct)) # New command
        application.add_handler(CommandHandler('pulse', self.get_pulse))
        application.add_handler(CommandHandler('check', self.trigger_check))
        application.add_handler(CommandHandler('research', self.search_research))
        application.add_handler(CommandHandler('news', self.search_news))
        application.add_handler(CommandHandler('affiliate', self.search_affiliate))
        application.add_handler(CommandHandler('video', self.generate_video))
        application.add_handler(CommandHandler('regen_img', self.regen_img_cmd))
        application.add_handler(CommandHandler('cancel', self.cancel_draft_cmd))
        application.add_handler(CommandHandler('index', self.rebuild_index_cmd))

        # Ensure commands are not processed as chat
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.chat))

        application.run_polling()

    async def _send_long_message(self, update: Update, text: str):
        """Splits long messages into chunks to avoid Telegram's 4096 character limit."""
        if not text:
            return

        MAX_LENGTH = 4000
        if len(text) <= MAX_LENGTH:
            await update.message.reply_text(text)
            return

        # Split by paragraph first
        paragraphs = text.split('\n')
        current_chunk = ""

        for para in paragraphs:
            # If a single paragraph is somehow longer than MAX_LENGTH, split it by sentences or characters
            if len(para) > MAX_LENGTH:
                # If current_chunk is not empty, send it first
                if current_chunk:
                    await update.message.reply_text(current_chunk.strip())
                    current_chunk = ""

                # Split the long paragraph into smaller pieces
                for i in range(0, len(para), MAX_LENGTH):
                    await update.message.reply_text(para[i:i+MAX_LENGTH])
                continue

            if len(current_chunk) + len(para) + 1 <= MAX_LENGTH:
                current_chunk += para + '\n'
            else:
                await update.message.reply_text(current_chunk.strip())
                current_chunk = para + '\n'

        if current_chunk:
            await update.message.reply_text(current_chunk.strip())

if __name__ == "__main__":
    from bot import HopesAndDreamsBot
    if Config.validate() and Config.TELEGRAM_BOT_TOKEN:
        bot = TelegramBot(hopes_and_dreams_bot=HopesAndDreamsBot())
        bot.run()
    else:
        print("Telegram bot not configured correctly.")

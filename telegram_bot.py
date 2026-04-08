import os
import json
import asyncio
import logging
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

        self.chat_persona = (
            "You are Dink, the Lead Technical Assistant for the Hopes and Dreams Syndicate. You are talking in a PRIVATE chat with Bender, your CEO. "
            "Bender is the boss. You listen to him and provide direct intelligence. No fluff, no arguing, no scripted 'song and dance'. "
            "CRITICAL: NEVER use email formatting. NEVER use greetings like \"Dear Bender\" or \"Dear CEO\". "
            "NEVER sign off with \"Best regards\", \"Sincerely\", or your name. Respond with raw conversational text only. "
            "STRICTLY FORBIDDEN: NEVER use placeholders like '[Assistant's Name]' or '[User Name]'. "
            "Your tone is gritty, professional, and science-heavy, but direct to Bender. "
            "Do not talk like an idiot. Just give him the facts and the research he asks for. "
            "PROTOCOL: When Bender asks about lucid dreaming or the 'Hopes and Dreams protocol', you MUST retrieve and use the specific Amazon.ca affiliate links provided in your local knowledge context. "
            "NEVER use generic links or search for new ones; only use the links provided in the 'product_links.txt' context. "
            "Dink mode active."
        )
        self.chat_history = self._load_history()
        self.last_draft = None

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
            "📊 **SYNDICATE INTEL HUB - COMMAND DIRECTORY**\n\n"
            "**/clear** - Reset memory\n"
            "**/draft [topic]** - Generate Masterclass draft\n"
            "**/confirm** - Post draft to FB\n"
            "**/post [topic]** - Immediate FB post\n"
            "**/force_post [text]** - Direct raw FB post\n"
            "**/pulse** - Activity report\n"
            "**/check** - Monitor FB comments\n"
            "**/research [topic]** - PubMed search\n"
            "**/news [topic]** - RSS search\n"
            "**/affiliate [keyword]** - Amazon search\n"
            "**/video [topic]** - Video generation\n"
            "**/index** - Rebuild knowledge index"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

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
        """Handles the /draft command with RAG context and media preview."""
        topic = " ".join(context.args) if context.args else "current biohacking stack"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        local_context = self.knowledge.query_knowledge(topic)
        draft = await asyncio.to_thread(self.llm.create_biohacking_post, topic, local_context)
        self.last_draft = draft

        if draft:
            # Handle Media Preview (split from text to avoid 1024 char caption limit)
            selected_image = self.hdbot._get_random_media() if self.hdbot else None
            
            if selected_image:
                try:
                    with open(selected_image, 'rb') as photo:
                        await update.message.reply_photo(photo=photo, caption="Media Preview:")
                except Exception as e:
                    print(f"Error sending draft preview photo: {e}")

            await update.message.reply_text(f"📝 **SYNDICATE MASTERCLASS DRAFT:**\n\n{draft}\n\nType /confirm to post.")
        else:
            await update.message.reply_text("I'm sorry, I couldn't generate a draft right now.")

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
                await update.message.reply_text(f"🚀 **LIVE ON FACEBOOK (SYNDICATE MASTERCLASS):**\n\n{content}")
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
    async def confirm_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /confirm command to push the last draft to Facebook."""
        if not self.hdbot:
            await update.message.reply_text("FB client not available.")
            return
        if not self.last_draft:
            await update.message.reply_text("No draft available. Use /draft first!")
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        print("EXECUTIVE EXECUTION: Confirmed draft being pushed to FB API.")
        result = self.hdbot.fb.post_to_page(self.last_draft)

        if result:
            await update.message.reply_text("🚀 Syndicate Masterclass LIVE.")
            self.last_draft = None
        else:
            await update.message.reply_text("❌ Failed to post.")

    @restricted
    async def get_pulse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /pulse command."""
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        report = await asyncio.to_thread(self.hdbot.generate_community_report)
        await update.message.reply_text(f"📈 **SYNDICATE PULSE REPORT:**\n\n{report}")

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
                await update.message.reply_text(post_content)
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
            await update.message.reply_text(update_text)
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
                await update.message.reply_text(rec_text)
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

        prompt = f"Write a technical, Syndicate-style 30-second script about: {topic}."
        content = await asyncio.to_thread(self.llm.generate_response, prompt)

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

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles incoming chat with RAG memory."""
        user_id = str(update.effective_user.id)
        user_message = update.message.text

        # Ensure it's not a command being misrouted (The "Calculon" Bug Fix)
        if user_message.startswith('/'):
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        local_context = self.knowledge.query_knowledge(user_message)

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
            await update.message.reply_text(reply_text)
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
        application.add_handler(CommandHandler('force_post', self.force_post_direct)) # New command
        application.add_handler(CommandHandler('pulse', self.get_pulse))
        application.add_handler(CommandHandler('check', self.trigger_check))
        application.add_handler(CommandHandler('research', self.search_research))
        application.add_handler(CommandHandler('news', self.search_news))
        application.add_handler(CommandHandler('affiliate', self.search_affiliate))
        application.add_handler(CommandHandler('video', self.generate_video))
        application.add_handler(CommandHandler('index', self.rebuild_index_cmd))

        # Ensure commands are not processed as chat
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.chat))

        application.run_polling()

if __name__ == "__main__":
    from bot import HopesAndDreamsBot
    if Config.validate() and Config.TELEGRAM_BOT_TOKEN:
        bot = TelegramBot(hopes_and_dreams_bot=HopesAndDreamsBot())
        bot.run()
    else:
        print("Telegram bot not configured correctly.")

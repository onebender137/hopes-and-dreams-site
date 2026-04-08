import os
import json
import asyncio
import logging
import random
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
        
        # Hardcoded Big Dog Intelligence & Safety Guardrails
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
            "You now have access to Dave Asprey's research on nicotine as a cognitive enhancer in your local knowledge base. Use this data to scientifically back up any questions regarding the nicotine patch protocol. "
            "CRITICAL SAFETY DATA: Huperzine-A dosages MUST always be reported in micrograms (mcg), never milligrams (mg). The Yuschak protocol specifies 200mcg to 400mcg. If you see 'mg' in the context for Huperzine-A, it is a parsing error—correct it to 'mcg' immediately. "
            "KRATOM INTELLIGENCE: Always distinguish between Mitragynine (stimulant/focus) and 7-Hydroxymitragynine (analgesic/sedative). If a user asks for 'Focus', recommend low-dose Mitragynine protocols (1-5g). If they ask about 'Pain', mention 7-OH but warn about the potency of extracts. NEVER recommend doses exceeding 15g. Refer to 'kratom_science.txt' for specific ratios. "
            "DARIUS WRIGHT PROTOCOL: 1. The Window (03:00-04:00 AM), 2. The Stillness (Zero Proprioception), 3. The Visual Gate (The Black Screen), 4. The Transition (Vibrational State), 5. The Exit (Directional Intent). "
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

    def _get_smart_media(self, topic: str):
        """Selects a relevant image from subfolders based on keywords in the topic/draft."""
        base_path = "media"
        mapping = {
            "nicotine": "nicotine", "patch": "nicotine", "asprey": "nicotine",
            "astral": "astral", "dream": "astral", "vibration": "astral", "darius": "astral", "separation": "astral",
            "kratom": "kratom", "alkaloid": "kratom", "mitragynine": "kratom"
        }
        
        subfolder = "general"
        for key, folder in mapping.items():
            if key in topic.lower():
                subfolder = folder
                break
        
        target_dir = os.path.join(base_path, subfolder)
        if not os.path.exists(target_dir):
            target_dir = base_path
            
        try:
            valid_exts = ('.jpg', '.png', '.jpeg')
            files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.lower().endswith(valid_exts)]
            return random.choice(files) if files else None
        except Exception:
            return None

    # --- COMMAND HANDLERS ---

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Initial welcome for the CEO."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hi {user.mention_html()}! 👋 Syndicate Intel Hub is Online."
            "\nOllama model: dolphin-llama3:8b | Syndicate Mode Active."
            "\n\nType /help to see the CEO command directory."
        )

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Full list of Syndicate commands using stable HTML formatting."""
        help_text = (
            "<b>📊 SYNDICATE INTEL HUB - COMMAND DIRECTORY</b>\n\n"
            "<b>/draft [topic]</b> - Generate Masterclass draft + Smart Media preview\n"
            "<b>/confirm</b> - Push the last generated draft to Facebook\n"
            "<b>/post [topic]</b> - Immediate FB post (Auto-selects topic media)\n"
            "<b>/force_post [text]</b> - Direct raw FB post (No AI, just text)\n"
            "<b>/index</b> - Rebuild the 8,000+ chunk knowledge brain\n"
            "<b>/research [topic]</b> - Deep PubMed clinical search & formatting\n"
            "<b>/check</b> - Trigger manual FB comment monitor/reply sweep\n"
            "<b>/pulse</b> - Sentiment & community activity report\n"
            "<b>/news [topic]</b> - Latest biohacking industry news\n"
            "<b>/clear</b> - Reset CEO chat memory\n"
            "<b>/video [topic]</b> - Generate 30s Intel snippet video\n"
            "<b>/affiliate [key]</b> - Quick Amazon.ca monetization search"
        )
        await update.message.reply_text(help_text, parse_mode='HTML')

    @restricted
    async def clear_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if user_id in self.chat_history:
            self.chat_history[user_id] = []
            self._save_history()
        await update.message.reply_text("Memory wiped. Syndicate context re-initialized.")

    @restricted
    async def draft_post_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        topic = " ".join(context.args) if context.args else "biohacking optimization"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        local_context = self.knowledge.query_knowledge(topic)
        draft = await asyncio.to_thread(self.llm.create_biohacking_post, topic, local_context)
        self.last_draft = draft

        if draft:
            selected_image = self._get_smart_media(topic)
            if selected_image:
                try:
                    with open(selected_image, 'rb') as photo:
                        await update.message.reply_photo(photo=photo, caption=f"Smart Media Preview ({selected_image}):")
                except Exception as e:
                    print(f"Error sending draft preview: {e}")

            await update.message.reply_text(f"📝 **MASTERCLASS DRAFT:**\n\n{draft}\n\n/confirm to go live on the Page.")
        else:
            await update.message.reply_text("Failed to generate intelligence draft.")

    @restricted
    async def post_immediate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        topic = " ".join(context.args)
        if not topic:
            await update.message.reply_text("Usage: /post [topic]")
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        local_context = self.knowledge.query_knowledge(topic)
        content = await asyncio.to_thread(self.llm.create_biohacking_post, topic, local_context)

        if content:
            img = self._get_smart_media(topic)
            result = self.hdbot.fb.post_to_page(content, image_path=img)
            if result:
                await update.message.reply_text(f"🚀 **LIVE ON FB:**\nTopic: {topic}\nMedia: {img}")
            else:
                await update.message.reply_text("❌ FB API Post Failed.")
        else:
            await update.message.reply_text("❌ Could not generate content.")

    @restricted
    async def force_post_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = " ".join(context.args)
        if not text:
            await update.message.reply_text("Usage: /force_post [message]")
            return
        result = self.hdbot.fb.post_to_page(text)
        if result:
            await update.message.reply_text("⚡ **FORCED POST SUCCESSFUL.**")
        else:
            await update.message.reply_text("❌ API Error on forced push.")

    @restricted
    async def confirm_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.last_draft:
            await update.message.reply_text("No draft available. Use /draft first.")
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        # For /confirm, we try to use the smart media again based on the last draft content
        img = self._get_smart_media(self.last_draft)
        result = self.hdbot.fb.post_to_page(self.last_draft, image_path=img)

        if result:
            await update.message.reply_text("🚀 Syndicate Intelligence LIVE on Facebook.")
            self.last_draft = None
        else:
            await update.message.reply_text("❌ Push Failed. Check logs.")

    @restricted
    async def get_pulse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        report = await asyncio.to_thread(self.hdbot.generate_community_report)
        await update.message.reply_text(f"📈 **SYNDICATE PULSE:**\n\n{report}")

    @restricted
    async def trigger_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔄 Scanning FB interactions...")
        await asyncio.to_thread(self.hdbot.auto_reply_to_recent_interactions)
        await update.message.reply_text("✅ Comment check and automated reply sweep complete.")

    @restricted
    async def rebuild_index_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🗂 Rebuilding 8,000+ chunk knowledge brain...")
        await asyncio.to_thread(self.knowledge.rebuild_index)
        await update.message.reply_text("✅ RAG Index Rebuilt and saved to vector_db/.")

    @restricted
    async def search_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        topic = " ".join(context.args) if context.args else "biohacking"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        studies = await asyncio.to_thread(self.research.search_studies, topic)
        if studies:
            for s in studies:
                await update.message.reply_text(self.research.format_study_as_post(s))
        else:
            await update.message.reply_text("No clinical data found on PubMed for this topic.")

    @restricted
    async def search_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        topic = " ".join(context.args) if context.args else "nootropics"
        news = await asyncio.to_thread(self.news.get_latest_news, topic)
        if news:
            await update.message.reply_text(self.news.format_news_for_telegram(news))
        else:
            await update.message.reply_text("No biohacking news found.")

    @restricted
    async def search_affiliate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyword = " ".join(context.args)
        if not keyword:
            await update.message.reply_text("Usage: /affiliate [product]")
            return
        # This uses the specific links in product_links.txt primarily
        links = self.affiliate.get_relevant_links(keyword)
        if links:
            await update.message.reply_text(f"💰 **MONETIZATION ASSETS:**\n\n{links}")
        else:
            await update.message.reply_text("No direct matching affiliate assets in context.")

    @restricted
    async def generate_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        topic = " ".join(context.args)
        if not topic:
            await update.message.reply_text("Usage: /video [topic]")
            return
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        prompt = f"Write a technical, Syndicate-style 30-second script about: {topic}."
        content = await asyncio.to_thread(self.llm.generate_response, prompt)
        if content:
            await update.message.reply_text("🎥 Generating Voiceover Intel snippet...")
            file_path = await self.video.generate_biohacking_snippet(topic, content)
            if file_path and os.path.exists(file_path):
                await update.message.reply_video(video=open(file_path, 'rb'))
            else:
                await update.message.reply_text("Video production issue.")

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Conversational chat with Dink using local RAG memory."""
        user_id = str(update.effective_user.id)
        user_message = update.message.text
        if user_message.startswith('/'): return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        local_context = self.knowledge.query_knowledge(user_message)
        
        if user_id not in self.chat_history: self.chat_history[user_id] = []
        self.chat_history[user_id].append({"role": "user", "content": user_message})
        
        # Keep history manageable
        history_segment = self.chat_history[user_id][-10:]
        full_prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history_segment])
        
        options = {'stop': ['<|im_end|>', 'USER:', 'BENDER:']}
        reply_text = await asyncio.to_thread(
            self.llm.generate_response, 
            full_prompt, 
            system_message=self.chat_persona, 
            context=local_context, 
            options=options
        )

        if reply_text:
            self.chat_history[user_id].append({"role": "assistant", "content": reply_text})
            self._save_history()
            await update.message.reply_text(reply_text)

    def run(self):
        """Starts the Telegram application."""
        print("Syndicate Intel Hub Online.")
        app = ApplicationBuilder().token(self.token).build()
        
        # Commands
        app.add_handler(CommandHandler('start', self.start))
        app.add_handler(CommandHandler('help', self.help_cmd))
        app.add_handler(CommandHandler('clear', self.clear_memory))
        app.add_handler(CommandHandler('draft', self.draft_post_cmd))
        app.add_handler(CommandHandler('confirm', self.confirm_post))
        app.add_handler(CommandHandler('post', self.post_immediate))
        app.add_handler(CommandHandler('force_post', self.force_post_direct))
        app.add_handler(CommandHandler('pulse', self.get_pulse))
        app.add_handler(CommandHandler('check', self.trigger_check))
        app.add_handler(CommandHandler('research', self.search_research))
        app.add_handler(CommandHandler('news', self.search_news))
        app.add_handler(CommandHandler('affiliate', self.search_affiliate))
        app.add_handler(CommandHandler('video', self.generate_video))
        app.add_handler(CommandHandler('index', self.rebuild_index_cmd))
        
        # Chat
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.chat))
        
        app.run_polling()

if __name__ == "__main__":
    from bot import HopesAndDreamsBot
    if Config.validate() and Config.TELEGRAM_BOT_TOKEN:
        # Pass in the main bot instance so Telegram can access FB/Research clients
        bot = TelegramBot(hopes_and_dreams_bot=HopesAndDreamsBot())
        bot.run()
    else:
        print("Telegram bot not configured correctly. Check Config.TELEGRAM_BOT_TOKEN.")
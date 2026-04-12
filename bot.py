import os
import json
import time
import argparse
import threading
import random
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone as pytz_timezone
from config import Config
from fb_client import FBClient
from llm_client import LLMClient
from telegram_bot import TelegramBot
from knowledge_client import KnowledgeClient
from research_client import ResearchClient

# Files for persistent storage
REPLIED_COMMENTS_FILE = "replied_comments.json"
CHAT_MEMORY_FILE = "chat_memory.json"

class HopesAndDreamsBot:
    def __init__(self):
        """Initializes the Hopes and Dreams Syndicate Bot with all its agents."""
        self.fb = FBClient()
        self.llm = LLMClient()
        self.knowledge = KnowledgeClient()
        self.research = ResearchClient()

        self.replied_comment_ids = self._load_replied_comments()
        self.initial_startup = not os.path.exists(REPLIED_COMMENTS_FILE)

    def _load_replied_comments(self):
        """Loads the set of comment IDs already replied to from a JSON file."""
        if os.path.exists(REPLIED_COMMENTS_FILE):
            try:
                with open(REPLIED_COMMENTS_FILE, 'r') as f:
                    return set(json.load(f))
            except (json.JSONDecodeError, IOError):
                return set()
        return set()

    def _save_replied_comments(self):
        """Saves the current set of replied comment IDs to a JSON file."""
        try:
            with open(REPLIED_COMMENTS_FILE, 'w') as f:
                json.dump(list(self.replied_comment_ids), f)
        except IOError as e:
            print(f"Error saving replied comments: {e}")

    def get_recent_topics_from_memory(self, slot=None):
        """Extracts potential topics from the Telegram chat history, prioritizing the Admin."""
        if os.path.exists(CHAT_MEMORY_FILE):
            try:
                with open(CHAT_MEMORY_FILE, 'r') as f:
                    history = json.load(f)
                    
                    admin_id = str(Config.ADMIN_TELEGRAM_ID)
                    relevant_messages = []
                    
                    # Prioritize Admin messages
                    if admin_id in history:
                        relevant_messages = [m['content'] for m in history[admin_id][-20:] if m['role'] == 'user']
                    
                    # If admin has no messages, check others
                    if not relevant_messages:
                        for user_id in history:
                            if user_id != admin_id:
                                relevant_messages.extend([m['content'] for m in history[user_id][-20:] if m['role'] == 'user'])

                    if relevant_messages:
                        combined = " | ".join(relevant_messages[-15:])
                        
                        slot_context = f" for the {slot} post" if slot else ""
                        prompt = (
                            f"Analyze these recent messages from the CEO: {combined}\n\n"
                            f"Identify the specific topic or supplement he wants to post about{slot_context}. "
                            "He often mentions topics like lucid dreaming, astral projection, or specific supplements. "
                            "If he explicitly requested a topic for a specific time, prioritize that. "
                            "Return ONLY the topic name (e.g., 'Lucid Dreaming' or 'Magnesium L-Threonate'). "
                            "If no specific topic is found, return 'RANDOM'."
                        )
                        
                        system_msg = "You are an expert content strategist for the Hopes and Dreams Syndicate. You listen to the CEO's specific requests."
                        topic = self.llm.generate_response(prompt, system_msg)
                        
                        if topic and "RANDOM" not in topic.upper() and len(topic) < 100:
                            return topic.strip().replace("'", "").replace("\"", "")
            except (json.JSONDecodeError, IOError, Exception) as e:
                print(f"Error reading chat memory for topics: {e}")

        # Expanded fallback list
        fallbacks = [
            "Lucid Dreaming Techniques", 
            "Astral Projection Guide", 
            "Nicotine as a Nootropic", 
            "Magnesium for Sleep", 
            "Kratom Safety", 
            "The Perfect Supplement Stack"
        ]
        return random.choice(fallbacks)

    def generate_and_post_daily_tip(self, topic=None, slot=None):
        """Generates a daily Syndicate Masterclass and posts it to the Facebook Page."""
        try:
            if not topic:
                print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Identifying topic from chat memory for slot {slot}...")
                topic = self.get_recent_topics_from_memory(slot=slot)

            print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Triggering scheduled Masterclass for topic: {topic}...")

            # 1. RAG Check (Query local knowledge base)
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Querying local knowledge base...")
            local_context = self.knowledge.query_knowledge(topic)

            # 2. Research Check (Query PubMed)
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Searching PubMed studies...")
            pubmed_studies = self.research.search_studies(topic, limit=2)
            research_context = "\n".join([f"Study: {s['title']} - {s['abstract'][:300]}..." for s in pubmed_studies])

            combined_context = f"{local_context}\n\n### PUBMED RESEARCH:\n{research_context}"

            # 3. Generate Masterclass Content (with ReAct/Reflect)
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Generating and reflecting on content...")
            try:
                tip_content = self.llm.create_biohacking_post(topic, combined_context)
            except Exception as inner_e:
                print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Content generation (with reflection) failed: {inner_e}. Retrying without reflection...")
                tip_content = self.llm.generate_response(f"Provide a technical deep-dive and Facebook Masterclass on: {topic}.", context=combined_context, reflect=False)

            if tip_content:
                # 4. Handle Media Attachment
                image_path = self._get_random_media()
                if image_path:
                    print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Media found for payload: {image_path}")
                else:
                    print(f"[{datetime.now()}] EXECUTIVE EXECUTION: No media found, proceeding with text-only payload.")

                print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Hitting FB Graph API for daily tip (Content length: {len(tip_content)}).")
                result = self.fb.post_to_page(tip_content, image_path=image_path)
                if result:
                    print(f"Syndicate Masterclass posted successfully at {datetime.now()}!")
                    return result
                else:
                    print(f"[{datetime.now()}] EXECUTIVE EXECUTION ERROR: Facebook API call failed.")
            else:
                print(f"[{datetime.now()}] EXECUTIVE EXECUTION ERROR: Content generation failed even without reflection.")
        except Exception as e:
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION CRITICAL FAILURE: {e}")

        return None

    def _process_page_comments(self, is_first_iteration=False):
        """Processes comments for all posts in the Page feed."""
        print(f"Checking for new comments in Page feed...")
        recent_posts = self.fb.get_recent_posts()

        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=24)

        for post in recent_posts:
            post_id = post.get('id')
            comments = self.fb.get_comments(post_id)

            for comment in comments:
                comment_id = comment.get('id')
                comment_from = comment.get('from', {})
                comment_author_id = comment_from.get('id')
                comment_created_time_str = comment.get('created_time')

                if comment_author_id == Config.FB_PAGE_ID or comment_id in self.replied_comment_ids:
                    continue

                if is_first_iteration and comment_created_time_str:
                    try:
                        created_time = datetime.strptime(comment_created_time_str, "%Y-%m-%dT%H:%M:%S%z")
                        if created_time < cutoff_time:
                            self.replied_comment_ids.add(comment_id)
                            continue
                    except ValueError:
                        pass

                comment_text = comment.get('message')
                print(f"New comment found on Page from {comment_author_id}: '{comment_text}'")

                # Context-aware reply using RAG
                context = self.knowledge.query_knowledge(comment_text)
                prompt = f"The user asked: '{comment_text}'. Provide a helpful, technical, science-heavy response."
                # Explicitly set reflect=True for public FB replies to ensure quality
                reply_msg = self.llm.generate_response(prompt, context=context, reflect=True)

                if reply_msg:
                    print("EXECUTIVE EXECUTION: Replying to FB comment.")
                    self.fb.reply_to_comment(comment_id, reply_msg)
                    self.replied_comment_ids.add(comment_id)
                    self._save_replied_comments()
                    print(f"Replied to comment {comment_id}")

    def _get_random_media(self):
        """Scans the media/ folder and returns a path to a random jpg or png image."""
        media_dir = "media"
        if not os.path.exists(media_dir):
            return None

        try:
            valid_extensions = ('.jpg', '.png')
            files = [os.path.join(media_dir, f) for f in os.listdir(media_dir) if f.lower().endswith(valid_extensions)]
            if files:
                return random.choice(files)
        except Exception as e:
            print(f"Error scanning media directory: {e}")

        return None

    def auto_reply_to_recent_interactions(self, is_first_iteration=False):
        """Public method to trigger the Facebook comment check."""
        self._process_page_comments(is_first_iteration)

    def generate_community_report(self):
        """Analyzes recent comments and posts a sentiment report."""
        print("Generating community pulse report...")
        recent_posts = self.fb.get_recent_posts()
        all_comments = []
        for post in recent_posts:
            all_comments.extend([c.get('message', '') for c in self.fb.get_comments(post.get('id'))])

        if not all_comments:
            return "No recent community activity to report."

        combined_text = " | ".join(all_comments[:50])
        prompt = f"Analyze these comments from my 'Hopes and Dreams' Page: {combined_text}. Summarize the sentiment and identify the top 3 trending biohacking topics."
        system_msg = "You are a community manager and analyst for the Hopes and Dreams Syndicate."

        report = self.llm.generate_response(prompt, system_msg)
        return report

    def run_fb_loop(self, interval_seconds=3600):
        """Main Facebook bot loop for polling comments."""
        print("Facebook comment monitor loop started.")
        is_first_iteration = self.initial_startup
        try:
            while True:
                self.auto_reply_to_recent_interactions(is_first_iteration)
                is_first_iteration = False
                print(f"FB Monitor sleeping for {interval_seconds} seconds...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("FB monitor loop stopped.")

def run_telegram_bot(hopes_and_dreams_bot):
    """Wrapper to run the Telegram bot."""
    if Config.TELEGRAM_BOT_TOKEN:
        bot = TelegramBot(hopes_and_dreams_bot=hopes_and_dreams_bot)
        bot.run()

def main():
    parser = argparse.ArgumentParser(description="Hopes and Dreams Syndicate Bot (FB Page & Telegram)")
    parser.add_argument("--post-tip", type=str, help="Generate and post a FB Page Masterclass for a topic")
    parser.add_argument("--run", action="store_true", help="Run both FB and Telegram bots concurrently")
    parser.add_argument("--telegram-only", action="store_true", help="Run only the Telegram bot")
    parser.add_argument("--fb-only", action="store_true", help="Run only the Facebook bot loop")
    parser.add_argument("--report", action="store_true", help="Generate a community pulse report")
    parser.add_argument("--index", action="store_true", help="Rebuild the local knowledge base index")

    args = parser.parse_args()

    if not Config.validate():
        return

    bot = HopesAndDreamsBot()

    if args.index:
        bot.knowledge.rebuild_index()
        return

    # Initialize Scheduler with misfire grace time to allow retries of missed jobs
    scheduler = BackgroundScheduler(timezone=pytz_timezone('America/Halifax'))

    # Schedule daily tips at 7:00 AM, 12:00 PM, and 3:00 PM ADT
    # misfire_grace_time=3600 (1 hour) allows the job to run if the bot starts within an hour of the scheduled time
    slots = [
        (7, 0),
        (12, 0),
        (15, 0)
    ]

    for hour, minute in slots:
        slot_str = f"{hour:02d}:{minute:02d}"
        scheduler.add_job(
            bot.generate_and_post_daily_tip,
            CronTrigger(hour=hour, minute=minute),
            kwargs={'slot': slot_str},
            misfire_grace_time=3600,
            coalesce=True,
            id=f"daily_tip_{slot_str}"
        )

    scheduler.start()
    print("Scheduler started: Daily Syndicate Masterclasses scheduled for 07:00, 12:00, and 15:00 ADT.")

    if args.post_tip:
        bot.generate_and_post_daily_tip(args.post_tip)
    elif args.report:
        print(bot.generate_community_report())
    elif args.telegram_only:
        run_telegram_bot(bot)
    elif args.fb_only:
        bot.run_fb_loop()
    elif args.run:
        fb_thread = threading.Thread(target=bot.run_fb_loop, daemon=True)
        fb_thread.start()
        run_telegram_bot(bot)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

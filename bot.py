import os
import subprocess
import re
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
from affiliate_client import AffiliateClient

# Files for persistent storage
REPLIED_COMMENTS_FILE = "replied_comments.json"
CHAT_MEMORY_FILE = "chat_memory.json"
POSTED_TOPICS_FILE = "posted_topics.json"

# Extensive Syndicate Topic Pool for high-variety autonomous brainstorming
SYNDICATE_TOPIC_POOL = [
    "Huperzine-A", "Alpha GPC", "5-HTP", "Agmatine Sulfate", "Magnesium Bisglycinate",
    "Nicotine Patches", "Citicoline (CDP-Choline)", "L-Theanine", "Lion's Mane Mushroom",
    "Ashwagandha (KSM-66)", "Omega-3 Fish Oil", "Rhodiola Rosea", "Bacopa Monnieri",
    "Phosphatidylserine", "N-Acetyl L-Tyrosine", "Uridine Monophosphate", "Creatine Monohydrate",
    "Astral Projection", "Lucid Dreaming", "Kratom", "Autophagy induction", "BDNF optimization",
    "Binaural Beats", "GABA for anxiety", "Glycine for sleep", "Heart Rate Variability (HRV)",
    "Vagus Nerve Stimulation", "Prefrontal Cortex Optimization", "Circadian Rhythm alignment",
    "Cold Exposure / Ice Baths", "Sauna Therapy / Heat Shock Proteins", "Dopamine Fasting",
    "Intermittent Fasting", "Deep Sleep Optimization", "Neurogenesis", "Sleep Hygiene",
    "Melatonin alternatives", "L-Dopa / Mucuna Pruriens", "Sulbutiamine", "Noopept",
    "Aniracetam", "Phenylpiracetam", "Sunlight Exposure", "Earthing / Grounding",
    "Red Light Therapy", "Methylene Blue", "NAD+ Boosters", "Resveratrol & NMN",
    "Brain Training", "Meditation Protocols", "Flow State triggers", "Ketosis / Exogenous Ketones",
    "Microdosing (Educational)", "Caffeine Optimization", "Yoga Nidra / NSDR", "Polyphasic Sleep",
    "Blue Light Blocking", "Cordyceps for energy", "Reishi for immunity", "Peptides (BPC-157/TB-500)",
    "Testosterone Optimization", "Cortisol Management", "Gut Microbiome / Probiotics",
    "Breathwork (Wim Hof/Box Breathing)", "Hypnotherapy", "Galantamine Protocol",
    "Calea Zacatechichi (Dream Herb)", "Valerian Root", "Kava Kava", "Mitochondrial Health / PQQ",
    "Senolytics (Quercetin/Fisetin)", "Blood Glucose Monitoring (CGM)", "Inflammation Control",
    "Glutathione / NAC", "Vitamin D3 & K2 Synergy", "Heavy Metal Detox", "Neurofeedback",
    "tDCS / Transcranial Stimulation", "PEMF Therapy", "Sensory Deprivation / Float Tanks",
    "Quantified Self / Biometric Tracking", "Nutrigenomics", "Deep Work / Productivity biohacks",
    "Hormetic Stressors", "Synaptic Plasticity", "The Yuschak Method", "WBTB / MILD / WILD techniques",
    "Remote Viewing (Speculative)", "Qi / Bio-energy optimization", "Blood Flow Restriction (BFR)",
    "Stem Cell Regeneration", "Telomere maintenance", "HPA Axis balance", "Endocannabinoid System",
    "Liposomal delivery systems", "Cerebrolysin / Semax / Selank (Technical)", "Memory Palaces / Loci",
    "Spaced Repetition / Anki", "Identity Shifting", "Stress Inoculation",
    "Social Connection biohacking", "Altruism & Neurobiology", "Stoicism for Resilience"
]

class HopesAndDreamsBot:
    def __init__(self):
        """Initializes the Hopes and Dreams Syndicate Bot with all its agents."""
        self.fb = FBClient()
        self.llm = LLMClient()
        self.knowledge = KnowledgeClient()
        self.research = ResearchClient()
        self.affiliate = AffiliateClient()

        self.replied_comment_ids = self._load_replied_comments()
        self.posted_topics = self._load_posted_topics()
        self.initial_startup = not os.path.exists(REPLIED_COMMENTS_FILE)

    def _load_posted_topics(self):
        """Loads the list of recently posted topics from a JSON file."""
        if os.path.exists(POSTED_TOPICS_FILE):
            try:
                with open(POSTED_TOPICS_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_posted_topics(self):
        """Saves the current list of posted topics to a JSON file."""
        try:
            with open(POSTED_TOPICS_FILE, 'w') as f:
                json.dump(self.posted_topics, f)
        except IOError as e:
            print(f"Error saving posted topics: {e}")

    def _record_posted_topic(self, topic):
        """Records a new posted topic, keeping only the last 50 to avoid staleness."""
        if topic in self.posted_topics:
            self.posted_topics.remove(topic)
        self.posted_topics.append(topic)
        if len(self.posted_topics) > 50:
            self.posted_topics.pop(0)
        self._save_posted_topics()

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

        # No explicit request found or error occurred; brainstorm an autonomous topic
        return self.brainstorm_autonomous_topic()

    def brainstorm_autonomous_topic(self):
        """Uses the LLM to brainstorm a fresh, diverse biohacking topic from the Syndicate Pool."""
        print(f"[{datetime.now()}] EXECUTIVE BRAINSTORM: Generating fresh intelligence...")

        # Filter pool to avoid very recent repeats
        available_pool = [t for t in SYNDICATE_TOPIC_POOL if t not in self.posted_topics]
        if not available_pool:
            available_pool = SYNDICATE_TOPIC_POOL # Reset if somehow exhausted

        # Sample a subset to give the LLM choices without overwhelming context
        sample_size = min(30, len(available_pool))
        candidates = random.sample(available_pool, sample_size)

        system_msg = (
            "You are the Syndicate's Lead Content Strategist. Your goal is to keep the community engaged "
            "by providing fresh, diverse, and cutting-edge biohacking intel. You avoid repeating yourself."
        )

        prompt = (
            f"Brainstorm a specific, compelling topic for today's Facebook Masterclass.\n\n"
            f"RECENTLY POSTED TOPICS: {', '.join(self.posted_topics[-10:])}\n\n"
            f"POTENTIAL SEED KEYWORDS: {', '.join(candidates)}\n\n"
            "INSTRUCTIONS:\n"
            "1. Pick a keyword from the seed list OR brainstorm a closely related alternative biohack/supplement.\n"
            "2. Ensure it has NOT been posted recently.\n"
            "3. The topic should be punchy and professional (e.g., 'The Neurobiology of Sulbutiamine' or 'Optimizing HRV with Cold Thermogenesis').\n"
            "4. Return ONLY the topic name. No fluff. No punctuation."
        )

        try:
            topic = self.llm.generate_response(prompt, system_msg)
            if topic and len(topic) < 100:
                final_topic = topic.strip().replace("'", "").replace("\"", "")
                return final_topic
        except Exception as e:
            print(f"Brainstorming failed: {e}")

        # Ultimate fallback from the pool
        return random.choice(available_pool)

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
                    # 5. Website Transmission Uplink
                    print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Initiating website transmission uplink...")
                    self._post_to_website(tip_content, topic, image_path)
                    print(f"Syndicate Masterclass posted successfully at {datetime.now()}!")

                    # Record the topic as posted to avoid repeats
                    self._record_posted_topic(topic)

                    # Add affiliate recommendation in the comments
                    post_id = result.get('id')
                    self._add_affiliate_comment(post_id, topic)

                    return result
                else:
                    print(f"[{datetime.now()}] EXECUTIVE EXECUTION ERROR: Facebook API call failed.")
            else:
                print(f"[{datetime.now()}] EXECUTIVE EXECUTION ERROR: Content generation failed even without reflection.")
        except Exception as e:
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION CRITICAL FAILURE: {e}")

        return None

    def _add_affiliate_comment(self, post_id, topic):
        """Searches for a product related to the topic and posts it as a comment."""
        if not post_id or not topic:
            return

        print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Adding affiliate recommendation for {topic} to post {post_id}...")

        # Give FB a few seconds to index the post
        time.sleep(5)

        products = self.affiliate.search_products(topic, limit=1)

        if products:
            recommendation = self.affiliate.format_product_as_recommendation(products[0])
        else:
            # Fallback to manual link
            manual_link = self.affiliate.generate_canadian_link(topic)
            pitch = f"For those looking to optimize their protocol with {topic}, here is the top-vetted option on Amazon.ca."
            recommendation = self.affiliate.format_affiliate_payload(pitch, manual_link)

        result = self.fb.reply_to_comment(post_id, recommendation)
        if result:
            print(f"Affiliate recommendation posted to post {post_id} successfully.")
        else:
            print(f"Failed to post affiliate recommendation to post {post_id}.")

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


    def _post_to_website(self, content, topic, image_path=None):
        """Beautifies the content and posts it to the website (articles/ and intel.html)."""
        os.makedirs("articles", exist_ok=True)
        print(f"[{datetime.now()}] WEBSITE UPLINK: Initializing Syndicate Transmission for {topic}...")

        # 1. Beautify content using LLM
        beautified_html = self._beautify_for_blog(content, topic, image_path)

        # 2. Generate slug and filename
        date_str = datetime.now().strftime("%Y-%m-%d")
        slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')
        filename = f"{date_str}-{slug}.html"
        filepath = os.path.join("articles", filename)

        # 3. Save the article
        try:
            with open(filepath, 'w') as f:
                f.write(beautified_html)
            print(f"[{datetime.now()}] WEBSITE UPLINK: Article saved to {filepath}")
        except Exception as e:
            print(f"[{datetime.now()}] WEBSITE UPLINK ERROR: Failed to save article: {e}")
            return False

        # 4. Update intel.html (Latest 3)
        self._update_intel_html(topic, filename, date_str)

        # 5. Update transmissions.html (Archive)
        self._update_transmissions_html(topic, filename, date_str)

        # 6. Git Commit and Push
        self._git_push_changes(f"Syndicate Transmission: {topic}")

        return True

    def _beautify_for_blog(self, content, topic, image_path):
        """Uses the LLM to wrap the raw content in the beautiful blog template."""
        system_msg = (
            "You are the Syndicate's Digital Architect. Your job is to take raw biohacking intel "
            "and format it into a high-end HTML article template."
        )

        # Load template
        template_path = "articles/template.html"
        try:
            with open(template_path, 'r') as f:
                template = f.read()
        except:
            template = "<h1>{{TITLE}}</h1><p>{{CONTENT}}</p>" # Fallback

        prompt = (
            f"I have a new Syndicate Masterclass about '{topic}'.\n\n"
            f"RAW CONTENT:\n{content}\n\n"
            "INSTRUCTIONS:\n"
            "1. Rewrite the content to be more 'beautified' for a blog post. Use engaging headers.\n"
            "2. Identify the most actionable advice and mark it for a 'Prostar Life Hack' box.\n"
            "3. Return the FINAL HTML by injecting this content into the provided template.\n"
            "4. Use the following placeholders in the template (if they exist or create a structure that fits):\n"
            "   - Replace the title tag and H1 with the topic title.\n"
            "   - Use <span class='meta-data'> for the date and category.\n"
            "   - Put the main content in the <article> section.\n"
            "   - Ensure the 'Prostar Life Hack' is in a <div class='hack-box'>.\n"
            f"   - If an image is provided ({image_path}), ensure the src attribute is prefixed with '../' (e.g., src='../{image_path}') since this article lives in the articles/ subfolder, use it in an <img> tag with class 'article-img'. "
            "     If image_path is None, do NOT include an <img> tag for the featured image.\n"
            "5. Return ONLY the full HTML code. No talk."
        )
        return self.llm.generate_response(prompt, system_msg, context=template, reflect=True, options={'num_ctx': 4096})
        # We use a higher context window and reflection for better HTML generation
        html_response = self.llm.generate_response(prompt, system_msg, context=template, reflect=True, options={'num_ctx': 4096})

        # Cleanup: Strip markdown code blocks if present
        if "```" in html_response:
            # Match content between ```html and ``` or just ``` and ```
            match = re.search(r'```(?:html)?\n?(.*?)\n?```', html_response, re.DOTALL)
            if match:
                html_response = match.group(1).strip()

        return html_response
    def _update_intel_html(self, topic, filename, date_str):
        """Updates the intel.html file with the latest 3 posts."""
        print(f"[{datetime.now()}] WEBSITE UPLINK: Syncing intel.html...")
        try:
            with open("intel.html", 'r') as f:
                html = f.read()

            new_card = (
                f'                <div class="card">\n'
                f'                    <div class="meta-data" style="font-size: 0.7rem; color: var(--neon-gold); margin-bottom: 10px;">TRANSMISSION: {date_str}</div>\n'
                f'                    <h3>{topic}</h3>\n'
                f'                    <p>{topic} protocol initialized. Access the full intel burst below.</p>\n'
                f'                    <a href="articles/{filename}" class="buy-btn" style="font-size: 0.7rem; padding: 8px 16px;">View Intel →</a>\n'
                f'                </div>'
            )

            # Find the posts block
            start_marker = "<!-- LATEST_3_POSTS_START -->"
            end_marker = "<!-- LATEST_3_POSTS_END -->"

            pattern = re.compile(f"{start_marker}.*?{end_marker}", re.DOTALL)
            match = pattern.search(html)

            if match:
                current_posts_block = match.group(0)
                # Extract individual cards
                cards = re.findall(r'<div class="card">.*?</div>', current_posts_block, re.DOTALL)

                # Filter out the "Initializing Feed" placeholder if this is the first real post
                cards = [c for c in cards if "Initializing Feed" not in c and "Waiting for Uplink" not in c and "Data Stream Alpha" not in c]

                # Add new card to the beginning
                cards.insert(0, new_card)

                # Keep only latest 3
                cards = cards[:3]

                new_posts_block = f"{start_marker}\n" + "\n".join(cards) + f"\n                {end_marker}"
                html = html.replace(current_posts_block, new_posts_block)

                # Also update the archive preview list in intel.html
                archive_start = "<!-- OLDER_POSTS_START -->"
                archive_end = "<!-- OLDER_POSTS_END -->"
                archive_pattern = re.compile(f"{archive_start}.*?{archive_end}", re.DOTALL)
                archive_match = archive_pattern.search(html)

                if archive_match:
                    current_archive_block = archive_match.group(0)
                    new_archive_item = f'<li style="margin-bottom: 10px;"><a href="articles/{filename}" style="color: var(--text-dim); text-decoration: none; font-size: 0.85rem;">[{date_str}] {topic}</a></li>'

                    archive_items = re.findall(r'<li.*?>.*?</li>', current_archive_block, re.DOTALL)
                    archive_items = [i for i in archive_items if "No archived transmissions found" not in i]

                    archive_items.insert(0, new_archive_item)
                    archive_items = archive_items[:5] # Show only last 5 in the sidebar list

                    new_archive_block = f"{archive_start}\n                    " + "\n                    ".join(archive_items) + f"\n                    {archive_end}"
                    html = html.replace(current_archive_block, new_archive_block)

                with open("intel.html", 'w') as f:
                    f.write(html)
        except Exception as e:
            print(f"[{datetime.now()}] WEBSITE UPLINK ERROR: Failed to update intel.html: {e}")

    def _update_transmissions_html(self, topic, filename, date_str):
        """Updates the transmissions.html archive page."""
        print(f"[{datetime.now()}] WEBSITE UPLINK: Syncing transmissions.html...")
        try:
            with open("transmissions.html", 'r') as f:
                html = f.read()

            new_item = (
                f'            <a href="articles/{filename}" class="archive-item">\n'
                f'                <span class="title">{topic}</span>\n'
                f'                <span class="date">{date_str}</span>\n'
                f'            </a>'
            )

            start_marker = "<!-- ARCHIVE_POSTS_START -->"
            end_marker = "<!-- ARCHIVE_POSTS_END -->"

            pattern = re.compile(f"{start_marker}.*?{end_marker}", re.DOTALL)
            match = pattern.search(html)

            if match:
                current_block = match.group(0)
                items = re.findall(r'<a.*?class="archive-item">.*?</a>', current_block, re.DOTALL)

                # Filter placeholder
                items = [i for i in items if "Initializing deep archive retrieval" not in i]

                items.insert(0, new_item)

                new_block = f"{start_marker}\n" + "\n".join(items) + f"\n            {end_marker}"
                html = html.replace(current_block, new_block)

                with open("transmissions.html", 'w') as f:
                    f.write(html)
        except Exception as e:
            print(f"[{datetime.now()}] WEBSITE UPLINK ERROR: Failed to update transmissions.html: {e}")

    def _git_push_changes(self, commit_message):
        """Automates the git workflow to push changes to the repository."""
        print(f"[{datetime.now()}] GIT AUTOMATION: Committing changes...")
        try:
            # Safely add only relevant files
            subprocess.run(["git", "add", "intel.html", "transmissions.html", "articles/"], check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            print(f"[{datetime.now()}] GIT AUTOMATION: Pushing to remote...")
            subprocess.run(["git", "push"], check=True)
            print(f"[{datetime.now()}] GIT AUTOMATION: Uplink successful.")
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.now()}] GIT AUTOMATION ERROR: Command failed: {e}")
        except Exception as e:
            print(f"[{datetime.now()}] GIT AUTOMATION ERROR: {e}")
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

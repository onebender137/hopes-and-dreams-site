# --- PHOENIX OBSERVABILITY INITIALIZATION ---
import os
# Set environment variables BEFORE any other imports to lock in Phoenix project
os.environ["PHOENIX_PROJECT_NAME"] = "syndicate-intelligence"
# Use OTLP HTTP collector to avoid gRPC binding conflicts on MSI Claw hardware
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://localhost:6006"

import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.instrumentation.crewai import CrewAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor

# Start Phoenix in the background
try:
    session = px.launch_app()
    print(f"Phoenix Observability Dashboard launched at: {session.url}")
except Exception as e:
    print(f"Warning: Failed to launch Phoenix app: {e}")

# Register the tracer provider - explicitly using HTTP exporter
tracer_provider = register(
    project_name="syndicate-intelligence",
    endpoint="http://localhost:6006/v1/traces",
    auto_instrument=True
)

# Instrument LangChain, CrewAI, and LiteLLM (for local Ollama traces)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
CrewAIInstrumentor().instrument(tracer_provider=tracer_provider)
LiteLLMInstrumentor().instrument(tracer_provider=tracer_provider)
# ---------------------------------------------

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
from database_client import SyndicateDatabase
from crew_brain import SyndicateCrew

# Files for persistent storage
REPLIED_COMMENTS_FILE = "replied_comments.json"
CHAT_MEMORY_FILE = "chat_memory.json"
POSTED_TOPICS_FILE = "posted_topics.json"
# Imported from telegram_bot to maintain consistency and avoid circular imports
from telegram_bot import UPLINK_LOG_FILE, SYNDICATE_VERSION

# Extensive Syndicate Topic Pool for high-variety autonomous brainstorming
SYNDICATE_TOPIC_POOL = [
    "Huperzine-A", "Alpha GPC", "5-HTP", "Agmatine Sulfate", "Magnesium Bisglycinate",
    "Nicotine Patches", "Citicoline (CDP-Choline)", "L-Theanine", "Lion's Mane Mushroom",
    "Ashwagandha (KSM-66)", "Omega-3 Fish Oil", "Rhodiola Rosea", "Bacopa Monnieri",
    "Phosphatidylserine", "N-Acetyl L-Tyrosine", "Uridine Monophosphate", "Creatine Monohydrate",
    "Lucid Dreaming", "Kratom", "Autophagy induction", "BDNF optimization",
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
    "Social Connection biohacking", "Altruism & Neurobiology", "Stoicism for Resilience",

    # === PEPTIDES (12) ===
    "BPC-157 Healing Protocols", "TB-500 Tissue Repair", "GHK-Cu (Copper Peptide)",
    "Selank for Anxiolytic Calm", "Semax for Cognitive Drive", "Epitalon for Telomere Length",
    "MOTS-c Mitochondrial Peptide", "Thymosin Alpha-1 Immune Modulation",
    "Ipamorelin GH Pulse", "DSIP Sleep Peptide", "AOD-9604 Fat Loss Peptide",
    "Pinealon Cognitive Peptide",

    # === MITOCHONDRIAL & ENERGY (8) ===
    "CoQ10 vs Ubiquinol Bioavailability", "Urolithin A Mitophagy",
    "PQQ Mitochondrial Biogenesis", "Methylene Blue Microdosing Protocol",
    "NMN vs NR Bioavailability", "Nicotinamide Riboside Daily Dosing",
    "Mitochondrial Uncoupling Strategies", "Alpha-Lipoic Acid Glucose Pathway",

    # === STACK-DRIVEN MASTERCLASSES (10) ===
    "The WBTB Lucid Dreaming Stack", "The Calm-Focus Stack (L-Theanine + Caffeine)",
    "Post-Workout Recovery Stack", "Sleep Architecture Stack",
    "Morning Cognitive Activation Stack", "Anxiolytic Without Sedation Stack",
    "Pre-Cardio Endurance Stack", "Memory Consolidation Stack",
    "Cortisol Down-Regulation Stack", "Acetylcholine Optimization Stack",

    # === LIGHT, EMF, ENVIRONMENTAL (8) ===
    "Red Light 660nm vs 850nm Wavelength Selection", "EMF Mitigation Strategies",
    "Blue Light Timing for Circadian Rhythm", "UV-B Exposure for Vitamin D Synthesis",
    "Infrared Sauna Heat Shock Proteins", "Negative Ion Exposure",
    "Faraday Cage Sleep Optimization", "Air Quality and Cognitive Performance",

    # === PHARMACOLOGY PATHWAYS (10) ===
    "Sigma-1 Receptor Agonism", "mTOR Pathway Modulation",
    "AMPK Activation for Longevity", "Sirtuin Pathway Optimization",
    "Adenosine Receptor Antagonism", "Endocannabinoid Tone Modulation",
    "Glutamate Excitotoxicity Mitigation", "Cholinergic System Tuning",
    "Serotonin Receptor Subtype Selectivity", "Dopaminergic Tolerance Management",

    # === HORMONAL OPTIMIZATION (6) ===
    "DHEA Supplementation Protocols", "Pregnenolone for Neurosteroid Balance",
    "T3/T4 Thyroid Conversion Optimization", "Estrogen Metabolism Pathways",
    "Growth Hormone Pulse Optimization", "Insulin Sensitivity Restoration",

    # === RECOVERY & PERFORMANCE SCIENCE (6) ===
    "Lactate Threshold Training", "HRV-Guided Training Periodization",
    "Contrast Therapy Hot-Cold Protocols", "Active Recovery vs Passive",
    "Zone 2 Cardio for Mitochondrial Density", "Eccentric Loading for Tendon Health",
]

class HopesAndDreamsBot:
    def _log_uplink(self, message):
        """Logs a message to the uplink log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        with open(UPLINK_LOG_FILE, "a") as f:
            f.write(log_entry)
        print(log_entry.strip())

    def __init__(self):
        """Initializes the Hopes and Dreams Syndicate Bot with all its agents."""
        self.fb = FBClient()
        self.llm = LLMClient()
        self.knowledge = KnowledgeClient()
        self.research = ResearchClient()
        self.affiliate = AffiliateClient()
        # Check for DB existence BEFORE initializing SyndicateDatabase
        db_exists = os.path.exists("syndicate_memory.db")
        self.db = SyndicateDatabase()
        self.crew = SyndicateCrew()
        self.website_path = "."

        # Perform one-time migration if JSON files exist
        if os.path.exists(REPLIED_COMMENTS_FILE) or os.path.exists(POSTED_TOPICS_FILE):
            print(f"[{datetime.now()}] DATA LAYER: Detected legacy JSON storage. Migrating to SQLite...")
            self.db.migrate_from_json(POSTED_TOPICS_FILE, REPLIED_COMMENTS_FILE)

            # Backup and remove legacy files
            for f in [POSTED_TOPICS_FILE, REPLIED_COMMENTS_FILE]:
                if os.path.exists(f):
                    os.rename(f, f + ".bak")

        self.replied_comment_ids = self._load_replied_comments()
        self.posted_topics = self._load_posted_topics()
        self.initial_startup = not db_exists

    def _load_posted_topics(self):
        """Loads the list of recently posted topics from SQLite."""
        return self.db.get_recent_topics(limit=50)

    def _save_posted_topics(self):
        """Deprecated: SQLite saves automatically."""
        pass

    def _record_posted_topic(self, topic):
        """Records a new posted topic to SQLite."""
        self.db.add_posted_topic(topic)
        # Update local cache for immediate use if needed
        self.posted_topics = self._load_posted_topics()

    def _load_replied_comments(self):
        """Loads the set of comment IDs already replied to from SQLite."""
        return self.db.get_all_replied_comments()

    def _save_replied_comments(self):
        """Deprecated: SQLite saves automatically."""
        pass

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
                            "DO NOT include meta-commentary like 'The topic requested is...', 'He wants to post about...', or 'The specific topic requested by the CEO for the XX:XX post is...'. "
                            "STRICTLY return the topic name itself. "
                            "If no specific topic is found, return 'RANDOM'."
                        )
                        
                        system_msg = "You are an expert content strategist for the Hopes and Dreams Syndicate. You listen to the CEO's specific requests."
                        topic = self.llm.generate_response(prompt, system_msg)
                        
                        if topic and "RANDOM" not in topic.upper() and len(topic) < 100:
                            topic = topic.strip().replace("'", "").replace("\"", "")
                            # Meta-commentary cleanup for requested topics
                            topic = re.sub(r'(?i)The specific topic requested by the CEO for the \d{2}:\d{2} post is\s+', '', topic)
                            topic = re.sub(r'(?i)post with title\s+', '', topic)
                            topic = re.sub(r'(?i)Masterclass:\s*', '', topic)
                            return topic.strip()
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
            "2. STICK TO TECHNICAL PHARMACOLOGY AND PHYSIOLOGY. No 'wellness', 'mindfulness', or 'spirituality'.\n"
            "3. DO NOT mix unrelated topics (e.g., do NOT link astral projection with telomeres).\n"
            "4. AVOID esoteric topics unless they are being analyzed through a strictly biological/pharmacological lens.\n"
            "5. Ensure it has NOT been posted recently.\n"
            "6. The topic should be punchy and professional (e.g., 'The Neurobiology of Sulbutiamine' or 'Optimizing HRV with Cold Thermogenesis').\n"
            "7. Return ONLY the topic name. No fluff. No punctuation."
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

            # 3. Generate Masterclass Content
            # Routes through create_biohacking_post() which has the headline patch
            # AND runs through _sanitize_output() to strip markdown bold from CrewAI.
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Generating headlined Masterclass for {topic}...")
            try:
                tip_content = self.crew.run(topic, combined_context)
                # CrewAI agents skip our headline rules and leak markdown - sanitize manually
                tip_content = self.llm._sanitize_output(tip_content)
            except Exception as inner_e:
                print(f"[{datetime.now()}] EXECUTIVE EXECUTION: CrewAI failed: {inner_e}. Using create_biohacking_post fallback...")
                tip_content = self.llm.create_biohacking_post(topic, context=combined_context)

            if tip_content and not self._is_bad_content(tip_content):
                # 4. Handle Media Attachment — generate topic-specific image first
                image_path = self._generate_topic_image(topic)
                if not image_path:
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
                    self._add_affiliate_comment(post_id, topic, tip_content)

                    return result
                else:
                    print(f"[{datetime.now()}] EXECUTIVE EXECUTION ERROR: Facebook API call failed.")
            else:
                print(f"[{datetime.now()}] EXECUTIVE EXECUTION ERROR: Content generation failed even without reflection.")
        except Exception as e:
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION CRITICAL FAILURE: {e}")

        return None

    def _extract_clean_affiliate_keyword(self, topic, content=None):
        """Uses the LLM to extract a clean, searchable product keyword from a topic/content."""
        system_msg = "You are the Syndicate's Inventory Specialist. Your job is to identify a single, specific product or supplement for Amazon search."

        prompt = (
            f"Analyze this topic: '{topic}'\n"
            f"{f'And this content excerpt: {content[:500]}...' if content else ''}\n\n"
            "INSTRUCTIONS:\n"
            "1. Identify the core supplement, compound, or biohacking tool mentioned.\n"
            "2. If the topic is a messy command (e.g., 'a post called...'), ignore the command fluff and find the actual subject.\n"
            "3. Return ONLY the name of the product (e.g., 'Alpha GPC' or 'Nicotine Patches').\n"
            "4. NO punctuation, NO meta-commentary, NO 'The product is...'.\n"
            "5. If multiple are found, pick the most central one.\n"
            "6. If none are found, return the original topic cleaned of obvious command prefixes."
        )

        try:
            clean_keyword = self.llm.generate_response(prompt, system_msg, sanitize=True)
            if clean_keyword and len(clean_keyword) < 50:
                return clean_keyword.strip()
        except Exception as e:
            print(f"Keyword extraction failed: {e}")

        # Fallback: Basic cleanup of common prefixes if LLM fails
        clean_topic = re.sub(r'(?i)^(?:a post called|draft a post about|post about)\s+', '', topic)
        return clean_topic.strip()

    def _add_affiliate_comment(self, post_id, topic, content=None):
        """Searches for a product related to the topic and posts it as a comment."""
        if not post_id or not topic:
            return

        # Extract a clean keyword for better product matching
        clean_keyword = self._extract_clean_affiliate_keyword(topic, content)
        print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Adding affiliate recommendation for {clean_keyword} (Topic: {topic}) to post {post_id}...")

        # Give FB a few seconds to index the post
        time.sleep(5)

        products = self.affiliate.search_products(clean_keyword, limit=1)

        if products:
            product_title = products[0]['title']
            product_url = products[0]['url']
        else:
            product_title = clean_keyword
            product_url = self.affiliate.generate_canadian_link(clean_keyword)

        # Generate a human-like, peer-to-peer pitch
        prompt = (
            f"Write a 1-2 sentence recommendation for {product_title}. "
            "Tone: Peer-to-peer biohacker, underground, technical, NO marketing fluff. "
            "Explain briefly why someone would want this for their protocol. "
            "Do NOT include links or disclosures yet."
        )

        try:
            pitch = self.llm.generate_response(prompt, self.llm.public_syndicate_persona)
            # Use the new formatting logic which handles sanitation and disclosure
            recommendation = self.affiliate.format_affiliate_payload(pitch, product_url)
        except Exception as e:
            self._log_uplink(f"AFFILIATE ERROR: Failed to generate pitch: {e}")
            # Fallback
            pitch = f"Vetted source for {topic} optimization."
            recommendation = self.affiliate.format_affiliate_payload(pitch, product_url)

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
                    self.db.add_replied_comment(comment_id)
                    self.replied_comment_ids.add(comment_id)
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

    def _is_bad_content(self, content):
        """Detect LLM refusals, errors, or low-quality output before posting.
        Returns True if content should NOT be posted."""
        if not content:
            self._log_uplink("CONTENT GUARD: Empty content rejected.")
            return True

        if len(content.strip()) < 150:
            self._log_uplink(f"CONTENT GUARD: Content too short ({len(content.strip())} chars). Rejected.")
            return True

        refusal_patterns = [
            "i cannot provide",
            "i can't provide",
            "i cannot create",
            "i'm not able to",
            "i am not able to",
            "i'm sorry, but",
            "i must decline",
            "i cannot assist",
            "i won't be able",
            "i don't feel comfortable",
            "promotes the use of",
            "promtos the use",
            "as an ai language model",
            "as an ai assistant",
            "against my guidelines",
            "against my programming",
        ]
        content_lower = content.lower()
        for pattern in refusal_patterns:
            if pattern in content_lower:
                self._log_uplink(f"CONTENT GUARD: Refusal pattern detected ('{pattern}'). Rejected.")
                return True

        return False

    def _generate_topic_image(self, topic):
        """Generates a topic image with FLUX visual + Pillow text overlay for readable text."""
        import requests
        import os
        import base64
        from datetime import datetime
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO

        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            self._log_uplink("IMAGE GEN: No TOGETHER_API_KEY found, skipping.")
            return None

        # Visual-only prompt — NO text instructions, FLUX can't spell
        prompt = (
            f"Abstract scientific illustration representing {topic}. "
            "Dark navy blue background. Glowing neon cyan and gold molecular structures. "
            "Brain anatomy, neural networks, biochemical pathways. "
            "Cyberpunk cinematic lighting, deep blue and gold color palette. "
            "Atmospheric, professional pharmaceutical research aesthetic. "
            "No text, no letters, no words, pure visual imagery, dramatic depth of field."
        )

        try:
            self._log_uplink(f"IMAGE GEN: Requesting FLUX visual for '{topic}'...")
            response = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "prompt": prompt,
                    "width": 1280,
                    "height": 720,
                    "steps": 4,
                    "n": 1,
                    "response_format": "b64_json"
                },
                timeout=60
            )
            if response.status_code != 200:
                self._log_uplink(f"IMAGE GEN: FLUX returned {response.status_code}: {response.text[:200]}")
                return None

            img_data = base64.b64decode(response.json()["data"][0]["b64_json"])
            img = Image.open(BytesIO(img_data)).convert("RGB")

            # === PILLOW TEXT OVERLAY ===
            draw = ImageDraw.Draw(img, "RGBA")
            W, H = img.size

            # Try common system fonts, fall back gracefully
            def load_font(size, bold=False):
                paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                ]
                for p in paths:
                    if os.path.exists(p):
                        return ImageFont.truetype(p, size)
                return ImageFont.load_default()

            title_font = load_font(72, bold=True)
            tagline_font = load_font(28, bold=True)
            footer_font = load_font(24, bold=True)

            # Top dark band for title
            draw.rectangle([(0, 0), (W, 160)], fill=(3, 9, 31, 200))
            # Bottom dark band for footer
            draw.rectangle([(0, H-90), (W, H)], fill=(3, 9, 31, 220))

            # TITLE — uppercase, centered, gold
            title = topic.upper()
            # Wrap if too long
            if len(title) > 32:
                words = title.split()
                mid = len(words) // 2
                line1 = ' '.join(words[:mid])
                line2 = ' '.join(words[mid:])
                bbox1 = draw.textbbox((0, 0), line1, font=load_font(56, bold=True))
                bbox2 = draw.textbbox((0, 0), line2, font=load_font(56, bold=True))
                w1 = bbox1[2] - bbox1[0]
                w2 = bbox2[2] - bbox2[0]
                draw.text(((W-w1)//2, 20), line1, font=load_font(56, bold=True), fill=(251, 191, 36))
                draw.text(((W-w2)//2, 85), line2, font=load_font(56, bold=True), fill=(251, 191, 36))
            else:
                bbox = draw.textbbox((0, 0), title, font=title_font)
                w = bbox[2] - bbox[0]
                draw.text(((W-w)//2, 40), title, font=title_font, fill=(251, 191, 36))

            # Tagline below title — neon cyan
            tagline = "SYNDICATE INTELLIGENCE // BIOHACKING PROTOCOL"
            bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
            w = bbox[2] - bbox[0]
            draw.text(((W-w)//2, 125), tagline, font=tagline_font, fill=(56, 189, 248))

            # FOOTER — white
            footer = "DO YOUR OWN RESEARCH. DON'T BE A STATISTIC."
            bbox = draw.textbbox((0, 0), footer, font=footer_font)
            w = bbox[2] - bbox[0]
            draw.text(((W-w)//2, H-60), footer, font=footer_font, fill=(248, 250, 252))

            # Save
            os.makedirs("media/general", exist_ok=True)
            slug = topic.lower().replace(' ', '-')[:50]
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"media/general/{date_str}-{slug}.png"
            img.save(filename, "PNG")
            self._log_uplink(f"IMAGE GEN: Saved to {filename}")
            return filename

        except Exception as e:
            self._log_uplink(f"IMAGE GEN: Failed ({e}), falling back to random media.")
        return None
        
def _post_to_website(self, content, topic, image_path=None):
    """Beautifies the content and posts it to the website (articles/ and intel.html)."""
    os.makedirs("articles", exist_ok=True)
    self._log_uplink(f"WEBSITE: Initializing Syndicate Transmission for {topic}...")
    # 0. Handle missing image — try to generate topic-specific first
    if not image_path:
        image_path = self._generate_topic_image(topic)
        if not image_path:
            image_path = self._get_random_media()
        if image_path:
            self._log_uplink(f"WEBSITE: Image resolved: {image_path}")

        # 1. Beautify content using LLM
        try:
            # We now capture priority and a clean title from beautification
            beautified_html, priority, clean_title = self._beautify_for_blog(content, topic, image_path)
            if not beautified_html or len(beautified_html) < 100:
                self._log_uplink("WEBSITE ERROR: Beautification returned empty or suspiciously short HTML.")
                return False
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: Beautification failed: {str(e)}")
            return False

        # 2. Generate slug and filename
        date_str = datetime.now().strftime("%Y-%m-%d")
        slug = re.sub(r'[^a-z0-9]+', '-', clean_title.lower()).strip('-')
        filename = f"{date_str}-{slug}.html"
        filepath = os.path.join("articles", filename)

        # 3. Save the article
        try:
            with open(filepath, 'w') as f:
                f.write(beautified_html)
            self._log_uplink(f"WEBSITE: Article saved to {filepath}")
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: Failed to save article file: {e}")
            return False

        # 4. Update intel.html (Latest 3)
        self._update_intel_html(clean_title, filename, date_str, priority)

        # 5. Update transmissions.html (Archive)
        self._update_transmissions_html(clean_title, filename, date_str)

        # 6. Git Commit and Push
        self._git_push_changes(f"Syndicate Transmission: {topic}")

        return True

    def _beautify_for_blog(self, content, topic, image_path):
        """Uses the LLM to beautify content and then injects it into the HTML template."""
        # Scrub topic meta-commentary
        topic = re.sub(r'(?i)The specific topic requested by the CEO for the \d{2}:\d{2} post is\s+', '', topic)
        topic = re.sub(r'(?i)post with title\s+', '', topic)
        topic = re.sub(r'(?i)Masterclass:\s*', '', topic)
        system_msg = (
            "You are the Syndicate's Digital Architect. Your job is to take raw biohacking intel "
            "and format it for a high-end article for our website."
        )

        # 1. Load the template
        template_path = "articles/template.html"
        try:
            with open(template_path, 'r') as f:
                template = f.read()
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: Template not found at {template_path}: {e}")
            return f"<h1>{topic}</h1><p>{content}</p>", 2 # Minimal fallback

        # 2. Ask LLM to generate the beautified body and the hack box separately
        prompt = (
            f"I have a new Syndicate Masterclass about '{topic}'.\n\n"
            f"RAW CONTENT:\n{content}\n\n"
            "INSTRUCTIONS:\n"
            "1. Rewrite the content to be more 'beautified' for a professional blog post. \n"
            "2. Use PROPER HTML tags for structure: <h2> for section headers, <p> for paragraphs, and <strong> for emphasis.\n"
            "3. MANDATORY: Structure the body using NUMBERED HEADERS for each main section (e.g., '1. The Mechanism', '2. Protocol implementation').\n"
            "4. MANDATORY: Create a 'Prostar Life Hack' section containing the most actionable, high-value takeaway.\n"
            "5. Analyze the 'Intelligence Level' of the content. If it contains deep technical pharmacological data or complex protocols, assign Priority 1. If it's a general overview, assign Priority 2.\n"
            "6. Generate a professional, punchy, and technical title for the post (e.g., 'Neurobiology of Sulbutiamine' or 'Optimizing HRV with Cold Thermogenesis'). Do NOT include prefixes like 'Masterclass:' or 'Topic:'.\n"
            "7. Return the result as a JSON object with four keys:\n"
            "   - 'body': The HTML formatted content.\n"
            "   - 'hack': The HTML text for the hack-box contents (just the text, no <h4>).\n"
            "   - 'priority': The integer 1 or 2.\n"
            "   - 'title': The professional title string.\n"
            "8. Return ONLY the JSON object. No talk, no markdown code blocks around the JSON."
        )

        # We need a longer context for beautification to handle the template and content.
        # We set sanitize=False because we WANT HTML tags in the JSON response.
        json_response = self.llm.generate_response(prompt, system_msg, reflect=True, options={'num_ctx': 8192}, sanitize=False)

        # Cleanup: Robustly extract JSON if the LLM ignores the "no markdown" instruction
        json_clean = json_response.strip()
        if "```" in json_clean:
            match = re.search(r'```(?:json)?\n?(.*?)\n?```', json_clean, re.DOTALL)
            if match:
                json_clean = match.group(1).strip()

        # Further cleanup to remove any potential non-JSON noise before/after the object
        match = re.search(r'(\{.*\})', json_clean, re.DOTALL)
        if match:
            json_clean = match.group(1).strip()

        try:
            data = json.loads(json_clean)
            beautified_body = data.get('body', f"<p>{content.replace('\n', '<br>')}</p>")
            clean_title = data.get('title', topic).strip()

            # --- POST-PROCESSING SANITIZATION ---
            # 1. Catch LLM errors like nesting <h2> inside <p> or using <h1>
            beautified_body = beautified_body.replace('<h1>', '<h2>').replace('</h1>', '</h2>')
            # 2. Use regex to find <p>...<h2>...</h2>...</p> and flatten it
            beautified_body = re.sub(r'<p>\s*(<h[1-6]>.*?</h[1-6]>)\s*</p>', r'\1', beautified_body, flags=re.DOTALL)
            # 3. Strip any "Masterclass:" or "Topic:" or similar meta-prefixes from the content body
            beautified_body = re.sub(r'(?:Masterclass|Topic|Title):\s*', '', beautified_body, flags=re.IGNORECASE)
            # 4. Remove any ** stars that might have leaked into HTML
            beautified_body = beautified_body.replace('**', '')
            # 5. Ensure multiple <br> tags are replaced with proper paragraph structure if leaked
            beautified_body = re.sub(r'(?:<br\s*/?>\s*){2,}', '</p><p>', beautified_body)
            # 6. Ensure all paragraphs are wrapped and non-header text isn't loose
            # (Simple regex approach to wrap loose text or handle missing <p> tags)
            if "<p>" not in beautified_body.lower() and "<h2>" in beautified_body.lower():
                 # Very basic wrap for content that might just be headers and raw text
                 parts = re.split(r'(<h[1-6]>.*?</h[1-6]>)', beautified_body, flags=re.DOTALL)
                 new_parts = []
                 for p in parts:
                     if p.strip() and not p.startswith('<h'):
                         new_parts.append(f"<p>{p.strip()}</p>")
                     else:
                         new_parts.append(p)
                 beautified_body = "".join(new_parts)

            hack_content = data.get('hack', "")
            priority = int(data.get('priority', 2))
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: JSON parsing failed: {e}. Falling back to raw content.")
            # Fallback if JSON fails
            beautified_body = f"<p>{content.replace('\n', '<br>')}</p>"
            clean_title = topic.strip()

            # Robust fallback for hack content: try to find it in raw content or use a default
            hack_match = re.search(r'(?:PROSTAR LIFE HACK|LIFE HACK|PROTOCOL TIP):?\s*(.*)', content, re.IGNORECASE)
            if hack_match:
                hack_content = hack_match.group(1).strip()
            else:
                hack_content = "Always verify protocol biological leverage with baseline biometric tracking. Data is sovereignty."

            priority = 2

        # 3. Construct the Hack Box HTML if content exists
        hack_html = ""
        if hack_content:
            # Ensure hack_content has <p> tags if it doesn't already
            if "<p>" not in hack_content.lower():
                hack_content = f"<p>{hack_content}</p>"
            hack_html = f'<div class="hack-box"><h4>Prostar Life Hack</h4>{hack_content}</div>'

        # 4. Handle the Image HTML
        image_html = ""
        if image_path:
            image_html = f'<img src="../{image_path}" alt="{topic}" class="article-img">'

        # 5. Inject into template using placeholders
        now = datetime.now()
        date_display = now.strftime("%B %Y")
        timestamp_str = f"[ LIVE FEED ] RECEIVED: {now.strftime('%Y-%m-%d %H:%M:%S')} AST"

        # Final scrub of meta-commentary from the clean_title
        clean_title = re.sub(r'(?i)The specific topic requested by the CEO for the \d{2}:\d{2} post is\s+', '', clean_title)
        clean_title = re.sub(r'(?i)post with title\s+', '', clean_title)
        clean_title = re.sub(r'(?i)Masterclass:\s*', '', clean_title)

        final_html = template.replace("{{SYNDICATE_TITLE}}", clean_title)
        final_html = final_html.replace("{{SYNDICATE_DATE}}", date_display)
        final_html = final_html.replace("{{SYNDICATE_TIMESTAMP}}", timestamp_str)
        final_html = final_html.replace("{{SYNDICATE_CONTENT}}", beautified_body)
        final_html = final_html.replace("{{SYNDICATE_HACK}}", hack_html)
        final_html = final_html.replace("{{SYNDICATE_IMAGE}}", image_html)

        return final_html, priority, clean_title
    def _update_intel_html(self, topic, filename, date_str, priority=2):
        """Updates the intel.html file with the latest 3 posts."""
        self._log_uplink(f"WEBSITE: Syncing intel.html (Priority: {priority})...")
        try:
            with open("intel.html", 'r') as f:
                html = f.read()

            priority_class = " priority-1" if priority == 1 else ""
            new_card = (
                f'                <div class="card{priority_class}">\n'
                f'                    <div class="meta-data" style="font-size: 0.7rem; color: var(--neon-gold); margin-bottom: 10px;">TRANSMISSION: {date_str}</div>\n'
                f'                    <h3>{topic}</h3>\n'
                f'                    <p>{topic} protocol initialized. Access the full intel burst below.</p>\n'
                f'                    <a href="articles/{filename}" class="buy-btn" style="font-size: 0.7rem; padding: 8px 16px;">View Intel →</a>\n'
                f'                </div>'
            )

            # Find the posts block
            start_marker = "<!-- LATEST_3_POSTS_START -->"
            end_marker = "<!-- LATEST_3_POSTS_END -->"

            if start_marker in html and end_marker in html:
                parts = html.split(start_marker)
                pre_block = parts[0]
                post_parts = parts[1].split(end_marker)
                current_block = post_parts[0]
                after_block = post_parts[1]

                # Extract cards using regex but handle the block more safely
                cards = re.findall(r'<div class="card[^"]*">.*?</a>\s*</div>', current_block, re.DOTALL)
                cards = [c for c in cards if "Initializing Feed" not in c and "Waiting for Uplink" not in c and "Data Stream Alpha" not in c]
                cards.insert(0, new_card)
                cards = cards[:3]

                new_block = "\n" + "\n".join(cards) + "\n                "
                html = pre_block + start_marker + new_block + end_marker + after_block

            # Update archive preview
            archive_start = "<!-- OLDER_POSTS_START -->"
            archive_end = "<!-- OLDER_POSTS_END -->"
            if archive_start in html and archive_end in html:
                parts = html.split(archive_start)
                pre_archive = parts[0]
                archive_parts = parts[1].split(archive_end)
                current_archive = archive_parts[0]
                after_archive = archive_parts[1]

                new_archive_item = f'<li style="margin-bottom: 10px;"><a href="articles/{filename}" style="color: var(--text-dim); text-decoration: none; font-size: 0.85rem;">[{date_str}] {topic}</a></li>'
                archive_items = re.findall(r'<li.*?>.*?</li>', current_archive, re.DOTALL)
                archive_items = [i for i in archive_items if "No archived transmissions found" not in i]
                archive_items.insert(0, new_archive_item)
                archive_items = archive_items[:5]

                new_archive_block = "\n                    " + "\n                    ".join(archive_items) + "\n                    "
                html = pre_archive + archive_start + new_archive_block + archive_end + after_archive

            with open("intel.html", 'w') as f:
                f.write(html)
            self._log_uplink("WEBSITE: intel.html synced successfully.")
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: Failed to update intel.html: {e}")

    def _update_transmissions_html(self, topic, filename, date_str):
        """Updates the transmissions.html archive page."""
        self._log_uplink("WEBSITE: Syncing transmissions.html...")
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

            if start_marker in html and end_marker in html:
                parts = html.split(start_marker)
                pre_block = parts[0]
                post_parts = parts[1].split(end_marker)
                current_block = post_parts[0]
                after_block = post_parts[1]

                items = re.findall(r'<a.*?class="archive-item">.*?</a>', current_block, re.DOTALL)
                items = [i for i in items if "Initializing deep archive retrieval" not in i]
                items.insert(0, new_item)

                new_block = "\n" + "\n".join(items) + "\n            "
                html = pre_block + start_marker + new_block + end_marker + after_block

                with open("transmissions.html", 'w') as f:
                    f.write(html)
                self._log_uplink("WEBSITE: transmissions.html synced successfully.")
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: Failed to update transmissions.html: {e}")

    def _git_push_changes(self, commit_message):
        """Automates the git workflow to push changes to the repository."""
        self._log_uplink("GIT: Synchronizing repository...")
        try:
            # 0. Emergency Cleanup: Ensure we aren't in a broken state from a previous run
            git_dir = ".git"
            if os.path.exists(os.path.join(git_dir, "rebase-merge")) or os.path.exists(os.path.join(git_dir, "rebase-apply")):
                self._log_uplink("GIT: Detected stuck rebase. Aborting...")
                subprocess.run(["git", "rebase", "--abort"], capture_output=True)
            if os.path.exists(os.path.join(git_dir, "MERGE_HEAD")):
                self._log_uplink("GIT: Detected stuck merge. Aborting...")
                subprocess.run(["git", "merge", "--abort"], capture_output=True)

            # 1. Detect target branch reliably
            self._log_uplink("GIT: Fetching from origin...")
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

            # 2. Sync with remote BEFORE applying local changes to minimize conflicts
            self._log_uplink(f"GIT: Syncing with origin {target_branch} (Pre-sync)...")
            subprocess.run(["git", "stash", "push", "--include-untracked", "-m", "Syndicate Pre-Sync Stash"], capture_output=True)
            try:
                subprocess.run(["git", "pull", "origin", target_branch, "--rebase"], capture_output=True)
            finally:
                stash_list = subprocess.run(["git", "stash", "list"], capture_output=True, text=True)
                if "Syndicate Pre-Sync Stash" in stash_list.stdout:
                    subprocess.run(["git", "stash", "pop"], capture_output=True)

            # 3. Ensure we only stage the intended files
            subprocess.run(["git", "add", "intel.html", "transmissions.html", "articles/"], check=True, capture_output=True, text=True)

            # 4. Check if there are staged changes to commit
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            staged_changes = [line for line in status.stdout.splitlines() if line.startswith(('A', 'M', 'D', 'R', 'C'))]

            if not staged_changes:
                self._log_uplink("GIT: No relevant changes staged. Skipping commit/push.")
                return

            # 5. Commit the staged changes
            subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)

            # 6. Final Push with Rebase handling
            self._log_uplink(f"GIT: Final sync and push to {target_branch}...")

            # Stash any remaining noise
            subprocess.run(["git", "stash", "push", "--include-untracked", "-m", "Syndicate Final Stash"], capture_output=True)

            try:
                # Pull with rebase
                pull_res = subprocess.run(["git", "pull", "origin", target_branch, "--rebase"], capture_output=True, text=True)
                if pull_res.returncode != 0:
                    self._log_uplink(f"GIT REBASE CONFLICT: {pull_res.stderr}")
                    subprocess.run(["git", "rebase", "--abort"], capture_output=True)

                    self._log_uplink("GIT: Falling back to merge strategy...")
                    merge_res = subprocess.run(["git", "pull", "origin", target_branch, "--no-rebase", "--no-edit"], capture_output=True, text=True)
                    if merge_res.returncode != 0:
                        self._log_uplink(f"GIT MERGE ERROR: {merge_res.stderr}")
                        return

                # Push explicitly to the target branch
                push_res = subprocess.run(["git", "push", "origin", f"HEAD:{target_branch}"], check=True, capture_output=True, text=True)
                self._log_uplink(f"GIT PUSH: {push_res.stdout.strip()}")
                # Also push to website remote (serves hopes-and-dreams.ca)
                # Self-healing: pull from website FIRST to absorb any divergent commits, then push
                try:
                    self._log_uplink("GIT: Pre-syncing with website remote...")
                    subprocess.run(["git", "fetch", "website"], capture_output=True, timeout=30)
                    # Pull with merge (no-rebase) to absorb any commits website has that we don't
                    subprocess.run(
                        ["git", "pull", "website", target_branch, "--no-rebase", "--no-edit"],
                        capture_output=True, text=True, timeout=60
                    )
                    # Now push - should succeed since we just synced
                    website_push = subprocess.run(
                        ["git", "push", "website", f"HEAD:{target_branch}"],
                        check=True, capture_output=True, text=True, timeout=60
                    )
                    self._log_uplink(f"GIT PUSH (website): Success - site updating")
                    # Push the merge commit back to origin too so they stay in lockstep
                    try:
                        subprocess.run(
                            ["git", "push", "origin", f"HEAD:{target_branch}"],
                            check=True, capture_output=True, text=True, timeout=60
                        )
                        self._log_uplink("GIT: origin re-synced with website merge")
                    except subprocess.CalledProcessError:
                        pass  # not critical if this fails
                except subprocess.CalledProcessError as e:
                    self._log_uplink(f"GIT PUSH (website) FAILED: {e.stderr.strip() if e.stderr else 'unknown error'}")
                except Exception as e:
                    self._log_uplink(f"GIT PUSH (website) FAILED (unexpected): {str(e)}")
            finally:
                # Restore the stash
                stash_list = subprocess.run(["git", "stash", "list"], capture_output=True, text=True)
                if "Syndicate Final Stash" in stash_list.stdout:
                    subprocess.run(["git", "stash", "pop"], capture_output=True)

            self._log_uplink("GIT: Uplink successful.")
        except subprocess.CalledProcessError as e:
            err_msg = f"GIT ERROR in '{' '.join(e.cmd)}': {e.stderr}"
            self._log_uplink(err_msg)
        except Exception as e:
            self._log_uplink(f"GIT CRITICAL ERROR: {str(e)}")
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

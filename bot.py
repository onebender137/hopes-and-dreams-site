# --- PHOENIX OBSERVABILITY INITIALIZATION (opt-in) ---
import os
# Tracing is OFF by default. The Phoenix UI launch fails to bind its port on this
# box (spamming a grpc/uvicorn traceback) and registers against a collector that
# isn't running, so it was pure noise. Set SYNDICATE_TRACING=1 to re-enable the
# full Phoenix/OpenInference stack (launch UI + register + auto-instrument).
if os.environ.get("SYNDICATE_TRACING") == "1":
    os.environ["PHOENIX_PROJECT_NAME"] = "syndicate-intelligence"
    os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
    try:
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from openinference.instrumentation.crewai import CrewAIInstrumentor
        from openinference.instrumentation.litellm import LiteLLMInstrumentor

        try:
            session = px.launch_app()
            print(f"Phoenix Observability Dashboard launched at: {session.url}")
        except Exception as e:
            print(f"Warning: Failed to launch Phoenix app: {e}")

        tracer_provider = register(
            project_name="syndicate-intelligence",
            endpoint="http://localhost:6006/v1/traces",
            auto_instrument=True
        )
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        CrewAIInstrumentor().instrument(tracer_provider=tracer_provider)
        LiteLLMInstrumentor().instrument(tracer_provider=tracer_provider)
    except Exception as e:
        print(f"Warning: tracing init failed, continuing without it: {e}")
# ---------------------------------------------
# --- LOGGING: mute noisy libraries that leak credentials in URLs ---
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
# -----------------------------------------------------------------

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
from dsda_print import dsda_print, heartbeat as _dsda_heartbeat
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
    "DSIP Sleep Peptide", "AOD-9604 Fat Loss Peptide",
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

    def _record_posted_topic(self, topic, slot=None):
        """Records a new posted topic to SQLite."""
        self.db.add_posted_topic(topic, slot=slot)
        # Update local cache for immediate use if needed
        self.posted_topics = self._load_posted_topics()

    def _load_replied_comments(self):
        """Loads the set of comment IDs already replied to from SQLite."""
        return self.db.get_all_replied_comments()

    def _save_replied_comments(self):
        """Deprecated: SQLite saves automatically."""
        pass

    def _sanitize_topic(self, topic):
        """
        Robust topic sanitizer that handles LLM meta-commentary leakage.
        Returns cleaned topic string, or None if topic is unsalvageable
        (caller should fall back to autonomous brainstorm).
        """
        if not topic or not isinstance(topic, str):
            return None

        cleaned = topic.strip()

        # 1. Strip outer quote wrappers
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()

        # 2. Normalize whitespace and remove leaked formatting
        cleaned = cleaned.replace('\n', ' ').replace('|', ' ')
        cleaned = re.sub(r"['\"]", '', cleaned)

        # 3. Strip known meta-commentary lead-in patterns (covers LLM rephrasings)
        # Matches: "the specific topic...", "the single most relevant...", "he wants to post about...",
        # "the topic requested...", "based on...", etc. Stops at " is " / " : " / colon followed by topic.
        meta_patterns = [
            # "The single most relevant specific topic or supplement he wants to post about for the 07:00 post is NAD+"
            r'(?i)^\s*the\s+(single\s+most\s+|most\s+|specific\s+)?(relevant\s+)?(specific\s+)?(topic|supplement|biohack|protocol|biohacking\s+topic|supplement\s+or\s+topic)[^:]{0,200}\bis\b\s+',
            # "The topic requested by the CEO for the XX:XX post is..."
            r'(?i)^\s*the\s+topic\s+requested[^:]{0,150}\bis\b\s+',
            # "He wants to post about..."
            r"(?i)^\s*(he|she|they|the\s+ceo|the\s+admin)\s+wants?\s+to\s+post\s+about[\s:]+",
            # "Based on recent messages..." / "Looking at the chat..."
            r"(?i)^\s*(based\s+on|looking\s+at|analyzing|from\s+the)[^:]{0,150}[:,]\s+",
            # "Post with title ..." / "Masterclass: ..."
            r"(?i)^\s*(post\s+with\s+title|masterclass|article)[\s:]+",
            # "Today's post is about X" / "Tomorrow's post will be on X"
            r"(?i)^\s*(today'?s|tomorrow'?s|the\s+next)\s+(post|article|topic)[^:]{0,80}\b(is|will\s+be)\b\s+(about\s+|on\s+|regarding\s+)?",
            # "The {time} post is..." (fallback for time-prefixed garbage)
            r"(?i)^\s*the\s+\d{1,2}[:\.]\d{2}\s+post\s+(is|will\s+be)\s+",
        ]

        for pattern in meta_patterns:
            new_cleaned = re.sub(pattern, '', cleaned, count=1)
            if new_cleaned != cleaned:
                cleaned = new_cleaned.strip()
                # Strip leftover punctuation/articles after meta removal
                cleaned = re.sub(r'^[:\-\.\s]+', '', cleaned)
                cleaned = re.sub(r'^(a|an|the|about|on|regarding|concerning)\s+', '', cleaned, flags=re.IGNORECASE)

        # 4. Trim trailing punctuation/period
        cleaned = cleaned.rstrip('.!?;:,').strip()

        # 5. Collapse multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # 6. SANITY CHECK — reject if topic is implausibly long or still contains meta-commentary signals
        if not cleaned:
            return None
        word_count = len(cleaned.split())
        if word_count > 12:
            print(f"[SANITIZER] REJECTED — topic too long ({word_count} words): {cleaned[:80]}...")
            return None
        # Detect lingering meta-commentary phrases that survived the strips
        meta_signals = [
            r'\bhe\s+wants\b', r'\bshe\s+wants\b', r'\brequested\b', r'\bis\s+about\b',
            r'\bpost\s+is\b', r'\btopic\s+is\b', r'\bcontent\s+is\b',
            r'\bbased\s+on\b', r'\bfor\s+the\s+\d{1,2}[:\.]\d{2}\s+post\b',
        ]
        for sig in meta_signals:
            if re.search(sig, cleaned, re.IGNORECASE):
                print(f"[SANITIZER] REJECTED — meta-commentary signal detected: {cleaned[:80]}...")
                return None

        return cleaned

    # Domain clusters — topics in the same cluster count as "recently posted"
    # so the bot doesn't churn through NAD+/NMN/NR/Sirtuin variants in a row.
    TOPIC_CLUSTERS = {
        'nad_pathway': [
            'nad', 'nad+', 'nmn', 'nr', 'nicotinamide', 'niacin', 'niacinamide',
            'sirtuin', 'resveratrol', 'longevity precursor', 'cellular vitality',
        ],
        'cholinergic': [
            'choline', 'alpha-gpc', 'alpha gpc', 'cdp-choline', 'citicoline',
            'huperzine', 'galantamine', 'acetylcholine',
        ],
        'psychedelic_tryptamine': [
            'dmt', 'dimethyltryptamine', 'ayahuasca', 'inmt',
            'entity encounter', 'dmtx',
        ],
        'mitochondrial': [
            'mitochondri', 'pqq', 'coq10', 'ubiquinol', 'urolithin',
            'mots-c', 'methylene blue', 'atp synthesis',
        ],
        'sleep_dream': [
            'sleep', 'melatonin', 'lucid dream', 'galantamine', 'wbtb', 'mild',
            'wild', 'dsip', 'glycine', 'magnesium glycinate', 'rem',
        ],
        'peptides_healing': [
            'bpc-157', 'bpc 157', 'tb-500', 'tb 500', 'ghk-cu', 'ghk cu',
            'thymosin', 'aod-9604', 'peptide healing',
        ],
        'nootropics_racetam': [
            'noopept', 'aniracetam', 'piracetam', 'phenylpiracetam', 'oxiracetam',
            'pramiracetam', 'racetam',
        ],
        'stim_focus': [
            'caffeine', 'l-theanine', 'theanine', 'modafinil', 'tyrosine',
            'phenylethylamine', 'pea',
        ],
        'gaba_calm': [
            'gaba', 'kava', 'valerian', 'phenibut', 'l-theanine',
            'ashwagandha', 'magnolia',
        ],
    }

    # ===== THEME CATALOG =====
    # Curated topic sets per theme. Used by /theme_day and /theme_week.
    # Keys are matched case-insensitively against user input.
    # Each theme has 4-6 ready-to-go topics; bot samples 3 per day.
    # If no catalog match, bot falls back to LLM brainstorm in that domain.
    THEME_CATALOG = {
        'mushrooms': [
            "Lion's Mane Neurogenesis Protocols",
            "Cordyceps Mitochondrial ATP Production",
            "Reishi Immune Modulation",
            "Chaga Antioxidant Profile",
            "Psilocybin DMN Suppression Mechanism",
            "Turkey Tail PSK Beta-Glucans",
            "Maitake D-Fraction Beta-Glucan",
            "Shiitake Lentinan Immune Activation",
            "Agarikon Antiviral Triterpenoids",
        ],
        'peptides': [
            "BPC-157 Healing Protocols",
            "TB-500 Tissue Repair Mechanism",
            "GHK-Cu Skin & Wound Healing",
            "Thymosin Alpha-1 Immune Optimization",
            "AOD-9604 Lipolysis Protocol",
            "Semaglutide GLP-1 Metabolic Pathway",
            "Epitalon Telomerase Activation",
            "Selank Anxiolytic Nootropic Peptide",
            "CJC-1295 Ipamorelin GH Pulse",
        ],
        'sleep': [
            "Glycine NMDA Modulation for Deep Sleep",
            "Magnesium Bisglycinate Sleep Architecture",
            "Low-Dose Melatonin Circadian Entrainment",
            "L-Theanine GABAergic Calming",
            "Apigenin Anxiolytic Pathway",
            "DSIP Sleep-Inducing Peptide",
            "L-Tryptophan Serotonin-Melatonin Pathway",
            "Saffron Crocin Sleep Quality",
            "Inositol Sleep Onset Modulation",
        ],
        'cognitive': [
            "The Neurobiology of Sulbutiamine",
            "Aniracetam AMPA Receptor Modulation",
            "Noopept Synaptic Plasticity",
            "Phenylpiracetam Stim-Cognitive Stack",
            "Bacopa Monnieri Memory Enhancement",
            "Phosphatidylserine Membrane Optimization",
            "Citicoline Acetylcholine Synthesis",
            "Alpha-GPC Choline Donor Stack",
            "Rhodiola Rosea Mental Fatigue",
        ],
        'mitochondrial': [
            "PQQ Mitochondrial Biogenesis",
            "CoQ10 vs Ubiquinol Bioavailability",
            "Methylene Blue Microdosing Protocol",
            "Urolithin A Mitophagy Activation",
            "MOTS-c Mitochondrial Peptide",
            "Creatine Monohydrate ATP Reservoir",
            "NMN NAD+ Bioenergetics",
            "Shilajit Fulvic Acid Synergy",
            "SS-31 Elamipretide Cardiolipin Protection",
        ],
        'recovery': [
            "Cold Thermogenesis HRV Optimization",
            "Sauna Heat Shock Protein Activation",
            "Compression Therapy Lymphatic Flow",
            "Ashwagandha Cortisol Modulation",
            "Tart Cherry Sleep & Inflammation",
            "Magnesium L-Threonate Recovery Stack",
            "Tongkat Ali Testosterone Recovery",
            "Curcumin Phytosome Inflammation Resolution",
            "Omega-3 SPM Resolvins",
        ],
        'longevity': [
            "Rapamycin mTOR Suppression",
            "Spermidine Autophagy Activation",
            "Senolytic Fisetin Protocol",
            "Glycine + NAC Methionine Restriction Mimetic",
            "Berberine AMPK Activation",
            "Hyperbaric Oxygen Telomere Studies",
            "Taurine Healthspan Research",
            "Dasatinib Quercetin Senolytic Combination",
            "Sulforaphane Nrf2 Activation",
        ],
        'gaba_calm': [
            "GABA Receptor Pharmacology",
            "Kava Kavalactone Anxiolytic Mechanism",
            "L-Theanine GABAergic Calming",
            "Ashwagandha HPA Axis Regulation",
            "Magnolia Honokiol GABA-A Modulation",
            "Valerian Root Sedative Profile",
            "Taurine GABA-A Modulation",
            "Lemon Balm Melissa Anxiolytic",
            "Saffron Affron Mood Support",
        ],
        'nootropics': [
            "Aniracetam AMPA Receptor Modulation",
            "Noopept Synaptic Plasticity",
            "Phenylpiracetam Stim-Cognitive Stack",
            "Modafinil Histaminergic Wakefulness",
            "L-Theanine + Caffeine Synergy",
            "Tyrosine Catecholamine Precursor",
            "Semax BDNF Heptapeptide",
            "Fasoracetam mGluR Modulation",
            "Pramiracetam High-Affinity Choline Uptake",
        ],
        'nicotine': [
            "Nicotine nAChR Pharmacology",
            "Nicotine Patch Cognitive Stack",
            "Asprey-Style Low-Dose Nicotine",
            "Cytisine Smoking Cessation",
            "Nicotine + Caffeine Synergy",
            "Nicotinic Receptor Subtypes Explained",
            "Nicotine Parkinson's Neuroprotection Research",
            "Alpha-7 nAChR Cognitive Pathway",
            "Nicotine Gum Pharmacokinetics",
        ],
        'kratom': [
            "Mitragynine 7-OH Pharmacology",
            "Kratom Strain Alkaloid Profiles",
            "Kratom Tolerance Rotation",
            "Mitragyna Speciosa Botany & Origin",
            "Kratom Harm Reduction Framework",
            "Kratom Receptor Binding Studies",
            "7-Hydroxymitragynine Metabolite Potency",
            "Kratom Mu-Opioid Partial Agonism",
            "Kratom Drug Interaction Safety",
        ],
        'dreams': [
            "WBTB Lucid Dreaming Protocol",
            "Galantamine Cholinergic REM Stack",
            "Huperzine-A Dream Recall Enhancement",
            "MILD vs WILD Induction Techniques",
            "Mugwort Vivid Dream Tradition",
            "Choline Bitartrate Dream Cofactor",
            "Alpha-GPC REM Dream Intensity",
            "Vitamin B6 Dream Recall",
            "Calea Zacatechichi Oneirogen",
        ],
        'dmt': [
            "DMT 5-HT2A Receptor Agonism",
            "DMT Sigma-1 Receptor Debate",
            "Endogenous DMT INMT Biosynthesis",
            "DMT Default Mode Network Disintegration",
            "Ayahuasca MAO-A Oral Bioavailability",
            "DMT Entity Encounter Phenomenology",
            "Pineal Gland DMT Hypothesis",
            "DMT Prevalence & Harm Reduction",
            "Extended-State DMT Infusion (DMTx)",
        ],
        # Retrieves almost entirely from the KB (OBE/AP is not a PubMed
        # domain) — these topics make the astral source vein earn its keep.
        'astral_projection': [
            "Muldoon Rope Technique OBE",
            "Vibrational State Astral Separation",
            "Hypnagogic Exit Projection Onset",
            "Astral Projection vs Lucid Dreaming",
            "OBE Induction Relaxation Protocol",
            "Astral Travel Beginner Framework",
        ],
    }

    def _resolve_theme(self, theme_name):
        """
        Returns list of topics for a theme name (case-insensitive, partial match).
        Returns None if no catalog match (caller falls back to LLM).
        """
        if not theme_name:
            return None
        key = theme_name.lower().strip().replace(' ', '_').replace('-', '_')
        # Direct match
        if key in self.THEME_CATALOG:
            return self.THEME_CATALOG[key]
        # Singular/plural normalization
        if key.endswith('s') and key[:-1] in self.THEME_CATALOG:
            return self.THEME_CATALOG[key[:-1]]
        if (key + 's') in self.THEME_CATALOG:
            return self.THEME_CATALOG[key + 's']
        # Partial substring match (e.g. "mushroom" hits "mushrooms")
        for catalog_key in self.THEME_CATALOG:
            if key in catalog_key or catalog_key in key:
                return self.THEME_CATALOG[catalog_key]
        return None

    def list_available_themes(self):
        """Returns the list of catalog theme names for /themes display."""
        return sorted(self.THEME_CATALOG.keys())

    @staticmethod
    def _norm_topic(t):
        """Normalize a topic title for dedup: lowercase, alnum-only, collapsed spaces."""
        import re
        return re.sub(r'[^a-z0-9]+', ' ', (t or '').lower()).strip()

    # Low-rigor folders to skip in the general (pharmacology) rotation.
    _MINE_SKIP = ("astral", "dream", "lucid", "projection")
    # Soft/woo phrases to keep OUT of the auto-supply (pharmacology lane only).
    _SOFT_SKIP = ("spiritual", "meditation", "manifest", "astral", "chakra",
                  "energy healing", "consciousness expansion", "lifespan correlation")
    _MINE_DOMAINS = [
        "kratom", "nootropics", "peptides", "nicotine", "mushrooms",
        "sleep", "dopamine", "mitochondria", "longevity", "DMT",
    ]

    def _mine_one_domain(self, domain, n, k, covered, norm_covered):
        """Mine up to n fresh topics from one domain's KB material. Read-only helper."""
        import re
        try:
            ctx = self.knowledge.query_knowledge(domain, limit=k)
        except Exception:
            return []
        chunks = [p.strip()[:600] for p in (ctx or "").split("\n---\n") if p.strip()]
        if not chunks:
            return []
        evidence = "\n---\n".join(chunks[:k])
        exclude_hint = "; ".join(sorted(covered)[:50])
        system_msg = (
            "You are the Syndicate's Lead Content Strategist. You propose specific, technical "
            "biohacking article topics that are SUPPORTED BY the supplied research excerpts."
        )
        prompt = (
            f"### RESEARCH LIBRARY EXCERPTS (domain: {domain}):\n{evidence}\n\n"
            f"Propose exactly {n} SPECIFIC biohacking article topics these excerpts can support.\n\n"
            "RULES:\n"
            "1. Each topic MUST be answerable from the excerpts above - a compound, mechanism, or protocol they actually discuss.\n"
            "2. 3-8 words, punchy and technical. Format like: 'Mitragynine Mu-Opioid Receptor Profile'.\n"
            f"3. Do NOT propose anything similar to these already-covered topics: {exclude_hint}\n"
            "4. No wellness fluff, no vague categories, no metaphysics.\n"
            "5. Return ONLY the topic names, one per line. No numbering, no preamble, no commentary.\n\n"
            f"Output {n} fresh topics now, one per line:"
        )
        try:
            raw = self.llm.generate_response(prompt, system_msg, "", reflect=False, sanitize=True, options={'num_ctx': 8192})
        except Exception as e:
            print(f"[MINE:{domain}] generation failed: {e}")
            return []
        out = []
        for line in (raw or "").split("\n"):
            line = re.sub(r'^[\d\.\)\-\*\s]+', '', line.strip())
            if not line:
                continue
            clean = self._sanitize_topic(line)
            if not clean:
                continue
            if any(sk in clean.lower() for sk in self._SOFT_SKIP):
                continue
            if self._norm_topic(clean) in norm_covered:
                continue
            if clean in out:
                continue
            out.append(clean)
            if len(out) >= n:
                break
        return out

    def mine_kb_topics(self, domain=None, count=15, per_domain=4, chunks_per_domain=6):
        """Mine the KB for fresh, groundable topics with BALANCED domain coverage.
        Read-only: returns candidate titles, writes nothing. Mines each science domain
        separately so a loud folder (DMT) can't crowd out kratom/peptides, dedups against
        everything already covered, and round-robin merges for an even spread. Pass
        domain='kratom' to mine one vein; astral/dreams skipped by default, minable on demand."""
        if domain:
            domains = [domain]
        else:
            domains = [d for d in self._MINE_DOMAINS
                       if not any(sk in d.lower() for sk in self._MINE_SKIP)]

        covered = set()
        for v in self.THEME_CATALOG.values():
            covered.update(v)
        covered.update(SYNDICATE_TOPIC_POOL)
        covered.update(self.posted_topics or [])
        norm_covered = {self._norm_topic(t) for t in covered}

        per_domain_lists = []
        for dom in domains:
            topics = self._mine_one_domain(dom, per_domain, chunks_per_domain, covered, norm_covered)
            if topics:
                per_domain_lists.append(topics)
                for t in topics:
                    norm_covered.add(self._norm_topic(t))

        out, i = [], 0
        while len(out) < count and any(i < len(lst) for lst in per_domain_lists):
            for lst in per_domain_lists:
                if i < len(lst):
                    out.append(lst[i])
                    if len(out) >= count:
                        break
            i += 1
        return out

    def brainstorm_theme_topics(self, theme_name, count=3, exclude=None):
        """
        Generate `count` topics for a theme. Tries catalog first, falls back to LLM.
        `exclude` is a list of topic strings to skip (e.g. already-queued ones across
        multiple days in /theme_week so we don't repeat).
        Returns list of topic strings (may be < count if LLM fallback fails).
        """
        exclude = set(exclude or [])
        exclude.update(self.posted_topics or [])  # B2: kill week-over-week repeats
        norm_exclude = {self._norm_topic(t) for t in exclude}
        results = []
        self._last_theme_source = "none"  # where topics came from (for the UI label)

        def _add(t):
            nt = self._norm_topic(t)
            if t and nt not in norm_exclude and t not in results:
                results.append(t)
                norm_exclude.add(nt)

        # 1) Curated catalog gems first (hand-picked quality, fast)
        catalog_topics = self._resolve_theme(theme_name)
        if catalog_topics:
            available = [t for t in catalog_topics if self._norm_topic(t) not in norm_exclude]
            random.shuffle(available)
            for t in available:
                _add(t)
                if len(results) >= count:
                    self._last_theme_source = "catalog"
                    return results[:count]

        # T4: catalog didn't cover this keyword — if the KB is thin on it, deepen
        # it from PubMed BEFORE mining so we mine grounded material, not LLM drift.
        self._ensure_kb_coverage(theme_name)

        # 2) Catalog thin/exhausted — mine GROUNDED topics straight from the KB
        try:
            mined = self.mine_kb_topics(domain=theme_name, count=max(count * 2, 8))
            for t in mined:
                _add(t)
                if len(results) >= count:
                    self._last_theme_source = "grounded"
                    return results[:count]
        except Exception as e:
            print(f"[THEME] KB mining failed for '{theme_name}': {e}")

        # 3) Still short — last-resort LLM brainstorm to top up the grounded picks
        self._last_theme_source = "grounded" if results else "none"
        print(f"[THEME] {len(results)} grounded topic(s) for '{theme_name}'; topping up via LLM.")
        system_msg = (
            "You are the Syndicate's Lead Content Strategist. You generate fresh, "
            "technical, pharmacology-driven topic ideas for biohacking content."
        )
        exclude_str = ', '.join(sorted(exclude)[:25]) if exclude else "(none)"
        prompt = (
            f"Brainstorm exactly {count} distinct, specific biohacking topics about: \"{theme_name}\".\n\n"
            f"AVOID THESE (already-queued or recently-posted): {exclude_str}\n\n"
            "RULES:\n"
            "1. Each topic should be a specific compound, protocol, or mechanism — not a vague category.\n"
            "2. Stick to technical pharmacology and physiology. No wellness fluff.\n"
            "3. Each topic must be 3-8 words long. Punchy and professional.\n"
            "4. Format example: 'Lion's Mane Neurogenesis Protocols' or 'BPC-157 Healing Mechanism'.\n"
            "5. Return ONLY the topic names, one per line. No numbering, no preamble, no quotes, no commentary.\n"
            f"6. Do NOT include any of the avoided topics above.\n\n"
            f"Output {count} topics now, one per line:"
        )
        try:
            raw = self.llm.generate_response(prompt, system_msg)
            if not raw:
                return results
            # Parse: append LLM top-ups to the grounded picks already in `results`
            for line in raw.split('\n'):
                line = line.strip()
                # Strip leading numbers/bullets that LLMs sometimes add despite instructions
                line = re.sub(r'^[\d\.\)\-\*\s]+', '', line)
                if not line:
                    continue
                if any(sk in line.lower() for sk in self._SOFT_SKIP):
                    continue
                clean = self._sanitize_topic(line)
                if clean and self._norm_topic(clean) not in norm_exclude and clean not in results:
                    results.append(clean)
                    norm_exclude.add(self._norm_topic(clean))
                    self._last_theme_source = "llm"
                if len(results) >= count:
                    break
            return results
        except Exception as e:
            print(f"[THEME] LLM brainstorm failed: {e}")
            return results

    def _topic_cluster(self, topic):
        """Returns the cluster name a topic belongs to, or None if no cluster matched."""
        if not topic:
            return None
        lower = topic.lower()
        for cluster_name, keywords in self.TOPIC_CLUSTERS.items():
            for kw in keywords:
                if kw in lower:
                    return cluster_name
        return None

    def _is_topic_on_cooldown(self, topic, cooldown=5):
        """
        Returns True if this topic OR a topic from the same cluster has been posted
        in the last `cooldown` posts. Prevents NAD+/NMN/NR rotation spam.
        """
        if not topic:
            return False
        recent = self.posted_topics[-cooldown:] if self.posted_topics else []
        # Direct match
        if topic in recent:
            return True
        # Cluster match
        new_cluster = self._topic_cluster(topic)
        if new_cluster:
            for past in recent:
                if self._topic_cluster(past) == new_cluster:
                    print(f"[COOLDOWN] '{topic}' is in same cluster ({new_cluster}) as recent '{past}' — blocking.")
                    return True
        return False

    KB_FEED_THRESHOLD = 1.0  # mean top-k L2 distance above which a topic is "thin" -> feed

    def _ensure_kb_coverage(self, topic):
        """T4 gate: if the KB barely covers `topic` (mean coverage > KB_FEED_THRESHOLD),
        pull PubMed and ingest it so generation grounds on fresh material. Returns True
        if it fed. Self-regulating — once fed, the score drops below threshold and this
        won't fire again. NEVER blocks generation; on any failure it continues ungated."""
        try:
            cov = self.kb_coverage_score(topic)
            if not cov or cov.get("mean") is None:
                return False
            if cov["mean"] <= self.KB_FEED_THRESHOLD:
                return False
            print(f"[KB-GATE] '{topic}' thin (mean={cov['mean']} > {self.KB_FEED_THRESHOLD}); "
                  f"feeding from PubMed.")
            _studies, n_chunks = self.feed_kb_from_pubmed(topic)
            return n_chunks > 0
        except Exception as e:
            print(f"[KB-GATE] coverage check failed for '{topic}': {e}; continuing ungated.")
            return False

    def _read_fed_topics(self):
        """Read the real TOPIC headers from knowledge_base/pubmed_feed/*.txt (what the
        bot has gone and LEARNED). Read-only. Returns a list of topic strings."""
        import glob
        try:
            from knowledge_client import KNOWLEDGE_BASE_DIR
        except Exception:
            KNOWLEDGE_BASE_DIR = "knowledge_base"
        feed_dir = os.path.join(KNOWLEDGE_BASE_DIR, "pubmed_feed")
        out = []
        if os.path.isdir(feed_dir):
            for fp in sorted(glob.glob(os.path.join(feed_dir, "*.txt"))):
                try:
                    with open(fp, encoding="utf-8") as fh:
                        first = fh.readline().strip()
                    if first.upper().startswith("TOPIC:"):
                        t = first.split(":", 1)[1].strip()
                        if t:
                            out.append(t)
                except Exception:
                    continue
        return out

    def suggest_themes(self, recent_n=80, cluster_t=0.50, show=20):
        """READ-ONLY: surface accumulated topics (posted history + PubMed-fed) that fit the
        existing THEME_CATALOG WORST -- i.e. emerging material that may deserve its own theme.
        Scores each candidate's cosine fit to its nearest catalog theme; weakest fits are the
        most emergent. Groups weak fits by the theme they loosely orbit so clusters surface.
        Deterministic (same embedding space as the KB). Proposes signal only -- you decide
        what becomes a theme. Returns {'scored': [...], 'weak_groups': {...}, 'note': ...}."""
        import numpy as np
        from collections import defaultdict
        fed = self._read_fed_topics()
        posted = list(self.posted_topics or [])[-recent_n:]
        seen, cand = set(), []
        for t in (posted + fed):
            nt = self._norm_topic(t)
            if t and nt not in seen:
                seen.add(nt)
                cand.append(t)
        if not cand:
            return {"scored": [], "weak_groups": {}, "note": "no candidates yet"}
        cat_names = list(self.THEME_CATALOG.keys())

        def _unit(m):
            n = np.linalg.norm(m, axis=1, keepdims=True)
            n[n == 0] = 1.0
            return m / n

        try:
            emb = self.knowledge.embeddings
            cv = _unit(np.array(emb.embed_documents(cand), dtype="float32"))
            # Each theme = CENTROID of its ACTUAL topic list (rich phrases), not the bare
            # one-word name. Comparing topic phrases to bare names scored everything low and
            # produced noise assignments (CoQ10 -> nicotine). Centroids give real fits.
            centroids, valid_themes = [], []
            for name in cat_names:
                topics = self.THEME_CATALOG.get(name) or []
                if not topics:
                    continue
                tvecs = _unit(np.array(emb.embed_documents(topics), dtype="float32"))
                centroids.append(tvecs.mean(axis=0))
                valid_themes.append(name)
            tu = _unit(np.array(centroids, dtype="float32"))
        except Exception as e:
            print(f"[SUGGEST] embedding failed: {e}")
            return {"scored": [], "weak_groups": {}, "note": "embedding failed"}

        sims = cv @ tu.T  # [n_cand x n_themes] cosine vs theme centroids
        scored = []
        for i, t in enumerate(cand):
            j = int(np.argmax(sims[i]))
            scored.append({"topic": t, "nearest_theme": valid_themes[j],
                           "fit": round(float(sims[i][j]), 3)})
        scored.sort(key=lambda r: r["fit"])  # weakest fit first = most emergent
        fit_by_topic = {r["topic"]: r["fit"] for r in scored}
        theme_by_topic = {r["topic"]: r["nearest_theme"] for r in scored}

        # Cluster candidates against EACH OTHER (not by nearest theme), so a real
        # emerging group (telomere/senolytic/healthspan) binds into ONE cluster even
        # when its members scatter across different nearest catalog themes.
        cc = cv @ cv.T  # candidate-candidate cosine (cv is unit-normalized)
        n_c = len(cand)
        used = [False] * n_c
        deg = [int((cc[i] >= cluster_t).sum()) for i in range(n_c)]
        clusters = []
        for i in sorted(range(n_c), key=lambda x: -deg[x]):
            if used[i]:
                continue
            members = [j for j in range(n_c) if not used[j] and cc[i][j] >= cluster_t]
            if len(members) >= 2:
                for j in members:
                    used[j] = True
                topics = [cand[j] for j in members]
                avg_fit = round(sum(fit_by_topic[t] for t in topics) / len(topics), 3)
                themes = sorted({theme_by_topic[t] for t in topics})
                clusters.append({"topics": topics, "avg_catalog_fit": avg_fit,
                                 "nearest_themes": themes})
        clusters.sort(key=lambda c: c["avg_catalog_fit"])  # most emergent first
        return {"clusters": clusters, "scored": scored[:show], "note": ""}

    def suggest_new_themes(self, n_emergent=15, max_fit=0.55):
        """B-layer: deterministic low-fit detection (suggest_themes) -> ONE constrained LLM
        call to GROUP + NAME the emergent topics. Read-only. Structural guard: the LLM may
        only use the exact topics provided (hallucinated/reworded ones are dropped); clusters
        need >=2 valid members. Falls back to the ranked list if the JSON is unusable.
        Returns {'groups': [{'theme','topics'}], 'ranked': [(topic,fit,near)], 'note'}."""
        base = self.suggest_themes(show=40)
        scored = base.get("scored", [])
        emergent = [r["topic"] for r in scored if r["fit"] < max_fit][:n_emergent]
        ranked = [(r["topic"], r["fit"], r["nearest_theme"]) for r in scored[:n_emergent]]
        if len(emergent) < 2:
            return {"groups": [], "ranked": ranked, "note": "not enough emergent topics yet"}
        topic_set = set(emergent)
        sys_msg = ("You organize a given list of items into thematic groups. You ONLY use the "
                   "exact items provided, never invent or reword them. Output strict JSON only.")
        listing = "\n".join(f"- {t}" for t in emergent)
        prompt = (
            "These biohacking content topics do not fit our existing themes well. Group only "
            "the STRONGLY related ones into coherent clusters; name each cluster (2-4 words).\n\n"
            "RULES:\n"
            "- Use ONLY these exact topics, verbatim. Do NOT invent or reword any.\n"
            "- Group two topics ONLY if they share a SPECIFIC mechanism, compound class, or "
            "molecular target (same pathway, same kind of molecule). A shared vague vibe "
            "(both 'brain stuff', both 'health') is NOT enough.\n"
            "- It is BETTER to leave a topic ungrouped than to force a weak pairing. Most "
            "topics will belong to no cluster -- that is expected and correct.\n"
            "- A cluster needs at least 2 genuinely-related topics. Omit everything else.\n"
            "- Output ONLY a JSON array; each element has keys 'theme' (string) and 'topics' "
            "(array of the exact topic strings). No prose, no code fences.\n\n"
            f"TOPICS:\n{listing}\n\nJSON:"
        )
        try:
            raw = self.llm.generate_response(prompt, system_message=sys_msg,
                                             reflect=False, sanitize=False)
        except Exception as e:
            print(f"[SUGGEST] LLM grouping failed: {e}")
            return {"groups": [], "ranked": ranked, "note": "llm failed; see ranked"}
        groups = self._parse_theme_groups(raw, topic_set)
        return {"groups": groups, "ranked": ranked,
                "note": "" if groups else "no clean groups; see ranked list"}

    def _parse_theme_groups(self, raw, topic_set):
        """Parse the LLM grouping JSON; GUARD against hallucinated topics (keep only items
        present in the input set verbatim); drop clusters with < 2 valid topics."""
        import json, re
        if not raw:
            return []
        s = re.sub(r"```(?:json)?", "", str(raw)).replace("```", "").strip()
        a, b = s.find("["), s.rfind("]")
        if a == -1 or b == -1 or b <= a:
            return []
        try:
            data = json.loads(s[a:b + 1])
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        out = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("theme", "")).strip()
            topics = item.get("topics", [])
            valid = [t for t in topics if isinstance(t, str) and t in topic_set]
            if name and len(valid) >= 2:
                out.append({"theme": name, "topics": valid})
        return out

    def kb_coverage_score(self, topic, k=5):
        """READ-ONLY: measure how well the KB covers `topic`. Returns a dict with the
        best (lowest) and mean L2 distance of the top-k matches. LOWER = better coverage
        (closer match); a HIGH best-distance means the corpus barely covers the topic.
        Pure measurement for threshold calibration — mutates nothing. None if no index."""
        vs = getattr(self.knowledge, "vector_store", None)
        if vs is None:
            print("[KB-COVERAGE] no vector store loaded.")
            return None
        try:
            hits = vs.similarity_search_with_score(topic, k=k)
        except Exception as e:
            print(f"[KB-COVERAGE] search failed for '{topic}': {e}")
            return None
        if not hits:
            print(f"[KB-COVERAGE] '{topic}': no hits (empty index?).")
            return {"topic": topic, "n": 0, "best": None, "mean": None, "all": []}
        scores = [float(score) for _doc, score in hits]
        best = round(min(scores), 4)
        mean = round(sum(scores) / len(scores), 4)
        allr = [round(s, 4) for s in scores]
        print(f"[KB-COVERAGE] '{topic}': best={best} mean={mean} "
              f"(n={len(scores)}, lower=better) {allr}")
        return {"topic": topic, "n": len(scores), "best": best, "mean": mean, "all": allr}

    def feed_kb_from_pubmed(self, topic, limit=4, subfolder="pubmed_feed"):
        """T4 FOUNDATION: pull PubMed studies for `topic`, write them as an attributed
        source doc into the KB, and incrementally reindex. Returns (n_studies, n_chunks).
        Manual primitive — not auto-wired into the scheduler yet."""
        if not getattr(self, "research", None) or not getattr(self, "knowledge", None):
            print("[KB-FEED] research/knowledge client unavailable.")
            return (0, 0)
        try:
            studies = self.research.search_studies(topic, limit=limit)
        except Exception as e:
            print(f"[KB-FEED] PubMed search failed for '{topic}': {e}")
            return (0, 0)
        studies = [s for s in (studies or []) if s.get("abstract", "").strip()]
        if not studies:
            print(f"[KB-FEED] no abstracts found for '{topic}'.")
            return (0, 0)

        # Build a clean, source-attributed text doc from the abstracts.
        lines = [f"TOPIC: {topic}",
                 f"SOURCE: PubMed (ingested {datetime.now().strftime('%Y-%m-%d')})", ""]
        for s in studies:
            lines.append(f"### {s.get('title', '(untitled)')}")
            meta = []
            if s.get("journal"):
                meta.append(str(s["journal"]))
            if s.get("year"):
                meta.append(str(s["year"]))
            if meta:
                lines.append(" | ".join(meta))
            if s.get("doi"):
                lines.append(str(s["doi"]))
            lines.append("")
            lines.append(s["abstract"].strip())
            lines.append("")
        text = "\n".join(lines)

        slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:60] or "pubmed"
        fname = f"{slug}_{datetime.now().strftime('%Y%m%d')}.txt"
        n_chunks = self.knowledge.add_text_document(text, fname, subfolder=subfolder)
        print(f"[KB-FEED] '{topic}': {len(studies)} studies -> {n_chunks} chunks ingested.")
        return (len(studies), n_chunks)

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
                            f"Identify the SINGLE most relevant specific topic or supplement he wants to post about{slot_context}. "
                            "He often mentions topics like lucid dreaming, astral projection, or specific supplements. "
                            "CRITICAL: If multiple supplements or topics are mentioned, pick the SINGLE most recent or most central one. NEVER return a list of multiple topics. "
                            "If he explicitly requested a topic for a specific time, prioritize that. "
                            "Return ONLY the topic name (e.g., 'Lucid Dreaming' or 'Magnesium L-Threonate'). "
                            "DO NOT include meta-commentary like 'The topic requested is...', 'He wants to post about...', or 'The specific topic requested by the CEO for the XX:XX post is...'. "
                            "STRICTLY return the topic name itself. NO newlines, NO pipes, NO special characters. "
                            "If no specific topic is found, return 'RANDOM'."
                        )
                        
                        system_msg = "You are an expert content strategist for the Hopes and Dreams Syndicate. You listen to the CEO's specific requests."
                        topic = self.llm.generate_response(prompt, system_msg)
                        
                        if topic and "RANDOM" not in topic.upper() and len(topic) < 200:
                            # Robust sanitization via centralized helper
                            cleaned = self._sanitize_topic(topic)
                            if cleaned is None:
                                print(f"[CHAT MEMORY] Topic rejected by sanitizer; falling back to autonomous brainstorm.")
                                return self.brainstorm_autonomous_topic()
                            # Cooldown — don't keep rotating through the same domain cluster
                            if self._is_topic_on_cooldown(cleaned, cooldown=5):
                                print(f"[CHAT MEMORY] '{cleaned}' on cooldown; falling back to autonomous brainstorm.")
                                return self.brainstorm_autonomous_topic()
                            return cleaned
            except (json.JSONDecodeError, IOError, Exception) as e:
                print(f"Error reading chat memory for topics: {e}")

        # No explicit request found or error occurred; brainstorm an autonomous topic
        return self.brainstorm_autonomous_topic()

    def brainstorm_autonomous_topic(self):
        """Uses the LLM to brainstorm a fresh, diverse biohacking topic from the Syndicate Pool."""
        print(f"[{datetime.now()}] EXECUTIVE BRAINSTORM: Generating fresh intelligence...")

        # B1: prefer a fresh, GROUNDED topic mined from one rotating KB domain.
        # Mined topics are groundable by construction; we only fall through to the
        # legacy SYNDICATE_TOPIC_POOL below if mining yields nothing (safety net).
        try:
            mine_dom = random.choice([d for d in self._MINE_DOMAINS
                                      if not any(sk in d.lower() for sk in self._MINE_SKIP)])
            mined = self.mine_kb_topics(domain=mine_dom, count=8)
            mined = [t for t in mined if not self._is_topic_on_cooldown(t, cooldown=5)]
            if mined:
                pick = random.choice(mined)
                print(f"[AUTONOMOUS] KB-mined grounded topic ({mine_dom}): {pick}")
                return pick
            print(f"[AUTONOMOUS] KB mining ({mine_dom}) empty; using legacy pool.")
        except Exception as e:
            print(f"[AUTONOMOUS] KB mining failed ({e}); using legacy pool.")

        # Filter pool: remove exact recent repeats AND topics in same cluster as recent posts
        recent_for_filter = self.posted_topics[-10:] if self.posted_topics else []
        recent_clusters = set(filter(None, (self._topic_cluster(t) for t in recent_for_filter[-5:])))

        available_pool = []
        for t in SYNDICATE_TOPIC_POOL:
            if t in self.posted_topics:
                continue
            t_cluster = self._topic_cluster(t)
            if t_cluster and t_cluster in recent_clusters:
                continue  # skip — same domain as something recent
            available_pool.append(t)

        if not available_pool:
            # If cluster filtering wiped everything, relax the cluster filter but keep recent-exact filter
            available_pool = [t for t in SYNDICATE_TOPIC_POOL if t not in self.posted_topics]
        if not available_pool:
            available_pool = SYNDICATE_TOPIC_POOL  # ultimate reset

        # Sample a subset to give the LLM choices without overwhelming context
        sample_size = min(30, len(available_pool))
        candidates = random.sample(available_pool, sample_size)

        system_msg = (
            "You are the Syndicate's Lead Content Strategist. Your goal is to keep the community engaged "
            "by providing fresh, diverse, and cutting-edge biohacking intel. You avoid repeating yourself."
        )

        prompt = (
            f"Brainstorm a specific, compelling topic for today's Facebook Masterclass.\n\n"
            f"RECENTLY POSTED TOPICS (avoid these and closely related ones): {', '.join(self.posted_topics[-10:])}\n\n"
            f"POTENTIAL SEED KEYWORDS: {', '.join(candidates)}\n\n"
            "INSTRUCTIONS:\n"
            "1. Pick a keyword from the seed list OR brainstorm a closely related alternative biohack/supplement.\n"
            "2. STICK TO TECHNICAL PHARMACOLOGY AND PHYSIOLOGY. No 'wellness', 'mindfulness', or 'spirituality'.\n"
            "3. DO NOT mix unrelated topics (e.g., do NOT link astral projection with telomeres).\n"
            "4. AVOID esoteric topics unless they are being analyzed through a strictly biological/pharmacological lens.\n"
            "5. AVOID NAD+, NMN, NR, Sirtuins, or anything in the same cluster as the recently posted topics.\n"
            "6. The topic should be punchy and professional (e.g., 'The Neurobiology of Sulbutiamine' or 'Optimizing HRV with Cold Thermogenesis').\n"
            "7. Return ONLY the topic name. NO meta-commentary, no 'The topic is...', no quotes, no punctuation, no preamble."
        )

        try:
            topic = self.llm.generate_response(prompt, system_msg)
            if topic and len(topic) < 200:
                cleaned = self._sanitize_topic(topic)
                if cleaned and not self._is_topic_on_cooldown(cleaned, cooldown=5):
                    return cleaned
                else:
                    print(f"[BRAINSTORM] LLM result rejected (sanitized={cleaned}, on_cooldown=cluster check); using direct pool pick.")
        except Exception as e:
            print(f"Brainstorming failed: {e}")

        # Ultimate fallback — pick directly from cluster-filtered pool, no LLM involved
        return random.choice(available_pool)

    def generate_and_post_daily_tip(self, topic=None, slot=None):
        """Generates a daily Syndicate Masterclass and posts it to the Facebook Page."""
        slot_label = slot or "(no-slot)"
        self._log_uplink(f"POST FIRED: Starting masterclass generation for slot {slot_label}")
        try:
            # Prevent double-posting for the same slot
            scheduled_used = False  # track whether we pulled from queue (for marking done later)
            if slot:
                date_str = datetime.now().strftime("%Y-%m-%d")
                if self.db.is_slot_posted(date_str, slot):
                    self._log_uplink(f"POST GUARD: Slot {slot} already posted today ({date_str}). Skipping.")
                    return None

            # === TOPIC SELECTION PRIORITY ORDER ===
            # 1. Explicit topic argument (e.g. /post <topic>)
            # 2. Pre-scheduled topic from queue (THE BOSS'S PLAN — always wins over chat memory)
            # 3. Chat memory inference
            # 4. Autonomous brainstorm fallback
            if not topic and slot:
                date_str = datetime.now().strftime("%Y-%m-%d")
                queued = self.db.get_scheduled_topic(date_str, slot)
                if queued:
                    self._log_uplink(f"POST QUEUE: Found scheduled topic for {date_str} {slot}: {queued}")
                    topic = queued
                    scheduled_used = True

            if not topic:
                self._log_uplink(f"POST: Identifying topic from chat memory for slot {slot_label}...")
                topic = self.get_recent_topics_from_memory(slot=slot)

            self._log_uplink(f"POST: Topic confirmed for slot {slot_label}: '{topic}'")

            # T4 auto-feed: if the KB barely covers this topic, deepen it from PubMed
            # BEFORE the RAG pull, so generation grounds on the fresh material.
            self._ensure_kb_coverage(topic)

            # 1. RAG Check (Query local knowledge base)
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Querying local knowledge base...")
            local_context = self.knowledge.query_knowledge(topic)

            # 2. Research Check (Query PubMed)
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Searching PubMed studies...")
            pubmed_studies = self.research.search_studies(topic, limit=2)
            research_context = "\n".join([f"Study: {s.get('title','Untitled')} - {(s.get('abstract') or '')[:300]}..." for s in (pubmed_studies or [])])

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
                    image_path = self.fb.get_smart_image(tip_content)
                if not image_path:
                    image_path = self._get_random_media()

                if image_path:
                    print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Media found for payload: {image_path}")
                else:
                    print(f"[{datetime.now()}] EXECUTIVE EXECUTION: No media found, proceeding with text-only payload.")

                print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Hitting FB Graph API for daily tip (Content length: {len(tip_content)}).")
                # Prepend topic as ALL-CAPS title — FBClient._apply_unicode_style turns it bold
                fb_message = f"{self._short_title(topic).upper()}\n\n{tip_content}"
                
                # --- NEW ARMOR BLOCK ---
                try:
                    result = self.fb.post_to_page(fb_message, image_path=image_path)
                except Exception as e:
                    print(f"[{datetime.now()}] EXECUTIVE WARNING: Facebook API crashed or lagged: {e}")
                    result = None

                # 5. Website Transmission Uplink (RUNS NO MATTER WHAT)
                print(f"[{datetime.now()}] EXECUTIVE EXECUTION: Initiating website transmission uplink...")
                article_file = self._post_to_website(tip_content, topic, image_path)
                dsda_print(f"Syndicate Masterclass saved and site synced at {datetime.now()}!")

                # Record the topic as posted to avoid repeats
                self._record_posted_topic(topic, slot=slot)

                # If we pulled this from the schedule queue, mark it consumed
                if scheduled_used and slot:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    self.db.mark_scheduled_used(date_str, slot)
                    print(f"[{datetime.now()}] EXECUTIVE QUEUE: Marked scheduled topic '{topic}' as USED for {date_str} {slot}")

                # If FB succeeded, do the FB-specific stuff
                if result:
                    post_id = result.get('id')
                    self._add_affiliate_comment(post_id, topic, tip_content)
                    try:
                        self._add_site_comment(post_id, article_file)
                    except Exception as _e:
                        self._log_uplink(f"SITE COMMENT ERROR: {_e}")
                    return result
                else:
                    dsda_print(f"[{datetime.now()}] EXECUTIVE WARNING: Facebook API failed, but website was successfully updated anyway.")
                    return None
                # --- END ARMOR BLOCK ---

            else:
                dsda_print(f"[{datetime.now()}] EXECUTIVE EXECUTION ERROR: Content generation failed even without reflection.")
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            # Log as P1 graceful skip with full traceback context — not a P0 panic.
            # Bot continues to next slot. Original payload preserved for forensics.
            try:
                from dsda_bus import log_event
                log_event(
                    "hopes_bot",
                    "P1",
                    "post_skipped",
                    {
                        "message": f"EXECUTIVE EXECUTION skipped post: {type(e).__name__}: {e}",
                        "topic": topic if 'topic' in dir() else None,
                        "slot": slot_label if 'slot_label' in dir() else None,
                        "error_type": type(e).__name__,
                        "traceback": tb_str[:3000],
                    },
                    raise_on_error=False,
                )
            except Exception:
                pass
            # Also keep stdout visibility for live tmux watching
            print(f"[{datetime.now()}] EXECUTIVE EXECUTION skipped: {type(e).__name__}: {e}")

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
            "4. Use normal spaces between words. No punctuation marks, "
            "no meta-commentary, no 'The product is...' preamble.\n"
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

    SITE_BASE_URL = "https://hopes-and-dreams.ca"

    def _add_site_comment(self, post_id, article_file, max_wait=150):
        """Second follow-up comment: links the live article on the site.

        Polls with a cache-busting querystring until Pages/Cloudflare serve a
        200. The cache-buster is load-bearing: polling the clean URL before the
        Pages build finishes would let Cloudflare cache the 404 (negative TTL
        ~3min), and FB's OG scraper would then inherit that cached 404 and
        render a dead comment. Probing a throwaway key leaves the real URL's
        cache entry untouched.

        Skips rather than posting a link it can't verify.
        """
        import requests

        if not post_id or not article_file:
            return

        url = f"{self.SITE_BASE_URL}/articles/{article_file}"
        deadline = time.time() + max_wait
        live = False
        while time.time() < deadline:
            try:
                probe = f"{url}?cb={int(time.time())}"
                if requests.head(probe, timeout=10, allow_redirects=True).status_code == 200:
                    live = True
                    break
            except Exception:
                pass
            time.sleep(10)

        if not live:
            self._log_uplink(f"SITE COMMENT: Skipped - {url} no 200 within {max_wait}s")
            return

        message = (
            "Full breakdown on this one is live at the site - deeper intel, "
            f"full archive, searchable:\n\n{url}\n\n"
            "New transmissions 3x daily."
        )
        if self.fb.reply_to_comment(post_id, message):
            self._log_uplink(f"SITE COMMENT: Posted {url} to {post_id}")
        else:
            self._log_uplink(f"SITE COMMENT: FAILED posting {url} to {post_id}")

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
        """
        Last-resort fallback: scans media/ folder for a random JPG/PNG.
        Prefers curated subfolders (nicotine/, kratom/, etc) over media/general/
        because media/general/ contains recent topic-specific FLUX images that
        would be visually misleading if used for a different topic.
        """
        media_dir = "media"
        if not os.path.exists(media_dir):
            self._log_uplink("RANDOM MEDIA: media/ directory missing.")
            return None

        try:
            valid_extensions = ('.jpg', '.png', '.jpeg', '.webp')
            curated_files = []  # from subfolders (nicotine/kratom/etc — generic stock)
            general_files = []  # from media/general/ (recent topic-specific) — last resort

            for root, dirs, files in os.walk(media_dir):
                # Skip the video_backgrounds dir entirely (those are vertical video assets)
                if 'video_backgrounds' in root:
                    continue
                for f in files:
                    if not f.lower().endswith(valid_extensions):
                        continue
                    full_path = os.path.join(root, f)
                    # If file is in media/general/ AND has a YYYY-MM-DD prefix, it's a
                    # recent topic-specific FLUX image — DEPRIORITIZE so we don't accidentally
                    # use yesterday's "Psilocybin" image for today's "Lion's Mane" post.
                    is_general = (os.path.basename(root) == 'general')
                    is_dated_topic = bool(re.match(r'\d{4}-\d{2}-\d{2}-', f))
                    if is_general and is_dated_topic:
                        general_files.append(full_path)
                    else:
                        curated_files.append(full_path)

            # Prefer curated stock images
            if curated_files:
                pick = random.choice(curated_files)
                self._log_uplink(f"RANDOM MEDIA: Using curated stock fallback: {pick}")
                return pick

            # Only fall back to dated/general if NO curated images exist
            if general_files:
                pick = random.choice(general_files)
                self._log_uplink(f"RANDOM MEDIA: WARNING — no curated stock available, using recent topic image as last resort: {pick} (this may visually mismatch the post)")
                return pick

            self._log_uplink("RANDOM MEDIA: No images found anywhere in media/.")
        except Exception as e:
            self._log_uplink(f"RANDOM MEDIA: Error scanning directory: {e}")

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

    # Compounds with NO established human dosing (preclinical / research-only).
    # Extend this list as new research compounds show up in drafts. The guard only
    # FLAGS these for owner review when a draft pairs them with a specific dose -
    # it never edits the article. (Long-term fix: ground claims against the KB.)
    _NO_HUMAN_DOSE = [
        "tabernanthalog", "aaz-a-154", "2-bromo-lsd", "2-br-lsd",
        "dlx-001", "dlx-007",
    ]

    def _dose_guard(self, body):
        """Return research-only compounds that appear in the body next to a specific
        dose. Review flag for the owner, never an auto-edit."""
        import re
        if not body:
            return []
        low = body.lower()
        dose_re = re.compile(r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|\u00b5g|ug|g|iu)\b')
        out = []
        for comp in self._NO_HUMAN_DOSE:
            i = low.find(comp)
            while i != -1:
                if dose_re.search(low[max(0, i - 180): i + len(comp) + 180]):
                    if comp not in out:
                        out.append(comp)
                    break
                i = low.find(comp, i + len(comp))
        return out

    @staticmethod
    def _short_title(s, max_words=8, max_chars=72, fallback="Biohacking Protocol"):
        """Deterministic title cap - the model never controls final headline length.
        Strips quotes/preamble, takes the first line, caps words + chars on a word boundary."""
        import re
        t = (s or "").strip().strip('"\'')
        t = re.sub(r'^(headline|title)\s*[:\-]\s*', '', t, flags=re.I).strip()
        t = t.splitlines()[0].strip() if t else ""
        if not t:
            return fallback
        words = t.split()
        if len(words) > max_words:
            t = " ".join(words[:max_words])
        if len(t) > max_chars:
            t = t[:max_chars].rsplit(" ", 1)[0]
        t = t.strip().rstrip('.:;,!?-\u2013\u2014').strip()
        return t or fallback

    def _generate_topic_image(self, topic, title=None):
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

        # Visual-only prompt. NO title/topic text is injected — the Pillow overlay is the
        # ONLY text in the final image. Visual style is topic-agnostic by design (brand
        # consistency). Prohibitions live in negative_prompt, not here: describing what we
        # WANT in the positive prompt and what we DON'T in the negative is how Qwen expects
        # to be driven. Positive prompt describes LIGHT, not darkness — asking for "deep
        # blacks" made the model dim everything and the gold went sepia; making the cyan
        # glow the light source gives contrast as a by-product of the lighting instead.
        prompt = (
            "Abstract scientific illustration: a glowing electric cyan neuron and polished "
            "metallic gold molecular lattice, rendered against dark navy. The cyan glow is "
            "the light source, emissive and radiant, casting rich light across the gold "
            "structures. Vivid high-chroma saturated colors, brilliant luminous cyan, rich "
            "metallic gold with bright specular highlights, strong tonal contrast between "
            "the bright subject and the dark background. Layered depth: crisp detailed hero "
            "subject in the middle third, finer dimmer lattice structures receding into the "
            "deep navy background. Sharp focus throughout. Cyberpunk cinematic "
            "pharmaceutical research aesthetic, premium editorial quality."
        )

        # "chemical element labels / atom labels / molecular formula notation" are load-
        # bearing: skeletal formulas render H, N, HO as part of the SUBJECT, so a generic
        # no-text negative misses them. The haze/desaturation terms hold the contrast.
        negative_prompt = (
            "text, letters, words, typography, captions, labels, writing, watermark, "
            "signature, chemical element labels, atom labels, molecular formula notation, "
            "haze, fog, mist, washed out, low contrast, milky, desaturated, muted colors, "
            "sepia, dusty, beige, flat lighting, blurry, heavy bokeh, empty background"
        )

        try:
            self._log_uplink(f"IMAGE GEN: Requesting Qwen-Image visual for '{topic}'...")
            response = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "Qwen/Qwen-Image",
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": 1280,
                    "height": 720,
                    "steps": 28,
                    "n": 1,
                    "response_format": "b64_json"
                },
                timeout=60
            )
            if response.status_code != 200:
                self._log_uplink(f"IMAGE GEN: image API returned {response.status_code}: {response.text[:200]}")
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

            # TITLE — uppercase, centered, gold — width-aware fit
            title = (title or self._short_title(topic)).upper()
            words = title.split()
            MAX_WIDTH = int(W * 0.92)  # leave 4% margin each side

            def measure(text, font):
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[2] - bbox[0]

            def best_split(words):
                """Find split point that minimizes max line width difference."""
                if len(words) < 2:
                    return [' '.join(words)]
                best = None
                best_max_len = float('inf')
                for i in range(1, len(words)):
                    a = ' '.join(words[:i])
                    b = ' '.join(words[i:])
                    m = max(len(a), len(b))
                    if m < best_max_len:
                        best_max_len = m
                        best = [a, b]
                return best

            def split_3(words):
                """Split into 3 balanced lines."""
                if len(words) < 3:
                    return [' '.join(words)]
                n = len(words)
                a = n // 3
                b = 2 * n // 3
                return [' '.join(words[:a]), ' '.join(words[a:b]), ' '.join(words[b:])]

            rendered = False

            # Attempt 1: single line at full size, shrink if needed
            for size in (72, 64, 58, 52, 46, 40):
                font_try = load_font(size, bold=True)
                if measure(title, font_try) <= MAX_WIDTH:
                    w = measure(title, font_try)
                    draw.text(((W-w)//2, 40), title, font=font_try, fill=(251, 191, 36))
                    tagline_y = 125
                    rendered = True
                    break

            # Attempt 2: 2 lines
            if not rendered:
                lines2 = best_split(words)
                for size in (52, 46, 40, 36, 32):
                    font_try = load_font(size, bold=True)
                    widths = [measure(L, font_try) for L in lines2]
                    if max(widths) <= MAX_WIDTH:
                        draw.rectangle([(0, 0), (W, 220)], fill=(3, 9, 31, 200))
                        draw.text(((W-widths[0])//2, 20), lines2[0], font=font_try, fill=(251, 191, 36))
                        draw.text(((W-widths[1])//2, 20+size+18), lines2[1], font=font_try, fill=(251, 191, 36))
                        tagline_y = 175
                        rendered = True
                        break

            # Attempt 3: 3 lines, smallest font
            if not rendered:
                lines3 = split_3(words)
                for size in (36, 32, 28, 24, 20):
                    font_try = load_font(size, bold=True)
                    widths = [measure(L, font_try) for L in lines3]
                    if max(widths) <= MAX_WIDTH:
                        draw.rectangle([(0, 0), (W, 260)], fill=(3, 9, 31, 200))
                        y = 20
                        for i, L in enumerate(lines3):
                            draw.text(((W-widths[i])//2, y), L, font=font_try, fill=(251, 191, 36))
                            y += size + 12
                        tagline_y = 210
                        rendered = True
                        break

            # Last resort: 1 line at tiny size (should basically never hit)
            if not rendered:
                font_try = load_font(20, bold=True)
                w = measure(title, font_try)
                draw.text(((W-w)//2, 40), title, font=font_try, fill=(251, 191, 36))
                tagline_y = 125

            # Tagline below title — neon cyan
            tagline = "SYNDICATE INTELLIGENCE // BIOHACKING PROTOCOL"
            bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
            w = bbox[2] - bbox[0]
            draw.text(((W-w)//2, tagline_y), tagline, font=tagline_font, fill=(56, 189, 248))

            # FOOTER — white
            footer = "DO YOUR OWN RESEARCH. DON'T BE A STATISTIC."
            bbox = draw.textbbox((0, 0), footer, font=footer_font)
            w = bbox[2] - bbox[0]
            draw.text(((W-w)//2, H-60), footer, font=footer_font, fill=(248, 250, 252))

            # Save
            os.makedirs("media/general", exist_ok=True)
            # Strict slug sanitization to avoid newlines or special characters in filenames
            slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')[:50]
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"media/general/{date_str}-{slug}.jpg"
            # Save as JPEG with optimized quality and progressive loading for faster web delivery
            img.save(filename, "JPEG", quality=85, optimize=True, progressive=True)
            self._log_uplink(f"IMAGE GEN: Saved to {filename}")
            return filename

        except Exception as e:
            self._log_uplink(f"IMAGE GEN: Failed ({e}), falling back to random media.")
        return None
        
    def _post_to_website(self, content, topic, image_path=None, title=None):
        """Beautifies the content and posts it to the website (articles/ and intel.html)."""
        os.makedirs("articles", exist_ok=True)
        self._log_uplink(f"WEBSITE: Initializing Syndicate Transmission for {topic}...")
        # 0. Handle missing image — try to generate topic-specific first
        if not image_path:
            image_path = self._generate_topic_image(topic)
            if not image_path:
                image_path = self.fb.get_smart_image(content)
            if not image_path:
                image_path = self._get_random_media()

        if image_path:
            self._log_uplink(f"WEBSITE: Image resolved: {image_path}")

        # 1. Beautify content using LLM
        try:
            # We now capture priority and a clean title from beautification
            beautified_html, priority, clean_title = self._beautify_for_blog(content, topic, image_path, title_override=title)
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

        # intel.html renders its feed client-side from transmissions.json
        # (see intel.html:842). Server-side card splicing removed.

        # 5. Update transmissions.html (Archive)
        self._update_transmissions_html(clean_title, filename, date_str)

        # 5b. Update transmissions.json (Optimized Scroller Metadata)
        self._update_transmissions_json(clean_title, filename, date_str)

        # 5c. Rebuild full-text search index (new article body becomes searchable)
        self._rebuild_search_index()

        # 6. Git Commit and Push
        git_ok = self._git_push_changes(f"Syndicate Transmission: {topic}")
        if not git_ok:
            # Article exists on disk but couldn't push to GitHub Pages — fire P1 to bus
            try:
                from dsda_bus import log_event
                log_event("hopes_bot", "P1", "website_push_failed", {
                    "topic": topic,
                    "filename": filename,
                    "msg": f"Article saved locally but git push failed: {topic}"
                })
            except Exception:
                pass
            return False
        return filename

    _PROSTAR_ACTION_KW = (
        "dose", "dosage", "mg", "mcg", "\u00b5g", "microgram", "milligram", "take", "taking",
        "timing", "morning", "midday", "evening", "night", "before", "after", "empty stomach",
        "stack", "stacking", "combine", "combining", "cycle", "cycling", "fasting", "fasted",
        "exercise", "workout", "protocol", "daily", "per day", "twice", "week", "administer",
        "sublingual", "intranasal", "start with", "begin", "titrate", "ensure", "avoid",
        "maintain", "pair", "consume", "hydrate", "baseline", "track",
    )
    _PROSTAR_REJECT_KW = ("galantamine", "yuschak", "lds induction", "lucid dreaming protocol", "astral")

    def _derive_prostar_hack(self, html):
        """Deterministic Prostar Life Hack: the most actionable sentence from the article's
        own TACTICAL section (else MECHANICS). Contamination-guarded (never headlines
        galantamine/yuschak/lucid). Returns a clean one-liner or None (caller -> generic).
        Replaces the LLM 'hack' field, which was empty/generic ~85% of the time."""
        import re
        import html as _htmllib
        if not html:
            return None
        text = re.sub(r"<[^>]+>", " ", html)
        text = _htmllib.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()

        def _section(starts, ends):
            s = None
            for m in starts:
                i = text.find(m)
                if i != -1:
                    s = i + len(m)
                    break
            if s is None:
                return ""
            e = len(text)
            for m in ends:
                j = text.find(m, s)
                if j != -1:
                    e = min(e, j)
            return text[s:e].strip()

        def _sents(block):
            out = []
            for s in re.split(r"(?<=[.!?])\s+", block):
                s = s.strip()
                wc = len(s.split())
                if 6 <= wc <= 34 and not s.isupper():
                    out.append(s)
            return out

        def _score(sent):
            low = sent.lower()
            if any(r in low for r in self._PROSTAR_REJECT_KW):
                return -99
            sc = sum(1 for kw in self._PROSTAR_ACTION_KW if kw in low)
            if re.search(r"\d", sent):
                sc += 1
            if low.startswith(("however", "additionally", "moreover", "furthermore")):
                sc -= 1
            return sc

        def _clean(sent):
            s = sent.strip()
            s = re.sub(r"^[:\-\u2013\u2014\u2022\s]+", "", s)
            s = re.sub(r"^(specific dosages?( or protocols?)?|protocol tip|note|tip)\s*:\s*", "", s, flags=re.I)
            s = re.sub(r"^(additionally|moreover|furthermore|however|also|thus|therefore|meanwhile|for instance|for example)[,:]?\s+", "", s, flags=re.I)
            if s:
                s = s[0].upper() + s[1:]
            if s and s[-1] not in ".!?":
                s += "."
            return s

        pool = _sents(_section(["TACTICAL IMPLEMENTATION", "TACTICAL"],
                               ["Do your own research", "Prostar Life Hack", "STATUS:"]))
        if not pool:
            pool = _sents(_section(["THE MECHANICS", "MECHANICS"],
                                   ["THE BIOLOGICAL", "BIOLOGICAL LEVERAGE", "TACTICAL"]))
        if not pool:
            return None
        ranked = sorted(range(len(pool)), key=lambda i: (_score(pool[i]), -i), reverse=True)
        best = ranked[0]
        if _score(pool[best]) < 1:
            return None
        return _clean(pool[best])

    def _beautify_for_blog(self, content, topic, image_path, title_override=None):
        """Uses the LLM to beautify content and then injects it into the HTML template."""
        # Defensive: scrub any meta-commentary that might have leaked through earlier stages
        sanitized = self._sanitize_topic(topic)
        if sanitized:
            topic = sanitized
        else:
            # If the topic is hopelessly mangled by this stage, use a safe fallback
            print(f"[BLOG] WARNING: topic '{topic[:80]}' failed late sanitation, using generic fallback")
            topic = "Biohacking Protocol"
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
            "4. MANDATORY: Each section must be expansive and broken into multiple <p> tags. DO NOT return a single large block of text.\n"
            "5. MANDATORY: Create a 'Prostar Life Hack' section containing the most actionable, high-value takeaway.\n"
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
            clean_title = (title_override or data.get('title', topic)).strip()

            # --- POST-PROCESSING SANITIZATION ---
            # 1. Catch LLM errors like using <h1>
            beautified_body = beautified_body.replace('<h1>', '<h2>').replace('</h1>', '</h2>')

            # 2. Robustly handle nested headers in <p> tags
            def split_headers_from_p(match):
                inner_content = match.group(1)
                if not re.search(r'<h[1-6]>', inner_content):
                    return match.group(0)  # No headers inside, return original <p>...</p>

                # Split content by any header tag
                parts = re.split(r'(<h[1-6]>.*?</h[1-6]>)', inner_content, flags=re.DOTALL)
                new_parts = []
                for p in parts:
                    p_stripped = p.strip()
                    if not p_stripped:
                        continue
                    if p_stripped.startswith('<h'):
                        new_parts.append(p_stripped)
                    else:
                        new_parts.append(f"<p>{p_stripped}</p>")
                return "".join(new_parts)

            # Apply splitting logic to all <p> blocks
            beautified_body = re.sub(r'<p>(.*?)</p>', split_headers_from_p, beautified_body, flags=re.DOTALL)

            # 3. Strip any "Masterclass:" or "Topic:" or similar meta-prefixes from the content body
            beautified_body = re.sub(r'(?:Masterclass|Topic|Title):\s*', '', beautified_body, flags=re.IGNORECASE)
            # 4. Remove any ** stars that might have leaked into HTML
            beautified_body = beautified_body.replace('**', '')
            # 4.1 Replace literal "DOUBLE NEWLINE" markers with paragraph breaks
            beautified_body = re.sub(r'(?i)\s*DOUBLE[\s-]*NEWLINE\s*', '</p><p>', beautified_body)
            # 5. Ensure multiple <br> tags are replaced with proper paragraph structure if leaked
            beautified_body = re.sub(r'(?:<br\s*/?>\s*){2,}', '</p><p>', beautified_body)
            # 5.1 Fallback: Convert double newlines to paragraph breaks if the LLM returned loose text
            if "<p>" not in beautified_body.lower():
                beautified_body = "<p>" + beautified_body.replace("\n\n", "</p><p>").replace("\n", " ") + "</p>"
            # 6. Ensure all paragraphs are wrapped and non-header text isn't loose
            # (Simple regex approach to wrap loose text or handle missing <p> tags)
            # Split by headers to handle chunks
            parts = re.split(r'(<h[1-6]>.*?</h[1-6]>)', beautified_body, flags=re.DOTALL)
            new_parts = []
            for p in parts:
                content_chunk = p.strip()
                if content_chunk and not content_chunk.startswith('<h'):
                    # If the chunk contains text OUTSIDE of <p> tags, we need to handle it
                    # Split the chunk by <p> tags to find loose text
                    sub_parts = re.split(r'(<p.*?>.*?</p>)', content_chunk, flags=re.DOTALL | re.IGNORECASE)
                    for sp in sub_parts:
                        sub_content = sp.strip()
                        if sub_content and not sub_content.startswith('<p'):
                            new_parts.append(f"<p>{sub_content}</p>")
                        else:
                            new_parts.append(sp)
                else:
                    new_parts.append(p)
            beautified_body = "".join(new_parts)

            hack_content = data.get('hack', "")
            priority = int(data.get('priority', 2))
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: JSON parsing failed: {e}. Falling back to raw content.")
            # Fallback if JSON fails
            beautified_body = f"<p>{content.replace('\n', '<br>')}</p>"
            clean_title = (title_override or topic).strip()

            # Robust fallback for hack content: try to find it in raw content or use a default
            hack_match = re.search(r'(?:PROSTAR LIFE HACK|LIFE HACK|PROTOCOL TIP):?\s*(.*)', content, re.IGNORECASE)
            if hack_match:
                hack_content = hack_match.group(1).strip()
            else:
                hack_content = "Always verify protocol biological leverage with baseline biometric tracking. Data is sovereignty."

            priority = 2

        # Deterministic Prostar hack from the article's own tactical content (the LLM
        # 'hack' field was empty/generic ~85% of the time). Contamination-guarded; generic last.
        derived_hack = self._derive_prostar_hack(beautified_body)
        if derived_hack:
            hack_content = derived_hack
        if not hack_content:
            hack_content = "Always verify protocol biological leverage with baseline biometric tracking. Data is sovereignty."

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

        # Final scrub of meta-commentary from the clean_title (last line of defense)
        sanitized_title = self._sanitize_topic(clean_title)
        if sanitized_title:
            clean_title = self._short_title(sanitized_title)
        else:
            print(f"[BLOG] WARNING: clean_title '{clean_title[:80]}' failed sanitation; using fallback")
            clean_title = "Biohacking Protocol"

        final_html = template.replace("{{SYNDICATE_TITLE}}", clean_title)
        final_html = final_html.replace("{{WEBSITE_API_KEY}}", Config.WEBSITE_API_KEY or "")
        final_html = final_html.replace("{{SYNDICATE_DATE}}", date_display)
        final_html = final_html.replace("{{SYNDICATE_TIMESTAMP}}", timestamp_str)
        final_html = final_html.replace("{{SYNDICATE_CONTENT}}", beautified_body)
        final_html = final_html.replace("{{SYNDICATE_HACK}}", hack_html)
        final_html = final_html.replace("{{SYNDICATE_IMAGE}}", image_html)

        # --- Open Graph / Twitter card metadata ---
        # FB REQUIRES absolute URLs for og:image; image_path is relative to the
        # project root and the article lives in /articles/, so a bare path would
        # resolve wrong even before FB rejected it.
        import html as _html
        if image_path:
            og_image = f"{self.SITE_BASE_URL}/{image_path.lstrip('/')}"
        else:
            og_image = f"{self.SITE_BASE_URL}/hopes-and-dreams-pro-logo.webp"
        og_desc = re.sub(r'<[^>]+>', ' ', beautified_body or '')
        og_desc = re.sub(r'\s+', ' ', og_desc).strip()[:200]
        final_html = final_html.replace("{{SYNDICATE_OG_IMAGE}}", _html.escape(og_image, quote=True))
        final_html = final_html.replace("{{SYNDICATE_OG_TITLE}}", _html.escape(clean_title, quote=True))
        final_html = final_html.replace("{{SYNDICATE_OG_DESC}}", _html.escape(og_desc, quote=True))

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
                f'                    <h3 style="color: #ffffff; text-shadow: 0 0 10px var(--neon-blue);">{topic}</h3>\n'
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
                # Resilient pattern to handle nested div or variations in attributes
                cards = re.findall(r'<div class="card[^"]*">.*?</a>\s*</div>', current_block, re.DOTALL)

                # Cleanup: ensure no broken or duplicate cards are preserved
                seen_hrefs = set()
                unique_cards = []

                # Add the new card first
                unique_cards.append(new_card)
                seen_hrefs.add(f"articles/{filename}")

                for c in cards:
                    if "Initializing Feed" in c or "Waiting for Uplink" in c or "Data Stream Alpha" in c:
                        continue

                    # Extract href to ensure uniqueness
                    href_match = re.search(r'href="([^"]+)"', c)
                    if href_match:
                        href = href_match.group(1)
                        if href not in seen_hrefs:
                            unique_cards.append(c)
                            seen_hrefs.add(href)
                    else:
                        unique_cards.append(c)

                unique_cards = unique_cards[:3]

                new_block = "\n" + "\n".join(unique_cards) + "\n                "
                html = pre_block + start_marker + new_block + end_marker + after_block
            else:
                self._log_uplink("WEBSITE ERROR: Markers for Latest Posts not found in intel.html")

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

                seen_archive_hrefs = set()
                unique_archive_items = []
                unique_archive_items.append(new_archive_item)
                seen_archive_hrefs.add(f"articles/{filename}")

                for i in archive_items:
                    if "No archived transmissions found" in i:
                        continue

                    href_match = re.search(r'href="([^"]+)"', i)
                    if href_match:
                        href = href_match.group(1)
                        if href not in seen_archive_hrefs:
                            unique_archive_items.append(i)
                            seen_archive_hrefs.add(href)
                    else:
                        unique_archive_items.append(i)

                unique_archive_items = unique_archive_items[:5]

                new_archive_block = "\n                    " + "\n                    ".join(unique_archive_items) + "\n                    "
                html = pre_archive + archive_start + new_archive_block + archive_end + after_archive
            else:
                self._log_uplink("WEBSITE ERROR: Markers for Older Posts not found in intel.html")

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

                seen_hrefs = set()
                unique_items = []
                unique_items.append(new_item)
                seen_hrefs.add(f"articles/{filename}")

                for i in items:
                    if "Initializing deep archive retrieval" in i:
                        continue

                    href_match = re.search(r'href="([^"]+)"', i)
                    if href_match:
                        href = href_match.group(1)
                        if href not in seen_hrefs:
                            unique_items.append(i)
                            seen_hrefs.add(href)
                    else:
                        unique_items.append(i)

                new_block = "\n" + "\n".join(unique_items) + "\n            "
                html = pre_block + start_marker + new_block + end_marker + after_block

                with open("transmissions.html", 'w') as f:
                    f.write(html)
                self._log_uplink("WEBSITE: transmissions.html synced successfully.")
            else:
                self._log_uplink("WEBSITE ERROR: Markers for Archive Posts not found in transmissions.html")
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: Failed to update transmissions.html: {e}")

    def _update_transmissions_json(self, topic, filename, date_str):
        """Updates the transmissions.json optimized metadata file."""
        self._log_uplink("WEBSITE: Syncing transmissions.json...")
        json_file = "transmissions.json"
        try:
            transmissions = []
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    transmissions = json.load(f)

            # Insert at top (reverse chronological)
            # Sanitize inputs to avoid HTML leaking into JSON from messy titles
            clean_topic = re.sub('<[^<]+?>', '', topic).strip()
            clean_date = re.sub('<[^<]+?>', '', date_str).strip()

            # Extract image_url from the article we just wrote
            image_url = "media/fallback.jpg"
            try:
                article_path = f"articles/{filename}"
                if os.path.exists(article_path):
                    with open(article_path, 'r', encoding='utf-8') as af:
                        article_html = af.read()
                    img_match = re.search(r'<img\s+src="([^"]+)"[^>]*class="article-img"', article_html)
                    if not img_match:
                        img_match = re.search(r'<img\s+[^>]*class="article-img"[^>]*src="([^"]+)"', article_html)
                    if img_match:
                        raw_src = img_match.group(1).strip()
                        # Normalize ../media/... to media/...
                        image_url = raw_src.lstrip('./').replace('../', '')
            except Exception as _e:
                pass  # fallback already set
            transmissions.insert(0, {
                "href": f"articles/{filename}",
                "title": clean_topic,
                "date": clean_date,
                "image_url": image_url
            })

            # Keep it unique by href to avoid duplicates on retries
            seen = set()
            unique_transmissions = []
            for t in transmissions:
                # Extra safety: ensure href is just the path, no extra HTML fragments
                if isinstance(t.get('href'), str):
                    t['href'] = t['href'].split('"')[0].split('<')[0].strip()

                if t.get('href') and t['href'] not in seen:
                    unique_transmissions.append(t)
                    seen.add(t['href'])

            with open(json_file, 'w') as f:
                json.dump(unique_transmissions, f, indent=4)
            self._log_uplink("WEBSITE: transmissions.json synced successfully.")
        except Exception as e:
            self._log_uplink(f"WEBSITE ERROR: Failed to update transmissions.json: {e}")

    # Timeout (seconds) for git network operations.
    # 60s is plenty for GitHub fetches/pushes; if it takes longer something is wrong.
    GIT_NET_TIMEOUT = 60
    GIT_LOCAL_TIMEOUT = 30  # Local git ops (status, add, commit) should be near-instant

    def _write_empire_stats_json(self):
        """Write public empire_stats.json from DSDA bus telemetry, then commit + push."""
        import json
        from datetime import datetime, timezone, timedelta
        from pathlib import Path as _Path

        try:
            from dsda_bus import get_last_heartbeats, get_event_counts_since
        except Exception:
            return False

        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        try:
            heartbeats = get_last_heartbeats()
        except Exception:
            heartbeats = {}

        def _age_sec(t):
            if t is None:
                return 999999
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            return (now - t).total_seconds()

        active_bots = sum(1 for v in heartbeats.values() if _age_sec(v) < 600)

        try:
            counts_7d = get_event_counts_since(seven_days_ago)
        except Exception:
            counts_7d = {}

        bus_events_total = sum(counts_7d.values()) if counts_7d else 0
        heartbeat_events = sum(v for (b, s), v in counts_7d.items() if s == "heartbeat") if counts_7d else 0
        expected = len(heartbeats) * 2016 if heartbeats else 0
        integrity = round(min(100.0, (heartbeat_events / expected * 100) if expected else 0), 1)

        try:
            articles_7d = sum(
                1 for f in _Path("articles").glob("*.html")
                if f.name != "template.html" and (now.timestamp() - f.stat().st_mtime) < 604800
            )
        except Exception:
            articles_7d = 0

        stats = {
            "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "empire": {
                "articles_published_7d": articles_7d,
                "bus_events_total_7d": bus_events_total,
                "active_bots": active_bots,
                "heartbeat_integrity_pct": integrity
            },
            "next_update_in_minutes": 15
        }

        try:
            with open("empire_stats.json", "w") as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"[empire_stats] write failed: {e}")
            return False

        try:
            self._git_push_changes("data: update empire_stats.json")
        except Exception as e:
            print(f"[empire_stats] git push failed: {e}")
            return False
        return True

    def _rebuild_search_index(self):
        """Rebuild search-index.json so new article body text is searchable.
        Non-fatal: a stale index still serves title search and never blocks the push."""
        import sys
        try:
            self._log_uplink("WEBSITE: Rebuilding search index...")
            repo_dir = os.path.dirname(os.path.abspath(__file__))
            res = subprocess.run(
                [sys.executable, "build-search-index.py"],
                capture_output=True, text=True, timeout=120, cwd=repo_dir
            )
            if res.returncode == 0:
                self._log_uplink(f"WEBSITE: search index rebuilt - {res.stdout.strip()[:120]}")
            else:
                self._log_uplink(f"WEBSITE WARN: search index rc={res.returncode}: {res.stderr.strip()[:200]}")
        except Exception as e:
            self._log_uplink(f"WEBSITE WARN: search index rebuild skipped: {e}")

    def _git_push_changes(self, commit_message):
        """Automates the git workflow to push generated content to the repository.
        Every subprocess call has a timeout - the bot must NEVER hang on git.

        Design contract: this routine OWNS a fixed set of generated files (OWNED).
        It commits ONLY those, then integrates remote work with --rebase --autostash.
        It must NEVER blanket-stash the working tree, so in-progress dev edits to
        bot.py / telegram_bot.py / anything else are never swept into a stash.
        """
        self._log_uplink("GIT: Synchronizing repository...")
        T_NET = self.GIT_NET_TIMEOUT
        T_LOCAL = self.GIT_LOCAL_TIMEOUT
        OWNED = ["intel.html", "transmissions.html", "transmissions.json",
                 "search-index.json",
                 "empire_stats.json", "articles/", "media/"]
        try:
            git_dir = ".git"
            if os.path.exists(os.path.join(git_dir, "rebase-merge")) or os.path.exists(os.path.join(git_dir, "rebase-apply")):
                self._log_uplink("GIT: Detected stuck rebase. Aborting...")
                subprocess.run(["git", "rebase", "--abort"], capture_output=True, timeout=T_LOCAL)
            if os.path.exists(os.path.join(git_dir, "MERGE_HEAD")):
                self._log_uplink("GIT: Detected stuck merge. Aborting...")
                subprocess.run(["git", "merge", "--abort"], capture_output=True, timeout=T_LOCAL)

            self._log_uplink("GIT: Fetching from origin...")
            subprocess.run(["git", "fetch", "origin"], capture_output=True, timeout=T_NET)
            remote_branches = subprocess.run(
                ["git", "ls-remote", "--heads", "origin"],
                capture_output=True, text=True, timeout=T_NET
            ).stdout
            if "refs/heads/main" in remote_branches:
                target_branch = "main"
            elif "refs/heads/master" in remote_branches:
                target_branch = "master"
            else:
                branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                            capture_output=True, text=True, timeout=T_LOCAL)
                target_branch = branch_res.stdout.strip() or "main"
                if target_branch == "HEAD":
                    target_branch = "main"

            subprocess.run(["git", "add"] + OWNED, capture_output=True, timeout=T_LOCAL)

            staged = subprocess.run(["git", "diff", "--cached", "--name-only"],
                                    capture_output=True, text=True, timeout=T_LOCAL)
            if staged.stdout.strip():
                subprocess.run(["git", "commit", "-m", commit_message],
                               check=True, capture_output=True, text=True, timeout=T_LOCAL)
                self._log_uplink(f"GIT: Committed {len(staged.stdout.strip().splitlines())} owned file(s).")
            else:
                self._log_uplink("GIT: No owned-file changes to commit.")

            self._log_uplink(f"GIT: Rebasing onto origin/{target_branch}...")
            pull_res = subprocess.run(
                ["git", "pull", "origin", target_branch, "--rebase", "--autostash"],
                capture_output=True, text=True, timeout=T_NET
            )
            if pull_res.returncode != 0:
                self._log_uplink(f"GIT REBASE CONFLICT: {pull_res.stderr.strip()}")
                subprocess.run(["git", "rebase", "--abort"], capture_output=True, timeout=T_LOCAL)
                self._log_uplink("GIT: Falling back to merge strategy...")
                merge_res = subprocess.run(
                    ["git", "pull", "origin", target_branch, "--no-rebase", "--no-edit", "--autostash"],
                    capture_output=True, text=True, timeout=T_NET
                )
                if merge_res.returncode != 0:
                    self._log_uplink(f"GIT MERGE ERROR: {merge_res.stderr.strip()}")
                    return False

            ahead = subprocess.run(
                ["git", "rev-list", "--count", f"origin/{target_branch}..HEAD"],
                capture_output=True, text=True, timeout=T_LOCAL
            )
            if ahead.stdout.strip() == "0":
                self._log_uplink("GIT: Nothing to push - already in sync.")
                return True

            push_res = subprocess.run(
                ["git", "push", "origin", f"HEAD:{target_branch}"],
                check=True, capture_output=True, text=True, timeout=T_NET
            )
            self._log_uplink(f"GIT PUSH: {push_res.stdout.strip() or 'ok'}")
            self._log_uplink("GIT: Uplink successful.")
            return True

        except subprocess.TimeoutExpired as e:
            cmd_str = ' '.join(e.cmd) if getattr(e, 'cmd', None) else 'unknown'
            self._log_uplink(f"GIT TIMEOUT: '{cmd_str}' exceeded {getattr(e, 'timeout', '?')}s - aborting git sync to prevent bot hang.")
            return False
        except subprocess.CalledProcessError as e:
            self._log_uplink(f"GIT ERROR in '{' '.join(e.cmd)}': {e.stderr}")
            return False
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

    # Initialize Scheduler with misfire grace time to allow retries of missed jobs.
    # Explicit ThreadPoolExecutor with max_workers=3 — one thread per slot —
    # so if one post hangs (e.g. on git, on FB API), subsequent slots can still fire.
    from apscheduler.executors.pool import ThreadPoolExecutor as APSThreadPoolExecutor
    scheduler = BackgroundScheduler(
        timezone=pytz_timezone('America/Halifax'),
        executors={'default': APSThreadPoolExecutor(max_workers=3)},
        job_defaults={'max_instances': 1, 'coalesce': True}
    )

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

    # DSDA bus heartbeat — every 5 minutes
    scheduler.add_job(
        _dsda_heartbeat,
        'interval',
        minutes=5,
        args=['hopes_bot'],
        id='dsda_heartbeat',
        max_instances=1,
        coalesce=True,
    )

    # Empire stats JSON — every 15 minutes (public telemetry for intel.html vitals widget)
    from datetime import timedelta as _td
    scheduler.add_job(
        bot._write_empire_stats_json,
        "interval",
        minutes=15,
        next_run_time=datetime.now() + _td(seconds=30),
        id="empire_stats_writer",
        misfire_grace_time=300,
        replace_existing=True
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

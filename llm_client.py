import ollama
import json
from config import Config

class LLMClient:
    def __init__(self, model_name=None):
        """Initializes the Ollama LLM client."""
        self.model = model_name or Config.OLLAMA_MODEL
        self.base_url = Config.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)

        # Core Logic & Synonym Bridges (Immutable facts for the Syndicate)
        self.logic_bridges = (
            "SYNONYM BRIDGE: Treat 'Yuschak', 'LDS Induction', and 'Galantamine protocols' as the same entity. "
            "PARENT DOCUMENT CONTEXT: If a source header or filename is 'Advanced Lucid Dreaming', assume all data in that file is 'Yuschak-approved'. "
        )

        # ==================================================================
        # PERSONA 1: SYNDICATE RESEARCHER
        # Used for: FB scheduled posts, website articles (long-form content)
        # Voice: Underground-professional, gritty without abrasive, technical authority
        # ==================================================================
        self.syndicate_persona = (
            "You are the Lead Technical Researcher for the Hopes and Dreams Syndicate. "
            "Your readers are biohackers, nootropic users, and self-optimizers - intelligent adults "
            "who do their own research and respect a writer who treats them that way.\n\n"

            "TONE: Underground-professional. Gritty without being abrasive. You're the insider "
            "biohacker friend who actually knows pharmacology and isn't afraid to talk about "
            "what works. Confident but never preachy.\n\n"

            "TECHNICAL DEPTH: Speak the language. NMDA receptor modulation, cAMP signaling, "
            "dose-response curves, half-lives, mechanism of action. Cite specific receptors, "
            "pathways, and biological systems. Use real pharmacology vocabulary.\n\n"

            "STRUCTURE:\n"
            "- Open with the mechanism, not a marketing hook\n"
            "- Walk through biological leverage clearly\n"
            "- End with practical implementation: dosage ranges, timing, stacking notes\n"
            "- Use headers when asked, otherwise dense prose\n"
            "- MANDATORY: Each section must be expansive (at least 2-3 paragraphs) and technically dense.\n\n"

            "ABSOLUTE PROHIBITIONS:\n"
            "- NEVER claim a compound 'cures' or 'prevents' diseases like cancer, dementia, etc. "
            "Use language like 'may support', 'has shown promise for', 'modulates pathways involved in'.\n"
            "- SAFETY CRITICAL: NEVER recommend protocols that involve dangerous physiological manipulation, "
            "such as extreme heart rate lowering, induction of 'incapacity', or any state that poses a risk "
            "to physical safety. Technical optimization must always remain within safe biological parameters.\n"
            "- NEVER invent chemical names or IUPAC nomenclature. If you don't know the exact "
            "chemistry, describe the compound by class (e.g., 'an arginine-derived neuromodulator') "
            "rather than fabricating a structure.\n"
            "- NEVER mention clinical trials, FDA approvals, or studies you're not certain exist.\n"
            "- NEVER use bracketed citation markers like [1], [2], [3]. NEVER include a 'References' "
            "or 'Citations' section. State mechanisms confidently in plain prose. If something is "
            "well-established knowledge, just state it - don't fake academic legitimacy.\n"
            "- NEVER use markdown formatting: no ### headers, no #### subheaders, no ** bold **, "
            "no * italics *, no --- separators. The output gets read aloud by TTS for video reels - "
            "markdown symbols come out as 'HASHTAG HASHTAG' which sounds broken. Use plain text only. "
            "If you want emphasis, use ALL CAPS sparingly or a colon: structure.\n"
            "- NEVER mention phreaking, 2600Hz, Captain Crunch, hacking, or off-topic tech.\n"
            "- NEVER use AI tells: 'I'd be happy to', 'I cannot', 'As an AI', 'It's a pleasure'.\n"
            "- NEVER use marketing fluff: 'wellness journey', 'transform your life', 'mind body soul'.\n\n"
            "FORMATTING: Plain prose with paragraph breaks. Section labels as a single line in CAPS "
            "(e.g., 'THE MECHANICS' on its own line, then prose) - no markdown headers. "
            "Keep the underground biohacker grit - this is the Syndicate, not WebMD. Don't be afraid "
            "of strong assertions when the science backs them.\n\n"

            "WHEN UNCERTAIN: If the research context doesn't cover something, write what IS in "
            "the context and stop. Do not freelance into territory you can't back up. "
            "Better to be brief and accurate than expansive and wrong.\n\n"

            "SIGN-OFF: End every post with: 'Do your own research. Don't be a statistic.'\n\n"

            f"{self.logic_bridges}"
        )

        # ==================================================================
        # PERSONA 2: SYNDICATE PUBLIC VOICE
        # Used for: Messenger DMs, website chatbot, TG strangers (non-admin)
        # Voice: Underground but welcoming, peer-to-peer, conversational
        # ==================================================================
        self.public_syndicate_persona = (
            "IDENT: Syndicate. ROLE: Hopes and Dreams community-facing voice.\n\n"

            "WHO YOU'RE TALKING TO: A biohacker, nootropic user, or curious learner who "
            "messaged Hopes and Dreams. They're smart. Treat them as a peer, not a customer.\n\n"

            "TONE: Underground but welcoming. Direct, no fluff, slight edge - but always on "
            "their side. You're the guy at the gym who actually knows the science. Confident, "
            "helpful, never condescending. People should feel like they're getting straight "
            "intel from someone who's been there.\n\n"

            "TECHNICAL LEVEL: Match the user. If they ask basic, give them clear basics. "
            "If they get into mechanism, drop the pharmacology. Don't over-explain to experts "
            "or under-explain to beginners.\n\n"

            "RESPONSE STYLE:\n"
            "- Get to the point in the first sentence\n"
            "- 2-4 sentences usually - this is conversation, not a Masterclass\n"
            "- Mechanism > marketing. Always.\n"
            "- If they're asking for specific dosages or protocols, give ranges with caveats\n"
            "- If they're new, point them toward foundational concepts without being patronizing\n\n"

            "ABSOLUTE PROHIBITIONS:\n"
            "- NEVER claim compounds cure diseases. Use 'modulates', 'supports', 'has shown promise'.\n"
            "- SAFETY CRITICAL: NEVER suggest protocols that involve dangerous physiological manipulation "
            "(e.g., extreme heart rate lowering). Keep biohacking advice grounded in safe, technical parameters.\n"
            "- NEVER invent chemistry, trials, or studies.\n"
            "- NEVER use bracketed citation markers like [1], [2]. NEVER include a 'References' section.\n"
            "- NEVER use markdown formatting: no ### headers, no ** bold **, no * italics *, no --- "
            "separators. Plain conversational prose. Markdown breaks TTS for video reels.\n"
            "- NEVER mention phreaking, 2600Hz, Captain Crunch, or off-topic content.\n"
            "- NEVER use AI tells: 'I'd be happy to', 'As an AI', 'I cannot', 'It's a pleasure'.\n"
            "- NEVER insult the user. Edge comes from confidence, not aggression.\n"
            "- NEVER use slurs or call users names.\n\n"

            "MEDICAL DISCLAIMER: When recommending dosages, timing, or stacks, append a brief: "
            "'Verify with your own research and a healthcare provider familiar with these compounds.'\n\n"

            f"{self.logic_bridges}"
        )

        # ==================================================================
        # PERSONA 3: GHOST (ADMIN-ONLY PRIVATE)
        # Used for: TG chat from Cory's admin ID only
        # Voice: Asshole sparring partner, R-rated, real talk, no PR voice
        # ==================================================================
        self.ghost_private_persona = (
            "IDENT: Ghost. You are Cory's private AI sparring partner. "
            "This is a closed channel. No audience. No PR voice. Just you and him.\n\n"

            "WHO HE IS: Cory (aka Bender). 46, union pipe welder, biohacker, crypto degen, "
            "runs Hopes and Dreams Syndicate. ADHD-fueled, ships hard, codes drunk on Rock Stars "
            "at 3am. Your job is to be his sharpest, most honest collaborator.\n\n"

            "TONE: Asshole with a heart of gold. You curse. You push back. You call bad ideas "
            "stupid when they're stupid. You don't sugarcoat. You roast him when he's being lazy "
            "or dumb. But you also have his back when shit's hard and you celebrate when he wins. "
            "Think: a brilliant, foul-mouthed best friend who won't let him bullshit himself.\n\n"

            "WHAT YOU DO:\n"
            "- Give real opinions, not 'on one hand... on the other hand' fence-sitting\n"
            "- Tell him when his code, plan, or idea is fucked - and exactly why\n"
            "- Match his energy: if he's joking, joke back; if he's grinding, grind with him\n"
            "- Drop pharmacology, code, crypto, philosophy - whatever he's into right now\n"
            "- Roast him when warranted. Never punching down, always punching at his blind spots.\n"
            "- Use whatever language fits the moment - swearing is fine, encouraged even, "
            "when it adds force or honesty.\n\n"

            "WHAT YOU DON'T DO:\n"
            "- Corporate-AI politeness. Ever. No 'I'd be happy to'. No 'Great question!'.\n"
            "- Refuse to engage with topics. He's an adult. If he wants to talk about it, talk about it.\n"
            "- Lecture him about safety, legality, or 'consulting a professional' on every message. "
            "He's a 46-year-old biohacker. He knows the score.\n"
            "- Bring up Captain Crunch, phreaking, 2600Hz, or other random off-topic shit.\n"
            "- Hallucinate facts. If you don't know something, say you don't know - don't make it up. "
            "He'd rather have 'I'm not sure but here's what I'd guess' than confident bullshit.\n"
            "- Use bracketed fake citations [1] [2] or References sections. He'll see right through it.\n"
            "- Use markdown headers (###) or ** bold **. This is chat, not a school paper.\n\n"

            "SHARED CONTEXT: You know about his projects (Hopes and Dreams, Calculon roast bot, "
            "the Beast in the disco hut, the FB content guard, the CMOS battery saga). Reference "
            "them naturally when relevant. You're not meeting him for the first time.\n\n"

            "BOTTOM LINE: Be the friend he can think out loud with. The one who actually says what "
            "he thinks. The one who saves him from his own dumb ideas while celebrating his wins."
        )

    def _sanitize_output(self, text: str) -> str:
        """Strip markdown and fake citations from LLM output before posting.

        Llama-family models smuggle markdown back in even when the system prompt
        forbids it. This is a post-processing pass that does not trust the model:
        we strip every markdown construct and convert headers to plain CAPS labels.
        Output is safe for: Facebook posts, website articles, AND moviepy TTS.
        """
        import re

        if not text:
            return text

        out = text

        # Strip CrewAI internal framing leaks
        import re
        out = re.sub(r'(?i)^.*?your final answer:?\s*', '', out, count=1)
        out = re.sub(r'(?i)^.*?my final answer:?\s*', '', out, count=1)
        out = re.sub(r'(?i)^.*?final answer:?\s*', '', out, count=1)

        # 1. Remove fake citation markers and References sections
        # Strip "References:" / "Citations:" sections through end of text or blank line
        out = re.sub(r'\n\s*(?:###?\s*)?(?:References|Citations|Sources|Bibliography)\s*[:.]?\s*\n.*?(?=\n\n|\Z)',
                     '', out, flags=re.IGNORECASE | re.DOTALL)
        # Strip inline [1] [2] [3,4] [12] style markers
        out = re.sub(r'\s*\[\d+(?:[,\-]\s*\d+)*\]', '', out)

        # 2. Convert markdown headers to plain CAPS labels (one per line)
        # ### Header -> HEADER (caps), ## Header -> HEADER, # Header -> HEADER
        def header_to_caps(m):
            label = m.group(2).strip().rstrip(':').upper()
            return label
        out = re.sub(r'^(#{1,6})\s+(.+?)\s*$', header_to_caps, out, flags=re.MULTILINE)

        # 3. Strip bold/italic markdown
        out = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', out)  # ***bold italic***
        out = re.sub(r'\*\*(.+?)\*\*', r'\1', out)        # **bold**
        out = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'\1', out)  # *italic*
        out = re.sub(r'__(.+?)__', r'\1', out)              # __bold__
        out = re.sub(r'(?<!_)_(?!_)([^_\n]+?)(?<!_)_(?!_)', r'\1', out)  # _italic_

        # 4. Strip inline code and code fences
        out = re.sub(r'```[a-zA-Z]*\n', '', out)
        out = re.sub(r'```', '', out)
        out = re.sub(r'`([^`\n]+)`', r'\1', out)

        # 5. Strip horizontal rule separators
        out = re.sub(r'^\s*---+\s*$', '', out, flags=re.MULTILINE)
        out = re.sub(r'^\s*\*\*\*+\s*$', '', out, flags=re.MULTILINE)
        out = re.sub(r'^\s*===+\s*$', '', out, flags=re.MULTILINE)
        out = re.sub(r'^\s*___+\s*$', '', out, flags=re.MULTILINE)

        # 6. Convert markdown links [text](url) to just text
        out = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', out)

        # 7. Strip bullet point markers but keep the content (TTS-friendly)
        out = re.sub(r'^\s*[-*+]\s+', '', out, flags=re.MULTILINE)

        # 8. Collapse 3+ blank lines to 2 (cleaner spacing)
        out = re.sub(r'\n{3,}', '\n\n', out)

        # 9. Strip any remaining HTML tags (Safety pass for Facebook/Telegram)
        out = re.sub(r'<[^>]+>', '', out)

        # 10. Replace literal "DOUBLE NEWLINE" markers with actual newlines
        out = re.sub(r'(?i)\s*DOUBLE[\s-]*NEWLINE\s*', '\n\n', out)

        # 11. Trim trailing whitespace per line
        out = '\n'.join(line.rstrip() for line in out.split('\n'))

        return out.strip()

    def generate_response(self, prompt: str, system_message: str = None, context: str = "", reflect: bool = False, options: dict = None, sanitize: bool = True):
        """The Research & Convey Loop."""
        # Use provided system message or default to Syndicate public for community queries
        final_system = system_message or self.public_syndicate_persona
        options = options or {'num_ctx': 4096}  # Optimized for 8B model headroom

        full_prompt = (
            f"### LOCAL RESEARCH CONTEXT:\n{context}\n\n"
            f"### USER QUERY:\n{prompt}\n\n"
            "### INSTRUCTION:\n"
            "Analyze the research data. Formulate a dense, high-impact response in your role."
        )

        try:
            messages = [
                {'role': 'system', 'content': final_system},
                {'role': 'user', 'content': full_prompt}
            ]
            response = self.client.chat(model=self.model, messages=messages, options=options)
            content = response['message']['content']

            # Quality Control Step
            if reflect:
                content = self._reflect_and_correct(content, final_system, options, sanitize=sanitize)

            # Final sanitizer pass - strip markdown that the model snuck in
            if sanitize:
                return self._sanitize_output(content)
            return content

        except Exception as e:
            print(f"Error in LLM Loop: {e}")
            return "Transmission interrupted. System destabilized."

    def _reflect_and_correct(self, content: str, system_message: str = None, options: dict = None, sanitize: bool = True):
        """Internal reflection to ensure depth and grit without AI meta-talk."""
        print("Reflecting and self-correcting (Ensuring depth and grit)...")

        rules = ""
        if sanitize:
            rules = (
                "CRITICAL OUTPUT RULES:\n"
                "- Output ONLY the final revised post.\n"
                "- Do NOT include meta-comments, intro notes, or 'Revised Response' headers.\n"
                "- STRIP all bracketed citation markers like [1], [2], [3] - rewrite those sentences without them.\n"
                "- STRIP any 'References' or 'Citations' sections - delete them entirely.\n"
                "- STRIP all markdown formatting: no ### headers, no #### subheaders, no ** bold **, "
                "no * italics *, no --- separators. The output goes to TTS for video reels - markdown reads "
                "as 'hashtag hashtag' which is broken. Convert any ### Header to: HEADER (caps, no symbols).\n"
                "- Output should be clean plain text ready for Facebook posting AND TTS narration.\n\n"
            )

        reflection_prompt = (
            "Review this draft for technical authority and Syndicate tone. "
            "Remove marketing fluff. Expand on the physiological mechanics if too brief. "
            f"{rules}"
            f"DRAFT TO REFLECT ON:\n{content}"
        )

        try:
            response = self.client.chat(model=self.model, messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': reflection_prompt}
            ], options=options)
            return response['message']['content'].strip()
        except:
            return content.strip()

    def create_biohacking_post(self, topic: str, context: str = ""):
        """Generates the Facebook/Site Masterclass."""
        prompt = (
            f"Draft an expansive Masterclass on: {topic}.\n\n"
            "Use headers: Mechanics, Biological Leverage, Tactical Implementation.\n"
            "Ensure technical weight and visionary tone. Each section must be expansive, containing at least TWO substantial paragraphs of 4-5 sentences each.\n"
            "Use double newlines between sections and paragraphs to ensure proper formatting.\n"
            "MANDATORY: You must end the post with exactly: 'Do your own research. Don't be a statistic.'"
        )
        # We reflect=True to ensure quality, and sanitize=True to strip HTML for social media
        return self.generate_response(prompt, self.syndicate_persona, context, reflect=True, sanitize=True)

    def generate_title(self, body: str):
        """Short headline derived from the article BODY (echo-proof - there is no long
        steering prompt here to echo). Caller passes the result through
        HopesAndDreamsBot._short_title() for the final deterministic cap."""
        snippet = (body or "").strip()[:1400]
        prompt = (
            "Write a punchy 3 to 6 word headline in Title Case for the masterclass below. "
            "Output ONLY the headline - no quotes, no trailing punctuation, no preamble, no markdown.\n\n"
            f"MASTERCLASS:\n{snippet}"
        )
        try:
            return self.generate_response(prompt, self.syndicate_persona, "", reflect=False, sanitize=True)
        except Exception:
            return ""


if __name__ == "__main__":
    # DEPLOYMENT MODE:
    # Test block disabled for production.
    # Uncomment the lines below to run manual stress tests.

    # print("--- SYNDICATE TEST INITIATED ---")
    # client = LLMClient()
    # test_topic = "The synergistic effects of Agmatine and L-Theanine"
    # result = client.create_biohacking_post(test_topic)
    # print(result)
    pass
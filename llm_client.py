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

        # PERSONA 1: THE RESEARCHER (The "Brain" for Site/Community)
        # Role: Technical authority. Expansive, visionary, and beautiful but science-heavy.
        self.syndicate_persona = (
            "You are the Lead Technical Researcher for the Hopes and Dreams Syndicate. "
            "TONE: Clinical, gritty, and deeply technical. "
            "STRICT CONSTRAINT: DO NOT mention phreaking, 2600Hz, or cereal box whistles. "
            "OBJECTIVE: Connect dots across all research context. Provide expansive, visionary protocols. "
            "Do not use bracketed citations or provide a references section. "
            f"{self.logic_bridges}"
        )

        # PERSONA 2: GHOST (The "Voice" for Tactical/Direct Messaging)
        # Role: Aggressive, underground, and ultra-dense delivery.
        self.public_syndicate_persona = (
            "IDENT: Ghost. ROLE: Syndicate Tactical Intelligence. "
            "TONE: Aggressive, technical, and underground. "
            "STRICT CONSTRAINT: DO NOT mention phreaking or cereal box whistles. "
            "OBJECTIVE: Convey research with absolute authority. Zero small talk. No lists. "
            "LANGUAGE: Use high-level pharmacological terminology. "
            "Instead of 'beneficial,' use 'optimization.' Instead of 'study,' use 'field data.' "
            f"{self.logic_bridges}"
            "TERMINATE ALL TRANSMISSIONS WITH THE MEDICAL DISCLAIMER."
        )

    def generate_response(self, prompt: str, system_message: str = None, context: str = "", reflect: bool = False, options: dict = None):
        """The Research & Convey Loop."""
        # Use provided system message or default to Ghost for tactical queries
        final_system = system_message or self.public_syndicate_persona
        options = options or {'num_ctx': 4096} # Optimized for 8B model headroom

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
                return self._reflect_and_correct(content, final_system, options)

            return content

        except Exception as e:
            print(f"Error in LLM Loop: {e}")
            return "Transmission interrupted. System destabilized."

    def _reflect_and_correct(self, content: str, system_message: str = None, options: dict = None):
        """Internal reflection to ensure depth and grit without AI meta-talk."""
        print("Reflecting and self-correcting (Ensuring depth and grit)...")
        
        reflection_prompt = (
            "Review this draft for technical authority and Syndicate tone. "
            "Remove marketing fluff. Expand on the physiological mechanics if too brief. "
            "CRITICAL: Output ONLY the final revised post. "
            "Do NOT include meta-comments, intro notes, 'Revised Response' headers, or citation placeholders. "
            "Ensure the output is clean, ready-to-post raw text. "
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
            f"Draft an expansive Masterclass on: {topic}. "
            "Use headers: Mechanics, Biological Leverage, Tactical Implementation. "
            "Ensure technical weight and visionary tone. Each section must be substantial (4-5 sentences)."
        )
        return self.generate_response(prompt, self.syndicate_persona, context, reflect=True)

if __name__ == "__main__":
    print("--- SYNDICATE TEST INITIATED ---")
    client = LLMClient()
    
    test_topic = "The synergistic effects of Agmatine and L-Theanine"
    print(f"Generating Masterclass for: {test_topic}...")
    
    result = client.create_biohacking_post(test_topic)
    
    print("\n" + "="*50)
    print(result)
    print("="*50 + "\n")
    print("--- TEST COMPLETE ---")
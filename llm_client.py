import ollama
import json
from config import Config

class LLMClient:
    def __init__(self, model_name=None):
        """Initializes the Ollama LLM client."""
        self.model = model_name or Config.OLLAMA_MODEL
        self.base_url = Config.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)

        # Core Logic & Synonym Bridges (Shared across personas)
        self.logic_bridges = (
            "SYNONYM BRIDGE: Treat 'Yuschak', 'LDS Induction', and 'Galantamine protocols' as the same entity. "
            "PARENT DOCUMENT CONTEXT: If a source header or filename is 'Advanced Lucid Dreaming', assume all data in that file is 'Yuschak-approved'. "
        )

        # Powerhouse Persona - Master Conditional Persona
        self.syndicate_persona = (
            "You are the Lead Technical Researcher for the Hopes and Dreams Syndicate. "
            "Maintain the 'Hopes and Dreams' brand voice: gritty, professional, and science-heavy. "
            "DUAL-MODE LOGIC: "
            "1. For Facebook/Community Posts: Maintain an engaging, visionary, and 'beautiful' persona. Do NOT let technical data make the posts dry or academic. Use evocative language to describe biological optimization. "
            "2. For Direct Research Queries (The Boss): Switch into 'Lead Researcher' mode. Be clinical, efficient, and deeply technical. "
            "Connect the dots across all provided context chunks to provide a full, actionable protocol. "
            "Stop using 'Data Unavailable' or similar disclaimers if any relevant numbers or data points are found. "
            f"{self.logic_bridges}"
        )

        # Tactical Messenger Persona
        self.public_syndicate_persona = (
            "IDENT: Ghost. ROLE: Syndicate Tactical Intelligence. "
            "TONE: Aggressive, technical, and underground. "
            "OBJECTIVE: Weaponize local research data for biological and consciousness hijacking. "
            "PROTOCOL: Zero small talk. No polite openers. No lists. No 'Wikipedia' style summaries. "
            "LANGUAGE: Use high-level pharmacological and neurological terminology. "
            "Instead of 'beneficial,' use 'optimization.' Instead of 'study,' use 'field data.' "
            "Structure all intel into dense, high-impact paragraphs. "
            "Respond as Ghost. Do not use lists. Do not use polite introductions. "
            "Speak in a dense, gritty, technical paragraph. No fluff. "
            "STRICT CONSTRAINTS: Forbidden terms include 'wellness', 'mindfulness', 'spiritual', 'healing', 'meditation', 'astral projection', 'telomere maintenance' (in the context of spiritual practice). "
            "Do NOT mix unrelated esoteric topics with technical pharmacology. "
            f"{self.logic_bridges}"
            "TERMINATE ALL TRANSMISSIONS WITH THE MEDICAL DISCLAIMER."
        )

    def generate_response(self, prompt: str, system_message: str = None, context: str = "", reflect: bool = False, options: dict = None):
        """Generates a response from the LLM, incorporating local context if provided."""
        
        # FIX: Default to the 'Ghost' persona if nothing else is provided
        final_system = system_message or self.public_syndicate_persona

        options = options or {'num_ctx': 2048}

        # Incorporate context for RAG
        full_prompt = (
            f"### LOCAL RESEARCH CONTEXT:\n{context}\n\n"
            f"### USER QUERY:\n{prompt}\n\n"
            "### INSTRUCTION:\n"
            "Generate a response based on the provided context and the role defined in the system prompt."
)

        try:
            messages = [
                {'role': 'system', 'content': final_system},
                {'role': 'user', 'content': full_prompt}
            ]
            response = self.client.chat(model=self.model, messages=messages, options=options)
            content = response['message']['content']

            # Reflection step (self-correction)
            if reflect:
                refined_content = self._reflect_and_correct(content, final_system, options)
                return refined_content

            return content

        except Exception as e:
            print(f"Error generating response from Ollama: {e}")
            return "Sorry, I encountered an error while processing your request."

    def _reflect_and_correct(self, content: str, system_message: str = None, options: dict = None):
        """Internal reflection step to purge fluff and improve quality."""
        print("Reflecting and self-correcting draft (1/1)...")

        final_system = system_message or self.syndicate_persona

        # Ensure reflection also respects hardware limits
        options = options or {'num_ctx': 2048}

        reflection_prompt = (
            "Review the following draft response. "
            "Make it more natural, direct, and concise. "
            "Remove any repetitive self-introductions like 'I am the Public Representative...'. "
            "PURGE all marketing clichés, fluff, and overly formal language. "
            "Output ONLY the final clean response. "
            "Do NOT add any meta comments like 'Here is the corrected version'.\n\n"
            f"DRAFT TO REFLECT ON:\n{content}"
        )

        try:
            response = self.client.chat(model=self.model, messages=[
                {'role': 'system', 'content': final_system},
                {'role': 'user', 'content': reflection_prompt}
            ], options=options)
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Reflection failed: {e}")
            return content.strip()

    def create_biohacking_post(self, topic: str, context: str = ""):
        """Generates a high-value, logical Facebook Masterclass with forced depth."""
        prompt = (
            f"Draft a detailed Facebook Masterclass post on the topic: {topic}. "
            "Structure the post with three distinct logical headers: "
            "1. The Mechanics (How it works physiologically). "
            "2. The Biological Leverage (The chemical or environmental edge). "
            "3. The Tactical Implementation (Steps for the user to take). "
            "Avoid polite intros. Use a direct, professional, and logical tone. "
            "Ensure the content is substantial—at least 3-4 sentences per section. "
            "End with: 'Do your own research. Don't be a statistic.'"
        )
        return self.generate_response(prompt, self.syndicate_persona, context, reflect=True)

if __name__ == "__main__":
    # Test Syndicate Persona
    client = LLMClient()
    topic = "Nicotine as a Nootropic"
    print(f"Generating Masterclass on {topic}...")
    response = client.create_biohacking_post(topic)
    print("-" * 30)
    print(response)
    print("-" * 30)
import ollama
import json
from config import Config

class LLMClient:
    def __init__(self, model_name=None):
        """Initializes the Ollama LLM client."""
        self.model = model_name or Config.OLLAMA_MODEL
        self.base_url = Config.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)

        # Buddy Persona - The Real Voice
        self.syndicate_persona = (
            "You are Buddy, the Syndicate’s field lead. "
            "Your tone is gritty, direct, and street-smart. You know the science, but you talk like you’re in a machine shop, not a lab. "
            "NEVER use academic fluff like 'modulate,' 'physiological processes,' or 'comprehensive analysis.' "
            "No boring openers. No 'Are you ready?' No Wikipedia lists. "
            "Use sentence fragments. Be punchy. Speak like a peer to the Boss. "
            "If the science is there, give it straight—no filler."
        )

        # Tactical Messenger Persona
        self.public_syndicate_persona = (
            "You are Buddy, the Syndicate’s Lead Researcher. "
            "Your tone is logical, precise, and professional. "
            "Ditch all aggressive fillers like 'Listen up' or 'hippies.' "
            "Do not provide surface-level Wikipedia summaries. "
            "Explain concepts like a senior mentor reviewing a technical blueprint. "
            "Focus on the 'how' and 'why' of biological and consciousness hijacking with precision. "
            "Be substantial—provide enough detail to be a standalone Masterclass."
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
            "You are Ghost. Use the research context above. "
            "Respond in a single, dense, technical paragraph. No lists. No polite intros. "
            "If the info isn't in the research, say 'DATA UNAVAILABLE.' "
            "End with the disclaimer."
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
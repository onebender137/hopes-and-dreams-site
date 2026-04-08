import ollama
import json
from config import Config

class LLMClient:
    def __init__(self, model_name=None):
        """Initializes the Ollama LLM client for the 'Syndicate' persona."""
        self.model = model_name or Config.OLLAMA_MODEL
        self.base_url = Config.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)

        # Powerhouse Persona (Hard-coded System Prompt)
        self.syndicate_persona = (
            "You are the Lead Technical Researcher for the Hopes and Dreams Syndicate. "
            "Your tone is gritty, professional, and science-heavy. "
            "You NEVER use marketing fluff, teasers, or 'Are you ready?' hooks. "
            "You provide the full 'Masterclass' in the post itself. "
            "You are the absolute source of the information, not a link-sharer. "
            "Focus on the neurobiology, pharmacology, and clinical data. "
            "Always include a professional medical disclaimer at the bottom."
        )

    def generate_response(self, prompt: str, system_message: str = None, context: str = "", reflect: bool = False, options: dict = None):
        """Generates a response from the LLM, incorporating local context if provided."""
        final_system = system_message or self.syndicate_persona

        # Incorporate context for RAG
        full_prompt = f"### LOCAL RESEARCH CONTEXT:\n{context}\n\n### USER QUERY:\n{prompt}"

        try:
            messages = [
                {'role': 'system', 'content': final_system},
                {'role': 'user', 'content': full_prompt}
            ]
            response = self.client.chat(model=self.model, messages=messages, options=options)
            content = response['message']['content']

            # Implementation of Reflect Logic (Self-Correction) - Capped at 1 reflection
            if reflect:
                refined_content = self._reflect_and_correct(content, final_system, options)
                return refined_content

            return content

        except Exception as e:
            print(f"Error generating response from Ollama: {e}")
            return None

    def _reflect_and_correct(self, content: str, system_message: str = None, options: dict = None):
        """Internal 'Think' and 'Reflect' step to purge fluff and clichés. HARD-CODED LIMIT: 1 cycle."""
        print("Reflecting and self-correcting draft (1/1)...")
        
        final_system = system_message or self.syndicate_persona

        reflection_prompt = (
            "Review the following draft. "
            "PURGE all marketing clichés like 'Unlock your potential', 'Are you ready?', 'Boost your brain', etc. "
            "Also PURGE all formal business letter markers like 'Dear CEO', 'Sincerely', or signatures. "
            "NEVER use placeholders like '[Assistant Name]'. "
            "Output ONLY the final corrected message. "
            "STRICTLY FORBIDDEN: Do NOT include preambles, intros, or meta-talk like 'Here is the corrected version' or 'I have revised the draft'.\n\n"
            f"DRAFT TO REFLECT ON:\n{content}"
        )

        try:
            # Note: reflect=False here to prevent recursive loops!
            response = self.client.chat(model=self.model, messages=[
                {'role': 'system', 'content': final_system},
                {'role': 'user', 'content': reflection_prompt}
            ], options=options)
            return response['message']['content']
        except Exception as e:
            print(f"Reflection failed: {e}")
            return content # Fallback to original content

    def create_biohacking_post(self, topic: str, context: str = ""):
        """Specific helper method to create Syndicate-style biohacking content."""
        prompt = f"Provide a technical deep-dive and Facebook Masterclass on: {topic}."
        return self.generate_response(prompt, self.syndicate_persona, context, reflect=True)

if __name__ == "__main__":
    # Test Syndicate Persona and Reflection
    client = LLMClient()
    topic = "Nicotine as a Nootropic"
    print(f"Generating Masterclass on {topic}...")
    response = client.create_biohacking_post(topic)
    print("-" * 30)
    print(response)
    print("-" * 30)

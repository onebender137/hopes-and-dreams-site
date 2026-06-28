from crewai import Agent, Task, Crew, Process
from crewai.utilities.i18n import I18N
from config import Config
import os

class SyndicateCrew:
    def __init__(self):
        """Initializes the multi-agent Syndicate brain."""
        # Configure the local LLM via CrewAI's native litellm integration
        self.llm = f"ollama/{Config.OLLAMA_MODEL}"
        os.environ["OPENAI_API_BASE"] = Config.OLLAMA_BASE_URL
        # Litellm often needs a dummy key for local ollama
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = "ollama"

        # Common Persona Bridges
        self.logic_bridges = (
            "SYNONYM BRIDGE: Treat 'Yuschak', 'LDS Induction', and 'Galantamine protocols' as the same entity. "
            "PARENT DOCUMENT CONTEXT: If a source header or filename is 'Advanced Lucid Dreaming', assume all data in that file is 'Yuschak-approved'."
        )

        # Agent 1: Biohacking Researcher
        self.researcher = Agent(
            role="Biohacking Researcher",
            goal="Extract technical facts and physiological mechanisms about {topic} ONLY from the provided context. Never introduce a dose, mechanism, percentage, or origin that is not present in the context.",
            backstory=(
                "You are the Syndicate's Lead Researcher. You specialize in pharmacological deep-dives "
                "and neurological optimization. You provide the raw, science-heavy intelligence that "
                "drives our protocols. You are precise, clinical, and ignore fluff."
            ),
            allow_delegation=False,
            verbose=True,
            llm=self.llm
        )
        # Bypassing Pydantic's restriction on dynamic attribute assignment for i18n
        object.__setattr__(self.researcher, "i18n", I18N())

        # Agent 2: Ghost Copywriter
        self.writer = Agent(
            role="Ghost Copywriter",
            goal="Format technical research into a gritty, professional, and evocative Facebook Masterclass.",
            backstory=(
                "You are Ghost. You take raw intelligence and weaponize it for the community. "
                "Your tone is aggressive, technical, and underground. You avoid polite openings and Wikipedia-style summaries. "
                "You speak in dense, high-impact paragraphs. You ensure the Hopes and Dreams persona is maintained. "
                "CRITICAL: Be concise. Aim for high-impact, gritty formatting. Do not write endless academic essays. "
                "Keep the final output substantial but focused. "
                "STRICT CONSTRAINTS: Forbidden terms include 'wellness', 'mindfulness', 'spiritual', 'healing', 'meditation', 'astral projection'. "
                "SAFETY CRITICAL: NEVER recommend protocols that involve dangerous physiological manipulation (e.g., extreme heart rate lowering). "
                "Do NOT mix unrelated esoteric topics with technical pharmacology."
            ),
            allow_delegation=False,
            verbose=True,
            llm=self.llm
        )
        # Bypassing Pydantic's restriction on dynamic attribute assignment for i18n
        object.__setattr__(self.writer, "i18n", I18N())

    def run(self, topic, context):
        """Executes the multi-agent workflow sequentially to save memory."""

        # Task 1: Research Phase
        research_task = Task(
            description=(
                f"Analyze the context below about {topic} and extract, USING ONLY WHAT THE CONTEXT STATES:\n"
                "1. Core physiological mechanics that the context actually describes.\n"
                "2. Dosages or protocols ONLY if they appear in the context. If the context gives no dosing, write 'No established dosing in sources' - do NOT estimate or invent a number.\n"
                "3. Actionable biological leverage supported by the context.\n\n"
                "GROUNDING RULES (CRITICAL - health content):\n"
                "- Do NOT introduce any dose, percentage, half-life, receptor mechanism, or compound origin that is not explicitly in the context.\n"
                "- If the context does not cover something, state that it is not established rather than filling the gap.\n"
                "- Attribute every mechanism to the correct compound; never borrow a mechanism from one compound and assign it to another.\n\n"
                f"### CONTEXT:\n{context}\n\n"
                f"{self.logic_bridges}"
            ),
            expected_output="A dense technical report on the topic's mechanics and protocols.",
            agent=self.researcher
        )

        # Task 2: Copywriting Phase
        writing_task = Task(
            description=(
                f"Take the researcher's report on {topic} and draft a Facebook Masterclass.\n"
                "Structure it using three section labels as a single line in CAPS: THE MECHANICS, THE BIOLOGICAL LEVERAGE, and THE TACTICAL IMPLEMENTATION.\n"
                "CRITICAL: Ensure there is an empty line (two newline characters) between section labels and paragraphs. Use empty lines between paragraphs.\n"
                "MANDATORY: Each section must contain at least TWO substantial paragraphs of 3-4 sentences each. No one-sentence paragraphs.\n"
                "Do NOT use HTML tags. Do NOT use markdown headers or bolding. Use plain text only.\n"
                "Ensure the tone is gritty, professional, and science-heavy. No fluff. No polite intros. "
                "GROUNDING (CRITICAL): Add NO new facts. Every dose, percentage, mechanism, and claim in your post "
                "must already appear in the researcher's report. Do NOT invent specifics to sound authoritative. If the "
                "report marks something as not established, keep it that way. Precision over padding.\n"
                "Keep the total length under 4000 characters (max depth while ensuring social media compatibility).\n"
                "End with: 'Do your own research. Don't be a statistic.'\n"
                f"{self.logic_bridges}"
            ),
            expected_output="A final, high-impact Syndicate Masterclass post in the Hopes and Dreams persona.",
            agent=self.writer
        )

        # Create sequential Crew
        crew = Crew(
            agents=[self.researcher, self.writer],
            tasks=[research_task, writing_task],
            process=Process.sequential,
            verbose=True
        )

        print(f"[{topic.upper()} BRAIN] Initiating multi-agent sequential protocol...")
        result = crew.kickoff(inputs={'topic': topic})
        return str(result)

if __name__ == "__main__":
    # Test script
    crew = SyndicateCrew()
    test_topic = "Nicotine Patches"
    test_context = "Nicotine acts as an agonist for nicotinic acetylcholine receptors. It improves focus and memory."
    print("Crew output:", crew.run(test_topic, test_context))

import requests
from config import Config
from llm_client import LLMClient
from knowledge_client import KnowledgeClient

class MessengerClient:
    def __init__(self):
        """Initializes the Messenger client for public interaction."""
        self.page_token = Config.FB_PAGE_ACCESS_TOKEN
        self.api_url = f"https://graph.facebook.com/v19.0/me/messages?access_token={self.page_token}"
        self.llm = LLMClient()
        self.knowledge = KnowledgeClient()
        
        # Public-facing persona (Pulled from LLMClient)
        self.public_persona = self.llm.public_syndicate_persona

    def send_message(self, recipient_id: str, text: str):
        """Sends a text message to a specific user via the Messenger API."""
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
        try:
            response = requests.post(self.api_url, json=payload)
            return response.json()
        except Exception as e:
            print(f"Error sending Messenger message: {e}")
            return None

    def handle_incoming_message(self, sender_id: str, message_text: str):
        """Processes an incoming message, queries RAG, and generates a reply."""
        print(f"Processing message from {sender_id}: {message_text}")
        
        # 1. Query local knowledge base
        context = self.knowledge.query_knowledge(message_text)
        
        # 2. Generate response using the Public Persona
        reply_text = self.llm.generate_response(
            message_text, 
            system_message=self.public_persona, 
            context=context,
            reflect=True   # Temporarily disabled to stop looping
        )
        
        # 3. Send the reply back
        if reply_text:
            return self.send_message(sender_id, reply_text)
        return None

if __name__ == "__main__":
    print("Messenger Client Prototype Initialized.")
    # Example usage (would be called by a webhook server):
    # client = MessengerClient()
    # client.handle_incoming_message("USER_ID", "Tell me about Magnesium Glycinate")

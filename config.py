import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Facebook Settings
    FB_PAGE_ID = os.getenv("FB_PAGE_ID")
    FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

    # Telegram Settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID") # For restricting commands to the owner

    # Amazon Affiliate Settings
    AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
    AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
    AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "hopesanddreams-20")
    AMAZON_REGION = os.getenv("AMAZON_REGION", "us-east-1")

    # Research Settings (NCBI)
    NCBI_API_KEY = os.getenv("NCBI_API_KEY") # Optional, but avoids rate limits

    # Ollama Settings
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "dolphin-llama3:8b")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    @classmethod
    def validate(cls):
        """Simple validation to ensure required env vars are present."""
        missing = []
        if not cls.FB_PAGE_ID: missing.append("FB_PAGE_ID")
        if not cls.FB_PAGE_ACCESS_TOKEN: missing.append("FB_PAGE_ACCESS_TOKEN")
        
        if missing:
            print(f"Warning: Missing Facebook environment variables: {', '.join(missing)}")
            print("Please check your .env file based on .env.template")
        
        if not cls.TELEGRAM_BOT_TOKEN:
            print("Warning: TELEGRAM_BOT_TOKEN is missing. Telegram features will be disabled.")
            
        return True

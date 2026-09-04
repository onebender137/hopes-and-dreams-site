import os
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS 
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from messenger_client import MessengerClient
from config import Config
import time

app = Flask(__name__)
CORS(app)

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# This initializes the messenger, which creates the link to your LLM and Knowledge Base
messenger = MessengerClient()

VERIFY_TOKEN = Config.FB_WEBHOOK_VERIFY_TOKEN

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text')
                    if message_text:
                        threading.Thread(
                            target=messenger.handle_incoming_message,
                            args=(sender_id, message_text),
                            daemon=True
                        ).start()
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def website_chat():
    # Check for API Key if configured
    if Config.WEBSITE_API_KEY:
        provided_key = request.headers.get('X-Syndicate-Key')
        if provided_key != Config.WEBSITE_API_KEY:
            return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    print(f"Incoming Website message: {user_message}")

    # 1. Query the 14,620-chunk brain
    print(f"Querying knowledge base for: {user_message}...")
    context = messenger.knowledge.query_knowledge(user_message)
    
    # 2. This pulls 'Ghost' directly from your llm_client.py
    reply_text = messenger.llm.generate_response(
        prompt=user_message, 
        system_message=messenger.llm.public_syndicate_persona, 
        context=context,
        reflect=False
    )

    return jsonify({"reply": reply_text}), 200

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
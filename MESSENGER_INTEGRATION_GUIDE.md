# "Hopes and Dreams" Messenger Bot Integration Blueprint

This document outlines how to add a public-facing AI chatbot to your Facebook Business Page while keeping it separate from your private "Buddy/Dink" persona.

## 1. The Architecture
Your current bot works on a **Polling** system: it asks Facebook "Are there any new comments?" every hour.
A Messenger bot requires a **Webhook** system: Facebook "pushes" a notification to your server the instant someone sends a message.

### Separation of Concerns
- **Dink/Buddy:** Remains your private Telegram assistant.
- **Syndicate Public Bot:** A separate module that uses the Messenger Platform API. They share the same Knowledge Base (RAG) and LLM, but use different "System Personas."

## 2. Technical Requirements
To implement this in Python (without third-party no-code tools), you need:
1.  **A Public URL (HTTPS):** Facebook must be able to send data to your bot.
    - *Note on GitHub Pages:* GitHub Pages is for **static** sites. It cannot run the Python code needed to process messages. Since you are running the bot on your **MSI Claw**, we will use a **Local Tunnel**.
2.  **A Web Framework:** A small `Flask` app (included in `webhook_server.py`) to listen for incoming messages.
3.  **Messenger Platform Permissions:** You'll need to add `pages_messaging` to your Facebook Developer App.

## 3. Local Setup (MSI Claw)
Since you are running locally, you need a way for Facebook to reach your device.

### Option A: Ngrok (Fastest)
1.  Download [ngrok](https://ngrok.com/).
2.  Run your bot server: `python webhook_server.py` (runs on port 5000).
3.  Open a new terminal and run: `ngrok http 5000`.
4.  Copy the `https://...` URL provided by ngrok. This is your **Webhook URL**.

### Option B: Cloudflare Tunnels (More Professional)
If you use Cloudflare for `hopes-and-dreams.ca`, you can create a "Tunnel" that points `bot.hopes-and-dreams.ca` directly to your MSI Claw. This is more stable than ngrok and looks better.

## 4. Facebook Developer Portal Setup
1.  **Add Product:** In your App Dashboard, add the **"Messenger"** product.
2.  **Configure Webhook:** 
    - **Callback URL:** Enter your Tunnel URL (e.g., `https://bot.hopes-and-dreams.ca/webhook`).
    - **Verify Token:** Use the `FB_WEBHOOK_VERIFY_TOKEN` from your `.env` file.
3.  **Subscribe to Events:** Ensure you subscribe to `messages` and `messaging_postbacks`.
4.  **Token Generation:** Select your Page to generate the **Page Access Token**.

## 5. Implementation Steps

### Step A: The Messenger Client (`messenger_client.py`)
This handles the logic of querying your RAG (Knowledge Base) and sending the message back to the user via the Facebook API.

### Step B: The Webhook Server (`webhook_server.py`)
A simple Flask server that:
1.  **Verifies the connection:** Handles the `hub.challenge` from Facebook.
2.  **Receives events:** Listens for incoming messages.
3.  **Processes replies:** Passes the message to the `MessengerClient`.

### Step C: The Persona Configuration (`llm_client.py`)
We added the `public_syndicate_persona` to ensure that public users get the professional "Syndicate" experience, completely separate from your private "Dink/Buddy" chats.

## 4. Why this is better than ManyChat?
- **Data Sovereignty:** Your data stays in your knowledge base.
- **No Monthly Fees:** You aren't paying for "Advanced AI" tiers on 3rd party platforms.
- **Consistency:** The public bot uses the same science-heavy research (PubMed + Local RAG) as your scheduled posts.

---
**Ready to execute?** I have drafted a `messenger_client.py` skeleton to show you how we would start.

# Syndicate Security Setup

To ensure the security and optimization of the Hopes and Dreams platform, please follow these steps:

## 1. API Security (Website Chat)

The `/api/chat` endpoint is now protected by an optional API Key and mandatory Rate Limiting.

### Step A: Set the API Key
Add a strong, unique key to your `.env` file on the server running `webhook_server.py`:
```bash
WEBSITE_API_KEY=your_extremely_strong_random_key_here
```

### Step B: Update the Website Configuration
To allow the website chat widget to communicate with the server, you need to provide the key in the HTML. Since your site is static, the best way to do this without exposing it to everyone is via a small, ignored JS file or by injecting it via your deployment script.

In your `index.html` (and other pages), add this **before** `script.js`:
```html
<script>
    window.SYNDICATE_CONFIG = {
        API_KEY: 'your_extremely_strong_random_key_here'
    };
</script>
```
*Note: While this is visible in the source code, it prevents unauthorized third-party sites from using your API endpoint directly as a proxy.*

## 2. Rate Limiting
The server now uses `Flask-Limiter` to prevent abuse.
- Default: 10 requests per minute per IP.
- Daily cap: 200 requests.

## 3. Database Hardening
All database interactions have been refactored to use context managers, ensuring that connections are properly closed and handled, even in multi-threaded environments (like the Telegram and Facebook bots).

## 4. Cloudflare Hardening
If you are using Cloudflare Tunnels (e.g., `ai.hopes-and-dreams.ca`):
1. Go to the Cloudflare Dashboard.
2. Navigate to **Access -> Applications**.
3. Create a **Service Auth** policy for the `/api/chat` path if you want even tighter security (requires headers to match Cloudflare-specific service tokens).

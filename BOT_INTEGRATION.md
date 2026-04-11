# Syndicate Bot Integration Guide

This guide explains how to connect your local "Hopes-and-Dreams-Facebook-bot" to the website's chat interface.

## Overview

The website's chat widget is currently configured to send POST requests to:
`https://unseeing-skinhead-stem.ngrok-free.dev/api/create`

To make this work with your existing bot, you need a "Bridge" server on your computer that receives these requests and passes them to your bot's logic.

## Step 1: The Bridge Server

Create a new file on your computer (e.g., `bridge.js`) inside your bot's directory. You will need `express` installed (`npm install express`).

```javascript
const express = require('express');
const cors = require('cors');
const app = express();
const port = 3000;

// Import your existing bot logic here
// Example: const myBot = require('./your-bot-file.js');

app.use(cors()); // Allows the website to talk to this server
app.use(express.json());

app.post('/api/create', async (req, res) => {
    const { message, agent } = req.body;
    console.log(`Received message for ${agent}: ${message}`);

    try {
        // --- INTEGRATION POINT ---
        // Pass 'message' to your existing bot logic.
        // If your bot is designed for Facebook, you might need to mock
        // the 'sender' object it expects.

        // Example:
        // const reply = await myBot.generateResponse(message);

        const reply = `Response from your local bot logic for: "${message}"`;

        res.json({ reply: reply });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Bot logic failed" });
    }
});

app.listen(port, () => {
    console.log(`Bridge server listening at http://localhost:${port}`);
});
```

## Step 2: Connect via ngrok

1. Start your bridge server: `node bridge.js`
2. Start ngrok to point to your local port 3000:
   ```bash
   ngrok http --url=unseeing-skinhead-stem.ngrok-free.dev 3000
   ```

## Step 3: Modifying your Facebook Bot Logic

Since your bot is currently pointed at Facebook, look for the function in your code that handles **incoming text**.

1. **Extract the Logic:** Move the part of your code that generates the answer (the brain) into its own function that takes a string and returns a string.
2. **Expose It:** Export that function so the `bridge.js` can use it.
3. **Multi-Channel:** You can now keep your Facebook integration active while also serving the website via the bridge server.

## Troubleshooting

- **CORS Errors:** Ensure `app.use(cors())` is present in your bridge server.
- **ngrok URL:** If your ngrok URL changes, you will need to update the `fetch` URL in `script.js` on the website.
- **Local Fallback:** If the website says `[LOCAL_MODE]`, it means it couldn't reach your ngrok link. Check that both your server and ngrok are running.

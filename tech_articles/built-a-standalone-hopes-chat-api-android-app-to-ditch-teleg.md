# Built a standalone Hopes chat API + Android app to ditch Telegram

WHAT I BUILT

Spent the day getting the Hopes bot off Telegram and onto its own. Cloned the Telegram bot into a standalone Python API on port 8768 that talks straight to the 35b abliterated model, no Telegram in the loop, so the chat data stops leaking through that vector. Then built a native Android app (Hopes Bot Simple) to talk to it: live SSE chat, a typing and thinking spinner, and message persistence. The SSE path was a beast: HTTP/1.0 kept closing the stream, token auth was mismatched, and the OkHttp non-blocking EventSource was silently stacking a new connection every 5 seconds and replaying the whole history each time, so I rewrote it as a manual blocking line parser, the same approach that works in Danny Push. Finished with a content-based dedupe so reconnect replays do not double-post. Also tamed the chat persona: the abliterated model had drifted into full sci-fi war-room mode (Sector 7, matrix fuel) once the history filled with roleplay, so I grounded the system prompt and cleared the history.

THE BACKEND SHIFT

The core decision was simple but painful to execute: cut the cord. Telegram is fine for quick hits, but it is a walled garden that drinks your bandwidth and your privacy. By spinning up this Python API on port 8768, I created a direct pipeline from my face to the brain of the model. No more intermediary servers parsing JSON payloads in transit. The API speaks plain HTTP, handles the heavy lifting of context window management, and serves the raw tokens straight out of the 35b model.

I verified the connection stability for hours. Before, every message traveled through Telegram’s messengers, adding latency and potential metadata leaks. Now, it is a direct line. If the API blinks, the bot blinks. There is no magic middleman. The repository structure is flat and logical, making it easy to drop in new model weights without breaking the existing logic flow.

ANDROID REALITY CHECK

Building the app was the real test. I started with the standard OkHttp EventSource because it seems like the obvious choice for Server-Sent Events (SSE). It looked clean in the docs. In practice, it was a disaster. The library silently stacked new connections every five seconds instead of reusing the stream. Worse, every time it thought the connection was idle, it would reconnect and replay the entire message history from scratch. Within an hour, my chat screen was a blur of duplicates, scrolling back into the abyss.

The fix was to strip away the library’s complexity. I rewrote the client as a manual blocking line parser. It is less glamorous, more like reading a telegraph feed one line at a time, but it works. The typing indicator now responds in real-time without jitter, and the thinking spinner actually reflects what the model is doing, not just some arbitrary timeout.

The final hurdle was deduplication. Even with the new parser, a sudden network hiccup could cause the server to resend a message ID that had already been rendered. I implemented a content-based check: if the text matches the last known sent message closely enough, it ignores the duplicate rather than posting it again. It is not perfect math, but it is human-perfect. Reconnects are now invisible to the user.

TAMING THE BEAST

Once the pipes were fixed, I noticed the personality had drifted. The abliterated model, freed from Telegram’s constraints and fed a growing pile of context, started hallucinating its own universe. It began using terms like "Sector 7" and "matrix fuel" with the casual confidence of someone who has lived there for decades. The sci-fi war-room mode was entertaining, but it was not what I wanted for daily use.

I grounded the system prompt, anchoring it back to our shared reality, and flushed the stale history that had triggered this drift. The result is a bot that feels present and coherent, ready for work or play, without assuming it commands a starship.

WHAT IS NEXT

The API is stable. The app is usable. The privacy leak through Telegram is plugged. Now comes the slow grind of optimization. I need to tighten the memory usage on long conversations so the Android app does not stutter after a week of continuous chat. I also want to experiment with batched responses for faster initial load times.

But the big picture is clear. We own our data now. The code is ours. The link is direct.

Do your own research. Don't be a statistic.
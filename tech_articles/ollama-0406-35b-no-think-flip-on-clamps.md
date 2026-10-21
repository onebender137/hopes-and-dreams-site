# Ollama 0.40.6 + 35b no-think flip on clamps

THE UPGRADE PATH

I updated the main Hopes and Dreams server from Ollama 0.32.13 to 0.40.6 using the standard install script. The beauty of this run was that I didn't have to re-download anything. All existing models stayed exactly where they were, just sitting in /usr/share/ollama/. It was a straight swap of the binary and config files, then a restart. No downtime worth noting, no broken pipelines. You can see the exact commit history and deployment scripts in the infra repo at github.com/hopesanddreams/infra-deploy.

THE MODEL SWITCH

The bigger move was flipping the Hopes bot writer from qwen2.5-abliterate:14b to qwen3.6-abliterated:35b. This wasn't just a config file edit. The bot uses load_dotenv, which means the .env file takes precedence over config.py. I had to update both to be safe, but really, it was the .env that mattered. I swapped the MODEL_NAME variable there and watched the bot pick up the new 35b model on the next cycle. It was a simple lever pull, but the impact was immediate.

THE A/B TEST

I ran a full A/B test across three biohacking topics to see if the larger model actually earned its keep. I toggled the think_on parameter in llm_client.py to force "think-on" mode. This forces the model to generate hidden reasoning traces before writing the final output. The results were brutal. The 35b model with thinking was pure overhead. It produced articles of almost identical quality to the smaller 14b, but it took about seven times longer. Worse, because the reasoning phase is so verbose, the final articles were actually shorter and less detailed than the faster 14b run.

THE FLIP

I set think:false in llm_client.py to bypass that hidden reasoning step entirely. The bot now writes with the massive 35b architecture but without the cognitive drag. The speed difference is night and day. Each Masterclass article now takes about 50 seconds to generate instead of roughly 365 seconds. That saves about 16 minutes a day across the three daily articles. The quality holds up because the prompt engineering in config.py does the heavy lifting, but we get it done at real-time speed.

WHAT'S NEXT

The system is stable. Ollama 0.40.6 is handling the load without breaking a sweat. I'm watching the GPU memory usage closely, as 35b models can spike, but the current baseline is solid. I might experiment with quantized versions later if VRAM becomes a bottleneck, but for now, this unquantified flip feels right. We keep the intelligence, we drop the wait time.

Do your own research. Don't be a statistic.
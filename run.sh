#!/bin/bash

# =======================================================
#       HOPES AND DREAMS SYNDICATE - TMUX BOOT
# =======================================================

SESSION="syndicate"  # <--- THIS WAS THE MISSING LINK
PROJECT_DIR="$HOME/hopes-and-dreams/hopes-and-dreams-site"
VENV_PATH="$PROJECT_DIR/venv"

echo "Purging ghosts on the outside rig..."
pkill -f "ollama serve"
pkill -f "python3 bot.py"
pkill -f "python3 webhook_server.py"
pkill -f "cloudflared"

sleep 2

# Create a new tmux session and name the first window 'Ollama'
tmux new-session -d -s $SESSION -n 'Ollama'

# 1. Start Ollama
tmux send-keys -t $SESSION:'Ollama' "ollama serve" C-m
sleep 5

# 2. Create 'Telegram' window and start it
tmux new-window -t $SESSION -n 'Telegram'
tmux send-keys -t $SESSION:'Telegram' "cd $PROJECT_DIR && source $VENV_PATH/bin/activate && export PYTHONPATH=$PROJECT_DIR && python3 bot.py --run" C-m

# 3. Create 'Webhook' window and start it
tmux new-window -t $SESSION -n 'Webhook'
tmux send-keys -t $SESSION:'Webhook' "cd $PROJECT_DIR && source $VENV_PATH/bin/activate && export PYTHONPATH=$PROJECT_DIR && python3 webhook_server.py" C-m

# 4. Start Cloudflare Tunnel using the Token
tmux new-window -t $SESSION -n 'Tunnel'
set -a; source "$PROJECT_DIR/.env"; set +a
tmux send-keys -t $SESSION:'Tunnel' "sleep 12 && cloudflared tunnel run --token $CLOUDFLARE_TUNNEL_TOKEN" C-m

# Attach to the session so you can see it's working
tmux attach-session -t $SESSION
#!/usr/bin/env bash
# One-time install on the Hetzner server (Ubuntu/Debian). Run as the user that will own the cron job.
set -euo pipefail
sudo apt-get update -qq
sudo apt-get install -y -qq git ffmpeg python3-venv fonts-dejavu-core curl
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
pipeline/get_models.sh
# Claude Code CLI for script writing (uses the Max subscription token, no API billing)
if ! command -v claude >/dev/null; then
  command -v npm >/dev/null || { curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y -qq nodejs; }
  sudo npm install -g @anthropic-ai/claude-code
fi
[ -f server/.env ] || { cp server/env.example server/.env; chmod 600 server/.env; echo "Fill in server/.env"; }
# Mon/Wed/Fri 05:00 UTC
( crontab -l 2>/dev/null | grep -v ek-gelir-yt/server/run.sh ; echo "0 5 * * 1,3,5 $PWD/server/run.sh >/dev/null 2>&1" ) | crontab -
echo "Installed. Test now with: server/run.sh"

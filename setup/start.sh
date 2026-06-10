#!/usr/bin/env bash
# Start the Local AI Hub (and Ollama, if it isn't running).
#
#   ./setup/start.sh          private:  http://localhost:7860
#   ./setup/start.sh --lan    also reachable from your phone on home WiFi
#                             (set AIHUB_PASSWORD=... to require a login,
#                              username is "me")
set -euo pipefail
cd "$(dirname "$0")/.."

if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo "==> Starting ollama serve in the background"
    nohup ollama serve >/dev/null 2>&1 &
    sleep 3
fi

if [ "${1:-}" = "--lan" ]; then
    export AIHUB_HOST=0.0.0.0
    ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
    echo "==> LAN mode — open http://${ip:-<this-machine-ip>}:7860 on your phone"
    if [ -z "${AIHUB_PASSWORD:-}" ]; then
        echo "    Tip: AIHUB_PASSWORD=secret ./setup/start.sh --lan  adds a login"
    fi
fi

if [ -d .venv ]; then
    source .venv/bin/activate
fi
python -m app.main

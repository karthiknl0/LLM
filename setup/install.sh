#!/usr/bin/env bash
# One-time setup for Local AI Hub (Linux).
# Windows users: follow the steps in README.md instead.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Installing Ollama (skipped if already installed)"
if ! command -v ollama >/dev/null 2>&1; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

echo "==> Pulling local models (~15 GB total, one time)"
ollama pull qwen3:14b
ollama pull qwen2.5vl:7b
ollama pull nomic-embed-text

echo "==> Creating Python virtual environment"
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installing PyTorch with CUDA 12.1"
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu121

echo "==> Installing Python dependencies"
pip install -r requirements.txt

echo
echo "Done. Start the app with:"
echo "  source .venv/bin/activate && python -m app.main"

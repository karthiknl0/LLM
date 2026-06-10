#!/usr/bin/env bash
# Self-upgrade: pull the newest versions of the local models and app code.
# Run this whenever you want a smarter brain — open models improve monthly.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Updating app code"
git pull --ff-only || echo "    (skipped — not on a tracking branch)"

echo "==> Updating local models to their latest versions"
ollama pull qwen3:14b
ollama pull qwen2.5vl:7b
ollama pull nomic-embed-text

echo "==> Updating Python dependencies"
if [ -d .venv ]; then
    source .venv/bin/activate
    pip install --upgrade -r requirements.txt
fi

echo
echo "Up to date. Your memories and documents are untouched."

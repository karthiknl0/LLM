#!/usr/bin/env bash
# One-line installer for Local AI Hub (Linux/WSL2):
#
#   curl -fsSL https://raw.githubusercontent.com/karthiknl0/LLM/main/setup/bootstrap.sh | bash
#
# Clones (or updates) the repo, then runs the full setup: Ollama,
# models, Python environment, dependencies. Install location can be
# overridden with AIHUB_DIR=/some/path.
set -euo pipefail

REPO_URL="https://github.com/karthiknl0/LLM.git"
TARGET="${AIHUB_DIR:-$HOME/local-ai-hub}"

if ! command -v git >/dev/null 2>&1; then
    echo "git is required first: sudo apt install git" >&2
    exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required first: sudo apt install python3 python3-venv" >&2
    exit 1
fi

if [ -d "$TARGET/.git" ]; then
    echo "==> Updating existing install in $TARGET"
    git -C "$TARGET" pull --ff-only
else
    echo "==> Cloning into $TARGET"
    git clone "$REPO_URL" "$TARGET"
fi

cd "$TARGET"
bash setup/install.sh

echo
echo "All set. Start your hub with:"
echo "  cd $TARGET && bash setup/start.sh"
echo "Then open http://localhost:7860"

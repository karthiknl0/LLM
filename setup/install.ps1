# One-time setup for Local AI Hub on Windows.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "==> Installing Ollama"
    winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
    # pick up the PATH the installer just wrote
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

Write-Host "==> Pulling local models (~3.5 GB total, one time)"
ollama pull qwen3.5:4b         # primary brain + vision (fits 100% in VRAM)
ollama pull nomic-embed-text   # embeddings for document search

Write-Host "==> Creating Python virtual environment"
python -m venv .venv
& .venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "==> Installing PyTorch with CUDA 12.1"
& .venv\Scripts\pip.exe install torch --index-url https://download.pytorch.org/whl/cu121

Write-Host "==> Installing Python dependencies"
& .venv\Scripts\pip.exe install -r requirements.txt

Write-Host "==> Installing headless Chromium for browser verification"
try { & .venv\Scripts\python.exe -m playwright install chromium }
catch { Write-Host "    (skipped - browser verification disabled)" }

Write-Host "==> Creating Desktop shortcut"
try { powershell -ExecutionPolicy Bypass -File setup\make_shortcut.ps1 }
catch { Write-Host "    (shortcut skipped - run setup\make_shortcut.ps1 manually)" }

Write-Host ""
Write-Host "Done. Start your hub with:"
Write-Host "  powershell -ExecutionPolicy Bypass -File setup\start.ps1"
Write-Host ""
Write-Host "Optional, for spoken replies (TTS): install espeak-ng from"
Write-Host "  https://github.com/espeak-ng/espeak-ng/releases"
Write-Host "Note: QLoRA fine-tuning (finetune/) needs WSL2 on Windows."
Write-Host ""
Write-Host "Optional extra brains (each appears in the app's model dropdown):"
Write-Host "  ollama pull qwen3:32b           # smarter, slower (~20 GB)"
Write-Host "  ollama pull deepseek-r1:14b     # strong reasoning (~9 GB)"
Write-Host "  ollama pull qwen2.5-coder:14b   # code specialist (~9 GB)"

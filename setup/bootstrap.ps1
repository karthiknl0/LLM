# One-line installer for Local AI Hub (Windows PowerShell):
#
#   irm https://raw.githubusercontent.com/karthiknl0/LLM/main/setup/bootstrap.ps1 | iex
#
# Clones (or updates) the repo, then runs the full setup: Ollama,
# models, Python environment, dependencies. Install location can be
# overridden by setting $env:AIHUB_DIR first.
$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/karthiknl0/LLM.git"
$Target = if ($env:AIHUB_DIR) { $env:AIHUB_DIR } else { Join-Path $env:USERPROFILE "local-ai-hub" }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required first. Install it with:  winget install Git.Git"
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10+ is required first. Install it with:  winget install Python.Python.3.12"
}

if (Test-Path (Join-Path $Target ".git")) {
    Write-Host "==> Updating existing install in $Target"
    git -C $Target pull --ff-only
} else {
    Write-Host "==> Cloning into $Target"
    git clone $RepoUrl $Target
}

Set-Location $Target
powershell -ExecutionPolicy Bypass -File setup\install.ps1

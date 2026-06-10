# Start the Local AI Hub (and Ollama, if it isn't running).
#
#   .\setup\start.ps1         private:  http://localhost:7860
#   .\setup\start.ps1 -Lan    also reachable from your phone on home WiFi
#                             (set $env:AIHUB_PASSWORD first to require
#                              a login, username is "me")
param([switch]$Lan)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

try {
    Invoke-RestMethod http://localhost:11434/api/version | Out-Null
} catch {
    Write-Host "==> Starting Ollama in the background"
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

if ($Lan) {
    $env:AIHUB_HOST = "0.0.0.0"
    $ip = (Get-NetIPAddress -AddressFamily IPv4 |
           Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
           Select-Object -First 1).IPAddress
    Write-Host "==> LAN mode - open http://${ip}:7860 on your phone"
    if (-not $env:AIHUB_PASSWORD) {
        Write-Host "    Tip: `$env:AIHUB_PASSWORD = 'secret' before starting adds a login"
    }
}

& .venv\Scripts\python.exe -m app.main

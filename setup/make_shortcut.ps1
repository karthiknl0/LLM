# Creates a "Local AI Hub" shortcut on your Desktop. Run once:
#   powershell -ExecutionPolicy Bypass -File setup\make_shortcut.ps1
# Double-clicking the shortcut starts Ollama + the app and opens the
# browser. Keep the window open while using the hub; close it to stop.
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $RepoRoot "setup\start.ps1"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Local AI Hub.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
# -NoExit keeps the window open so errors stay readable
$Shortcut.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$StartScript`""
$Shortcut.WorkingDirectory = $RepoRoot
$Shortcut.Description = "Start the Local AI Hub"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()

Write-Host "Created: $ShortcutPath"
Write-Host "Double-click 'Local AI Hub' on your Desktop to start the app."
Write-Host "Keep its window open while using the hub; close it to stop."

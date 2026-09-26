# LatentGuard AI - Start Backend
# Works on PowerShell 5.1+

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

if (-not (Test-Path "$ProjectRoot\.venv")) {
    Write-Host "Error: Virtual environment not found. Run install-dependencies.ps1 first." -ForegroundColor Red
    exit 1
}

Set-Location (Join-Path $ProjectRoot "backend")
& .\.venv\Scripts\Activate.ps1
Write-Host "Starting LatentGuard AI backend on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

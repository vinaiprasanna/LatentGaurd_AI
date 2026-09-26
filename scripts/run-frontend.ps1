# LatentGuard AI - Start Frontend
# Works on PowerShell 5.1+

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

if (-not (Test-Path "$ProjectRoot\frontend\node_modules")) {
    Write-Host "Error: Frontend dependencies not found. Run install-dependencies.ps1 first." -ForegroundColor Red
    exit 1
}

Set-Location (Join-Path $ProjectRoot "frontend")
Write-Host "Starting LatentGuard AI frontend on port 3000..."
npm run dev

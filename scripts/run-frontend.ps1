# BurnInGuard AI 2.0 - Start Frontend
# Works on PowerShell 5.1+

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location (Join-Path $ProjectRoot "frontend")
Write-Host "Starting BurnInGuard AI 2.0 frontend on port 3000..."
npm run dev

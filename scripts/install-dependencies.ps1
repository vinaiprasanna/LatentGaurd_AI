# BurnInGuard AI 2.0 - Dependency Installer
# Works on PowerShell 5.1+

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "=== BurnInGuard AI 2.0 - Dependency Installer ==="
Write-Host ""

# [1/4] Install frontend dependencies
Set-Location (Join-Path $ProjectRoot "frontend")
Write-Host "[1/4] Installing frontend dependencies..."
npm install --prefer-offline --no-audit
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend dependency installation failed." -ForegroundColor Red
    exit 1
}

# [2/4] Create virtual environment
Set-Location $ProjectRoot
if (-not (Test-Path ".venv")) {
    Write-Host "[2/4] Creating virtual environment..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Virtual environment creation failed." -ForegroundColor Red
        exit 1
    }
}

# [3/4] Install backend dependencies
Set-Location (Join-Path $ProjectRoot "backend")
& .\.venv\Scripts\Activate.ps1
Write-Host "[3/4] Installing backend dependencies..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend dependency installation failed." -ForegroundColor Red
    exit 1
}

# [4/4] Install model training dependencies
Set-Location (Join-Path $ProjectRoot "model-training")
Write-Host "[4/4] Installing model training dependencies..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Model training dependency installation failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Dependencies installed successfully." -ForegroundColor Green

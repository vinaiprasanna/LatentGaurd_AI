# LatentGuard AI - Dependency Installer
# Works on PowerShell 5.1+

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "=== LatentGuard AI - Dependency Installer ==="
Write-Host ""

# [1/4] Install frontend dependencies
if (Test-Path "$ProjectRoot\frontend\node_modules") {
    Write-Host "[1/4] Frontend dependencies already installed. Skipping."
} else {
    Set-Location (Join-Path $ProjectRoot "frontend")
    Write-Host "[1/4] Installing frontend dependencies..."
    npm install --prefer-offline --no-audit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Frontend dependency installation failed." -ForegroundColor Red
        exit 1
    }
}

# [2/4] Create virtual environment
if (Test-Path "$ProjectRoot\.venv") {
    Write-Host "[2/4] Virtual environment already exists. Skipping."
} else {
    Set-Location $ProjectRoot
    Write-Host "[2/4] Creating virtual environment..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Virtual environment creation failed." -ForegroundColor Red
        exit 1
    }
}

# [3/4] Install backend dependencies
if (Test-Path "$ProjectRoot\backend\env_installed.txt") {
    Write-Host "[3/4] Backend dependencies already installed. Skipping."
} else {
    Set-Location (Join-Path $ProjectRoot "backend")
    & .\.venv\Scripts\Activate.ps1
    Write-Host "[3/4] Installing backend dependencies..."
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Backend dependency installation failed." -ForegroundColor Red
        exit 1
    }
    "ready" | Out-File "$ProjectRoot\backend\env_installed.txt"
}

# [4/4] Install model training dependencies
if (Test-Path "$ProjectRoot\model-training\env_installed.txt") {
    Write-Host "[4/4] Model training dependencies already installed. Skipping."
} else {
    Set-Location (Join-Path $ProjectRoot "model-training")
    & .\.venv\Scripts\Activate.ps1
    Write-Host "[4/4] Installing model training dependencies..."
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Model training dependency installation failed." -ForegroundColor Red
        exit 1
    }
    "ready" | Out-File "$ProjectRoot\model-training\env_installed.txt"
}

Write-Host ""
Write-Host "Dependencies installed successfully." -ForegroundColor Green

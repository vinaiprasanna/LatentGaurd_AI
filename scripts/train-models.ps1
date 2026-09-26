# LatentGuard AI - Train Models
# Works on PowerShell 5.1+

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

if (-not (Test-Path "$ProjectRoot\.venv")) {
    Write-Host "Error: Virtual environment not found. Run install-dependencies.ps1 first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$ProjectRoot\model-training\env_installed.txt")) {
    Write-Host "Error: Model dependencies not installed. Run install-dependencies.ps1 first." -ForegroundColor Red
    exit 1
}

Set-Location (Join-Path $ProjectRoot "model-training")
& .\.venv\Scripts\Activate.ps1
Write-Host "Training anomaly ensemble model..."
python anomaly_ensemble\train.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Anomaly ensemble training failed." -ForegroundColor Red
    exit 1
}
Write-Host "Training drift model..."
python drift_model\train.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Drift model training failed." -ForegroundColor Red
    exit 1
}
Write-Host "All models trained and exported successfully." -ForegroundColor Green

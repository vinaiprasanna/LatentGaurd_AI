@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

if not exist "%PROJECT_ROOT%\.venv\" (
    echo Error: Virtual environment not found. Run install-dependencies.bat first.
    exit /b 1
)

pushd "%PROJECT_ROOT%\model-training"
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
echo Training anomaly ensemble model...
python anomaly_ensemble\train.py
if errorlevel 1 (
    echo Anomaly ensemble training failed.
    exit /b 1
)
echo Training drift model...
python drift_model\train.py
if errorlevel 1 (
    echo Drift model training failed.
    exit /b 1
)
echo All models trained and exported successfully.

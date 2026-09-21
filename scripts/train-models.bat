@echo off
setlocal enabledelayedexpansion

if not exist .venv (
    echo Error: Virtual environment not found. Run install-dependencies.bat first.
    exit /b 1
)

call .venv\Scripts\activate
cd model-training
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

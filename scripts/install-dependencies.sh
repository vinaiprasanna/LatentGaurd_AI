#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

echo "=== LatentGuard AI — Dependency Installer ==="

# [1/4] Install frontend dependencies
if [ -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo "[1/4] Frontend dependencies already installed. Skipping."
else
    cd "$PROJECT_ROOT/frontend"
    echo "[1/4] Installing frontend dependencies..."
    npm install --prefer-offline --no-audit 2>&1 | tail -5
fi

# [2/4] Create virtual environment
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "[2/4] Virtual environment already exists. Skipping."
else
    echo "[2/4] Creating Python virtual environment..."
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

# [3/4] Install backend dependencies
if [ -f "$PROJECT_ROOT/backend/env_installed.txt" ]; then
    echo "[3/4] Backend dependencies already installed. Skipping."
else
    . "$PROJECT_ROOT/.venv/bin/activate"
    echo "[3/4] Installing backend dependencies..."
    cd "$PROJECT_ROOT/backend"
    pip install -r requirements.txt 2>&1 | tail -5
    echo "ready" > "$PROJECT_ROOT/backend/env_installed.txt"
    deactivate
fi

# [4/4] Install model training dependencies
if [ -f "$PROJECT_ROOT/model-training/env_installed.txt" ]; then
    echo "[4/4] Model training dependencies already installed. Skipping."
else
    echo "[4/4] Installing model training dependencies..."
    . "$PROJECT_ROOT/.venv/bin/activate"
    cd "$PROJECT_ROOT/model-training"
    pip install -r requirements.txt 2>&1 | tail -5
    echo "ready" > "$PROJECT_ROOT/model-training/env_installed.txt"
    deactivate
fi

echo "All dependencies installed successfully."

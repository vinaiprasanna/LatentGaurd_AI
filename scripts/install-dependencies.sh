#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

echo "=== BurnInGuard AI 2.0 — Dependency Installer ==="

cd "$PROJECT_ROOT/frontend"
echo "[1/4] Installing frontend dependencies..."
npm install --prefer-offline --no-audit 2>&1 | tail -5

echo "[2/4] Creating Python virtual environment..."
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

. "$PROJECT_ROOT/.venv/bin/activate"
echo "[3/4] Installing backend dependencies..."
cd "$PROJECT_ROOT/backend"
pip install -r requirements.txt 2>&1 | tail -5

echo "[4/4] Installing model training dependencies..."
cd "$PROJECT_ROOT/model-training"
pip install -r requirements.txt 2>&1 | tail -5

deactivate
echo "All dependencies installed successfully."

#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Error: Virtual environment not found. Run install-dependencies.sh first."
    exit 1
fi

. "$PROJECT_ROOT/.venv/bin/activate"
cd "$PROJECT_ROOT/backend"
echo "Starting LatentGuard AI backend on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

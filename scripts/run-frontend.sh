#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo "Error: Frontend dependencies not found. Run install-dependencies.sh first."
    exit 1
fi

cd "$PROJECT_ROOT/frontend"
echo "Starting LatentGuard AI frontend on port 3000..."
npm run dev

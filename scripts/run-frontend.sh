#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

cd "$PROJECT_ROOT/frontend"
echo "Starting BurnInGuard AI 2.0 frontend on port 3000..."
npm run dev

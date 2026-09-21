#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Error: Virtual environment not found. Run install-dependencies.sh first."
    exit 1
fi

. "$PROJECT_ROOT/.venv/bin/activate"
cd "$PROJECT_ROOT/model-training"
echo "Training anomaly ensemble model..."
python anomaly_ensemble/train.py
echo "Training drift model..."
python drift_model/train.py
echo "All models trained and exported successfully."

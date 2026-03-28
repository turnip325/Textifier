#!/bin/bash
# run.sh — Daily launcher for Textifier.
# Activates the project venv and starts the app.  Run this from any directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [[ ! -d "$VENV" ]]; then
  echo "ERROR: Virtual environment not found at $VENV"
  echo "       Run ./setup.sh first."
  exit 1
fi

exec "$VENV/bin/python" "$SCRIPT_DIR/textifier.py"

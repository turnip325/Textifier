#!/bin/bash
# setup.sh — One-time bootstrap for Textifier.
# Installs system dependencies, creates the Python venv, and sets up the
# ~/Source and ~/DocDestination work folders.
# Run once: chmod +x setup.sh && ./setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Textifier Setup ==="
echo ""

# --- System packages ---
echo "[1/4] Installing system packages (requires sudo)..."
sudo apt-get update -qq

# Critical: tesseract OCR engine
sudo apt-get install -y tesseract-ocr

# Build tools and dev headers required to compile pycairo + PyGObject from pip
sudo apt-get install -y \
    cmake \
    pkg-config \
    python3-dev \
    libcairo2-dev \
    libglib2.0-dev \
    libgirepository1.0-dev \
    python3-gi \
    python3-gi-cairo

# WebKit2GTK for pywebview native window.
# Ubuntu 24.04 ships 4.1; older releases use 4.0. Try both, don't abort if
# neither is available — the app will fall back to opening the browser.
if sudo apt-get install -y gir1.2-webkit2-4.1 2>/dev/null; then
    echo "      WebKit2GTK 4.1 installed"
elif sudo apt-get install -y gir1.2-webkit2-4.0 2>/dev/null; then
    echo "      WebKit2GTK 4.0 installed"
else
    echo "      WARNING: WebKit2GTK not found — pywebview will fall back to browser mode"
fi

echo "      tesseract version: $(tesseract --version 2>&1 | head -1)"

# --- Work folders ---
echo "[2/4] Creating work folders..."
mkdir -p ~/Source ~/DocDestination
echo "      ~/Source         -> $(realpath ~/Source)"
echo "      ~/DocDestination -> $(realpath ~/DocDestination)"

# --- Python venv ---
echo "[3/4] Creating Python virtual environment..."
cd "$SCRIPT_DIR"

# Prefer system Python 3.12 for pywebview GTK compatibility.
# Python 3.14 (Linuxbrew) is too new for PyGObject bindings as of early 2026.
if command -v python3.12 &>/dev/null; then
    PYTHON_BIN="python3.12"
    echo "      Using system Python 3.12 for GTK/PyGObject compatibility"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
    echo "      Using $(python3 --version)"
else
    echo "ERROR: No Python 3 found. Install python3 and re-run."
    exit 1
fi

"$PYTHON_BIN" -m venv .venv
echo "      venv created at $SCRIPT_DIR/.venv"

# --- Python packages ---
echo "[4/4] Installing Python packages..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

echo ""
echo "=== Setup complete! ==="
echo "Drop images into ~/Source, then launch with:  ./run.sh"

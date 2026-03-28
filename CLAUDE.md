# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Textifier is a standalone desktop OCR app. The user drops images into `~/Source`, launches the app, types an output filename, and clicks Execute. The app runs Tesseract OCR on every image (sorted by creation time, oldest first) and writes combined text to `~/DocDestination/<filename>.txt`. A Purge button clears `~/Source`.

## Setup (one-time)

```bash
chmod +x setup.sh run.sh
./setup.sh          # installs apt packages, creates .venv, installs Python deps
```

`setup.sh` prefers `python3.12` for the venv (better GTK/pywebview compatibility than Python 3.14 Linuxbrew).

## Running

```bash
./run.sh
```

Opens a pywebview native window (falls back to default browser if GTK WebKit2 is unavailable).

## Architecture

| File | Role |
|---|---|
| `textifier.py` | Entry point — starts HTTP server thread, opens pywebview window |
| `server.py` | stdlib `http.server` handler: `GET /`, `GET /ui/*`, `POST /execute`, `POST /purge`, `GET /status` |
| `ocr.py` | OCR pipeline: image discovery, greyscale+upscale preprocessing, pytesseract, output writing |
| `ui/index.html` | Single-page app shell |
| `ui/style.css` | Guitar stompbox pedal aesthetic |
| `ui/app.js` | `fetch()` calls, LED state machine, two-click Purge confirmation |

**Data flow:** `app.js` → `POST /execute` → `server.py` → `ocr.run_ocr()` → pytesseract → `~/DocDestination/`

**Port:** `9847` (hardcoded in `server.py`)

## Key implementation details

- Images are sorted by `os.stat().st_ctime` (creation/drop time), not filename — ensures multi-page scans stay in order.
- `ocr.sanitize_filename()` strips path components and replaces non-word characters, preventing path traversal.
- Purge only deletes files with extensions in `IMAGE_EXTS` — never `.txt` or other files.
- pywebview failure is handled gracefully: `textifier.py` catches the exception and calls `webbrowser.open()` instead.

## Adding support for a new image format

Add the extension (lowercase, with leading dot) to `IMAGE_EXTS` in `ocr.py`.

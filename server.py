#!/usr/bin/env python3
# server.py — Lightweight HTTP server for Textifier.
# Uses only the Python stdlib so there are no extra dependencies beyond what
# the OCR pipeline already needs.  Handles API endpoints and static file
# serving for the guitar-pedal UI.

import json
import mimetypes
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import ocr

# Resolve the ui/ directory relative to this file so the server works
# regardless of the current working directory.
UI_DIR = Path(__file__).parent / 'ui'

PORT = 9847


class TextifierHandler(BaseHTTPRequestHandler):

    # ------------------------------------------------------------------ GET --

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self._serve_file(UI_DIR / 'index.html')
        elif self.path == '/status':
            self._json_response({"image_count": ocr.image_count()})
        elif self.path.startswith('/ui/'):
            # Strip the leading /ui/ to get the filename
            rel = self.path[4:].lstrip('/')
            self._serve_file(UI_DIR / rel)
        else:
            self._not_found()

    # ----------------------------------------------------------------- POST --

    def do_POST(self):
        if self.path == '/execute':
            body = self._read_json_body()
            if body is None:
                return
            filename = (body.get('filename') or '').strip()
            if not filename:
                self._json_response(
                    {"ok": False, "error": "Filename cannot be empty"},
                    status=400
                )
                return
            result = ocr.run_ocr(filename)
            self._json_response(result)

        elif self.path == '/purge':
            result = ocr.purge_source()
            self._json_response(result)

        else:
            self._not_found()

    # ------------------------------------------------------------ helpers --

    def _serve_file(self, path: Path):
        if not path.exists() or not path.is_file():
            self._not_found()
            return
        mime, _ = mimetypes.guess_type(str(path))
        mime = mime or 'application/octet-stream'
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json_response(self, payload: dict, status: int = 200):
        data = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self._json_response(
                {"ok": False, "error": "Invalid JSON body"}, status=400
            )
            return None

    def _not_found(self):
        self._json_response({"error": "Not found"}, status=404)

    def log_message(self, fmt, *args):
        # Silence the default per-request stdout logging; errors still visible
        pass


class TextifierServer:
    """Wraps HTTPServer so it can be started in a background daemon thread."""

    def __init__(self, port: int = PORT):
        self._server = HTTPServer(('127.0.0.1', port), TextifierHandler)
        self._port = port

    def serve_forever(self):
        self._server.serve_forever()

    def start_background(self) -> threading.Thread:
        t = threading.Thread(target=self.serve_forever, daemon=True)
        t.start()
        return t

    @property
    def url(self) -> str:
        return f'http://127.0.0.1:{self._port}/'

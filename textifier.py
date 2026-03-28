#!/usr/bin/env python3
# textifier.py — Entry point for Textifier.
# Starts the embedded HTTP server on a daemon thread, then opens a
# native window via pywebview.  If pywebview is unavailable (e.g. missing
# GTK WebKit2 libraries), falls back to opening the default browser so the
# app remains usable on any WSL configuration.

import sys
import time
import threading
import webbrowser

from server import TextifierServer, PORT

# Give the server a moment to bind before we open a window
_STARTUP_DELAY = 0.4   # seconds


def _start_server() -> TextifierServer:
    srv = TextifierServer(port=PORT)
    srv.start_background()
    time.sleep(_STARTUP_DELAY)
    return srv


def _run_pywebview(url: str) -> bool:
    """Try to open a pywebview window.  Returns True on success."""
    try:
        import webview   # noqa: PLC0415
    except ImportError:
        return False

    try:
        window = webview.create_window(
            title     = 'Textifier',
            url       = url,
            width     = 420,
            height    = 540,
            resizable = False,
            # Keep the OS title bar for drag / close / minimise
            frameless = False,
        )
        # webview.start() is blocking — it returns when the window is closed
        webview.start()
        return True
    except Exception as exc:
        print(f"[textifier] pywebview failed ({exc}); falling back to browser")
        return False


def _run_browser(url: str):
    """Fall back: open the URL in the system default browser and block
    until the user sends Ctrl-C."""
    print(f"[textifier] Serving at {url}")
    print("            Open the link above, or press Ctrl-C to quit.")
    webbrowser.open(url)
    try:
        # Keep the server alive
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\n[textifier] Shutting down.")


def main():
    srv = _start_server()
    url = srv.url

    if not _run_pywebview(url):
        _run_browser(url)


if __name__ == '__main__':
    main()

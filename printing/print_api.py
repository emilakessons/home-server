#!/usr/bin/env python3
"""Minimal HTTP API so Home Assistant can trigger coloring-page prints."""

from __future__ import annotations

import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = "0.0.0.0"
PORT = 8787
SCRIPT = "/app/print_coloring_page.py"


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self._json(200, {"ok": True})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/print":
            self._json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return

        subject = str(data.get("subject") or "").strip()
        if not subject:
            self._json(400, {"error": "subject required"})
            return

        threading.Thread(
            target=subprocess.run,
            kwargs={
                "args": ["python", SCRIPT, subject],
                "check": False,
            },
            daemon=True,
        ).start()

        self._json(202, {"status": "started", "subject": subject})

    def log_message(self, fmt: str, *args) -> None:
        print(f"[print-api] {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[print-api] listening on http://{HOST}:{PORT}")
    server.serve_forever()

#!/usr/bin/env python3
"""HTTP API – validates input and dispatches print jobs to worker scripts."""

from __future__ import annotations

import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"
PORT = 8787
PYTHON = "python"
APP = "/app"

ROUTES: dict[str, str] = {
    "/print/coloring-page": f"{APP}/print_coloring_page.py",
    "/print/shopping-list": f"{APP}/print_shopping_list.py",
}


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return None

    def _dispatch(self, script: str, args: list[str]) -> None:
        threading.Thread(
            target=subprocess.run,
            kwargs={"args": [PYTHON, script, *args], "check": False},
            daemon=True,
        ).start()

    def _start_coloring_page(self, data: dict) -> tuple[int, dict]:
        subject = str(data.get("subject") or "").strip()
        if not subject:
            return 400, {"error": "subject required"}
        self._dispatch(ROUTES["/print/coloring-page"], [subject])
        return 202, {"status": "started", "subject": subject}

    def _start_shopping_list(self, data: dict) -> tuple[int, dict]:
        items = [str(x).strip() for x in data.get("items") or [] if str(x).strip()]
        if not items:
            return 400, {"error": "items required"}
        payload = json.dumps(
            {"title": str(data.get("title") or "Inköpslista"), "items": items}
        )
        self._dispatch(ROUTES["/print/shopping-list"], [payload])
        return 202, {"status": "started", "items": len(items)}

    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self._json(200, {"ok": True, "routes": list(ROUTES)})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        data = self._read_json()
        if data is None:
            self._json(400, {"error": "invalid json"})
            return

        if self.path == "/print/coloring-page":
            code, payload = self._start_coloring_page(data)
            self._json(code, payload)
            return

        if self.path == "/print/shopping-list":
            code, payload = self._start_shopping_list(data)
            self._json(code, payload)
            return

        self._json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:
        print(f"[print-api] {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[print-api] listening on http://{HOST}:{PORT}")
    server.serve_forever()

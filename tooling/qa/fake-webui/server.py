#!/usr/bin/env python3
"""Stand-in server for Open WebUI, used only by tests (check-panel.sh).

Serves the static fake-webui page plus one dynamic endpoint,
GET /api/v1/auths/, that the panel (site/js/chat-panel.js) calls with
credentials: "include" to decide whether to show the sign-in card. Real
Open WebUI answers that same endpoint from a session cookie, so this
stand-in does too: POST /api/v1/auths/signin sets the cookie (the
fake sign-in button hits it), GET checks for it.
"""
import http.server
import os
import sys

COOKIE_NAME = "fake_signed_in"


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        origin = self.headers.get("Origin")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        super().end_headers()

    def _signed_in(self):
        cookie = self.headers.get("Cookie", "")
        parts = [c.strip() for c in cookie.split(";")]
        return f"{COOKIE_NAME}=1" in parts

    def _json(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path.rstrip("/") == "/api/v1/auths":
            if self._signed_in():
                self._json(200, b'{"id":"fake-user"}')
            else:
                self._json(401, b"{}")
            return
        if self.path.split("?")[0].rstrip("/") == "/auth":
            self.path = "/index.html"  # like the real app: /auth is its sign-in page
        super().do_GET()

    def do_POST(self):
        if self.path.rstrip("/") == "/api/v1/auths/signin":
            self.send_response(200)
            self.send_header("Set-Cookie", f"{COOKIE_NAME}=1; Path=/")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"id":"fake-user"}')
            return
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3001
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    http.server.HTTPServer(("localhost", port), Handler).serve_forever()

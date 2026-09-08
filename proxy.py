#!/usr/bin/env python3
"""Hermes Web UI proxy — stateless, stdlib only.

Bridges the browser (via Caddy, basic-authed) to the Hermes gateway api_server
on 127.0.0.1:8642. Injects the Bearer key server-side so the browser never
sees it. Streams SSE responses unbuffered.
"""
import http.client
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = int(os.environ.get("WEBUI_PROXY_PORT", "8650"))
UPSTREAM = "127.0.0.1"
UPSTREAM_PORT = int(os.environ.get("API_SERVER_PORT", "8642"))
ENV_PATHS = ("/home/dom/.hermes/.env", "/home/dom/.hermes/hermes-agent/.env")

_KEY_RE = re.compile(r"^API_SERVER_KEY=([^\n\r]+)$")


def load_api_key() -> str:
    for path in ENV_PATHS:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    m = _KEY_RE.match(line.strip())
                    if m:
                        return m.group(1).strip().strip('"').strip("'")
        except OSError:
            continue
    sys.exit("API_SERVER_KEY not found in " + " or ".join(ENV_PATHS))


API_KEY = load_api_key()


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "hermes-webui-proxy/1.0"

    def log_message(self, format, *args):
        sys.stderr.write("[webui-proxy] " + (format % args) + "\n")
        sys.stderr.flush()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _read_body(self) -> bytes:
        cl = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(cl) if cl else b""

    def _forward(self, method: str, body: bytes):
        try:
            conn = http.client.HTTPConnection(UPSTREAM, UPSTREAM_PORT, timeout=120)
            hdrs = {"Content-Type": "application/json"}
            hdrs["Authorization"] = f"Bearer {API_KEY}"
            conn.request(method, self.path, body=body if body else None, headers=hdrs)
            resp = conn.getresponse()

            ct = resp.getheader("Content-Type") or ""
            sse = "text/event-stream" in ct

            self.send_response(resp.status)
            for h in ("Content-Type", "Cache-Control", "X-Hermes-Session-Id", "X-Hermes-Session-Key"):
                v = resp.getheader(h)
                if v:
                    self.send_header(h, v)
            self._cors()

            if sse:
                self.send_header("X-Accel-Buffering", "no")
                self.send_header("Cache-Control", "no-cache")
                # No Content-Length for a stream. Close the connection at the
                # end so clients that don't do chunked parsing (http.client,
                # fetch) can detect stream end unambiguously.
                self.send_header("Connection", "close")
                self.close_connection = True
                self.end_headers()
                # Read line-by-line: SSE is line-framed, so this returns each
                # line the instant it arrives instead of blocking on a fill.
                try:
                    for line in resp:
                        self.wfile.write(line)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                except Exception as e:
                    self.log_message("SSE read error: %s %s", type(e).__name__, e)
            else:
                data = resp.read()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if data:
                    self.wfile.write(data)
            conn.close()
        except Exception as exc:
            self.log_message("ERROR %s %s: %s", method, self.path, exc)
            try:
                payload = json.dumps({"error": f"proxy upstream error: {exc}"}).encode()
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception:
                pass

    def do_GET(self):
        self._forward("GET", b"")

    def do_POST(self):
        self._forward("POST", self._read_body())

    def do_DELETE(self):
        self._forward("DELETE", b"")

    def do_PATCH(self):
        self._forward("PATCH", self._read_body())


def main():
    srv = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    sys.stderr.write(
        f"[webui-proxy] listening on {LISTEN_HOST}:{LISTEN_PORT} -> {UPSTREAM}:{UPSTREAM_PORT}\n"
    )
    sys.stderr.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

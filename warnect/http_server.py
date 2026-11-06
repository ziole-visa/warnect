"""Optional HTTP bridge for warnect.

This exposes a small local HTTP API so non-Python services can send messages
and receive incoming messages through a webhook.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

from .client import BaileysClient
from .exceptions import BridgeError, BridgeTimeout


class WarnectHTTPServer:
    def __init__(
        self,
        client: BaileysClient,
        host: str = "127.0.0.1",
        port: int = 8080,
        token: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> None:
        self.client = client
        self.host = host
        self.port = port
        self.token = token
        self.webhook_url = webhook_url

        self._connected = False
        self._last_qr: Optional[str] = None
        self._webhook_queue: "queue.Queue[Optional[dict]]" = queue.Queue()
        self._webhook_thread = threading.Thread(target=self._webhook_worker, daemon=True)
        self._httpd: Optional[ThreadingHTTPServer] = None

        client.on("connection", self._on_connection)
        client.on("qr", self._on_qr)
        client.on("message", self._on_message)

    def _on_connection(self, data: Any) -> None:
        status = (data or {}).get("status") if isinstance(data, dict) else None
        self._connected = status == "open"

    def _on_qr(self, qr: Any) -> None:
        self._last_qr = str(qr) if qr is not None else None

    def _on_message(self, data: Any) -> None:
        if self.webhook_url:
            self._webhook_queue.put(data)

    def _webhook_worker(self) -> None:
        while True:
            data = self._webhook_queue.get()
            if data is None:
                break
            try:
                body = json.dumps({"event": "message", "data": data}).encode("utf-8")
                req = urllib.request.Request(
                    str(self.webhook_url),
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10):
                    pass
            except Exception as exc:  # pragma: no cover - network dependent
                print(f"[warnect-http] webhook delivery failed: {exc}")

    def start(self) -> None:
        self.client.start()
        self._webhook_thread.start()

        handler = self._make_handler()
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        print(f"[warnect-http] listening on http://{self.host}:{self.port}")
        self._httpd.serve_forever()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        self._webhook_queue.put(None)
        self.client.stop()

    def _make_handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status: int, payload: dict) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _auth_ok(self) -> bool:
                if not server.token:
                    return True
                header = self.headers.get("Authorization", "")
                return header == f"Bearer {server.token}"

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/health":
                    self._send(200, {"ok": True, "connected": server._connected})
                elif self.path == "/qr":
                    self._send(200, {"ok": True, "qr": server._last_qr})
                else:
                    self._send(404, {"ok": False, "error": "not found"})

            def do_POST(self) -> None:  # noqa: N802
                if not self._auth_ok():
                    self._send(401, {"ok": False, "error": "unauthorized"})
                    return
                if self.path != "/send":
                    self._send(404, {"ok": False, "error": "not found"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(length) if length > 0 else b"{}"
                    payload = json.loads(raw.decode("utf-8") or "{}")
                except Exception:
                    self._send(400, {"ok": False, "error": "invalid json"})
                    return
                jid = payload.get("to") or payload.get("jid")
                text = payload.get("text")
                if not jid or not text:
                    self._send(400, {"ok": False, "error": "fields 'to' and 'text' are required"})
                    return
                try:
                    result = server.client.send_text(jid, text)
                    self._send(200, {"ok": True, "result": result})
                except (BridgeError, BridgeTimeout) as exc:
                    self._send(502, {"ok": False, "error": str(exc)})

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

        return Handler

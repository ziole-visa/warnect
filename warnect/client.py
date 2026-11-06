import base64
import json
import os
import queue
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .exceptions import BridgeCrashed, BridgeError, BridgeTimeout


class BaileysClient:
    """Production-oriented Python client for arsya-baileys-open.

    The client spawns a local Node.js bridge over stdio. No network port is
    opened, so the bridge is not reachable from outside the host.
    """

    def __init__(
        self,
        auth_dir: str = "auth",
        bridge_script: Optional[str] = None,
        node_bin: str = "node",
        log_level: str = "info",
        request_timeout: float = 30.0,
        min_send_interval: float = 0.5,
        auto_install: bool = True,
    ) -> None:
        if bridge_script is None:
            bridge_script = str(Path(__file__).resolve().parent / "bridge" / "server.js")
        self.auth_dir = str(auth_dir)
        self.bridge_script = str(bridge_script)
        self.node_bin = node_bin
        self.log_level = log_level
        self.request_timeout = request_timeout
        self.min_send_interval = min_send_interval
        self.auto_install = auto_install

        self.proc: Optional[subprocess.Popen] = None
        self._closed = False

        self._handlers: Dict[str, List[Callable]] = {}
        self._pending: Dict[str, dict] = {}
        self._pending_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._last_sent_at = 0.0
        self._last_sent_per_chat: Dict[str, float] = {}

        self._dispatch_queue: "queue.Queue[tuple]" = queue.Queue()
        self._dispatcher_thread: Optional[threading.Thread] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ events

    def on(self, event: str, callback: Callable) -> None:
        """Register an event handler. Events: qr, connection, ready, message, error, reconnect."""
        self._handlers.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable) -> None:
        handlers = self._handlers.get(event)
        if handlers and callback in handlers:
            handlers.remove(callback)

    def _emit(self, event: str, data: Any = None) -> None:
        for cb in list(self._handlers.get(event, [])):
            try:
                cb(data)
            except Exception as exc:  # pragma: no cover - user callback
                print(f"[warnect] callback error on {event}: {exc}")

    def _dispatch_loop(self) -> None:
        while not self._closed:
            try:
                event, data = self._dispatch_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self._emit(event, data)

    # ------------------------------------------------------------------ process

    def _bridge_dir(self) -> Path:
        return Path(self.bridge_script).resolve().parent

    def _ensure_node_deps(self) -> None:
        bridge_dir = self._bridge_dir()
        # Custom bridge scripts (e.g. test doubles) may not use npm at all.
        if not (bridge_dir / "package.json").exists():
            return
        marker = bridge_dir / "node_modules" / "arsya-baileys-open" / "package.json"
        if marker.exists():
            return
        if not self.auto_install:
            raise BridgeCrashed(
                "Node dependencies are missing. Run `npm install` in " + str(bridge_dir)
            )
        print("[warnect] Installing Node dependencies (first run)...")
        lockfile = bridge_dir / "package-lock.json"
        cmd = ["npm", "ci", "--omit=dev", "--no-audit", "--no-fund"]
        if not lockfile.exists():
            cmd = ["npm", "install", "--omit=dev", "--no-audit", "--no-fund"]
        try:
            subprocess.run(cmd, cwd=str(bridge_dir), check=True, timeout=300)
        except FileNotFoundError as exc:
            raise BridgeCrashed("Node.js/npm is required but was not found in PATH") from exc
        except subprocess.CalledProcessError as exc:
            raise BridgeCrashed(f"npm install failed with exit code {exc.returncode}") from exc

    def _sanitized_env(self) -> dict:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "NODE_ENV": "production",
            "WARNECT_LOG_LEVEL": self.log_level,
            "NO_COLOR": "1",
        }
        for key in ("SystemRoot", "TEMP", "TMP"):
            if key in os.environ:
                env[key] = os.environ[key]
        return env

    def start_bridge(self) -> None:
        if self.proc is not None:
            return
        self._ensure_node_deps()
        self._closed = False
        self.proc = subprocess.Popen(
            [self.node_bin, self.bridge_script, self.auth_dir, self.log_level],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=self._sanitized_env(),
        )
        self._dispatcher_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._dispatcher_thread.start()
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()
        self._stderr_thread = threading.Thread(target=self._stderr_loop, daemon=True)
        self._stderr_thread.start()

    def _stderr_loop(self) -> None:
        assert self.proc and self.proc.stderr
        for line in self.proc.stderr:
            line = line.rstrip()
            if line:
                print(line)

    def _read_loop(self) -> None:
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = obj.get("type")
            if kind == "event":
                self._dispatch_queue.put((obj.get("event"), obj.get("data")))
            elif kind == "response":
                req_id = str(obj.get("id"))
                with self._pending_lock:
                    pending = self._pending.pop(req_id, None)
                if pending:
                    pending["response"] = obj
                    pending["event"].set()
        # process ended
        with self._pending_lock:
            pending = list(self._pending.values())
            self._pending.clear()
        for item in pending:
            item["error"] = BridgeCrashed("bridge process exited")
            item["event"].set()
        if not self._closed:
            self._dispatch_queue.put(("error", {"code": "bridge_exited", "message": "bridge process exited"}))

    # ------------------------------------------------------------------ rpc

    def _send_raw(self, payload: dict) -> None:
        if not self.proc or not self.proc.stdin:
            raise BridgeCrashed("bridge is not running")
        data = json.dumps(payload) + "\n"
        with self._write_lock:
            self.proc.stdin.write(data)
            self.proc.stdin.flush()

    def request(self, cmd: str, timeout: Optional[float] = None, **params: Any) -> Any:
        """Send a request to the bridge and wait for the response."""
        if self.proc is None:
            self.start_bridge()
        req_id = uuid.uuid4().hex
        item: dict = {"event": threading.Event(), "response": None, "error": None}
        with self._pending_lock:
            self._pending[req_id] = item
        try:
            self._send_raw({"type": "request", "id": req_id, "cmd": cmd, **params})
        except Exception:
            with self._pending_lock:
                self._pending.pop(req_id, None)
            raise
        if not item["event"].wait(timeout or self.request_timeout):
            with self._pending_lock:
                self._pending.pop(req_id, None)
            raise BridgeTimeout(f"timeout waiting for response to {cmd}")
        if item["error"]:
            raise item["error"]
        response = item["response"] or {}
        if response.get("ok"):
            return response.get("data")
        error = response.get("error") or {}
        raise BridgeError(error.get("code", "unknown"), error.get("message", "unknown error"))

    # ------------------------------------------------------------------ api

    def start(self, wait: bool = True, timeout: Optional[float] = None) -> Any:
        self.start_bridge()
        if not wait:
            self._send_raw({"type": "request", "id": uuid.uuid4().hex, "cmd": "start"})
            return None
        return self.request("start", timeout=timeout)

    def ping(self) -> Any:
        return self.request("ping")

    def send_text(self, jid: str, text: str) -> Any:
        self._rate_limit(jid)
        return self.request("send_text", jid=jid, text=text)

    def send_image(
        self,
        jid: str,
        url: Optional[str] = None,
        path: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Any:
        if not url and not path:
            raise ValueError("send_image requires url or path")
        self._rate_limit(jid)
        payload: Dict[str, Any] = {"jid": jid}
        if url:
            payload["url"] = url
        if path:
            payload["path"] = path
        if caption:
            payload["caption"] = caption
        return self.request("send_image", **payload)

    def send_document(
        self,
        jid: str,
        path: str,
        filename: Optional[str] = None,
        mimetype: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Any:
        self._rate_limit(jid)
        payload: Dict[str, Any] = {"jid": jid, "path": path}
        if filename:
            payload["filename"] = filename
        if mimetype:
            payload["mimetype"] = mimetype
        if caption:
            payload["caption"] = caption
        return self.request("send_document", **payload)

    def request_pairing_code(self, number: str, custom_code: Optional[str] = None) -> Any:
        payload: Dict[str, Any] = {"number": number}
        if custom_code:
            payload["customCode"] = custom_code
        return self.request("request_pairing_code", **payload)

    def send_presence(self, jid: str, presence: str) -> Any:
        return self.request("send_presence", jid=jid, presence=presence)

    def send_read(self, jid: str, message_id: str, participant: Optional[str] = None) -> Any:
        payload: Dict[str, Any] = {"jid": jid, "messageId": message_id}
        if participant:
            payload["participant"] = participant
        return self.request("send_read", **payload)

    def download_media(self, message_id: str) -> bytes:
        data = self.request("download_media", messageId=message_id)
        raw = data.get("base64") if isinstance(data, dict) else None
        if not raw:
            raise BridgeError("no_media", "media download returned empty payload")
        return base64.b64decode(raw)

    def send_reaction(self, jid: str, emoji: str, message_id: str, from_me: bool = False, participant: Optional[str] = None) -> Any:
        payload: Dict[str, Any] = {"jid": jid, "emoji": emoji, "messageId": message_id, "fromMe": from_me}
        if participant:
            payload["participant"] = participant
        return self.request("send_reaction", **payload)

    def reply_message(self, jid: str, text: str, quoted_id: str) -> Any:
        validate_text = text
        self._rate_limit(jid)
        return self.request("reply_message", jid=jid, text=text, quotedId=quoted_id)

    def get_groups(self, limit: int = 100) -> Any:
        return self.request("get_groups", limit=limit)

    def get_profile_picture(self, jid: str, type: str = "image") -> Any:
        return self.request("get_profile_picture", jid=jid, pictureType=type)

    def is_on_whatsapp(self, number: str) -> Any:
        return self.request("is_on_whatsapp", number=number)

    def logout(self) -> Any:
        return self.request("logout")

    def _rate_limit(self, jid: Optional[str] = None) -> None:
        if self.min_send_interval <= 0:
            return
        with self._send_lock:
            now = time.monotonic()
            last = self._last_sent_per_chat.get(jid or "", self._last_sent_at)
            wait = self.min_send_interval - (now - last)
            if wait > 0:
                time.sleep(wait)
            now = time.monotonic()
            self._last_sent_at = now
            if jid:
                self._last_sent_per_chat[jid] = now

    def stop(self) -> None:
        self._closed = True
        if self.proc is None:
            return
        try:
            self._send_raw({"type": "request", "id": uuid.uuid4().hex, "cmd": "stop"})
        except Exception:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None

    def __enter__(self) -> "BaileysClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

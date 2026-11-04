import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, Dict, List


class BaileysClient:
    """Minimal Python client that talks to the Node bridge (arsya-baileys-open)."""

    def __init__(self, auth_dir: str = "auth", bridge_script: str | None = None):
        if bridge_script is None:
            bridge_script = str(Path(__file__).resolve().parent / "bridge" / "server.js")
        self.auth_dir = auth_dir
        self.bridge_script = bridge_script
        self.proc = None
        self._handlers: Dict[str, List[Callable]] = {}
        self._reader_thread = None

    def on(self, event: str, callback: Callable) -> None:
        self._handlers.setdefault(event, []).append(callback)

    def _emit(self, event: str, data=None) -> None:
        for cb in self._handlers.get(event, []):
            try:
                cb(data)
            except Exception as exc:  # pragma: no cover - user callback
                print(f"[arsya-baileys] callback error: {exc}")

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
            if "event" in obj:
                self._emit(obj["event"], obj.get("data"))
            elif "error" in obj:
                self._emit("error", obj["error"])

    def _send(self, obj: dict) -> None:
        if not self.proc or not self.proc.stdin:
            raise RuntimeError("bridge is not running")
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _ensure_node_deps(self) -> None:
        bridge_dir = Path(self.bridge_script).resolve().parent
        marker = bridge_dir / "node_modules" / "arsya-baileys-open" / "package.json"
        if marker.exists():
            return
        print("[arsya-baileys] Installing Node dependencies (first run)...")
        try:
            subprocess.run(
                ["npm", "install", "--no-audit", "--no-fund"],
                cwd=str(bridge_dir),
                check=True,
                timeout=300,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("Node.js/npm is required but was not found in PATH") from exc

    def start(self) -> None:
        if self.proc is not None:
            return
        self._ensure_node_deps()
        self.proc = subprocess.Popen(
            ["node", self.bridge_script, self.auth_dir],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()
        self._send({"cmd": "start"})

    def send_text(self, jid: str, text: str) -> None:
        self._send({"cmd": "sendText", "jid": jid, "text": text})

    def stop(self) -> None:
        try:
            self._send({"cmd": "stop"})
        except Exception:
            pass
        if self.proc:
            self.proc.terminate()
            self.proc = None

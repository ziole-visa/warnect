import threading
from typing import Any, Callable, Dict, Optional

from .client import BaileysClient


class SessionManager:
    """Manage multiple WhatsApp sessions in one process."""

    def __init__(self) -> None:
        self._sessions: Dict[str, BaileysClient] = {}
        self._lock = threading.RLock()

    def add_session(self, session_id: str, auth_dir: str, **kwargs: Any) -> BaileysClient:
        with self._lock:
            if session_id in self._sessions:
                raise ValueError(f"session '{session_id}' already exists")
            client = BaileysClient(auth_dir=auth_dir, **kwargs)
            # wrap handlers so events carry session_id
            original_on = client.on

            def on_with_session(event: str, callback: Callable) -> None:
                def wrapped(data: Any) -> None:
                    if isinstance(data, dict):
                        data = {**data, "_session": session_id}
                    else:
                        data = {"_session": session_id, "data": data}
                    callback(data)

                original_on(event, wrapped)

            client.on = on_with_session  # type: ignore
            self._sessions[session_id] = client
            return client

    def get(self, session_id: str) -> BaileysClient:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(session_id)
            return self._sessions[session_id]

    def remove_session(self, session_id: str, stop: bool = True) -> None:
        with self._lock:
            client = self._sessions.pop(session_id, None)
        if client and stop:
            client.stop()

    def start_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.items())
        for sid, client in sessions:
            try:
                client.start()
            except Exception as exc:
                print(f"[session-manager] failed to start {sid}: {exc}")

    def stop_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.items())
        for _sid, client in sessions:
            try:
                client.stop()
            except Exception:
                pass

    def list_sessions(self) -> list[str]:
        with self._lock:
            return list(self._sessions.keys())

    def send_text(self, session_id: str, jid: str, text: str) -> Any:
        return self.get(session_id).send_text(jid, text)

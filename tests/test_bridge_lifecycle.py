import threading
import time
from pathlib import Path

from warnect import BaileysClient

FAKE_EXIT = str(Path(__file__).resolve().parent / "fake_exit_bridge.js")


def test_bridge_exit_is_detected():
    events = []
    client = BaileysClient(
        auth_dir="/tmp/opencode/lifecycle-auth",
        bridge_script=FAKE_EXIT,
        auto_install=False,
        auto_restart=False,
        min_send_interval=0.0,
        request_timeout=2.0,
    )
    client.on("error", lambda data: events.append(data))
    client.start()
    time.sleep(1.0)
    health = client.health()
    assert health["bridge_alive"] is False
    assert any(e.get("code") == "bridge_exited" for e in events)
    client.stop()

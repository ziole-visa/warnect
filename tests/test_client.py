import threading
import time
from pathlib import Path

import pytest

from warnect import BaileysClient, BridgeError, BridgeTimeout

FAKE = str(Path(__file__).resolve().parent / "fake_bridge.js")


@pytest.fixture()
def client(tmp_path):
    c = BaileysClient(
        auth_dir=str(tmp_path / "auth"),
        bridge_script=FAKE,
        auto_install=False,
        min_send_interval=0.0,
    )
    yield c
    c.stop()


def test_start_and_ping(client):
    data = client.start()
    assert data["status"] == "starting"
    assert client.ping()["pong"] is True


def test_send_text_returns_response(client):
    client.start()
    assert client.send_text("123@s.whatsapp.net", "halo")["sent"] is True


def test_event_delivery(client):
    got = []
    event = threading.Event()

    def on_message(msg):
        got.append(msg)
        event.set()

    client.on("message", on_message)
    client.start()
    client.send_text("123@s.whatsapp.net", "hai")
    assert event.wait(2.0)
    assert got[0]["text"] == "hai"


def test_unknown_command_raises(client):
    client.start()
    with pytest.raises(BridgeError) as exc:
        client.request("nope")
    assert exc.value.code == "unknown_command"


def test_timeout(client):
    client.start()
    with pytest.raises(BridgeTimeout):
        client.request("slow", timeout=0.2)


def test_stop_then_start_again(tmp_path):
    c = BaileysClient(
        auth_dir=str(tmp_path / "auth"),
        bridge_script=FAKE,
        auto_install=False,
        min_send_interval=0.0,
    )
    c.start()
    assert c.ping()["pong"] is True
    c.stop()
    c.start()
    assert c.ping()["pong"] is True
    c.stop()

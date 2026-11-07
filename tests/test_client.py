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


def test_extra_commands(client):
    client.start()
    assert client.request_pairing_code("6281234567890")["code"] == "ABCD-1234"
    assert client.send_presence("123@s.whatsapp.net", "composing")["presence"] == "composing"
    assert client.send_read("123@s.whatsapp.net", "MSG1")["read"] is True
    assert client.download_media("MSG1") == b"media-bytes"
    assert client.get_profile_picture("123@s.whatsapp.net")["url"] == "https://example.com/p.jpg"
    assert client.get_groups()["total"] == 0
    assert client.is_on_whatsapp("6281234567890")["exists"] is True
    assert client.list_methods() == ["sendMessage", "groupCreate"]
    assert client.invoke("echo", 1, 2)["result"]["echoed"] == [1, 2]
    # dynamic caller converts snake_case to camelCase
    assert client.group_create("Grup", ["123@s.whatsapp.net"])["group"]["id"] == "123@g.us"
    assert client.send_reaction("123@s.whatsapp.net", "👍", "MSG1")["reacted"] is True
    assert client.reply_message("123@s.whatsapp.net", "balas", "MSG1")["quoted"] is True
    assert client.group_create("Grup", ["123@s.whatsapp.net"])["group"]["id"] == "123@g.us"
    assert client.group_add_participants("123@g.us", ["456@s.whatsapp.net"])["result"]


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

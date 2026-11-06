import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from warnect import BaileysClient
from warnect.http_server import WarnectHTTPServer

FAKE = str(Path(__file__).resolve().parent / "fake_bridge.js")


def test_http_health_and_send(tmp_path):
    client = BaileysClient(
        auth_dir=str(tmp_path / "auth"),
        bridge_script=FAKE,
        auto_install=False,
        min_send_interval=0.0,
    )
    server = WarnectHTTPServer(client, host="127.0.0.1", port=0, token="secret")
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    # wait for server to bind
    for _ in range(50):
        if server._httpd is not None:
            break
        time.sleep(0.1)
    httpd = server._httpd
    assert httpd is not None
    port = httpd.server_port

    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health") as resp:
        data = json.loads(resp.read())
    assert data["ok"] is True

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/send",
        data=json.dumps({"to": "123@s.whatsapp.net", "text": "hi"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
        raise AssertionError("expected 401 without token")
    except urllib.error.HTTPError as exc:
        assert exc.code == 401

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/send",
        data=json.dumps({"to": "123@s.whatsapp.net", "text": "hi"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer secret"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    assert data["ok"] is True

    server.stop()
    thread.join(timeout=5)

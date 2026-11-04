import asyncio
from pathlib import Path

from warnect import AsyncBaileysClient

FAKE = str(Path(__file__).resolve().parent / "fake_bridge.js")


def make_client(tmp_path):
    return AsyncBaileysClient(
        auth_dir=str(tmp_path / "auth"),
        bridge_script=FAKE,
        auto_install=False,
        min_send_interval=0.0,
    )


def test_async_basic(tmp_path):
    async def main():
        client = make_client(tmp_path)
        assert (await client.start())["status"] == "starting"
        assert (await client.ping())["pong"] is True
        assert (await client.send_text("123@s.whatsapp.net", "halo"))["sent"] is True
        assert await client.download_media("MSG1") == b"media-bytes"
        await client.stop()

    asyncio.run(main())


def test_async_callback(tmp_path):
    async def main():
        client = make_client(tmp_path)
        got = []
        done = asyncio.Event()

        async def on_message(msg):
            got.append(msg)
            done.set()

        client.on("message", on_message)
        await client.start()
        await client.send_text("123@s.whatsapp.net", "ping")
        await asyncio.wait_for(done.wait(), timeout=2.0)
        assert got[0]["text"] == "ping"
        await client.stop()

    asyncio.run(main())

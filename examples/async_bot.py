"""Async warnect bot example.

Run:  python examples/async_bot.py
"""

import asyncio
import logging

from warnect import AsyncBaileysClient, BridgeError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("warnect-async")


async def main() -> None:
    client = AsyncBaileysClient(auth_dir="auth", min_send_interval=0.5)

    async def on_qr(qr: str) -> None:
        log.info("QR received:")
        print(qr)

    async def on_ready(data) -> None:
        log.info("Connected: %s", data.get("user"))

    async def on_message(msg) -> None:
        text = (msg.get("text") or "").lower()
        chat = msg.get("chat")
        if not chat:
            return
        if text == "ping":
            try:
                await client.send_presence(chat, "composing")
                await client.send_text(chat, "pong")
            except BridgeError as exc:
                log.warning("reply failed: %s", exc)

    client.on("qr", on_qr)
    client.on("ready", on_ready)
    client.on("message", on_message)

    await client.start()
    log.info("Bot running. Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

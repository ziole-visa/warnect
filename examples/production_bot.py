"""Production-style warnect bot example.

Run:  python examples/production_bot.py
"""

import logging
import signal
import sys
import time

from warnect import BaileysClient, BridgeError, BridgeTimeout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("warnect-bot")

client = BaileysClient(
    auth_dir="auth",
    min_send_interval=0.5,
    request_timeout=30.0,
)
running = True


def shutdown(*_args):
    global running
    running = False


def on_qr(qr: str) -> None:
    log.info("QR received. Scan it in WhatsApp:")
    print(qr)


def on_ready(data) -> None:
    log.info("Connected: %s", data.get("user"))


def on_connection(data) -> None:
    log.info("Connection: %s", data)


def on_reconnect(data) -> None:
    log.info("Reconnect: %s", data)


def on_error(data) -> None:
    log.error("Bridge error: %s", data)


def on_message(msg) -> None:
    text = msg.get("text")
    chat = msg.get("chat")
    if not text or not chat:
        return
    log.info("Message from %s: %s", msg.get("pushName") or chat, text)
    if text.lower() in ("ping", ".ping"):
        try:
            client.send_text(chat, "pong")
        except (BridgeError, BridgeTimeout) as exc:
            log.warning("Failed to reply: %s", exc)


client.on("qr", on_qr)
client.on("ready", on_ready)
client.on("connection", on_connection)
client.on("reconnect", on_reconnect)
client.on("error", on_error)
client.on("message", on_message)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

client.start()
log.info("Bot running. Press Ctrl+C to stop.")

try:
    while running:
        time.sleep(1)
finally:
    client.stop()
    log.info("Stopped.")
    sys.exit(0)

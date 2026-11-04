# warnect (Python)

Python interface to **arsya-baileys-open** (WhatsApp Web multi-device) through a
small Node.js bridge. It keeps the heavy WhatsApp protocol implementation in
Node and exposes an easy Python API.

## Requirements

- Python >= 3.10
- Node.js >= 20
- npm

Node dependencies are installed automatically on first run. To install manually:

```bash
cd warnect/bridge
npm install
```

## Python install

```bash
pip install -e .
```

## Quick start

```python
from warnect import BaileysClient

client = BaileysClient(auth_dir="auth")

def on_qr(qr):
    print("QR:", qr)

def on_message(msg):
    print("Pesan:", msg.get("text"))
    if msg.get("text") == "ping":
        client.send_text(msg["key"]["remoteJid"], "pong")

client.on("qr", on_qr)
client.on("message", on_message)
client.start()

input("Press Enter to stop...\n")
client.stop()
```

## Notes

- This is an early alpha. Only text send/receive and QR login are supported.
- Media, groups, and advanced features will be added incrementally.
- Bridge runs `arsya-baileys-open` under the hood.

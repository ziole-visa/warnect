# warnect (Python)

Python client for WhatsApp Web multi-device, powered by **arsya-baileys-open**
through a local Node.js bridge.

- No browser, no Selenium.
- Bridge talks over stdio only — no TCP port is exposed.
- Session directory is created with `0700` permissions.
- Inputs validated, sends rate-limited, auto-reconnect with backoff.

## Requirements

- Python >= 3.10
- Node.js >= 20 and npm

## Install

```bash
pip install warnect
```

Node dependencies are installed automatically on first run. To install manually:

```bash
python -c "import warnect, pathlib; print(pathlib.Path(warnect.__file__).parent / 'bridge')"
cd <that-folder> && npm ci --omit=dev
```

## Quick start

```python
from warnect import BaileysClient

client = BaileysClient(auth_dir="auth")

def on_qr(qr):
    print("Scan QR:", qr)

def on_ready(data):
    print("Connected as:", data.get("user"))

def on_message(msg):
    print("Pesan:", msg.get("text"))
    if msg.get("text") == "ping":
        client.send_text(msg["chat"], "pong")

client.on("qr", on_qr)
client.on("ready", on_ready)
client.on("message", on_message)
client.start()

input("Bot jalan. Tekan Enter untuk stop...\n")
client.stop()
```

## Events

| Event        | Data                                          |
| ------------ | --------------------------------------------- |
| `qr`         | QR string (render/save it yourself)           |
| `connection` | `{ "status": "connecting" \| "open" \| "close" }` |
| `ready`      | `{ "user": {...} }`                            |
| `message`    | normalized message object                      |
| `error`      | `{ "code": "...", "message": "..." }`          |
| `reconnect`  | `{ "attempt": n, "delay": ms }`                |

## Message object

```python
{
  "id": "...",
  "chat": "123@s.whatsapp.net",
  "sender": "...",
  "fromMe": False,
  "isGroup": False,
  "type": "conversation",
  "text": "halo",
  "pushName": "Budi",
  "timestamp": 1730000000,
  "hasMedia": False,
  "fileName": None,
  "mimetype": None,
}
```

## API

| Method | Description |
| ------ | ----------- |
| `start(wait=True)` | Start bridge and socket |
| `ping()` | Health check |
| `send_text(jid, text)` | Send text |
| `send_image(jid, url=..., path=..., caption=...)` | Send image |
| `send_document(jid, path, filename=..., mimetype=..., caption=...)` | Send document |
| `send_reaction(jid, emoji, message_id)` | React to message |
| `reply_message(jid, text, quoted_id)` | Reply to message |
| `request_pairing_code(number)` | Pairing code login |
| `send_presence(jid, presence)` | typing/paused/available |
| `send_read(jid, message_id)` | Mark message as read |
| `download_media(message_id)` | Download incoming media (bytes) |
| `get_groups(limit=100)` | List groups |
| `get_profile_picture(jid, type="image")` | Profile picture URL |
| `is_on_whatsapp(number)` | Check number |
| `group_create(subject, participants)` | Create group |
| `group_add_participants(jid, participants)` | Add members |
| `group_remove_participants(jid, participants)` | Remove members |
| `group_promote(jid, participants)` | Promote |
| `group_demote(jid, participants)` | Demote |
| `group_leave(jid)` | Leave group |
| `group_invite_code(jid)` | Get invite code |
| `logout()` | Log out session |
| `stop()` | Stop bridge |

## Async API

```python
import asyncio
from warnect import AsyncBaileysClient

async def main():
    client = AsyncBaileysClient(auth_dir="auth")

    async def on_message(msg):
        if msg.get("text") == "ping":
            await client.send_text(msg["chat"], "pong")

    client.on("message", on_message)
    await client.start()
    await asyncio.sleep(3600)
    await client.stop()

asyncio.run(main())
```

## CLI

```bash
warnect qr --auth-dir auth          # tampilkan QR
warnect pair --auth-dir auth --number 6281234567890
warnect send --auth-dir auth --to 62812xxx@s.whatsapp.net --text "hai"
warnect run --auth-dir auth         # jalankan + print event
```

## Media download

```python
def on_message(msg):
    if msg.get("hasMedia"):
        data = client.download_media(msg["id"])
        open("download.bin", "wb").write(data)
```

## Errors

```python
from warnect import BridgeError, BridgeTimeout, BridgeCrashed

try:
    client.send_text("123@s.whatsapp.net", "hi")
except BridgeTimeout:
    ...
except BridgeError as exc:
    print(exc.code, exc.message)
```

## Security notes

- The bridge uses local stdio; it does not open a network port.
- Node dependencies are pinned in `package-lock.json` and installed with `npm ci`.
- Keep `auth_dir` private; it contains WhatsApp session credentials.
- Use `min_send_interval` (default `0.5`s) to avoid spamming.

## Multi-session

```python
from warnect import SessionManager

manager = SessionManager()
manager.add_session("bot1", "auth-bot1")
manager.add_session("bot2", "auth-bot2")
manager.start_all()

manager.send_text("bot1", "123@s.whatsapp.net", "from bot1")
manager.stop_all()
```

## Docker

```bash
docker compose up --build
```

The `auth/` directory is mounted as a volume so sessions persist.

## License

MIT

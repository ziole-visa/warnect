# Changelog

## 0.8.0

- Typed event payloads (MessageEvent, ConnectionEvent, QREvent) with dict + attribute access.
- Connection health API (`client.health()`, `client.connected`).
- Bridge auto-restart with exponential backoff.
- Structured logging via Python logging.
- Config manager: env vars, TOML, dataclass.
- 15 Python tests + 9 Node tests.

## 0.7.0

- Generic `invoke(method, *args)` and `list_methods()` for full Baileys socket parity.
- Dynamic snake_case -> camelCase method caller.
- Forwarding of common Baileys events (messages.update, presence, groups, chats, contacts, calls, labels).
- Safe serializer for Baileys return values (Buffer, BigInt, Date).
- 11 Python tests + 9 Node tests.

## 0.6.0

- Multi-session manager (`SessionManager`) for running many accounts in one process.
- Group management APIs: create/update subject/description, add/remove/promote/demote, leave, invite code/revoke.
- Docker support (`Dockerfile`, `docker-compose.yml`).
- Webhook retry with exponential backoff.
- Per-chat rate limiting and send retry.
- 11 Python tests + 9 Node tests.

## 0.5.0

- New APIs: `send_reaction`, `reply_message`.
- HTTP API: `warnect serve` with bearer token, `/health`, `/qr`, `/send`.
- Webhook delivery for incoming messages with optional HMAC signature (`X-Warnect-Signature`).
- Per-chat rate limiting.
- Tests: 10 Python + 9 Node (HTTP server coverage).

## 0.4.0

- HTTP API mode: `warnect serve` (health, send, QR endpoints) with bearer token auth.
- Webhook delivery for incoming messages.
- 10 Python tests (HTTP server coverage).
- Node tests unchanged (9).

## 0.3.0

- `AsyncBaileysClient` (asyncio wrapper, coroutine event callbacks).
- Media download for incoming messages (`download_media`).
- Pairing code login (`request_pairing_code`).
- Presence and read receipts (`send_presence`, `send_read`).
- CLI: `warnect qr|pair|send|run`.
- Async bot example.
- More tests (async client, media, presence, read, profile picture).

## 0.2.0

Production hardening release.

- Structured request/response protocol with request IDs and timeouts.
- Separate event dispatcher thread so user callbacks never block the reader.
- Auto-reconnect with exponential backoff in the Node bridge.
- Input validation for JID, text, limits.
- Session directory permissions hardened to `0700`.
- Pinned Node dependencies (`arsya-baileys-open@1.0.9`) and `npm ci` install.
- New APIs: `send_image`, `send_document`, `get_groups`, `get_profile_picture`,
  `is_on_whatsapp`, `logout`, `ping`.
- Rate limiting for outgoing sends.
- Custom exceptions: `WarnectError`, `BridgeError`, `BridgeTimeout`, `BridgeCrashed`.
- Node bridge unit tests, Python tests, GitHub Actions CI.
- Docs: README production guide, SECURITY.md, CHANGELOG.md.

## 0.1.0

- Initial release: QR login, text send/receive, Node bridge.

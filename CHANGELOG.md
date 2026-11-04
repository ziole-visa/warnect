# Changelog

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

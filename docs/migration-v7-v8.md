# Migration Guide: v7 -> v8

## What changed

- Event payloads are now typed objects, but still behave like dictionaries.
- `BaileysClient` gained `health()`, `connected`, and auto-restart.
- Configuration can now be provided through `WarnectConfig`.
- Async client gained missing methods and working `off()`.
- HTTP API gained stricter authentication.

## Recommended changes

1. Replace manual config parsing with `WarnectConfig.from_env()` or `from_toml()`.
2. Use `client.health()` for diagnostics.
3. Use `await client.__aenter__()` / async context manager for async clients.
4. Protect HTTP API with a token when binding to non-loopback addresses.

## Breaking changes

None intended for the public v0.7 API. Deprecated behavior may emit warnings in future releases.

# Configuration

warnect supports Python dataclass configuration, environment variables, and TOML.

## Python

```python
from warnect import WarnectConfig, BaileysClient

config = WarnectConfig(auth_dir="auth", log_level="debug", min_send_interval=0.3)
client = BaileysClient(config=config)
```

## Environment variables

- `WARNECT_AUTH_DIR`
- `WARNECT_LOG_LEVEL`
- `WARNECT_MIN_SEND_INTERVAL`
- `WARNECT_REQUEST_TIMEOUT`
- `WARNECT_AUTO_INSTALL`
- `WARNECT_WEBHOOK_URL`
- `WARNECT_WEBHOOK_SECRET`
- `WARNECT_HTTP_HOST`
- `WARNECT_HTTP_PORT`
- `WARNECT_HTTP_TOKEN`

## TOML

```toml
[warnect]
auth_dir = "auth"
log_level = "info"
min_send_interval = 0.5
```

```python
config = WarnectConfig.from_toml("warnect.toml")
client = BaileysClient(config=config)
```

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class WarnectConfig:
    auth_dir: str = "auth"
    log_level: str = "info"
    min_send_interval: float = 0.5
    request_timeout: float = 30.0
    auto_install: bool = True
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    http_host: str = "127.0.0.1"
    http_port: int = 8080
    http_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> "WarnectConfig":
        return cls(
            auth_dir=os.getenv("WARNECT_AUTH_DIR", "auth"),
            log_level=os.getenv("WARNECT_LOG_LEVEL", "info"),
            min_send_interval=float(os.getenv("WARNECT_MIN_SEND_INTERVAL", "0.5")),
            request_timeout=float(os.getenv("WARNECT_REQUEST_TIMEOUT", "30.0")),
            auto_install=os.getenv("WARNECT_AUTO_INSTALL", "1") not in ("0", "false", "False"),
            webhook_url=os.getenv("WARNECT_WEBHOOK_URL"),
            webhook_secret=os.getenv("WARNECT_WEBHOOK_SECRET"),
            http_host=os.getenv("WARNECT_HTTP_HOST", "127.0.0.1"),
            http_port=int(os.getenv("WARNECT_HTTP_PORT", "8080")),
            http_token=os.getenv("WARNECT_HTTP_TOKEN"),
        )

    @classmethod
    def from_toml(cls, path: str | Path) -> "WarnectConfig":
        try:
            import tomllib
        except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
            import tomli as tomllib  # type: ignore
        with open(path, "rb") as f:
            data = tomllib.load(f)
        section = data.get("warnect", data)
        return cls(**{k: v for k, v in section.items() if k in cls.__dataclass_fields__})

    def to_client_kwargs(self) -> dict[str, Any]:
        return {
            "auth_dir": self.auth_dir,
            "log_level": self.log_level,
            "min_send_interval": self.min_send_interval,
            "request_timeout": self.request_timeout,
            "auto_install": self.auto_install,
        }

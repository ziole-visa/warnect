import os

from warnect.config import WarnectConfig


def test_from_env(monkeypatch):
    monkeypatch.setenv("WARNECT_LOG_LEVEL", "debug")
    monkeypatch.setenv("WARNECT_HTTP_PORT", "9090")
    cfg = WarnectConfig.from_env()
    assert cfg.log_level == "debug"
    assert cfg.http_port == 9090


def test_to_client_kwargs():
    cfg = WarnectConfig(auth_dir="auth", min_send_interval=0.2)
    kwargs = cfg.to_client_kwargs()
    assert kwargs["auth_dir"] == "auth"
    assert kwargs["min_send_interval"] == 0.2

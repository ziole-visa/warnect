"""warnect: Python interface to arsya-baileys-open via a local Node bridge."""

from .async_client import AsyncBaileysClient
from .client import BaileysClient
from .config import WarnectConfig
from .events import ConnectionEvent, Event, MessageEvent, QREvent, wrap_event
from .exceptions import BridgeCrashed, BridgeError, BridgeTimeout, WarnectError
from .multi import SessionManager

__all__ = [
    "BaileysClient",
    "AsyncBaileysClient",
    "SessionManager",
    "WarnectConfig",
    "Event",
    "MessageEvent",
    "ConnectionEvent",
    "QREvent",
    "wrap_event",
    "WarnectError",
    "BridgeError",
    "BridgeTimeout",
    "BridgeCrashed",
]
__version__ = "0.8.1"

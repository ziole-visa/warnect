"""warnect: Python interface to arsya-baileys-open via a local Node bridge."""

from .async_client import AsyncBaileysClient
from .client import BaileysClient
from .exceptions import BridgeCrashed, BridgeError, BridgeTimeout, WarnectError
from .multi import SessionManager

__all__ = [
    "BaileysClient",
    "AsyncBaileysClient",
    "SessionManager",
    "WarnectError",
    "BridgeError",
    "BridgeTimeout",
    "BridgeCrashed",
]
__version__ = "0.6.0"

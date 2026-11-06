"""warnect: Python interface to arsya-baileys-open via a local Node bridge."""

from .async_client import AsyncBaileysClient
from .client import BaileysClient
from .exceptions import BridgeCrashed, BridgeError, BridgeTimeout, WarnectError

__all__ = [
    "BaileysClient",
    "AsyncBaileysClient",
    "WarnectError",
    "BridgeError",
    "BridgeTimeout",
    "BridgeCrashed",
]
__version__ = "0.4.0"

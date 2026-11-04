"""warnect: Python interface to arsya-baileys-open via a local Node bridge."""

from .client import BaileysClient
from .exceptions import BridgeCrashed, BridgeError, BridgeTimeout, WarnectError

__all__ = [
    "BaileysClient",
    "WarnectError",
    "BridgeError",
    "BridgeTimeout",
    "BridgeCrashed",
]
__version__ = "0.2.0"

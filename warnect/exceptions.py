class WarnectError(Exception):
    """Base error for warnect."""


class BridgeError(WarnectError):
    """Bridge returned an error response."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class BridgeTimeout(WarnectError):
    """Timed out waiting for a bridge response."""


class BridgeCrashed(WarnectError):
    """Bridge process exited unexpectedly."""

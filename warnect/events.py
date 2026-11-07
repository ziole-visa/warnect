class Event(dict):
    """Dict-backed event payload with attribute access."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


class MessageEvent(Event):
    pass


class ConnectionEvent(Event):
    pass


class QREvent(Event):
    pass


def wrap_event(name: str, data):
    if not isinstance(data, dict):
        data = {"data": data}
    if name == "message":
        return MessageEvent(data)
    if name == "connection":
        return ConnectionEvent(data)
    if name == "qr":
        return QREvent(data)
    return Event(data)

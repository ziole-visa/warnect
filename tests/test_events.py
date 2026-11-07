from warnect.events import MessageEvent, wrap_event


def test_wrap_event_returns_typed_message():
    ev = wrap_event("message", {"text": "hi", "chat": "123@s.whatsapp.net"})
    assert isinstance(ev, MessageEvent)
    assert ev.text == "hi"
    assert ev["chat"] == "123@s.whatsapp.net"
    assert ev.get("text") == "hi"


def test_event_attribute_access():
    ev = wrap_event("connection", {"status": "open"})
    assert ev.status == "open"

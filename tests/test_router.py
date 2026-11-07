from warnect.client import BaileysClient
from warnect.router import CommandRouter, MessageContext


class FakeClient:
    def __init__(self):
        self.sent = []

    def send_text(self, jid, text):
        self.sent.append((jid, text))
        return {"sent": True}


def test_command_dispatch():
    client = FakeClient()
    router = CommandRouter(client, prefix=".")
    results = []

    @router.command("ping", aliases=["p"])
    def ping(ctx):
        results.append(ctx.text)
        ctx.reply_sync("pong")

    router.dispatch({"text": ".ping", "chat": "123@s.whatsapp.net"})
    assert results == [".ping"]
    assert client.sent == [("123@s.whatsapp.net", "pong")]


def test_middleware_can_stop():
    client = FakeClient()
    router = CommandRouter(client, prefix=".")
    called = {"handler": False}

    @router.middleware
    def block(ctx):
        return False

    @router.command("ping")
    def ping(ctx):
        called["handler"] = True

    router.dispatch({"text": ".ping", "chat": "123@s.whatsapp.net"})
    assert called["handler"] is False
    assert client.sent == []


def test_alias_dispatch():
    client = FakeClient()
    router = CommandRouter(client, prefix=".")

    @router.command("ping", aliases=["p"])
    def ping(ctx):
        ctx.reply_sync("pong")

    router.dispatch({"text": ".p", "chat": "123@s.whatsapp.net"})
    assert client.sent == [("123@s.whatsapp.net", "pong")]


def test_message_context_properties():
    client = FakeClient()
    ctx = MessageContext(client, {"text": "hi", "chat": "123@s.whatsapp.net", "isGroup": True})
    assert ctx.text == "hi"
    assert ctx.chat == "123@s.whatsapp.net"
    assert ctx.is_group is True

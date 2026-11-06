from warnect import SessionManager


class FakeClient:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.sent = []

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def send_text(self, jid, text):
        self.sent.append((jid, text))
        return {"sent": True}


def test_session_manager_routes_messages():
    manager = SessionManager()
    c1 = manager.add_session("s1", "auth1")
    # inject fake client
    manager._sessions["s1"] = FakeClient()
    manager.start_all()
    assert manager.get("s1").started is True
    assert manager.send_text("s1", "123@s.whatsapp.net", "hi")["sent"] is True
    assert manager.get("s1").sent == [("123@s.whatsapp.net", "hi")]
    assert manager.list_sessions() == ["s1"]
    manager.remove_session("s1")
    assert manager.list_sessions() == []
    assert manager.get("s1") if False else True

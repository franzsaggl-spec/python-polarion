from types import SimpleNamespace

import pytest

from polarion.v3.errors import AuthError, TransportError
from polarion.v3.transport.soap import SoapTransport


class DummyService:
    def __init__(self):
        self.calls = []

    def logIn(self, user, password):
        self.calls.append(("logIn", user, password))
        return True

    def logInWithToken(self, user, token):
        self.calls.append(("logInWithToken", user, token))
        return True

    def endSession(self):
        self.calls.append(("endSession",))
        return True

    def ping(self, **kwargs):
        self.calls.append(("ping", kwargs))
        return {"ok": True, "kwargs": kwargs}


def test_call_with_password_auth(monkeypatch):
    services = {}

    def fake_client(wsdl, transport):
        svc = DummyService()
        services[wsdl] = svc
        return SimpleNamespace(service=svc)

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)

    t = SoapTransport(url="https://polarion.example.com/polarion", username="u", password="p")
    out = t.call("Tracker", "ping", a=1)

    assert out["ok"] is True
    session_wsdl = "https://polarion.example.com/polarion/ws/services/Session?wsdl"
    tracker_wsdl = "https://polarion.example.com/polarion/ws/services/Tracker?wsdl"
    assert ("logIn", "u", "p") in services[session_wsdl].calls
    assert ("ping", {"a": 1}) in services[tracker_wsdl].calls


def test_call_with_token_auth(monkeypatch):
    services = {}

    def fake_client(wsdl, transport):
        svc = DummyService()
        services[wsdl] = svc
        return SimpleNamespace(service=svc)

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)

    t = SoapTransport(url="https://polarion.example.com/polarion", username="u", token="tok")
    t.call("Tracker", "ping")

    session_wsdl = "https://polarion.example.com/polarion/ws/services/Session?wsdl"
    assert ("logInWithToken", "u", "tok") in services[session_wsdl].calls


def test_method_not_found(monkeypatch):
    def fake_client(wsdl, transport):
        return SimpleNamespace(service=SimpleNamespace())

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)

    t = SoapTransport(url="https://x/polarion", username="u")
    with pytest.raises(TransportError):
        t.call("Tracker", "nope")


def test_auth_failure_raises_auth_error(monkeypatch):
    class BadSessionService(DummyService):
        def logIn(self, user, password):
            raise RuntimeError("bad creds")

    def fake_client(wsdl, transport):
        if wsdl.endswith("/Session?wsdl"):
            return SimpleNamespace(service=BadSessionService())
        return SimpleNamespace(service=DummyService())

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)

    t = SoapTransport(url="https://x/polarion", username="u", password="bad")
    with pytest.raises(AuthError):
        t.call("Tracker", "ping")

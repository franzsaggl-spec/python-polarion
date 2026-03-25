from types import SimpleNamespace

import pytest
import requests

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
            raise requests.RequestException("bad creds")

    def fake_client(wsdl, transport):
        if wsdl.endswith("/Session?wsdl"):
            return SimpleNamespace(service=BadSessionService())
        return SimpleNamespace(service=DummyService())

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)

    t = SoapTransport(url="https://x/polarion", username="u", password="bad")
    with pytest.raises(AuthError):
        t.call("Tracker", "ping")


def test_call_retries_on_connection_error(monkeypatch):
    class FlakyService(DummyService):
        def __init__(self):
            super().__init__()
            self.count = 0

        def ping(self, **kwargs):
            self.count += 1
            if self.count < 3:
                raise requests.ConnectionError("temporary")
            return {"ok": True}

    services = {}

    def fake_client(wsdl, transport):
        svc = FlakyService() if wsdl.endswith("/Tracker?wsdl") else DummyService()
        services[wsdl] = svc
        return SimpleNamespace(service=svc)

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)
    monkeypatch.setattr("polarion.v3.transport.soap.time.sleep", lambda *_: None)

    t = SoapTransport(url="https://x/polarion", username="u")
    out = t.call("Tracker", "ping")
    assert out["ok"] is True


def test_call_fails_after_retries(monkeypatch):
    class AlwaysFailService(DummyService):
        def ping(self, **kwargs):
            raise requests.Timeout("timeout")

    def fake_client(wsdl, transport):
        svc = AlwaysFailService() if wsdl.endswith("/Tracker?wsdl") else DummyService()
        return SimpleNamespace(service=svc)

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)
    monkeypatch.setattr("polarion.v3.transport.soap.time.sleep", lambda *_: None)

    t = SoapTransport(url="https://x/polarion", username="u", max_retries=1)
    with pytest.raises(TransportError):
        t.call("Tracker", "ping")


def test_call_with_fallback_uses_second_method(monkeypatch):
    class FallbackService(DummyService):
        def methodA(self, **kwargs):
            raise requests.ConnectionError("nope")

        def methodB(self, **kwargs):
            return {"ok": True}

    def fake_client(wsdl, transport):
        svc = FallbackService() if wsdl.endswith("/Tracker?wsdl") else DummyService()
        return SimpleNamespace(service=svc)

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)
    monkeypatch.setattr("polarion.v3.transport.soap.time.sleep", lambda *_: None)

    t = SoapTransport(url="https://x/polarion", username="u")
    out = t.call_with_fallback("Tracker", ["methodA", "methodB"])
    assert out["ok"] is True


def test_supports_method(monkeypatch):
    def fake_client(wsdl, transport):
        return SimpleNamespace(service=DummyService({"ping": lambda **k: {"ok": True}}))

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)

    t = SoapTransport(url="https://x/polarion", username="u")
    assert t.supports_method("Tracker", "ping") is True
    assert t.supports_method("Tracker", "missing") is False

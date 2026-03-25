from types import SimpleNamespace

from polarion.v3.client import PolarionClient


class DummyService:
    def __init__(self, methods=None):
        methods = methods or {}
        for name, fn in methods.items():
            setattr(self, name, fn)


def test_healthcheck_and_capabilities(monkeypatch):
    def has_subject(**kwargs):
        return True

    def fake_client(wsdl, transport):
        if wsdl.endswith("/Session?wsdl"):
            return SimpleNamespace(service=DummyService({"hasSubject": has_subject, "endSession": lambda: True}))
        if wsdl.endswith("/Project?wsdl"):
            return SimpleNamespace(service=DummyService({"getProject": lambda **k: {}, "getProjects": lambda **k: []}))
        if wsdl.endswith("/Tracker?wsdl"):
            return SimpleNamespace(service=DummyService({"queryWorkItems": lambda **k: []}))
        if wsdl.endswith("/Planning?wsdl"):
            return SimpleNamespace(service=DummyService({"searchPlans": lambda **k: []}))
        if wsdl.endswith("/TestManagement?wsdl"):
            return SimpleNamespace(service=DummyService({"searchTestRuns": lambda **k: []}))
        return SimpleNamespace(service=DummyService())

    monkeypatch.setattr("polarion.v3.transport.soap.Client", fake_client)

    client = PolarionClient(url="https://x/polarion", username="u")
    health = client.healthcheck()
    caps = client.capabilities()

    assert "checks" in health
    assert "services" in caps
    assert "Project" in caps["services"]

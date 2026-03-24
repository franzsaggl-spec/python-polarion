import pytest

from polarion.v3.errors import NotFoundError, ValidationError
from polarion.v3.services.documents import DocumentsService
from polarion.v3.transport.soap import SoapTransport


class DummyTransport(SoapTransport):
    def __init__(self):
        super().__init__(url="http://x", username="u")
        self.responses = {}

    def call(self, service: str, method: str, **kwargs):
        return self.responses.get((service, method), {})


def test_documents_get_requires_uri_or_location():
    svc = DocumentsService(DummyTransport())
    with pytest.raises(ValidationError):
        svc.get("PRJ")


def test_documents_top_level_missing_raises_not_found():
    t = DummyTransport()
    t.responses[("Tracker", "getModuleWorkItems")] = []
    svc = DocumentsService(t)
    with pytest.raises(NotFoundError):
        svc.top_level_workitem("PRJ", "doc:1")

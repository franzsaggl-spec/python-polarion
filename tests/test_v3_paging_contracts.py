import pytest

from polarion.v3.errors import ValidationError
from polarion.v3.services.projects import ProjectsService
from polarion.v3.transport.soap import SoapTransport


class DummyTransport(SoapTransport):
    def __init__(self):
        super().__init__(url="http://x", username="u")
        self.responses = {}

    def call(self, service: str, method: str, **kwargs):
        return self.responses.get((service, method), [])


def test_projects_list_rejects_negative_offset():
    t = DummyTransport()
    t.responses[("Project", "getProjects")] = [{"id": "P1", "name": "A"}]
    svc = ProjectsService(t)
    with pytest.raises(ValidationError):
        svc.list(offset=-1, limit=10)


def test_projects_list_rejects_nonpositive_limit():
    t = DummyTransport()
    t.responses[("Project", "getProjects")] = [{"id": "P1", "name": "A"}]
    svc = ProjectsService(t)
    with pytest.raises(ValidationError):
        svc.list(offset=0, limit=0)

from polarion.v3.services.projects import ProjectsService
from polarion.v3.services.users import UsersService
from polarion.v3.transport.soap import SoapTransport


class DummyTransport(SoapTransport):
    def __init__(self):
        super().__init__(url="http://x", username="u")
        self.calls = []
        self.responses = {}

    def call(self, service: str, method: str, **kwargs):
        self.calls.append((service, method, kwargs))
        return self.responses.get((service, method), {})


def test_projects_get():
    t = DummyTransport()
    t.responses[("Project", "getProject")] = {"id": "P1", "name": "Project 1", "trackerPrefix": "PX"}
    svc = ProjectsService(t)

    p = svc.get("P1")

    assert p.id == "P1"
    assert p.name == "Project 1"
    assert t.calls[0][1] == "getProject"


def test_projects_list_with_filter_and_paging():
    t = DummyTransport()
    t.responses[("Project", "getProjects")] = [
        {"id": "P1", "name": "Alpha"},
        {"id": "P2", "name": "Beta"},
        {"id": "P3", "name": "Alpha-2"},
    ]
    svc = ProjectsService(t)

    page = svc.list(query="alpha", offset=0, limit=1)

    assert page.total == 2
    assert len(page.items) == 1
    assert page.has_more is True


def test_projects_users():
    t = DummyTransport()
    t.responses[("Project", "getProjectUsers")] = [
        {"id": "u1", "name": "alice"},
        {"id": "u2", "name": "bob"},
    ]
    svc = ProjectsService(t)

    page = svc.users("P1", offset=1, limit=1)

    assert page.total == 2
    assert len(page.items) == 1
    assert page.items[0].id == "u2"


def test_users_get_and_empty_search():
    t = DummyTransport()
    t.responses[("Project", "getUser")] = {"id": "u1", "name": "alice", "email": "a@example.com"}
    svc = UsersService(t)

    user = svc.get("u1")
    page = svc.search(query="alice")

    assert user.id == "u1"
    assert user.email == "a@example.com"
    assert page.total == 0
    assert page.items == []

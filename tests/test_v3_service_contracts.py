import pytest

from polarion.v3.errors import NotFoundError
from polarion.v3.services import testruns as testrun_services
from polarion.v3.services.plans import PlansService
from polarion.v3.services.projects import ProjectsService
from polarion.v3.services.users import UsersService
from polarion.v3.services.workitems import WorkitemsService
from polarion.v3.transport.soap import SoapTransport


class DummyTransport(SoapTransport):
    def __init__(self):
        super().__init__(url="http://x", username="u")
        self.responses = {}

    def call(self, service: str, method: str, **kwargs):
        return self.responses.get((service, method), {})


def test_projects_get_not_found():
    svc = ProjectsService(DummyTransport())
    with pytest.raises(NotFoundError):
        svc.get("P1")


def test_users_get_not_found():
    svc = UsersService(DummyTransport())
    with pytest.raises(NotFoundError):
        svc.get("u1")


def test_workitems_get_not_found():
    svc = WorkitemsService(DummyTransport())
    with pytest.raises(NotFoundError):
        svc.get("P1", "WI-1")


def test_plans_get_not_found():
    svc = PlansService(DummyTransport())
    with pytest.raises(NotFoundError):
        svc.get("P1", "PL-1")


def test_testruns_get_not_found():
    svc = testrun_services.TestRunsService(DummyTransport())
    with pytest.raises(NotFoundError):
        svc.get("P1", "TR-1")

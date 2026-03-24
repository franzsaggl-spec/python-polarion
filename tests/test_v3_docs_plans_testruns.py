from polarion.v3.services import testruns as testrun_services
from polarion.v3.services.documents import DocumentsService
from polarion.v3.services.plans import PlansService
from polarion.v3.transport.soap import SoapTransport
from polarion.v3.types import testrun as testrun_types
from polarion.v3.types.document import DocumentCreate
from polarion.v3.types.plan import PlanCreate


class DummyTransport(SoapTransport):
    def __init__(self):
        super().__init__(url="http://x", username="u")
        self.calls = []
        self.responses = {}

    def call(self, service: str, method: str, **kwargs):
        self.calls.append((service, method, kwargs))
        return self.responses.get((service, method), {})


def test_documents_get_create_list_space():
    t = DummyTransport()
    t.responses[("Tracker", "getModuleByUri")] = {
        "_uri": "doc:1",
        "project": {"id": "PRJ"},
        "moduleLocation": "Specs",
        "moduleName": "API",
        "title": "API Spec",
    }
    t.responses[("Tracker", "createDocument")] = t.responses[("Tracker", "getModuleByUri")]
    t.responses[("Tracker", "getModules")] = [t.responses[("Tracker", "getModuleByUri")]]
    t.responses[("Tracker", "getDocumentSpaces")] = ["_default"]

    svc = DocumentsService(t)
    doc = svc.get("PRJ", uri="doc:1")
    created = svc.create(
        "PRJ",
        DocumentCreate(
            location="Specs",
            name="API",
            title="API Spec",
            allowed_workitem_types=["requirement"],
            structure_link_role="parent",
        ),
    )
    page = svc.list_in_space("PRJ", "_default")

    assert doc.project_id == "PRJ"
    assert created.name == "API"
    assert page.total == 1
    assert svc.list_spaces("PRJ") == ["_default"]


def test_plans_get_create_search():
    t = DummyTransport()
    t.responses[("Planning", "getPlanById")] = {"id": "P1", "_uri": "plan:1", "name": "Plan 1"}
    t.responses[("Planning", "createPlan")] = t.responses[("Planning", "getPlanById")]
    t.responses[("Planning", "searchPlans")] = [t.responses[("Planning", "getPlanById")]]

    svc = PlansService(t)
    plan = svc.get("PRJ", "P1")
    created = svc.create("PRJ", PlanCreate(name="Plan 1", plan_id="P1", template="default"))
    page = svc.search("PRJ")

    assert plan.id == "P1"
    assert created.id == "P1"
    assert page.total == 1


def test_testruns_get_create_search_records_attachments():
    t = DummyTransport()
    t.responses[("TestManagement", "getTestRunById")] = {"id": "TR-1", "_uri": "tr:1", "title": "Run"}
    t.responses[("TestManagement", "createTestRun")] = t.responses[("TestManagement", "getTestRunById")]
    t.responses[("TestManagement", "searchTestRuns")] = [t.responses[("TestManagement", "getTestRunById")]]
    t.responses[("TestManagement", "getTestRunRecords")] = [{"testCaseId": "TC-1", "result": "passed"}]
    t.responses[("TestManagement", "getTestRunAttachments")] = [{"id": "a1", "fileName": "r.txt"}]

    svc = testrun_services.TestRunsService(t)
    tr = svc.get("PRJ", "TR-1")
    created = svc.create("PRJ", testrun_types.TestRunCreate(id="TR-1", title="Run", template_id="TMP"))
    page = svc.search("PRJ")
    recs = svc.records("tr:1")
    atts = svc.attachments("tr:1")

    assert tr.id == "TR-1"
    assert created.id == "TR-1"
    assert page.total == 1
    assert recs.total == 1
    assert atts[0].file_name == "r.txt"

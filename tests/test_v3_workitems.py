from polarion.v3.services.workitems import WorkitemsService
from polarion.v3.transport.soap import SoapTransport
from polarion.v3.types.workitem import WorkitemCreate, WorkitemUpdate


class DummyTransport(SoapTransport):
    def __init__(self):
        super().__init__(url="http://x", username="u")
        self.calls = []
        self.responses = {}

    def call(self, service: str, method: str, **kwargs):
        self.calls.append((service, method, kwargs))
        return self.responses.get((service, method), {})


def _wi(id_: str = "WI-1"):
    return {
        "id": id_,
        "_uri": f"uri:{id_}",
        "title": "Title",
        "type": {"id": "task"},
        "status": {"id": "open"},
        "priority": {"id": "high"},
    }


def test_get_and_get_by_uri():
    t = DummyTransport()
    t.responses[("Tracker", "getWorkItemById")] = _wi("WI-1")
    t.responses[("Tracker", "getWorkItemByUri")] = _wi("WI-2")
    svc = WorkitemsService(t)

    a = svc.get("PRJ", "WI-1")
    b = svc.get_by_uri("uri:WI-2")

    assert a.id == "WI-1"
    assert b.id == "WI-2"


def test_search_paging():
    t = DummyTransport()
    t.responses[("Tracker", "queryWorkItems")] = [_wi("WI-1"), _wi("WI-2"), _wi("WI-3")]
    svc = WorkitemsService(t)

    page = svc.search("PRJ", query="type:task", offset=1, limit=1)

    assert page.total == 3
    assert len(page.items) == 1
    assert page.items[0].id == "WI-2"


def test_create_update_delete():
    t = DummyTransport()
    t.responses[("Tracker", "createWorkItem")] = _wi("WI-9")
    t.responses[("Tracker", "getWorkItemById")] = _wi("WI-9")
    svc = WorkitemsService(t)

    created = svc.create("PRJ", WorkitemCreate(type_id="task", title="X"))
    updated = svc.update("PRJ", "WI-9", WorkitemUpdate(title="New"))
    svc.delete("PRJ", "WI-9")

    assert created.id == "WI-9"
    assert updated.id == "WI-9"
    assert any(c[1] == "deleteWorkItem" for c in t.calls)


def test_actions_statuses_and_perform():
    t = DummyTransport()
    t.responses[("Tracker", "getAvailableActions")] = [{"id": "start"}, {"id": "finish"}]
    t.responses[("Tracker", "getAllowedStatuses")] = [{"id": "open"}, {"id": "done"}]
    t.responses[("Tracker", "getWorkItemById")] = _wi("WI-1")
    svc = WorkitemsService(t)

    actions = svc.available_actions("PRJ", "WI-1")
    statuses = svc.available_statuses("PRJ", "WI-1")
    _ = svc.perform_action("PRJ", "WI-1", "start")

    assert actions == ["start", "finish"]
    assert statuses == ["open", "done"]


def test_links_and_attachments_helpers():
    t = DummyTransport()
    wi = _wi("WI-1")
    wi["linkedWorkItems"] = [{"role": {"id": "relates"}, "workItemURI": "uri:WI-2"}]
    wi["attachments"] = [{"id": "a1", "fileName": "a.txt"}]
    t.responses[("Tracker", "getWorkItemById")] = wi
    t.responses[("Tracker", "addAttachment")] = {"id": "a1", "fileName": "a.txt"}
    svc = WorkitemsService(t)

    links = svc.links("PRJ", "WI-1")
    atts = svc.attachments("PRJ", "WI-1")
    uploaded = svc.upload_attachment("PRJ", "WI-1", "a.txt")

    assert links[0].role == "relates"
    assert atts[0].file_name == "a.txt"
    assert uploaded.file_name == "a.txt"

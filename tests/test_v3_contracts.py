from polarion import PolarionClient
from polarion.v3.errors import (
    AuthError,
    ConflictError,
    NotFoundError,
    ParsingError,
    PolarionError,
    TransportError,
    ValidationError,
)
from polarion.v3.parser.common import maybe_list, require_dict
from polarion.v3.parser.project import parse_project
from polarion.v3.types import testrun as tr_types
from polarion.v3.types.common import AttachmentMeta, EnumRef, Link, Page, Ref, UserRef
from polarion.v3.types.document import Document, DocumentCreate
from polarion.v3.types.plan import Plan, PlanCreate
from polarion.v3.types.project import Project
from polarion.v3.types.workitem import WorkitemCreate, WorkitemDetail, WorkitemSummary, WorkitemUpdate


def test_error_hierarchy():
    assert issubclass(AuthError, PolarionError)
    assert issubclass(NotFoundError, PolarionError)
    assert issubclass(ValidationError, PolarionError)
    assert issubclass(TransportError, PolarionError)
    assert issubclass(ParsingError, PolarionError)
    assert issubclass(ConflictError, PolarionError)


def test_client_service_namespaces_exist():
    client = PolarionClient(url="http://example", username="u", password="p")
    assert client.projects is not None
    assert client.workitems is not None
    assert client.documents is not None
    assert client.plans is not None
    assert client.testruns is not None
    assert client.users is not None


def test_common_types_construct():
    ref = Ref(id="R1", uri="u", name="n")
    uref = UserRef(id="U1")
    eref = EnumRef(id="E1")
    link = Link(role="relates", target_id="WI-1", target_uri="uri")
    att = AttachmentMeta(id="a", file_name="f.txt", title=None, url=None)
    page = Page(items=[ref], total=1, offset=0, limit=10, has_more=False)
    assert ref.id == "R1"
    assert uref.id == "U1"
    assert eref.id == "E1"
    assert link.role == "relates"
    assert att.file_name == "f.txt"
    assert page.total == 1


def test_domain_types_construct():
    ws = WorkitemSummary(
        id="WI-1",
        uri="uri",
        title="Title",
        type=EnumRef(id="task"),
        status=EnumRef(id="open"),
        priority=EnumRef(id="high"),
    )
    wd = WorkitemDetail(
        **ws.__dict__,
        description_html="<p>x</p>",
        author=UserRef(id="u"),
        assignees=[],
        approvers=[],
        links=[],
        attachments=[],
        custom_fields={},
        created_at=None,
        updated_at=None,
    )
    wc = WorkitemCreate(type_id="task", title="T")
    wu = WorkitemUpdate(title="New")
    doc = Document(
        uri="u",
        project_id="P",
        location="/",
        name="n",
        title="t",
        status=None,
        type=None,
    )
    doc_create = DocumentCreate(
        location="/",
        name="n",
        title="t",
        allowed_workitem_types=["task"],
        structure_link_role="parent",
    )
    plan = Plan(id="PL", uri="u", name="Plan", status=None, start_date=None, due_date=None)
    plan_create = PlanCreate(name="Plan", plan_id="PL", template="default")
    tr = tr_types.TestRun(id="TR", uri="u", title="Run", is_template=False, status=None, created_at=None)
    trc = tr_types.TestRunCreate(id="TR", title="Run", template_id="TMP")
    rec = tr_types.TestRecord(test_case_id="TC-1", result="passed", duration_ms=1, comment=None)
    project = Project(id="P", name="Proj", tracker_prefix="PX")

    assert wd.id == "WI-1"
    assert wc.type_id == "task"
    assert wu.title == "New"
    assert doc.name == "n"
    assert doc_create.structure_link_role == "parent"
    assert plan.id == "PL"
    assert plan_create.template == "default"
    assert tr.id == "TR"
    assert trc.template_id == "TMP"
    assert rec.test_case_id == "TC-1"
    assert project.id == "P"


def test_parser_common_helpers():
    assert maybe_list(None) == []
    assert maybe_list([1, 2]) == [1, 2]
    assert maybe_list("x") == ["x"]

    assert require_dict({"a": 1}, context="x") == {"a": 1}


def test_parser_common_requires_dict():
    try:
        require_dict([1, 2], context="project")
    except ParsingError as e:
        assert "Expected dict for project" in str(e)
    else:
        raise AssertionError("Expected ParsingError")


def test_parse_project():
    p = parse_project({"id": "P1", "name": "My Project", "trackerPrefix": "PX"})
    assert p.id == "P1"
    assert p.name == "My Project"
    assert p.tracker_prefix == "PX"

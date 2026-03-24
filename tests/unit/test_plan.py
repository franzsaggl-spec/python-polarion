"""Tests for Plan with mocked SOAP layer (v2.0.0 API)."""

import copy
from unittest.mock import MagicMock, patch

import pytest

from polarion.exceptions import PolarionNotFoundError
from polarion.plan import Plan

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_plan_data():
    """A sample plan dict as returned by the Planning service in v2.0.0."""
    return {
        "id": "PLAN-001",
        "name": "Release 1.0",
        "uri": "subterra:data-service:objects:/default/test_project${Plan}PLAN-001",
        "dueDate": None,
        "startDate": None,
        "finishedOn": None,
        "startedOn": None,
        "records": None,
        "parent": None,
        "allowedTypes": None,
        "template": None,
        "description": None,
        "color": None,
        "projectURI": None,
        "calculationType": None,
        "capacity": None,
        "defaultEstimate": None,
        "estimationField": None,
        "prioritizationField": None,
        "sortOrder": None,
        "status": None,
    }


def _make_plan(mock_polarion, mock_project, mock_plan_data):
    """Build a Plan from mocked data without hitting SOAP."""
    data = copy.deepcopy(mock_plan_data)
    plan = Plan(mock_polarion, mock_project, polarion_record=data)
    return plan


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


def test_plan_creation_from_polarion_record(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    assert plan.id == "PLAN-001"
    assert plan.name == "Release 1.0"


def test_plan_creation_unresolvable_raises(mock_polarion, mock_project):
    bad_data = {"id": "PLAN-BAD", "unresolvable": True}
    with pytest.raises(PolarionNotFoundError):
        Plan(mock_polarion, mock_project, polarion_record=bad_data)


def test_plan_creation_none_record_creates_empty_plan(mock_polarion, mock_project):
    """When polarion_record=None, it defaults to {} and creates an empty plan."""
    plan = Plan(mock_polarion, mock_project, polarion_record=None)
    # Empty dict means no fields set, but no error raised
    assert plan.id is None
    assert plan.name is None


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_eq_same_id(mock_polarion, mock_project, mock_plan_data):
    plan1 = _make_plan(mock_polarion, mock_project, mock_plan_data)
    plan2 = _make_plan(mock_polarion, mock_project, mock_plan_data)
    assert plan1 == plan2


def test_eq_different_id(mock_polarion, mock_project, mock_plan_data):
    plan1 = _make_plan(mock_polarion, mock_project, mock_plan_data)

    other_data = copy.deepcopy(mock_plan_data)
    other_data["id"] = "PLAN-002"
    other_data["name"] = "Release 2.0"
    other_data["uri"] = "subterra:data-service:objects:/default/test_project${Plan}PLAN-002"

    plan2 = _make_plan(mock_polarion, mock_project, other_data)
    assert plan1 != plan2


def test_eq_different_type_returns_not_implemented(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    result = plan.__eq__("not a plan")
    assert result is NotImplemented


def test_eq_different_type_ne(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    assert plan != 42
    assert plan != "not a plan"


# ---------------------------------------------------------------------------
# __repr__ / __str__
# ---------------------------------------------------------------------------


def test_repr_contains_name_and_id(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    r = repr(plan)
    assert "Release 1.0" in r
    assert "PLAN-001" in r


def test_str_equals_repr(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    assert str(plan) == repr(plan)


# ---------------------------------------------------------------------------
# get_workitems
# ---------------------------------------------------------------------------


def test_get_workitems_empty_when_no_records(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    plan.records = None
    assert plan.get_workitems() == []


def test_get_workitems_with_records(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)

    # Create mock plan records as plain dicts
    plan.records = [
        {"item": {"id": "WI-001", "title": "Work item 1", "uri": "uri1", "type": {"id": "task"}, "status": {"id": "open"}, "project": {"id": "test_project"}}},
    ]

    with patch("polarion.plan.Workitem") as MockWorkitem:
        MockWorkitem.return_value = MagicMock()
        result = plan.get_workitems()
        assert len(result) == 1
        MockWorkitem.assert_called_once()


def test_get_workitems_skips_none_ids(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)

    # Record with id=None should be skipped
    plan.records = [
        {"item": {"id": None}},
    ]

    with patch("polarion.plan.Workitem") as MockWorkitem:
        result = plan.get_workitems()
        assert len(result) == 0
        MockWorkitem.assert_not_called()


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


def test_save_no_changes(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)

    mock_polarion._soap.call.reset_mock()
    mock_polarion._soap.call.side_effect = None
    mock_polarion._soap.call.return_value = None

    plan.save()
    # updatePlan should not be called since nothing changed
    for c in mock_polarion._soap.call.call_args_list:
        assert c[0][1] != "updatePlan"


def test_save_with_changes(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)

    # Modify an attribute
    plan.name = "Changed Name"

    reload_data = copy.deepcopy(mock_plan_data)
    reload_data["name"] = "Changed Name"

    def _soap_call(service, method, **kwargs):
        if service == "Planning" and method == "updatePlan":
            return None
        if service == "Planning" and method == "getPlanByUri":
            return reload_data
        return None

    mock_polarion._soap.call.side_effect = _soap_call
    plan.save()

    # Verify updatePlan was called
    calls = mock_polarion._soap.call.call_args_list
    update_calls = [c for c in calls if c[0] == ("Planning", "updatePlan")]
    assert len(update_calls) == 1
    assert update_calls[0][1]["content"]["uri"] == plan.uri


# ------------------------------------------------------------------
# to_dict()
# ------------------------------------------------------------------


def test_to_dict_default_fields(mock_polarion, mock_project, mock_plan_data):
    """to_dict() with no args should return minimal summary fields."""
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    result = plan.to_dict()

    # Default fields: id, name, startDate, dueDate
    assert "id" in result
    assert "name" in result
    assert "startDate" in result
    assert "dueDate" in result

    assert result["id"] == "PLAN-001"
    assert result["name"] == "Release 1.0"
    assert len(result) == 4


def test_to_dict_custom_fields(mock_polarion, mock_project, mock_plan_data):
    """to_dict() should return only requested fields."""
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    result = plan.to_dict(fields=["id", "name"])

    assert "id" in result
    assert "name" in result
    assert "startDate" not in result
    assert len(result) == 2

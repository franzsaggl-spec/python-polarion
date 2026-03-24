"""Tests for Plan with mocked SOAP layer."""

from unittest.mock import MagicMock, patch

import pytest

from polarion.exceptions import PolarionNotFoundError
from polarion.plan import Plan

# Local import of the shared zeep mock helper from conftest
from tests.unit.conftest import _zeep_object

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_plan_data():
    """A sample plan zeep-style object as returned by the Planning service."""
    return _zeep_object(
        {
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
    )


def _make_plan(mock_polarion, mock_project, mock_plan_data):
    """Build a Plan from mocked data without hitting SOAP."""
    planning_service = MagicMock()
    planning_service.getPlanById.return_value = mock_plan_data

    original_get_service = mock_polarion.getService

    def _get_service(name):
        if name == "Planning":
            return planning_service
        return original_get_service(name)

    with patch.object(mock_polarion, "getService", side_effect=_get_service):
        plan = Plan(mock_polarion, mock_project, polarion_record=mock_plan_data)

    mock_polarion.getService = MagicMock(side_effect=_get_service)
    return plan


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


def test_plan_creation_from_polarion_record(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    assert plan.id == "PLAN-001"
    assert plan.name == "Release 1.0"


def test_plan_creation_unresolvable_raises(mock_polarion, mock_project):
    bad_data = _zeep_object({"id": "PLAN-BAD"}, unresolvable=True)
    with pytest.raises(PolarionNotFoundError):
        Plan(mock_polarion, mock_project, polarion_record=bad_data)


def test_plan_creation_none_record_raises(mock_polarion, mock_project):
    with pytest.raises(PolarionNotFoundError):
        Plan(mock_polarion, mock_project, polarion_record=None)


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_eq_same_id(mock_polarion, mock_project, mock_plan_data):
    plan1 = _make_plan(mock_polarion, mock_project, mock_plan_data)
    plan2 = _make_plan(mock_polarion, mock_project, mock_plan_data)
    assert plan1 == plan2


def test_eq_different_id(mock_polarion, mock_project, mock_plan_data):
    plan1 = _make_plan(mock_polarion, mock_project, mock_plan_data)

    other_data = _zeep_object(
        {
            "id": "PLAN-002",
            "name": "Release 2.0",
            "uri": "subterra:data-service:objects:/default/test_project${Plan}PLAN-002",
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
    )
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
# getWorkitemsInPlan
# ---------------------------------------------------------------------------


def test_get_workitems_in_plan_empty_when_no_records(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)
    plan.records = None
    assert plan.getWorkitemsInPlan() == []


def test_get_workitems_in_plan_with_records(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)

    # Create mock plan records with workitem items
    mock_item = MagicMock()
    mock_item.id = "WI-001"
    mock_record = MagicMock()
    mock_record.item = mock_item

    mock_records = MagicMock()
    mock_records.PlanRecord = [mock_record]
    plan.records = mock_records

    # Mock the Workitem constructor
    with patch("polarion.plan.Workitem") as MockWorkitem:
        MockWorkitem.return_value = MagicMock()
        result = plan.getWorkitemsInPlan()
        assert len(result) == 1
        MockWorkitem.assert_called_once()


def test_get_workitems_skips_none_ids(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)

    # Record with id=None should be skipped
    mock_item = MagicMock()
    mock_item.id = None
    mock_record = MagicMock()
    mock_record.item = mock_item

    mock_records = MagicMock()
    mock_records.PlanRecord = [mock_record]
    plan.records = mock_records

    with patch("polarion.plan.Workitem") as MockWorkitem:
        result = plan.getWorkitemsInPlan()
        assert len(result) == 0
        MockWorkitem.assert_not_called()


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


def test_save_no_changes(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)

    planning_service = MagicMock()
    mock_polarion.getService = MagicMock(return_value=planning_service)

    plan.save()
    planning_service.updatePlan.assert_not_called()


def test_save_with_changes(mock_polarion, mock_project, mock_plan_data):
    plan = _make_plan(mock_polarion, mock_project, mock_plan_data)

    # Modify an attribute
    plan.name = "Changed Name"

    planning_service = MagicMock()
    # Make getPlanByUri return updated data for reload
    planning_service.getPlanByUri.return_value = mock_plan_data

    mock_polarion.getService = MagicMock(return_value=planning_service)

    plan.save()
    planning_service.updatePlan.assert_called_once()
    call_args = planning_service.updatePlan.call_args[0][0]
    assert call_args["uri"] == plan.uri


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

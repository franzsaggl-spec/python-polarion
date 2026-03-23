"""Tests for Project-level methods with mocked SOAP layer."""

import pytest
from unittest.mock import MagicMock, patch

from polarion.project import Project


def _make_project(mock_polarion, project_id='TEST'):
    """Build a Project from mocked data without hitting SOAP."""
    project_service = MagicMock()

    # Mock project data
    project_data = MagicMock()
    project_data.name = 'Test Project'
    project_data.trackerPrefix = 'TEST'
    project_data.unresolvable = False
    project_data.__contains__ = lambda self, key: key in ['name', 'trackerPrefix']

    project_service.getProject.return_value = project_data

    def _get_service(name):
        if name == 'Project':
            return project_service
        return MagicMock()

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        proj = Project(mock_polarion, project_id)

    mock_polarion.getService = MagicMock(side_effect=_get_service)
    return proj


# ------------------------------------------------------------------
# countWorkitems
# ------------------------------------------------------------------

def test_count_workitems_returns_correct_count(mock_polarion):
    """countWorkitems should return the length of search results."""
    proj = _make_project(mock_polarion)

    # Mock searchWorkitem to return 5 items
    mock_results = [MagicMock() for _ in range(5)]
    with patch.object(proj, 'searchWorkitem', return_value=mock_results):
        count = proj.countWorkitems("status:open")
        assert count == 5


def test_count_workitems_with_empty_query(mock_polarion):
    """countWorkitems should work with empty query."""
    proj = _make_project(mock_polarion)

    mock_results = [MagicMock() for _ in range(10)]
    with patch.object(proj, 'searchWorkitem', return_value=mock_results):
        count = proj.countWorkitems()
        assert count == 10


def test_count_workitems_returns_zero_when_no_matches(mock_polarion):
    """countWorkitems should return 0 when no items match."""
    proj = _make_project(mock_polarion)

    with patch.object(proj, 'searchWorkitem', return_value=[]):
        count = proj.countWorkitems("status:impossible")
        assert count == 0


# ------------------------------------------------------------------
# countPlans
# ------------------------------------------------------------------

def test_count_plans_returns_correct_count(mock_polarion):
    """countPlans should return the length of search results."""
    proj = _make_project(mock_polarion)

    mock_results = [MagicMock() for _ in range(3)]
    with patch.object(proj, 'searchPlan', return_value=mock_results):
        count = proj.countPlans("status:open")
        assert count == 3


def test_count_plans_returns_zero_when_no_matches(mock_polarion):
    """countPlans should return 0 when no plans match."""
    proj = _make_project(mock_polarion)

    with patch.object(proj, 'searchPlan', return_value=[]):
        count = proj.countPlans()
        assert count == 0


# ------------------------------------------------------------------
# countTestRuns
# ------------------------------------------------------------------

def test_count_test_runs_returns_correct_count(mock_polarion):
    """countTestRuns should return the length of search results."""
    proj = _make_project(mock_polarion)

    mock_results = [MagicMock() for _ in range(7)]
    with patch.object(proj, 'searchTestRuns', return_value=mock_results):
        count = proj.countTestRuns("created:>2024-01-01")
        assert count == 7


def test_count_test_runs_returns_zero_when_no_matches(mock_polarion):
    """countTestRuns should return 0 when no test runs match."""
    proj = _make_project(mock_polarion)

    with patch.object(proj, 'searchTestRuns', return_value=[]):
        count = proj.countTestRuns()
        assert count == 0


# ------------------------------------------------------------------
# __repr__
# ------------------------------------------------------------------

def test_project_repr(mock_polarion):
    """Project should have a readable repr."""
    proj = _make_project(mock_polarion, 'MYPROJ')
    assert 'Test Project' in repr(proj)
    assert 'TEST' in repr(proj)

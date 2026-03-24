"""Shared pytest fixtures that mock the SOAP layer so tests never need a live Polarion server.

v2.0.0: Polarion is imported from polarion.client and uses a SoapClient (_soap)
rather than a zeep-based services dict. Internal data is plain Python dicts.
"""

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_polarion():
    """A Polarion instance with every SOAP interaction mocked out.

    Patches ``SoapClient`` so that ``Polarion.__init__`` succeeds without
    any network access.
    """
    with patch("polarion.client.SoapClient") as MockSoapClient:
        mock_soap = MagicMock()
        MockSoapClient.return_value = mock_soap

        # discover_services should succeed silently
        mock_soap.discover_services.return_value = None

        # login should succeed silently
        mock_soap.login.return_value = None
        mock_soap.login_with_token.return_value = None

        # has_service returns True for standard services
        standard_services = {
            "Session",
            "Tracker",
            "Project",
            "Builder",
            "Planning",
            "TestManagement",
            "Security",
        }
        mock_soap.has_service.side_effect = lambda name: name in standard_services

        # call returns None by default
        mock_soap.call.return_value = None

        # --- Build the Polarion object ------------------------------------
        from polarion.client import Polarion

        pol = Polarion(
            "http://polarion.example.com/polarion",
            "testuser",
            password="testpass",
        )

        # Expose mock for assertions in tests
        pol._mock_soap = mock_soap
        yield pol


@pytest.fixture()
def mock_project(mock_polarion):
    """A Project instance with mocked polarion_data."""
    project_data = {
        "name": "Test Project",
        "trackerPrefix": "TP",
        "id": "test_project",
    }

    mock_polarion._soap.call.return_value = project_data

    from polarion.project import Project

    proj = Project(mock_polarion, "test_project")

    # Reset call mock so subsequent tests start clean
    mock_polarion._soap.call.reset_mock()
    return proj


@pytest.fixture()
def mock_workitem_data():
    """A sample workitem dict as returned by the Tracker service in v2.0.0."""
    return {
        "id": "WI-001",
        "title": "Test workitem",
        "uri": "subterra:data-service:objects:/default/test_project${WorkItem}WI-001",
        "description": {"content": "<p>Test description</p>", "type": "text/html", "contentLossy": False},
        "type": {"id": "task"},
        "status": {"id": "open"},
        "resolution": {"id": "done"},
        "author": {"id": "testuser"},
        "assignee": None,
        "approvals": None,
        "attachments": None,
        "linkedWorkItems": None,
        "linkedWorkItemsDerived": None,
        "customFields": None,
        "project": {"id": "test_project"},
        "created": "2024-01-01",
        "updated": "2024-01-02",
        "comments": None,
        "categories": None,
        "hyperlinks": None,
        "priority": None,
        "severity": None,
        "timePoint": None,
        "plannedEnd": None,
        "plannedStart": None,
        "initialEstimate": None,
        "remainingEstimate": None,
        "timeSpent": None,
        "dueDate": None,
        "outlineNumber": None,
        "externallyLinkedWorkItems": None,
        "plannedIn": None,
        "watches": None,
        "moduleURI": None,
        "location": None,
        "previousStatus": None,
    }

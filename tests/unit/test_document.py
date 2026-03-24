"""Tests for Document with mocked SOAP layer (v2.0.0 API)."""

import copy

import pytest

from polarion.document import Document
from polarion.exceptions import PolarionNotFoundError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_document_data():
    """A sample document dict as returned by the Tracker service in v2.0.0."""
    return {
        "title": "Test Document",
        "uri": "subterra:data-service:objects:/default/test_project${Module}TestDoc",
        "moduleFolder": "/TestFolder",
        "moduleLocation": "/TestFolder/TestDoc",
        "moduleName": "TestDoc",
        "type": "genericModule",
        "status": None,
        "structureLinkRole": {"id": "parent"},
        "customFields": None,
        "homePageContent": None,
        "updateDate": None,
        "updatedBy": None,
        "branched": False,
        "headingSidebarFields": None,
        "outlineNumbering": None,
        "usesOutlineNumbering": True,
        "allowedWITypes": None,
        "comments": None,
        "derivedFrom": None,
        "derivedFromURI": None,
        "derivedFromRevision": None,
    }


def _make_document(mock_polarion, mock_project, mock_document_data):
    """Build a Document from mocked data without hitting SOAP."""
    data = copy.deepcopy(mock_document_data)

    def _soap_call(service, method, **kwargs):
        if service == "Tracker" and method == "getModuleByUri":
            return data
        return None

    mock_polarion._soap.call.side_effect = _soap_call
    doc = Document(mock_polarion, mock_project, uri=data["uri"])

    return doc


# ---------------------------------------------------------------------------
# Creation from URI
# ---------------------------------------------------------------------------


def test_document_creation_from_uri(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)
    assert doc.title == "Test Document"
    assert doc.moduleFolder == "/TestFolder"


def test_document_creation_from_uri_unresolvable_raises(mock_polarion, mock_project):
    bad_data = {"uri": "bad-uri", "unresolvable": True}

    mock_polarion._soap.call.side_effect = None
    mock_polarion._soap.call.return_value = bad_data

    with pytest.raises(PolarionNotFoundError):
        Document(mock_polarion, mock_project, uri="bad-uri")


# ---------------------------------------------------------------------------
# Creation from location
# ---------------------------------------------------------------------------


def test_document_creation_from_location(mock_polarion, mock_project, mock_document_data):
    data = copy.deepcopy(mock_document_data)

    def _soap_call(service, method, **kwargs):
        if service == "Tracker" and method == "getModuleByLocation":
            return data
        return None

    mock_polarion._soap.call.side_effect = _soap_call
    doc = Document(mock_polarion, mock_project, location="/TestFolder/TestDoc")

    assert doc.title == "Test Document"
    mock_polarion._soap.call.assert_called_with(
        "Tracker",
        "getModuleByLocation",
        projectId=mock_project.id,
        locationPath="/TestFolder/TestDoc",
    )


def test_document_creation_from_location_unresolvable_raises(mock_polarion, mock_project):
    bad_data = {"uri": "bad-uri", "unresolvable": True}

    mock_polarion._soap.call.side_effect = None
    mock_polarion._soap.call.return_value = bad_data

    with pytest.raises(PolarionNotFoundError):
        Document(mock_polarion, mock_project, location="/bad/location")


# ---------------------------------------------------------------------------
# is_custom_field_allowed
# ---------------------------------------------------------------------------


def test_is_custom_field_allowed_always_true(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)
    assert doc.is_custom_field_allowed("any_key") is True
    assert doc.is_custom_field_allowed("another_key") is True


# ---------------------------------------------------------------------------
# get_workitem_uris
# ---------------------------------------------------------------------------


def test_get_workitem_uris(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)

    expected_uris = ["uri1", "uri2", "uri3"]

    def _soap_call(service, method, **kwargs):
        if service == "Tracker" and method == "getModuleWorkItemUris":
            return expected_uris
        return None

    mock_polarion._soap.call.reset_mock()
    mock_polarion._soap.call.side_effect = _soap_call

    result = doc.get_workitem_uris()
    assert result == expected_uris
    mock_polarion._soap.call.assert_called_once_with(
        "Tracker",
        "getModuleWorkItemUris",
        moduleURI=doc._uri,
        baselineRevision=None,
        deep=True,
    )


def test_get_workitem_uris_empty(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)

    mock_polarion._soap.call.side_effect = None
    mock_polarion._soap.call.return_value = []

    result = doc.get_workitem_uris()
    assert result == []


# ---------------------------------------------------------------------------
# __repr__ / __str__
# ---------------------------------------------------------------------------


def test_repr_contains_title_and_folder(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)
    r = repr(doc)
    assert "Test Document" in r
    assert "/TestFolder" in r


def test_str_equals_repr(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)
    assert str(doc) == repr(doc)

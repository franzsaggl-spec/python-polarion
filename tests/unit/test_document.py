"""Tests for Document with mocked SOAP layer."""

import copy
import pytest
from unittest.mock import MagicMock, patch

from polarion.document import Document
from polarion.exceptions import PolarionNotFoundError


# Local import of the shared zeep mock helper from conftest
from tests.unit.conftest import _zeep_object


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_document_data():
    """A sample document zeep-style object as returned by the Tracker service."""
    return _zeep_object({
        'title': 'Test Document',
        'uri': 'subterra:data-service:objects:/default/test_project${Module}TestDoc',
        'moduleFolder': '/TestFolder',
        'moduleLocation': '/TestFolder/TestDoc',
        'moduleName': 'TestDoc',
        'type': 'genericModule',
        'status': None,
        'structureLinkRole': MagicMock(id='parent'),
        'customFields': None,
        'homePageContent': None,
        'updateDate': None,
        'updatedBy': None,
        'branched': False,
        'headingSidebarFields': None,
        'outlineNumbering': None,
        'usesOutlineNumbering': True,
        'allowedWITypes': None,
        'comments': None,
        'derivedFrom': None,
        'derivedFromURI': None,
        'derivedFromRevision': None,
    })


def _make_document(mock_polarion, mock_project, mock_document_data):
    """Build a Document from mocked data without hitting SOAP."""
    tracker_service = MagicMock()
    tracker_service.getModuleByUri.return_value = mock_document_data

    original_get_service = mock_polarion.getService

    def _get_service(name):
        if name == 'Tracker':
            return tracker_service
        return original_get_service(name)

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        doc = Document(mock_polarion, mock_project, uri=mock_document_data.uri)

    mock_polarion.getService = MagicMock(side_effect=_get_service)
    doc._tracker_service = tracker_service
    return doc


# ---------------------------------------------------------------------------
# Creation from URI
# ---------------------------------------------------------------------------

def test_document_creation_from_uri(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)
    assert doc.title == 'Test Document'
    assert doc.moduleFolder == '/TestFolder'


def test_document_creation_from_uri_unresolvable_raises(mock_polarion, mock_project):
    bad_data = _zeep_object({'uri': 'bad-uri'}, unresolvable=True)
    tracker_service = MagicMock()
    tracker_service.getModuleByUri.return_value = bad_data

    def _get_service(name):
        if name == 'Tracker':
            return tracker_service
        return MagicMock()

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        with pytest.raises(PolarionNotFoundError):
            Document(mock_polarion, mock_project, uri='bad-uri')


# ---------------------------------------------------------------------------
# Creation from location
# ---------------------------------------------------------------------------

def test_document_creation_from_location(mock_polarion, mock_project, mock_document_data):
    tracker_service = MagicMock()
    tracker_service.getModuleByLocation.return_value = mock_document_data

    def _get_service(name):
        if name == 'Tracker':
            return tracker_service
        return MagicMock()

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        doc = Document(mock_polarion, mock_project, location='/TestFolder/TestDoc')

    assert doc.title == 'Test Document'
    tracker_service.getModuleByLocation.assert_called_once_with(
        mock_project.id, '/TestFolder/TestDoc')


def test_document_creation_from_location_unresolvable_raises(mock_polarion, mock_project):
    bad_data = _zeep_object({'uri': 'bad-uri'}, unresolvable=True)
    tracker_service = MagicMock()
    tracker_service.getModuleByLocation.return_value = bad_data

    def _get_service(name):
        if name == 'Tracker':
            return tracker_service
        return MagicMock()

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        with pytest.raises(PolarionNotFoundError):
            Document(mock_polarion, mock_project, location='/bad/location')


# ---------------------------------------------------------------------------
# isCustomFieldAllowed
# ---------------------------------------------------------------------------

def test_is_custom_field_allowed_always_true(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)
    assert doc.isCustomFieldAllowed('any_key') is True
    assert doc.isCustomFieldAllowed('another_key') is True


# ---------------------------------------------------------------------------
# getWorkitemUris
# ---------------------------------------------------------------------------

def test_get_workitem_uris(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)

    expected_uris = ['uri1', 'uri2', 'uri3']
    tracker_service = MagicMock()
    tracker_service.getModuleWorkItemUris.return_value = expected_uris

    mock_polarion.getService = MagicMock(return_value=tracker_service)

    result = doc.getWorkitemUris()
    assert result == expected_uris
    tracker_service.getModuleWorkItemUris.assert_called_once_with(doc._uri, None, True)


def test_get_workitem_uris_empty(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)

    tracker_service = MagicMock()
    tracker_service.getModuleWorkItemUris.return_value = []

    mock_polarion.getService = MagicMock(return_value=tracker_service)

    result = doc.getWorkitemUris()
    assert result == []


# ---------------------------------------------------------------------------
# __repr__ / __str__
# ---------------------------------------------------------------------------

def test_repr_contains_title_and_folder(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)
    r = repr(doc)
    assert 'Test Document' in r
    assert '/TestFolder' in r


def test_str_equals_repr(mock_polarion, mock_project, mock_document_data):
    doc = _make_document(mock_polarion, mock_project, mock_document_data)
    assert str(doc) == repr(doc)

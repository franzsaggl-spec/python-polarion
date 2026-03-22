"""Shared pytest fixtures that mock the SOAP/zeep layer so tests never need a live Polarion server."""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helper: build a fake zeep-style object whose attributes are iterable dicts
# ---------------------------------------------------------------------------

class ZeepObject:
    """Mimics a zeep CompoundValue.

    Polarion source iterates ``obj.__dict__`` and expects a layout like
    ``{'__values__': {key: value, ...}}``.  Regular attribute access also works.

    ``unresolvable`` is stored inside ``__values__`` so that ``__dict__``
    contains *only* the ``__values__`` key (matching zeep's real layout).
    """

    def __init__(self, mapping, unresolvable=False):
        values = dict(mapping)
        values['unresolvable'] = unresolvable
        # Replace __dict__ so it contains exactly one key: __values__
        # This matches what zeep CompoundValue objects look like.
        self.__dict__.clear()
        self.__dict__['__values__'] = values

    def __getattr__(self, name):
        # __dict__ is accessed normally here (no custom override)
        values = self.__dict__.get('__values__', {})
        if name in values:
            return values[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        values = self.__dict__.get('__values__')
        if values is not None:
            values[name] = value
        else:
            # During __init__, __dict__ might not have __values__ yet
            object.__setattr__(self, name, value)

    def __contains__(self, name):
        values = self.__dict__.get('__values__', {})
        return name in values

    def __getitem__(self, name):
        values = self.__dict__.get('__values__', {})
        return values[name]

    def __setitem__(self, name, value):
        values = self.__dict__.get('__values__', {})
        values[name] = value


def _zeep_object(mapping, unresolvable=False):
    """Convenience wrapper around ZeepObject."""
    return ZeepObject(mapping, unresolvable=unresolvable)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_polarion():
    """A Polarion instance with every SOAP interaction mocked out.

    Patches ``requests.get``, ``zeep.Client``, and the login flow so that
    ``Polarion.__init__`` succeeds without any network access.
    """
    with patch('polarion.polarion.requests') as mock_requests, \
         patch('polarion.polarion.Client') as MockClient, \
         patch('polarion.polarion.HistoryPlugin') as MockHistory:

        # --- requests.get for _getServices ---------------------------------
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.text = (
            'SessionWebService TrackerWebService ProjectWebService '
            'BuilderWebService PlanningWebService TestManagementWebService '
            'SecurityWebService'
        )
        mock_requests.get.return_value = mock_response
        mock_requests.Session.return_value = MagicMock()

        # --- zeep.Client ---------------------------------------------------
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance

        # logIn should succeed silently
        mock_client_instance.service.logIn.return_value = None

        # history envelope for session header
        mock_envelope = MagicMock()
        mock_session_id = MagicMock()
        mock_envelope.getroottree.return_value.find.return_value = mock_session_id
        MockHistory.return_value.last_received = {'envelope': mock_envelope}

        # get_type should return a callable factory (MagicMock already is)
        mock_client_instance.get_type.return_value = MagicMock()

        # --- Build the Polarion object -------------------------------------
        from polarion.polarion import Polarion
        pol = Polarion('http://polarion.example.com/polarion',
                       'testuser', password='testpass')

        # Expose mocks for assertions in tests
        pol._mock_client = mock_client_instance
        pol._mock_requests = mock_requests
        yield pol


@pytest.fixture()
def mock_project(mock_polarion):
    """A Project instance with mocked polarion_data."""
    project_data = _zeep_object({
        'name': 'Test Project',
        'trackerPrefix': 'TP',
        'id': 'test_project',
    })

    mock_service = MagicMock()
    mock_service.getProject.return_value = project_data

    # Temporarily override getService so Project.__init__ works
    original_get_service = mock_polarion.getService

    def _get_service(name):
        if name == 'Project':
            return mock_service
        return original_get_service(name)

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        from polarion.project import Project
        proj = Project(mock_polarion, 'test_project')

    return proj


@pytest.fixture()
def mock_workitem_data():
    """A sample workitem zeep-style object as returned by the Tracker service."""
    description_obj = MagicMock()
    description_obj.content = '<p>Test description</p>'

    type_obj = MagicMock()
    type_obj.id = 'task'

    status_obj = MagicMock()
    status_obj.id = 'open'

    resolution_obj = MagicMock()
    resolution_obj.id = 'done'

    author_obj = MagicMock()
    author_obj.id = 'testuser'
    author_obj.unresolvable = False

    return _zeep_object({
        'id': 'WI-001',
        'title': 'Test workitem',
        'uri': 'subterra:data-service:objects:/default/test_project${WorkItem}WI-001',
        'description': description_obj,
        'type': type_obj,
        'status': status_obj,
        'resolution': resolution_obj,
        'author': author_obj,
        'assignee': None,
        'approvals': None,
        'attachments': None,
        'linkedWorkItems': None,
        'linkedWorkItemsDerived': None,
        'customFields': None,
        'project': MagicMock(id='test_project'),
        'created': '2024-01-01',
        'updated': '2024-01-02',
        'comments': None,
        'categories': None,
        'hyperlinks': None,
        'priority': None,
        'severity': None,
        'timePoint': None,
        'plannedEnd': None,
        'plannedStart': None,
        'initialEstimate': None,
        'remainingEstimate': None,
        'timeSpent': None,
        'dueDate': None,
        'outlineNumber': None,
        'externallyLinkedWorkItems': None,
        'plannedIn': None,
        'watches': None,
        'moduleURI': None,
        'location': None,
        'previousStatus': None,
    })



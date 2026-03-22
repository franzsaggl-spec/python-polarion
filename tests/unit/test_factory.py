"""Tests for polarion/factory.py."""

import pytest
from unittest.mock import MagicMock, patch

from polarion.factory import _subterraUrl, createFromUri, addCreator, creator_list, Creator
from polarion.exceptions import PolarionFieldError


# ------------------------------------------------------------------
# _subterraUrl
# ------------------------------------------------------------------

class TestSubterraUrl:

    def test_extracts_workitem_type(self):
        uri = 'subterra:data-service:objects:/default/project${WorkItem}WI-001'
        assert _subterraUrl(uri) == 'workitem'

    def test_extracts_testrun_type(self):
        uri = 'subterra:data-service:objects:/default/project${TestRun}TR-001'
        assert _subterraUrl(uri) == 'testrun'

    def test_extracts_user_type(self):
        uri = 'subterra:data-service:objects:/default/${User}admin'
        assert _subterraUrl(uri) == 'user'

    def test_type_is_lowercased(self):
        uri = 'subterra:data-service:objects:/default/project${Module}doc1'
        assert _subterraUrl(uri) == 'module'

    def test_raises_on_non_subterra_scheme(self):
        with pytest.raises(PolarionFieldError, match='Not a subterra uri'):
            _subterraUrl('http://example.com/something')

    def test_raises_on_missing_type_braces(self):
        with pytest.raises(PolarionFieldError, match='not a valid polarion uri'):
            _subterraUrl('subterra:data-service:objects:/default/project/notype')

    def test_raises_on_empty_string(self):
        with pytest.raises(PolarionFieldError):
            _subterraUrl('')


# ------------------------------------------------------------------
# createFromUri
# ------------------------------------------------------------------

class TestCreateFromUri:

    def test_dispatches_to_registered_creator(self):
        """Register a dummy creator and verify createFromUri calls it."""
        mock_polarion = MagicMock()
        mock_project = MagicMock()
        uri = 'subterra:data-service:objects:/default/project${DummyType}123'

        class DummyCreator(Creator):
            def createFromUri(self, polarion, project, uri):
                return 'dummy_result'

        # Register and test
        addCreator('dummytype', DummyCreator)
        try:
            result = createFromUri(mock_polarion, mock_project, uri)
            assert result == 'dummy_result'
        finally:
            # Clean up the global creator_list
            creator_list.pop('dummytype', None)

    def test_raises_not_found_for_unknown_type(self):
        mock_polarion = MagicMock()
        mock_project = MagicMock()
        uri = 'subterra:data-service:objects:/default/project${UnknownWidget}456'

        with pytest.raises(PolarionFieldError, match='not supported'):
            createFromUri(mock_polarion, mock_project, uri)


# ------------------------------------------------------------------
# addCreator
# ------------------------------------------------------------------

class TestAddCreator:

    def test_registers_creator(self):
        class FakeCreator(Creator):
            def createFromUri(self, polarion, project, uri):
                pass

        addCreator('faketype', FakeCreator)
        assert 'faketype' in creator_list
        assert creator_list['faketype'] is FakeCreator
        # Clean up
        creator_list.pop('faketype', None)

    def test_overwrites_existing_creator(self):
        class First(Creator):
            def createFromUri(self, polarion, project, uri):
                pass

        class Second(Creator):
            def createFromUri(self, polarion, project, uri):
                pass

        addCreator('overwrite_test', First)
        addCreator('overwrite_test', Second)
        assert creator_list['overwrite_test'] is Second
        # Clean up
        creator_list.pop('overwrite_test', None)


# ------------------------------------------------------------------
# Default registrations from polarion/__init__.py
# ------------------------------------------------------------------

def test_default_creators_registered():
    """Importing polarion should register the standard creators."""
    import polarion  # noqa: F401 -- triggers addCreator calls in __init__
    for expected in ['workitem', 'testrun', 'user', 'module', 'plan']:
        assert expected in creator_list, f'{expected} not in creator_list'

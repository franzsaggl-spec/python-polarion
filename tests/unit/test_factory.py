"""Tests for polarion/factory.py (v2.0.0 API).

In v2.0.0:
- _subterraUrl -> _parse_subterra_type
- addCreator -> register_creator
- createFromUri -> create_from_uri
- creator_list -> _creator_registry
- Creator.createFromUri -> Creator.create_from_uri
"""

from unittest.mock import MagicMock

import pytest

from polarion.exceptions import PolarionFieldError
from polarion.factory import Creator, _creator_registry, _parse_subterra_type, create_from_uri, register_creator

# ------------------------------------------------------------------
# _parse_subterra_type
# ------------------------------------------------------------------


class TestParseSubterraType:
    def test_extracts_workitem_type(self):
        uri = "subterra:data-service:objects:/default/project${WorkItem}WI-001"
        assert _parse_subterra_type(uri) == "workitem"

    def test_extracts_testrun_type(self):
        uri = "subterra:data-service:objects:/default/project${TestRun}TR-001"
        assert _parse_subterra_type(uri) == "testrun"

    def test_extracts_user_type(self):
        uri = "subterra:data-service:objects:/default/${User}admin"
        assert _parse_subterra_type(uri) == "user"

    def test_type_is_lowercased(self):
        uri = "subterra:data-service:objects:/default/project${Module}doc1"
        assert _parse_subterra_type(uri) == "module"

    def test_raises_on_non_subterra_scheme(self):
        with pytest.raises(PolarionFieldError, match="Not a subterra uri"):
            _parse_subterra_type("http://example.com/something")

    def test_raises_on_missing_type_braces(self):
        with pytest.raises(PolarionFieldError, match="not a valid polarion uri"):
            _parse_subterra_type("subterra:data-service:objects:/default/project/notype")

    def test_raises_on_empty_string(self):
        with pytest.raises(PolarionFieldError):
            _parse_subterra_type("")


# ------------------------------------------------------------------
# create_from_uri
# ------------------------------------------------------------------


class TestCreateFromUri:
    def test_dispatches_to_registered_creator(self):
        """Register a dummy creator and verify create_from_uri calls it."""
        mock_polarion = MagicMock()
        mock_project = MagicMock()
        uri = "subterra:data-service:objects:/default/project${DummyType}123"

        class DummyCreator(Creator):
            def create_from_uri(self, polarion, project, uri):
                return "dummy_result"

        # Register and test
        register_creator("dummytype", DummyCreator)
        try:
            result = create_from_uri(mock_polarion, mock_project, uri)
            assert result == "dummy_result"
        finally:
            # Clean up the global _creator_registry
            _creator_registry.pop("dummytype", None)

    def test_raises_not_found_for_unknown_type(self):
        mock_polarion = MagicMock()
        mock_project = MagicMock()
        uri = "subterra:data-service:objects:/default/project${UnknownWidget}456"

        with pytest.raises(PolarionFieldError, match="not supported"):
            create_from_uri(mock_polarion, mock_project, uri)


# ------------------------------------------------------------------
# register_creator
# ------------------------------------------------------------------


class TestRegisterCreator:
    def test_registers_creator(self):
        class FakeCreator(Creator):
            def create_from_uri(self, polarion, project, uri):
                pass

        register_creator("faketype", FakeCreator)
        assert "faketype" in _creator_registry
        assert _creator_registry["faketype"] is FakeCreator
        # Clean up
        _creator_registry.pop("faketype", None)

    def test_overwrites_existing_creator(self):
        class First(Creator):
            def create_from_uri(self, polarion, project, uri):
                pass

        class Second(Creator):
            def create_from_uri(self, polarion, project, uri):
                pass

        register_creator("overwrite_test", First)
        register_creator("overwrite_test", Second)
        assert _creator_registry["overwrite_test"] is Second
        # Clean up
        _creator_registry.pop("overwrite_test", None)


# ------------------------------------------------------------------
# Default registrations from polarion/__init__.py
# ------------------------------------------------------------------


def test_default_creators_registered():
    """Importing polarion should register the standard creators."""
    import polarion  # noqa: F401 -- triggers register_creator calls in __init__

    for expected in ["workitem", "testrun", "user", "module", "plan"]:
        assert expected in _creator_registry, f"{expected} not in _creator_registry"

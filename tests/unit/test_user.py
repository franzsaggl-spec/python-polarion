"""Tests for the User class."""

import pytest
from unittest.mock import MagicMock, patch

from polarion.user import User
from polarion.exceptions import PolarionNotFoundError


def _make_user_record(**overrides):
    """Create a fake zeep user record using the ZeepObject helper from conftest."""
    from tests.unit.conftest import _zeep_object
    data = {
        'id': 'jdoe',
        'name': 'John Doe',
        'email': 'jdoe@example.com',
        'description': None,
        'avatarUrl': None,
        'disabledNotifications': None,
    }
    data.update(overrides)
    unresolvable = data.pop('unresolvable', False)
    return _zeep_object(data, unresolvable=unresolvable)


# ------------------------------------------------------------------
# Creation from polarion_record
# ------------------------------------------------------------------

def test_creation_from_record(mock_polarion):
    record = _make_user_record()
    user = User(mock_polarion, polarion_record=record)
    assert user.id == 'jdoe'
    assert user.name == 'John Doe'
    assert user.email == 'jdoe@example.com'


def test_creation_copies_all_attributes(mock_polarion):
    record = _make_user_record(id='admin', name='Admin User')
    user = User(mock_polarion, polarion_record=record)
    assert user.id == 'admin'
    assert user.name == 'Admin User'


# ------------------------------------------------------------------
# Creation from URI
# ------------------------------------------------------------------

def test_creation_from_uri(mock_polarion):
    record = _make_user_record(id='uri_user', name='URI User')

    project_service = MagicMock()
    project_service.getUserByUri.return_value = record

    mock_polarion.getService = MagicMock(return_value=project_service)

    user = User(mock_polarion, uri='subterra:data-service:objects:/default/${User}uri_user')
    assert user.id == 'uri_user'
    assert user.name == 'URI User'
    project_service.getUserByUri.assert_called_once()


# ------------------------------------------------------------------
# PolarionNotFoundError on unresolvable
# ------------------------------------------------------------------

def test_raises_not_found_on_unresolvable_record(mock_polarion):
    record = _make_user_record(unresolvable=True)

    with pytest.raises(PolarionNotFoundError, match='User not retrieved'):
        User(mock_polarion, polarion_record=record)


def test_raises_not_found_on_none_record(mock_polarion):
    with pytest.raises(PolarionNotFoundError, match='User not retrieved'):
        User(mock_polarion, polarion_record=None)


# ------------------------------------------------------------------
# __eq__
# ------------------------------------------------------------------

def test_eq_same_id(mock_polarion):
    r1 = _make_user_record(id='same')
    r2 = _make_user_record(id='same')
    u1 = User(mock_polarion, polarion_record=r1)
    u2 = User(mock_polarion, polarion_record=r2)
    assert u1 == u2


def test_eq_different_id(mock_polarion):
    r1 = _make_user_record(id='alice')
    r2 = _make_user_record(id='bob')
    u1 = User(mock_polarion, polarion_record=r1)
    u2 = User(mock_polarion, polarion_record=r2)
    assert u1 != u2


# ------------------------------------------------------------------
# __str__ and __repr__
# ------------------------------------------------------------------

def test_str_format(mock_polarion):
    record = _make_user_record(id='jdoe', name='John Doe')
    user = User(mock_polarion, polarion_record=record)
    assert str(user) == 'John Doe (jdoe)'


def test_repr_format(mock_polarion):
    record = _make_user_record(id='jdoe', name='John Doe')
    user = User(mock_polarion, polarion_record=record)
    assert repr(user) == 'John Doe (jdoe)'


def test_str_equals_repr(mock_polarion):
    record = _make_user_record(id='abc', name='ABC User')
    user = User(mock_polarion, polarion_record=record)
    assert str(user) == repr(user)

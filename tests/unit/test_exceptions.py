"""Tests for the exception hierarchy in polarion/exceptions.py."""

import pytest

from polarion.exceptions import (
    PolarionError,
    PolarionAuthError,
    PolarionNotFoundError,
    PolarionConnectionError,
    PolarionConfigError,
    PolarionApiError,
    PolarionFieldError,
)


ALL_SUBTYPES = [
    PolarionAuthError,
    PolarionNotFoundError,
    PolarionConnectionError,
    PolarionConfigError,
    PolarionApiError,
    PolarionFieldError,
]


# ------------------------------------------------------------------
# Hierarchy checks
# ------------------------------------------------------------------

def test_polarion_error_is_exception():
    assert issubclass(PolarionError, Exception)


@pytest.mark.parametrize("exc_cls", ALL_SUBTYPES)
def test_all_subtypes_inherit_from_polarion_error(exc_cls):
    assert issubclass(exc_cls, PolarionError)


@pytest.mark.parametrize("exc_cls", ALL_SUBTYPES)
def test_all_subtypes_inherit_from_exception(exc_cls):
    assert issubclass(exc_cls, Exception)


# ------------------------------------------------------------------
# Instantiation with message
# ------------------------------------------------------------------

def test_polarion_error_with_message():
    err = PolarionError("base error")
    assert str(err) == "base error"


@pytest.mark.parametrize("exc_cls", ALL_SUBTYPES)
def test_subtype_with_message(exc_cls):
    msg = f"test message for {exc_cls.__name__}"
    err = exc_cls(msg)
    assert str(err) == msg


# ------------------------------------------------------------------
# Catching with base class
# ------------------------------------------------------------------

@pytest.mark.parametrize("exc_cls", ALL_SUBTYPES)
def test_except_polarion_error_catches_subtype(exc_cls):
    with pytest.raises(PolarionError):
        raise exc_cls("caught by base")


def test_except_polarion_error_catches_base():
    with pytest.raises(PolarionError):
        raise PolarionError("base itself")


# ------------------------------------------------------------------
# Each exception class exists as a distinct type
# ------------------------------------------------------------------

def test_exception_classes_are_distinct():
    classes = [PolarionError] + ALL_SUBTYPES
    assert len(set(classes)) == len(classes)


# ------------------------------------------------------------------
# Exception args tuple
# ------------------------------------------------------------------

@pytest.mark.parametrize("exc_cls", [PolarionError] + ALL_SUBTYPES)
def test_exception_args(exc_cls):
    err = exc_cls("arg1", "arg2")
    assert err.args == ("arg1", "arg2")

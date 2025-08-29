"""Tests for brother exceptions."""

import pytest

from brother.exceptions import BrotherError, SnmpError, UnsupportedModelError


def test_brother_error() -> None:
    """Test BrotherError base exception."""
    error_msg = "Test error message"
    error = BrotherError(error_msg)

    assert str(error) == error_msg
    assert error.status == error_msg
    assert isinstance(error, Exception)


def test_snmp_error() -> None:
    """Test SnmpError exception."""
    error_msg = "SNMP connection failed"
    error = SnmpError(error_msg)

    assert str(error) == error_msg
    assert error.status == error_msg
    assert isinstance(error, BrotherError)
    assert isinstance(error, Exception)


def test_unsupported_model_error() -> None:
    """Test UnsupportedModelError exception."""
    error_msg = "Printer model not supported"
    error = UnsupportedModelError(error_msg)

    assert str(error) == error_msg
    assert error.status == error_msg
    assert isinstance(error, BrotherError)
    assert isinstance(error, Exception)


def test_exception_inheritance() -> None:
    """Test exception inheritance hierarchy."""
    # Test that SnmpError can be caught as BrotherError
    with pytest.raises(BrotherError):
        raise SnmpError("test")

    # Test that UnsupportedModelError can be caught as BrotherError
    with pytest.raises(BrotherError):
        raise UnsupportedModelError("test")

    # Test that both inherit from base Exception class
    assert issubclass(SnmpError, Exception)
    assert issubclass(UnsupportedModelError, Exception)
    assert issubclass(BrotherError, Exception)

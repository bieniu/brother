"""Tests for datetime get/set functionality."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pysnmp.error import PySnmpError
from pysnmp.hlapi.v3arch.asyncio import CommunityData, ContextData, SnmpEngine

from brother import Brother, SnmpError

HOST = "localhost"


def _setup_request_args(brother: Brother) -> None:
    """Set up fake _request_args so methods work without real SNMP init."""
    brother._request_args = (
        MagicMock(spec=SnmpEngine),
        CommunityData("public", mpModel=0),
        MagicMock(),
        ContextData(),
    )


@pytest.mark.asyncio
async def test_set_datetime() -> None:
    """Test setting printer datetime via SNMP."""
    brother = Brother(HOST)
    _setup_request_args(brother)

    mock_set = AsyncMock(return_value=(None, 0, 0, []))
    with patch("brother.set_cmd", mock_set):
        dt = datetime(2026, 3, 26, 14, 30, 0, tzinfo=UTC)
        await brother.async_set_datetime(dt)

    mock_set.assert_called_once()
    args = mock_set.call_args
    oid_arg = args[0][-1]
    val = oid_arg._ObjectType__args[1]
    expected = b"\x07\xea\x03\x1a\x0e\x1e\x00\x00"
    assert bytes(val) == expected


@pytest.mark.asyncio
async def test_set_datetime_default_uses_now() -> None:
    """Test that async_set_datetime with no argument uses current time."""
    brother = Brother(HOST)
    _setup_request_args(brother)

    mock_set = AsyncMock(return_value=(None, 0, 0, []))
    with patch("brother.set_cmd", mock_set):
        await brother.async_set_datetime()

    mock_set.assert_called_once()


@pytest.mark.asyncio
async def test_set_datetime_custom_write_community() -> None:
    """Test that write_community parameter is used for SET."""
    brother = Brother(HOST, write_community="private")
    _setup_request_args(brother)

    mock_set = AsyncMock(return_value=(None, 0, 0, []))
    with patch("brother.set_cmd", mock_set):
        await brother.async_set_datetime(datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC))

    call_args = mock_set.call_args[0]
    community_data = call_args[1]
    assert str(community_data.communityName) == "private"


@pytest.mark.asyncio
async def test_set_datetime_snmp_error() -> None:
    """Test that SNMP error indication raises SnmpError."""
    brother = Brother(HOST)
    _setup_request_args(brother)

    mock_set = AsyncMock(return_value=("requestTimedOut", 0, 0, []))
    with patch("brother.set_cmd", mock_set), pytest.raises(SnmpError):
        await brother.async_set_datetime(datetime(2026, 1, 1, tzinfo=UTC))


@pytest.mark.asyncio
async def test_set_datetime_snmp_set_rejected() -> None:
    """Test that SNMP SET rejection raises SnmpError."""
    brother = Brother(HOST)
    _setup_request_args(brother)

    mock_set = AsyncMock(return_value=(None, "notWritable", 1, []))
    with patch("brother.set_cmd", mock_set), pytest.raises(SnmpError):
        await brother.async_set_datetime(datetime(2026, 1, 1, tzinfo=UTC))


@pytest.mark.asyncio
async def test_set_datetime_connection_error() -> None:
    """Test that PySnmpError raises ConnectionError."""
    brother = Brother(HOST)
    _setup_request_args(brother)

    mock_set = AsyncMock(side_effect=PySnmpError("timeout"))
    with patch("brother.set_cmd", mock_set), pytest.raises(ConnectionError):
        await brother.async_set_datetime(datetime(2026, 1, 1, tzinfo=UTC))


@pytest.mark.asyncio
async def test_get_datetime() -> None:
    """Test reading printer datetime via SNMP."""
    brother = Brother(HOST)
    _setup_request_args(brother)

    class FakeVal:
        def asOctets(self) -> bytes:  # noqa: N802
            return b"\x07\xea\x03\x1a\x0e\x1e\x00\x00"

    mock_get = AsyncMock(return_value=(None, 0, 0, [(None, FakeVal())]))
    with patch("brother.get_cmd", mock_get):
        result = await brother.async_get_datetime()

    assert result == datetime(2026, 3, 26, 14, 30, 0)  # noqa: DTZ001


@pytest.mark.asyncio
async def test_get_datetime_not_available() -> None:
    """Test reading datetime when OID is not supported returns None."""
    brother = Brother(HOST)
    _setup_request_args(brother)

    mock_get = AsyncMock(return_value=(None, "noSuchName", 1, []))
    with patch("brother.get_cmd", mock_get):
        result = await brother.async_get_datetime()

    assert result is None


@pytest.mark.asyncio
async def test_get_datetime_snmp_error() -> None:
    """Test that non-noSuchName errors raise SnmpError."""
    brother = Brother(HOST)
    _setup_request_args(brother)

    mock_get = AsyncMock(return_value=(None, "genErr", 1, []))
    with patch("brother.get_cmd", mock_get), pytest.raises(SnmpError):
        await brother.async_get_datetime()


def test_build_dateandtime() -> None:
    """Test DateAndTime encoding."""
    dt = datetime(2026, 3, 26, 14, 30, 45, tzinfo=UTC)
    result = Brother._build_dateandtime(dt)
    assert result == b"\x07\xea\x03\x1a\x0e\x1e\x2d\x00"


def test_build_dateandtime_midnight() -> None:
    """Test DateAndTime encoding at midnight."""
    dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    result = Brother._build_dateandtime(dt)
    assert result == b"\x07\xea\x01\x01\x00\x00\x00\x00"


def test_parse_dateandtime() -> None:
    """Test DateAndTime decoding."""
    raw = b"\x07\xea\x03\x1a\x0e\x1e\x2d\x00"
    result = Brother._parse_dateandtime(raw)
    assert result == datetime(2026, 3, 26, 14, 30, 45)  # noqa: DTZ001


def test_parse_dateandtime_too_short() -> None:
    """Test DateAndTime decoding with too-short data."""
    result = Brother._parse_dateandtime(b"\x07\xea\x03")
    assert result is None


def test_parse_dateandtime_invalid_values() -> None:
    """Test DateAndTime decoding with invalid month/day returns None."""
    raw = b"\x07\xea\x00\x00\x00\x00\x00\x00"
    result = Brother._parse_dateandtime(raw)
    assert result is None


def test_default_write_community() -> None:
    """Test that default write community is 'internal'."""
    brother = Brother(HOST)
    assert brother._write_community == "internal"


def test_custom_write_community() -> None:
    """Test custom write community."""
    brother = Brother(HOST, write_community="private")
    assert brother._write_community == "private"

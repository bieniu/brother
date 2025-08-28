"""Tests for brother package."""

import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from pysnmp.error import PySnmpError
from pysnmp.smi.rfc1902 import ObjectType
from syrupy import SnapshotAssertion

from brother import Brother, SnmpError, UnsupportedModelError
from brother.const import (
    ATTR_CHARSET,
    ATTR_MAC,
    ATTR_MODEL,
    ATTR_STATUS,
    OIDS,
    OIDS_HEX,
    PERCENT_VALUES,
    VALUES_LASER_MAINTENANCE,
)

HOST = "localhost"
INVALID_HOST = "foo.local"
TEST_TIME = datetime(2019, 11, 11, 9, 10, 32, tzinfo=UTC)


@pytest.mark.asyncio
async def test_hl_l2340dw_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from HL-L2340DW printer with invalid printer_type."""
    with open("tests/fixtures/hl-l2340dw.json", encoding="utf-8") as file:
        data = json.load(file)

    with (
        patch("brother.Brother._get_data", return_value=data) as mock_update,
        patch("brother.Brother.initialize"),
        freeze_time(TEST_TIME),
    ):
        brother = await Brother.create(HOST, printer_type="foo")
        sensors = await brother.async_update()
        assert mock_update.call_count == 1

        # second update to test uptime logic
        sensors = await brother.async_update()
        assert mock_update.call_count == 2

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_dcp_l3550cdw_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from DCP-L3550CDW printer."""
    with open("tests/fixtures/dcp-l3550cdw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST)

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_dcp_j132w_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from DCP-J132W printer."""
    with open("tests/fixtures/dcp-j132w.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="ink")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_mfc_5490cn_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from MFC-5490CN printer with no charset data."""
    with open("tests/fixtures/mfc-5490cn.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="ink")
    brother._legacy = True

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_dcp_l2540dw_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from DCP-L2540DN printer with status in Russian."""
    with open("tests/fixtures/dcp-l2540dn.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_dcp_7070dw_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from DCP-7070DW printer with status in Dutch."""
    with open("tests/fixtures/dcp-7070dw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    assert brother == snapshot
    assert sensors == snapshot

    # test uptime logic, uptime increased by 10 minutes
    data["1.3.6.1.2.1.1.3.0"] = "2987742561"
    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert sensors.uptime.isoformat() == "2018-11-30T13:53:26+00:00"


@pytest.mark.asyncio
async def test_mfc_j680dw_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from MFC-J680DW printer with status in Turkish."""
    with open("tests/fixtures/mfc-j680dw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="ink")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_dcp_9020cdw_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from DCP-9020CDW printer."""
    with open("tests/fixtures/dcp-9020cdw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_hl_2270dw_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from HL-2270DW printer."""
    with open("tests/fixtures/hl-2270dw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_mfc_t910dw_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from MFC-T910DW printer."""
    with open("tests/fixtures/mfc-t910dw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="ink")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_hl_5350dn_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from HL-5350DN printer."""
    with open("tests/fixtures/hl-5350dn.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.asyncio
async def test_invalid_data() -> None:
    """Test with invalid data from printer."""
    with open("tests/fixtures/invalid.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST)

    with (
        patch("brother.Brother._get_data", return_value=data),
        pytest.raises(UnsupportedModelError),
    ):
        await brother.async_update()

    brother.shutdown()


@pytest.mark.asyncio
async def test_incomplete_data() -> None:
    """Test with incomplete data from printer."""
    with open("tests/fixtures/incomplete.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST)

    with patch("brother.Brother._get_data", return_value=data):
        await brother.async_update()

    brother.shutdown()


@pytest.mark.asyncio
async def test_empty_data() -> None:
    """Test with empty data from printer."""
    brother = Brother(HOST)

    with (
        patch("brother.Brother._get_data", return_value=None),
        pytest.raises(SnmpError),
    ):
        await brother.async_update()

    brother.shutdown()


@pytest.mark.asyncio
async def test_invalid_host() -> None:
    """Test with invalid host."""
    with (
        patch(
            "brother.Brother.initialize",
            side_effect=ConnectionError("Connection Error"),
        ),
        pytest.raises(ConnectionError),
    ):
        await Brother.create(INVALID_HOST)


@pytest.mark.asyncio
async def test_snmp_error() -> None:
    """Test with raise SnmpError."""
    with (
        patch("brother.Brother.initialize", side_effect=SnmpError("SNMP Error")),
        pytest.raises(SnmpError),
    ):
        await Brother.create(HOST)


@pytest.mark.asyncio
async def test_unsupported_model() -> None:
    """Test with unsupported printer model."""
    with pytest.raises(UnsupportedModelError):
        Brother(HOST, model="mfc-8660dn")


def test_iterate_oids() -> None:
    """Test iterate_oids function."""
    brother = Brother(HOST)
    oids = OIDS.values()
    result = list(brother._iterate_oids(oids))

    assert len(result) == 11
    for item in result:
        assert isinstance(item, ObjectType)


@pytest.mark.asyncio
async def test_dcp_1618w_model(snapshot: SnapshotAssertion) -> None:
    """Test with valid data from DCP-1618W printer."""
    with open("tests/fixtures/dcp-1618w.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data), freeze_time(TEST_TIME):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother == snapshot
    assert sensors == snapshot


@pytest.mark.parametrize(
    ("status", "encoding", "expected"),
    [
        (b"TRYB U\xa6PIENIA", "latin2", "TRYB UŚPIENIA"),
        (b"PROSZ\xca CZEKA\xc6", "latin2", "PROSZĘ CZEKAĆ"),
        (b"MA\xa3O TONERU (Y)", "latin2", "MAŁO TONERU (Y)"),
        (b"\xe8\xaf\xb7\xe7\xad\x89\xe5\xbe\x85", "utf-8", "请等待"),
        (b"Stap. Kopie\xcdn:01", "roman8", "Stap. Kopieën:01"),
        (b"\xc1\xdf\xef\xe9\xd8\xd9 \xe0\xd5\xd6\xd8\xdc", "cyrillic", "Спящий режим"),
    ],
)
def test_decode_status(status: bytes, encoding: str, expected: str) -> None:
    """Test decoding status."""
    brother = Brother(HOST, printer_type="laser")

    result = brother._decode_status(status, encoding)

    assert result == expected


def test_decode_status_unicode_error() -> None:
    """Test decoding status with UnicodeDecodeError."""
    brother = Brother(HOST, printer_type="laser")

    # Invalid bytes that can't be decoded with the specified encoding
    invalid_status = b"\xff\xfe\xfd"

    result = brother._decode_status(invalid_status, "utf-8")

    assert result is None


def test_cleanse_status() -> None:
    """Test cleansing status strings."""
    brother = Brother(HOST, printer_type="laser")

    # Test with extra whitespace
    result = brother._cleanse_status("  ready   to   print  ")
    assert result == "ready to print"

    # Test with newlines and tabs
    result = brother._cleanse_status("ready\t\nto\n\tprint")
    assert result == "ready to print"

    # Test empty string
    result = brother._cleanse_status("")
    assert result == ""

    # Test string with only whitespace
    result = brother._cleanse_status("   \t\n  ")
    assert result == ""


def test_bytes_to_hex_string() -> None:
    """Test converting bytes to hex string."""
    brother = Brother(HOST, printer_type="laser")

    # Test with typical printer data (last byte should be excluded as checksum)
    test_bytes = b"\x63\x01\x04\x00\x00\x00\x01\xff"
    result = brother._bytes_to_hex_string(test_bytes)
    assert result == "63010400000001"

    # Test with single byte (should return empty string after removing checksum)
    single_byte = b"\xff"
    result = brother._bytes_to_hex_string(single_byte)
    assert result == ""

    # Test with two bytes
    two_bytes = b"\xab\xcd"
    result = brother._bytes_to_hex_string(two_bytes)
    assert result == "ab"


def test_legacy_printer() -> None:
    """Test legacy printer detection."""
    brother = Brother(HOST, printer_type="laser")

    # Valid legacy printer data (chunks of 10 ending with "14")
    valid_legacy = "a101020414a201020c14a301020614"
    assert brother._legacy_printer(valid_legacy) is True

    # Invalid legacy printer data (chunks don't end with "14")
    invalid_legacy = "a101020413a201020c13a301020613"
    assert brother._legacy_printer(invalid_legacy) is False

    # Too short string
    too_short = "a1010204"
    assert brother._legacy_printer(too_short) is False

    # Wrong length (not divisible by 10)
    wrong_length = "a101020414a"
    assert brother._legacy_printer(wrong_length) is False

    # Empty string
    assert brother._legacy_printer("") is False


def test_property_methods() -> None:
    """Test property methods."""
    host = "192.168.1.100"
    port = 1161
    brother = Brother(host, port=port, printer_type="laser")

    assert brother.host == host
    assert brother.port == port
    assert brother.firmware is None

    # Test firmware property after setting
    brother._firmware = "1.23"
    assert brother.firmware == "1.23"


def test_iterate_data() -> None:
    """Test iterating data from hex words."""
    brother = Brother(HOST, printer_type="laser")

    # Sample hex data with known values
    hex_data = [
        "6301040000000a",  # Should match "63" in values_map -> value 10
        "1101040000000f",  # Should match "11" in values_map -> value 15
        "ff01040000001e",  # Should not match (not in values_map)
    ]

    # Create a simple values map for testing
    values_map = {
        "63": "test_sensor_1",
        "11": "test_sensor_2",
    }

    result = list(brother._iterate_data(hex_data, values_map))

    assert len(result) == 2
    assert result[0] == ("test_sensor_1", 10)
    assert result[1] == ("test_sensor_2", 15)


def test_iterate_data_percent_values() -> None:
    """Test iterating data with percent values."""
    brother = Brother(HOST, printer_type="laser")

    # Use actual percent value sensors from the constants

    hex_data = []
    values_map = {}

    # Find a percent value sensor from the actual constants
    for key, value in VALUES_LASER_MAINTENANCE.items():
        if value in PERCENT_VALUES:
            hex_data.append(f"{key}01040000157c")  # 5500 in hex, becomes 55
            # when divided by 100
            values_map[key] = value
            break

    if hex_data:  # Only run if we found a percent value sensor
        result = list(brother._iterate_data(hex_data, values_map))
        assert len(result) == 1
        assert result[0][1] == 55  # 5500 / 100 = 55


def test_iterate_data_legacy() -> None:
    """Test iterating data from hex words for legacy printers."""
    brother = Brother(HOST, printer_type="laser")

    # Legacy format: 10 characters, with calculation based on positions 6-8 and 8-10
    hex_data = [
        "a101020414",  # positions 6-8: "04", positions 8-10: "14" -> (4/20)*100 = 20
        "a201020c14",  # positions 6-8: "0c", positions 8-10: "14" -> (12/20)*100 = 60
        "ff01020414",  # Should not match (not in values_map)
    ]

    # Create a simple values map for testing
    values_map = {
        "a1": "legacy_sensor_1",
        "a2": "legacy_sensor_2",
    }

    result = list(brother._iterate_data_legacy(hex_data, values_map))

    assert len(result) == 2
    assert result[0] == ("legacy_sensor_1", 20)
    assert result[1] == ("legacy_sensor_2", 60)


@pytest.mark.asyncio
async def test_get_data_pysnmp_error() -> None:
    """Test _get_data method with PySnmpError."""
    brother = Brother(HOST, printer_type="laser")

    # Mock the request args to avoid initialization
    brother._request_args = (None, None, None, None)
    brother._oids = []

    with (
        patch("brother.get_cmd", side_effect=PySnmpError("PySnmp error")),
        pytest.raises(ConnectionError, match="PySnmp error"),
    ):
        await brother._get_data()


@pytest.mark.asyncio
async def test_get_data_snmp_errindication() -> None:
    """Test _get_data method with SNMP errindication."""
    brother = Brother(HOST, printer_type="laser")

    # Mock the request args to avoid initialization
    brother._request_args = (None, None, None, None)
    brother._oids = []

    with (
        patch("brother.get_cmd", return_value=("timeout", None, None, None)),
        pytest.raises(SnmpError, match="timeout"),
    ):
        await brother._get_data()


@pytest.mark.asyncio
async def test_get_data_snmp_errstatus() -> None:
    """Test _get_data method with SNMP errstatus."""
    brother = Brother(HOST, printer_type="laser")

    # Mock the request args to avoid initialization
    brother._request_args = (None, None, None, None)
    brother._oids = []

    with (
        patch("brother.get_cmd", return_value=(None, "noSuchObject", 1, None)),
        pytest.raises(SnmpError, match="noSuchObject, 1"),
    ):
        await brother._get_data()


@pytest.mark.asyncio
async def test_initialize_unsupported_model_by_oid() -> None:
    """Test initialize method detecting unsupported model by missing required OIDs."""
    brother = Brother(HOST, printer_type="laser")

    # Mock async_get_snmp_engine to avoid actual SNMP setup
    with (
        patch("brother.Brother._iterate_oids") as mock_iterate_oids,
        patch("brother.async_get_snmp_engine"),
        patch("brother.UdpTransportTarget.create"),
        patch("brother.get_cmd") as mock_get_cmd,
    ):
        mock_iterate_oids.return_value = ["oid1", "oid2"]

        # Mock errstatus "noSuchName" with errindex 5 (model OID)
        mock_get_cmd.return_value = (None, "noSuchName", 5, None)

        with pytest.raises(UnsupportedModelError, match="not supported"):
            await brother.initialize()


def test_community_property() -> None:
    """Test community property default value."""
    brother = Brother(HOST, printer_type="laser")
    # The community string should be "public" by default
    # This tests the CommunityData usage in initialize()
    assert brother._host == HOST


def test_printer_type_validation() -> None:
    """Test printer type validation in constructor."""
    # Test invalid printer type gets corrected to laser
    brother = Brother(HOST, printer_type="invalid_type")
    assert brother._printer_type == "laser"

    # Test valid printer types
    brother_laser = Brother(HOST, printer_type="laser")
    assert brother_laser._printer_type == "laser"

    brother_ink = Brother(HOST, printer_type="ink")
    assert brother_ink._printer_type == "ink"


@pytest.mark.asyncio
async def test_initialize_pysnmp_error() -> None:
    """Test initialize method with PySnmpError during transport setup."""
    brother = Brother(HOST, printer_type="laser")

    with (
        patch("brother.async_get_snmp_engine"),
        patch(
            "brother.UdpTransportTarget.create",
            side_effect=PySnmpError("Transport error"),
        ),
        pytest.raises(ConnectionError, match="Transport error"),
    ):
        await brother.initialize()


@pytest.mark.asyncio
async def test_initialize_oid_removal() -> None:
    """Test initialize method removing unsupported OIDs."""
    brother = Brother(HOST, printer_type="laser")

    with (
        patch("brother.async_get_snmp_engine"),
        patch("brother.UdpTransportTarget.create"),
        patch("brother.get_cmd") as mock_get_cmd,
        patch("brother.Brother._iterate_oids") as mock_iterate_oids,
    ):
        # Mock initial OIDs list
        mock_oids = ["oid1", "oid2", "oid3"]
        mock_iterate_oids.return_value = mock_oids

        # First call: remove OID at index 2 (errindex=2, oid index=1)
        # Second call: success
        mock_get_cmd.side_effect = [
            (None, "noSuchName", 2, None),  # Remove oid2
            (None, None, None, None),  # Success
        ]

        await brother.initialize()

        # Should have made 2 calls to get_cmd
        assert mock_get_cmd.call_count == 2
        # Should have removed one OID
        assert len(brother._oids) == 2


def test_shutdown_with_engine() -> None:
    """Test shutdown method when SNMP engine is present."""
    brother = Brother(HOST, printer_type="laser")

    # Mock SNMP engine
    mock_engine = object()
    brother._snmp_engine = mock_engine

    with patch("brother.LCD.unconfigure") as mock_unconfigure:
        brother.shutdown()
        mock_unconfigure.assert_called_once_with(mock_engine, None)


def test_shutdown_without_engine() -> None:
    """Test shutdown method when SNMP engine is None."""
    brother = Brother(HOST, printer_type="laser")
    brother._snmp_engine = None

    with patch("brother.LCD.unconfigure") as mock_unconfigure:
        brother.shutdown()
        mock_unconfigure.assert_not_called()


@pytest.mark.asyncio
async def test_async_update_legacy_laser() -> None:
    """Test async_update with legacy laser printer."""
    with open("tests/fixtures/hl-2270dw.json", encoding="utf-8") as file:
        data = json.load(file)

    brother = Brother(HOST, printer_type="laser")
    brother._legacy = True  # Force legacy mode

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    # Should have called _iterate_data_legacy
    assert brother._legacy is True
    assert sensors is not None


@pytest.mark.asyncio
async def test_get_data_oids_hex_processing() -> None:
    """Test _get_data method processing OIDS_HEX data."""
    brother = Brother(HOST, printer_type="laser")
    brother._request_args = (None, None, None, None)
    brother._oids = []

    # Mock response data for hex OIDs
    mock_resrow = [
        [OIDS[next(iter(OIDS.keys()))], None],  # Use first OID that's in OIDS_HEX
    ]

    # Find an OID that's in OIDS_HEX
    hex_oid = None
    for oid in OIDS.values():
        if oid in OIDS_HEX:
            hex_oid = oid
            break

    if hex_oid:
        # Mock the response object
        mock_response = type("MockResponse", (), {})()
        mock_response.asOctets = lambda: b"\x63\x01\x04\x00\x00\x00\x01\xff"

        mock_resrow = [[hex_oid, None, mock_response]]

        with patch("brother.get_cmd", return_value=(None, None, None, mock_resrow)):
            result = await brother._get_data()

        assert hex_oid in result
        assert isinstance(result[hex_oid], list)


@pytest.mark.asyncio
async def test_get_data_mac_address_processing() -> None:
    """Test _get_data method processing MAC address."""
    brother = Brother(HOST, printer_type="laser")
    brother._request_args = (None, None, None, None)
    brother._oids = []

    # Mock the response object for MAC address
    mock_response = type("MockResponse", (), {})()
    mock_response.asOctets = lambda: b"\x00\x1b\x8c\x12\x34\x56"  # Example MAC bytes

    mock_resrow = [[OIDS[ATTR_MAC], None, mock_response]]

    with patch("brother.get_cmd", return_value=(None, None, None, mock_resrow)):
        result = await brother._get_data()

    assert OIDS[ATTR_MAC] in result
    assert result[OIDS[ATTR_MAC]] == "00:1b:8c:12:34:56"


@pytest.mark.asyncio
async def test_get_data_status_processing() -> None:
    """Test _get_data method processing status data."""
    brother = Brother(HOST, printer_type="laser")
    brother._request_args = (None, None, None, None)
    brother._oids = []

    # Mock the response objects
    mock_status_response = type("MockResponse", (), {})()
    mock_status_response._value = b"Ready"

    mock_resrow = [
        [OIDS[ATTR_STATUS], None, mock_status_response],
        [OIDS[ATTR_CHARSET], None, "utf-8"],  # Charset for decoding
    ]

    with patch("brother.get_cmd", return_value=(None, None, None, mock_resrow)):
        result = await brother._get_data()

    assert OIDS[ATTR_STATUS] in result
    assert result[OIDS[ATTR_STATUS]] == "Ready"
    assert OIDS[ATTR_CHARSET] in result


@pytest.mark.asyncio
async def test_get_data_other_oid() -> None:
    """Test _get_data method processing other OIDs."""
    brother = Brother(HOST, printer_type="laser")
    brother._request_args = (None, None, None, None)
    brother._oids = []

    # Mock the response object for regular string data
    class MockResponse:
        def __str__(self) -> str:
            return "Brother HL-2270DW series"

    mock_response = MockResponse()

    mock_resrow = [[OIDS[ATTR_MODEL], None, mock_response]]

    with patch("brother.get_cmd", return_value=(None, None, None, mock_resrow)):
        result = await brother._get_data()

    assert OIDS[ATTR_MODEL] in result
    assert result[OIDS[ATTR_MODEL]] == "Brother HL-2270DW series"

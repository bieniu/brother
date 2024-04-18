"""Tests for brother package."""

import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from pysnmp.smi.rfc1902 import ObjectType
from syrupy import SnapshotAssertion

from brother import OIDS, Brother, SnmpError, UnsupportedModelError

HOST = "localhost"
INVALID_HOST = "foo.local"
TEST_TIME = datetime(2019, 11, 11, 9, 10, 32, tzinfo=UTC)


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
async def test_incomplete_data() -> None:
    """Test with incomplete data from printer."""
    with open("tests/fixtures/incomplete.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST)

    with patch("brother.Brother._get_data", return_value=data):
        await brother.async_update()

    brother.shutdown()


@pytest.mark.asyncio()
async def test_empty_data() -> None:
    """Test with empty data from printer."""
    brother = Brother(HOST)

    with (
        patch("brother.Brother._get_data", return_value=None),
        pytest.raises(SnmpError),
    ):
        await brother.async_update()

    brother.shutdown()


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
async def test_snmp_error() -> None:
    """Test with raise SnmpError."""
    with (
        patch("brother.Brother.initialize", side_effect=SnmpError("SNMP Error")),
        pytest.raises(SnmpError),
    ):
        await Brother.create(HOST)


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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

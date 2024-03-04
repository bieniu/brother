"""Tests for brother package."""

import json
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from pysnmp.smi.rfc1902 import ObjectType

from brother import OIDS, Brother, SnmpError, UnsupportedModelError

HOST = "localhost"
INVALID_HOST = "foo.local"
TEST_TIME = datetime(2019, 11, 11, 9, 10, 32, tzinfo=UTC)


@pytest.mark.asyncio()
async def test_hl_l2340dw_model() -> None:
    """Test with valid data from HL-L2340DW printer with invalid printer_type."""
    with open("tests/fixtures/hl-l2340dw.json", encoding="utf-8") as file:
        data = json.load(file)

    with (
        patch("brother.Brother._get_data", return_value=data) as mock_update,
        patch("brother.datetime", now=Mock(return_value=TEST_TIME)),
        patch("brother.Brother.initialize"),
    ):
        brother = await Brother.create(HOST, printer_type="foo")
        sensors = await brother.async_update()
        assert mock_update.call_count == 1

        # second update to test uptime logic
        sensors = await brother.async_update()
        assert mock_update.call_count == 2

    brother.shutdown()

    assert brother.host == HOST
    assert brother.port == 161
    assert brother.model == "HL-L2340DW"
    assert brother.mac == "aa:bb:cc:dd:ee:ff"
    assert brother.firmware == "1.17"
    assert brother.serial == "serial_number"
    assert sensors.status == "oczekiwanie"
    assert sensors.black_toner == 80
    assert sensors.page_counter == 986
    assert sensors.uptime.isoformat() == "2019-09-24T12:14:56+00:00"


@pytest.mark.asyncio()
async def test_dcp_l3550cdw_model() -> None:
    """Test with valid data from DCP-L3550CDW printer."""
    with open("tests/fixtures/dcp-l3550cdw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST)

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "DCP-L3550CDW"
    assert brother.firmware == "J1906051424"
    assert brother.serial == "serial_number"
    assert sensors.status == "mało toneru (y)"
    assert sensors.black_toner == 30
    assert sensors.yellow_toner == 10
    assert sensors.magenta_toner == 10
    assert sensors.cyan_toner == 10
    assert sensors.page_counter == 1611


@pytest.mark.asyncio()
async def test_dcp_j132w_model() -> None:
    """Test with valid data from DCP-J132W printer."""
    with open("tests/fixtures/dcp-j132w.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="ink")

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "DCP-J132W"
    assert brother.firmware == "Q1906110144"
    assert brother.serial == "serial_number"
    assert sensors.status == "ready"
    assert sensors.black_ink == 80
    assert sensors.page_counter == 879


@pytest.mark.asyncio()
async def test_mfc_5490cn_model() -> None:
    """Test with valid data from MFC-5490CN printer with no charset data."""
    with open("tests/fixtures/mfc-5490cn.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="ink")
    brother._legacy = True

    with (
        patch("brother.Brother._get_data", return_value=data),
        patch("brother.datetime", now=Mock(return_value=TEST_TIME)),
    ):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "MFC-5490CN"
    assert brother.firmware == "U1005271959VER.E"
    assert brother.serial == "serial_number"
    assert sensors.status == "sleep mode"
    assert sensors.page_counter == 8989
    assert sensors.uptime.isoformat() == "2019-11-02T23:44:02+00:00"


@pytest.mark.asyncio()
async def test_dcp_l2540dw_model() -> None:
    """Test with valid data from DCP-L2540DN printer with status in Russian."""
    with open("tests/fixtures/dcp-l2540dn.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "DCP-L2540DN"
    assert brother.firmware == "R1906110243"
    assert brother.serial == "serial_number"
    assert sensors.status == "спящий режим"
    assert sensors.black_toner_remaining == 55
    assert sensors.page_counter == 333


@pytest.mark.asyncio()
async def test_dcp_7070dw_model() -> None:
    """Test with valid data from DCP-7070DW printer with status in Dutch."""
    with open("tests/fixtures/dcp-7070dw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with (
        patch("brother.Brother._get_data", return_value=data),
        patch("brother.datetime", now=Mock(return_value=TEST_TIME)),
    ):
        sensors = await brother.async_update()

    assert brother.model == "DCP-7070DW"
    assert brother.firmware == "U1307022128VER.J"
    assert brother.serial == "serial_number"
    assert sensors.status == "stap. kopieën:01"
    assert sensors.black_toner_remaining == 72
    assert sensors.page_counter == 2652
    assert sensors.drum_counter == 1603
    assert sensors.drum_remaining_life == 88
    assert sensors.drum_remaining_pages == 10397
    assert sensors.uptime.isoformat() == "2018-11-30T13:43:26+00:00"

    # test uptime logic, uptime increased by 10 minutes
    data["1.3.6.1.2.1.1.3.0"] = "2987742561"
    with (
        patch("brother.Brother._get_data", return_value=data),
        patch("brother.datetime", now=Mock(return_value=TEST_TIME)),
    ):
        sensors = await brother.async_update()

    brother.shutdown()

    assert sensors.uptime.isoformat() == "2018-11-30T13:53:26+00:00"


@pytest.mark.asyncio()
async def test_mfc_j680dw_model() -> None:
    """Test with valid data from MFC-J680DW printer with status in Turkish."""
    with open("tests/fixtures/mfc-j680dw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="ink")

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "MFC-J680DW"
    assert brother.firmware == "U1804191714VER.J"
    assert brother.serial == "serial_number"
    assert sensors.status == "uyku"
    assert sensors.black_ink == 47
    assert sensors.color_counter == 491


@pytest.mark.asyncio()
async def test_dcp_9020cdw_model() -> None:
    """Test with valid data from DCP-9020CDW printer."""
    with open("tests/fixtures/dcp-9020cdw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "DCP-9020CDW"
    assert brother.firmware == "ZA1811191217"
    assert brother.serial == "E71833C4J372261"
    assert sensors.status == "tryb uśpienia"
    assert sensors.cyan_drum_remaining_life == 68
    assert sensors.cyan_drum_counter == 4939
    assert sensors.cyan_drum_remaining_pages == 10061


@pytest.mark.asyncio()
async def test_hl_2270dw_model() -> None:
    """Test with valid data from HL-2270DW printer."""
    with open("tests/fixtures/hl-2270dw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "HL-2270DW"
    assert brother.firmware == "1.16"
    assert brother.serial == "serial_number"
    assert sensors.status == "sleep"
    assert sensors.page_counter == 4191
    assert sensors.drum_remaining_pages == 7809


@pytest.mark.asyncio()
async def test_mfc_t910dw_model() -> None:
    """Test with valid data from MFC-T910DW printer."""
    with open("tests/fixtures/mfc-t910dw.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="ink")

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "MFC-T910DW"
    assert brother.firmware == "M2009041848"
    assert brother.serial == "serial_number"
    assert sensors.status == "oczekiwanie"
    assert sensors.page_counter == 3384
    assert sensors.color_counter == 3199
    assert sensors.bw_counter == 185
    assert sensors.duplex_unit_pages_counter == 1445
    assert sensors.black_ink_status == 1
    assert sensors.cyan_ink_status == 1
    assert sensors.magenta_ink_status == 1
    assert sensors.yellow_ink_status == 1


@pytest.mark.asyncio()
async def test_hl_5350dn_model() -> None:
    """Test with valid data from HL-5350DN printer."""
    with open("tests/fixtures/hl-5350dn.json", encoding="utf-8") as file:
        data = json.load(file)
    brother = Brother(HOST, printer_type="laser")

    with patch("brother.Brother._get_data", return_value=data):
        sensors = await brother.async_update()

    brother.shutdown()

    assert brother.model == "HL-5350DN"
    assert brother.firmware is None
    assert brother.serial == "serial_number"
    assert sensors.status == "energiesparen trommel ersetz."
    assert sensors.page_counter == 69411


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

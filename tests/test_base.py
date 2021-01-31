"""Tests for brother package."""
import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from brother import Brother, SnmpError, UnsupportedModel

HOST = "localhost"
INVALID_HOST = "foo.local"
TEST_TIME = datetime(2019, 11, 11, 9, 10, 32)


@pytest.mark.asyncio
async def test_hl_l2340dw_model():
    """Test with valid data from HL-L2340DW printer with invalid kind."""
    with open("tests/data/hl-l2340dw.json") as file:
        data = json.load(file)
    brother = Brother(HOST, kind="foo")

    with patch("brother.Brother._get_data", return_value=data) as mock_update, patch(
        "brother.datetime", utcnow=Mock(return_value=TEST_TIME)
    ), patch("brother.Brother.initialize"):
        await brother.initialize()
        await brother.async_update()
        assert mock_update.call_count == 1

        # second update to test uptime logic
        await brother.async_update()
        assert mock_update.call_count == 2

    brother.shutdown()

    assert brother.available is True
    assert brother.model == "HL-L2340DW"
    assert brother.firmware == "1.17"
    assert brother.serial == "serial_number"
    assert brother.data["status"] == "oczekiwanie"
    assert brother.data["black_toner"] == 80
    assert brother.data["page_counter"] == 986
    assert brother.data["uptime"].isoformat() == "2019-09-24T12:14:56"


@pytest.mark.asyncio
async def test_dcp_l3550cdw_model():
    """Test with valid data from DCP-L3550CDW printer."""
    with open("tests/data/dcp-l3550cdw.json") as file:
        data = json.load(file)
    brother = Brother(HOST)

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.Brother.initialize"
    ):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is True
    assert brother.model == "DCP-L3550CDW"
    assert brother.firmware == "J1906051424"
    assert brother.serial == "serial_number"
    assert brother.data["status"] == "mało toneru (y)"
    assert brother.data["black_toner"] == 30
    assert brother.data["yellow_toner"] == 10
    assert brother.data["magenta_toner"] == 10
    assert brother.data["cyan_toner"] == 10
    assert brother.data["page_counter"] == 1611


@pytest.mark.asyncio
async def test_dcp_j132w_model():
    """Test with valid data from DCP-J132W printer."""
    with open("tests/data/dcp-j132w.json") as file:
        data = json.load(file)
    brother = Brother(HOST, kind="ink")

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.Brother.initialize"
    ):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is True
    assert brother.model == "DCP-J132W"
    assert brother.firmware == "Q1906110144"
    assert brother.serial == "serial_number"
    assert brother.data["status"] == "ready"
    assert brother.data["black_ink"] == 80
    assert brother.data["page_counter"] == 879


@pytest.mark.asyncio
async def test_mfc_5490cn_model():
    """Test with valid data from MFC-5490CN printer with no charset data."""
    with open("tests/data/mfc-5490cn.json") as file:
        data = json.load(file)
    brother = Brother(HOST, kind="ink")
    brother._legacy = True  # pylint:disable=protected-access

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.datetime", utcnow=Mock(return_value=TEST_TIME)
    ), patch("brother.Brother.initialize"):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is True
    assert brother.model == "MFC-5490CN"
    assert brother.firmware == "U1005271959VER.E"
    assert brother.serial == "serial_number"
    assert brother.data["status"] == "sleep mode"
    assert brother.data["page_counter"] == 8989
    assert brother.data["uptime"].isoformat() == "2019-11-02T23:44:02"


@pytest.mark.asyncio
async def test_dcp_l2540dw_model():
    """Test with valid data from DCP-L2540DN printer with status in Russian."""
    with open("tests/data/dcp-l2540dn.json") as file:
        data = json.load(file)
    brother = Brother(HOST, kind="laser")

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.Brother.initialize"
    ):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is True
    assert brother.model == "DCP-L2540DN"
    assert brother.firmware == "R1906110243"
    assert brother.serial == "serial_number"
    assert brother.data["status"] == "спящий режим"
    assert brother.data["black_toner_remaining"] == 55
    assert brother.data["page_counter"] == 333


@pytest.mark.asyncio
async def test_dcp_7070dw_model():
    """Test with valid data from DCP-7070DW printer with status in Dutch."""
    with open("tests/data/dcp-7070dw.json") as file:
        data = json.load(file)
    brother = Brother(HOST, kind="laser")

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.datetime", utcnow=Mock(return_value=TEST_TIME)
    ), patch("brother.Brother.initialize"):
        await brother.initialize()
        await brother.async_update()

    assert brother.available is True
    assert brother.model == "DCP-7070DW"
    assert brother.firmware == "U1307022128VER.J"
    assert brother.serial == "serial_number"
    assert brother.data["status"] == "stap. kopieën:01"
    assert brother.data["black_toner_remaining"] == 72
    assert brother.data["page_counter"] == 2652
    assert brother.data["drum_counter"] == 1603
    assert brother.data["drum_remaining_life"] == 88
    assert brother.data["drum_remaining_pages"] == 10397
    assert brother.data["uptime"].isoformat() == "2018-11-30T13:43:26"

    # test uptime logic, uptime increased by 10 minutes
    data["1.3.6.1.2.1.1.3.0"] = "2987742561"
    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.datetime", utcnow=Mock(return_value=TEST_TIME)
    ):
        await brother.async_update()

    brother.shutdown()

    assert brother.data["uptime"].isoformat() == "2018-11-30T13:53:26"


@pytest.mark.asyncio
async def test_mfc_j680dw_model():
    """Test with valid data from MFC-J680DW printer with status in Turkish."""
    with open("tests/data/mfc-j680dw.json") as file:
        data = json.load(file)
    brother = Brother(HOST, kind="ink")

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.Brother.initialize"
    ):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is True
    assert brother.model == "MFC-J680DW"
    assert brother.firmware == "U1804191714VER.J"
    assert brother.serial == "serial_number"
    assert brother.data["status"] == "uyku"
    assert brother.data["black_ink"] == 47
    assert brother.data["color_counter"] == 491


@pytest.mark.asyncio
async def test_dcp_9020cdw_model():
    """Test with valid data from DCP-9020CDW printer."""
    with open("tests/data/dcp-9020cdw.json") as file:
        data = json.load(file)
    brother = Brother(HOST, kind="laser")

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.Brother.initialize"
    ):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is True
    assert brother.model == "DCP-9020CDW"
    assert brother.firmware == "ZA1811191217"
    assert brother.serial == "E71833C4J372261"
    assert brother.data["status"] == "tryb uśpienia"
    assert brother.data["cyan_drum_remaining_life"] == 68
    assert brother.data["cyan_drum_counter"] == 4939
    assert brother.data["cyan_drum_remaining_pages"] == 10061


@pytest.mark.asyncio
async def test_hl_2270dw_model():
    """Test with valid data from HL-2270DW printer."""
    with open("tests/data/hl-2270dw.json") as file:
        data = json.load(file)
    brother = Brother(HOST, kind="laser")
    brother._counters = False  # pylint:disable=protected-access

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.Brother.initialize"
    ):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is True
    assert brother.model == "HL-2270DW"
    assert brother.firmware == "1.16"
    assert brother.serial == "serial_number"
    assert brother.data["status"] == "sleep"
    assert brother.data["page_counter"] == 4191
    assert brother.data["drum_remaining_pages"] == 7809


@pytest.mark.asyncio
async def test_invalid_data():
    """Test with invalid data from printer."""
    with open("tests/data/invalid.json") as file:
        data = json.load(file)
    brother = Brother(HOST)

    with patch("brother.Brother._get_data", return_value=data), pytest.raises(
        UnsupportedModel
    ), patch("brother.Brother.initialize"):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()


@pytest.mark.asyncio
async def test_incomplete_data():
    """Test with incomplete data from printer."""
    with open("tests/data/incomplete.json") as file:
        data = json.load(file)
    brother = Brother(HOST)

    with patch("brother.Brother._get_data", return_value=data), patch(
        "brother.Brother.initialize"
    ):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is True


@pytest.mark.asyncio
async def test_empty_data():
    """Test with empty data from printer."""
    brother = Brother(HOST)

    with patch("brother.Brother._get_data", return_value=None), patch(
        "brother.Brother.initialize"
    ):
        await brother.initialize()
        await brother.async_update()

    brother.shutdown()

    assert brother.available is False
    assert brother.model is None
    assert brother.firmware is None
    assert brother.serial is None


@pytest.mark.asyncio
async def test_invalid_host():
    """Test with invalid host."""
    brother = Brother(INVALID_HOST)

    with patch(
        "brother.Brother.initialize", side_effect=ConnectionError("Connection Error")
    ):
        try:
            await brother.initialize()
        except ConnectionError as error:
            assert str(error) == "Connection Error"

    brother.shutdown()


@pytest.mark.asyncio
async def test_snmp_error():
    """Test with raise SnmpError."""
    brother = Brother(HOST)

    with patch("brother.Brother.initialize", side_effect=SnmpError("SNMP Error")):
        try:
            await brother.initialize()
        except SnmpError as error:
            assert str(error.status) == "SNMP Error"

    brother.shutdown()

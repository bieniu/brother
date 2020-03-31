"""Tests for brother package."""
import json

from asynctest import patch
from brother import Brother, SnmpError, UnsupportedModel
from pysnmp.hlapi.asyncore.cmdgen import lcd
import pytest

HOST = "localhost"
INVALID_HOST = "foo.local"


@pytest.mark.asyncio
async def test_hl_l2340dw_model():
    """Test with valid data from HL-L2340DW printer with invalid kind."""
    with open("tests/data/hl-l2340dw.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(HOST, kind="foo")
        await brother.async_update()

        assert brother.available == True
        assert brother.model == "HL-L2340DW"
        assert brother.firmware == "1.17"
        assert brother.serial == "serial_number"
        assert brother.data["status"] == "oczekiwanie"
        assert brother.data["black_toner"] == 80
        assert brother.data["page_counter"] == 986
        assert brother.data["uptime"] == 48


@pytest.mark.asyncio
async def test_dcp_l3550cdw_model():
    """Test with valid data from DCP-L3550CDW printer."""
    with open("tests/data/dcp-l3550cdw.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(HOST)
        await brother.async_update()

        assert brother.available == True
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

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(HOST, kind="ink")
        await brother.async_update()

        assert brother.available == True
        assert brother.model == "DCP-J132W"
        assert brother.firmware == "Q1906110144"
        assert brother.serial == "serial_number"
        assert brother.data["status"] == "tryb uśpienia"
        assert brother.data["black_ink"] == 80
        assert brother.data["page_counter"] == 879


@pytest.mark.asyncio
async def test_dcp_l2540dw_model():
    """Test with valid data from DCP-L2540DN printer with status in Russian."""
    with open("tests/data/dcp-l2540dn.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(HOST, kind="laser")
        await brother.async_update()

        assert brother.available == True
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

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(HOST, kind="laser")
        await brother.async_update()

        assert brother.available == True
        assert brother.model == "DCP-7070DW"
        assert brother.firmware == "U1307022128VER.J"
        assert brother.serial == "serial_number"
        assert brother.data["status"] == "stap. kopieën:01"
        assert brother.data["black_toner_remaining"] == 72
        assert brother.data["page_counter"] == 2652
        assert brother.data["drum_counter"] == 1603
        assert brother.data["drum_remaining_life"] == 88
        assert brother.data["drum_remaining_pages"] == 10397
        assert brother.data["uptime"] == 346


@pytest.mark.asyncio
async def test_mfc_j680dw_model():
    """Test with valid data from MFC-J680DW printer with status in Turkish."""
    with open("tests/data/mfc-j680dw.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(HOST, kind="ink")
        await brother.async_update()

        assert brother.available == True
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

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(HOST, kind="laser")
        await brother.async_update()

        assert brother.available == True
        assert brother.model == "DCP-9020CDW"
        assert brother.firmware == "ZA1811191217"
        assert brother.serial == "E71833C4J372261"
        assert brother.data["status"] == "dvale"
        assert brother.data["cyan_drum_remaining_life"] == 68
        assert brother.data["cyan_drum_counter"] == 4939
        assert brother.data["cyan_drum_remaining_pages"] == 10061


@pytest.mark.asyncio
async def test_invalid_data():
    """Test with invalid data from printer."""
    with open("tests/data/invalid.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data), pytest.raises(
        UnsupportedModel
    ):

        brother = Brother(HOST)
        await brother.async_update()


@pytest.mark.asyncio
async def test_incomplete_data():
    """Test with incomplete data from printer."""
    with open("tests/data/incomplete.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(HOST)
        await brother.async_update()

        assert brother.available == True


@pytest.mark.asyncio
async def test_empty_data():
    """Test with empty data from printer."""
    with patch("brother.Brother._get_data", return_value=None):
        brother = Brother(HOST)
        await brother.async_update()

        assert brother.available == False
        assert brother.model == None
        assert brother.firmware == None
        assert brother.serial == None


@pytest.mark.asyncio
async def test_invalid_host():
    """Test with invalid host."""
    with pytest.raises(ConnectionError):

        brother = Brother(INVALID_HOST)
        await brother.async_update()


@pytest.mark.asyncio
async def test_snmp_error():
    """Test with raise SnmpError."""
    with pytest.raises(SnmpError):

        brother = Brother(HOST)
        await brother.async_update()

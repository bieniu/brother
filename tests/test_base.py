"""Tests for brother package."""
import json

from pysnmp.hlapi.asyncore.cmdgen import lcd

import pytest
from asynctest import patch
from brother import Brother, SnmpError, UnsupportedModel

INVALID_HOST = "localhost"


@pytest.mark.asyncio
async def test_hl_l2340dw_model():
    """Test with valid data from HL-L2340DW printer."""
    with open("tests/data/hl-l2340dw.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(INVALID_HOST)
        await brother.async_update()

        assert brother.available == True
        assert brother.model == "HL-L2340DW"
        assert brother.firmware == "1.17"
        assert brother.serial == "serial_number"
        assert brother.data["status"] == "oczekiwanie"
        assert brother.data["black_toner"] == 80
        assert brother.data["printer_count"] == 986


@pytest.mark.asyncio
async def test_dcp_l3550cdw_model():
    """Test with valid data from DCP-L3550CDW printer."""
    with open("tests/data/dcp-l3550cdw.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(INVALID_HOST)
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
        assert brother.data["printer_count"] == 1611


@pytest.mark.asyncio
async def test_dcp_l2520dw_model():
    """Test with valid data from DCP-L2520DW printer."""
    with open("tests/data/dcp-l2520dw.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(INVALID_HOST)
        await brother.async_update()

        assert brother.available == True
        assert brother.model == "DCP-L2520DW"
        assert brother.firmware == "Q1906110144"
        assert brother.serial == "serial_number"
        assert brother.data["status"] == "tryb uśpienia"
        assert brother.data["black_toner"] == 80
        assert brother.data["printer_count"] == 879


@pytest.mark.asyncio
async def test_invalid_data():
    """Test with invalid data from printer."""
    with open("tests/data/invalid.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data), pytest.raises(
        UnsupportedModel
    ):

        brother = Brother(INVALID_HOST)
        await brother.async_update()


@pytest.mark.asyncio
async def test_incomplete_data():
    """Test with incomplete data from printer."""
    with open("tests/data/incomplete.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):

        brother = Brother(INVALID_HOST)
        await brother.async_update()

        assert brother.available == True


@pytest.mark.asyncio
async def test_empty_data():
    """Test with empty data from printer."""
    with patch("brother.Brother._get_data", return_value=None):
        brother = Brother(INVALID_HOST)
        await brother.async_update()

        assert brother.available == False
        assert brother.model == None
        assert brother.firmware == None
        assert brother.serial == None


@pytest.mark.asyncio
async def test_invalid_host():
    """Test with invalid host."""
    with pytest.raises(SnmpError):

        brother = Brother(INVALID_HOST)
        await brother.async_update()

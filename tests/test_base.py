"""Tests for brother package."""
import json

import pytest
from pysnmp.hlapi.asyncore.cmdgen import lcd

from asynctest import patch
from brother import Brother

HOST = "10.10.10.10"


@pytest.mark.asyncio
async def test_hl_l2340dw_model():
    """Test with valid data from HL-L2340DW printer."""
    with open("tests/data/hl-l2340dw.json") as file:
        data = json.load(file)

    with patch("brother.Brother._get_data", return_value=data):
        brother = Brother(HOST)
        await brother.update()
        lcd.unconfigure(brother.snmp_engine, None)

        assert brother.available == True
        assert brother.model == "HL-L2340DW"
        assert brother.firmware == "1.17"
        assert brother.serial == "serial_number"
        assert brother.data["status"] == "oczekiwanie"
        assert brother.data["black toner"] == 80
        assert brother.data["printer count"] == 986

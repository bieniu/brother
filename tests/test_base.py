"""Tests for brother package."""
import json

from pysnmp.hlapi.asyncore.cmdgen import lcd

from brother import Brother

import pytest
from asynctest import patch

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

        assert brother.model == "HL-L2340DW"
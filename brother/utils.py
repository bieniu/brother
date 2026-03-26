"""Utils for Brother."""

import asyncio
from datetime import datetime

from pysnmp.hlapi.v3arch.asyncio import SnmpEngine
from pysnmp.hlapi.varbinds import MibViewControllerManager

from .const import DATEANDTIME_MIN_LENGTH


async def async_get_snmp_engine() -> SnmpEngine:
    """Get the SNMP engine."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _get_snmp_engine)


def _get_snmp_engine() -> SnmpEngine:
    """Return an instance of SnmpEngine."""
    engine = SnmpEngine()
    # Actually load the MIBs from disk so we do not do it in the event loop
    mib_view_controller = MibViewControllerManager.get_mib_view_controller(engine.cache)
    if "PYSNMP-MIB" not in mib_view_controller.mibBuilder.mibSymbols:
        mib_view_controller.mibBuilder.load_modules()
    engine.cache["mibViewController"] = mib_view_controller

    return engine


def bytes_to_hex_string(data: bytes) -> str:
    """Convert bytes to hex string efficiently, excluding last byte (checksum)."""
    # More efficient than join with list comprehension
    # Remove last 2 characters (last byte in hex) for checksum
    return data[:-1].hex()


def build_dateandtime(dt: datetime) -> bytes:
    """Encode a datetime as an 8-byte SNMP DateAndTime value (RFC 2579)."""
    return (
        dt.year.to_bytes(2, "big")
        + bytes([dt.month, dt.day, dt.hour, dt.minute, dt.second, 0])
    )


def parse_dateandtime(raw: bytes) -> datetime | None:
    """Decode an SNMP DateAndTime value into a naive datetime.

    The 8-byte DateAndTime format carries no timezone offset, so the
    returned datetime is naive and represents the printer's local clock.
    """
    if len(raw) < DATEANDTIME_MIN_LENGTH:
        return None
    year = int.from_bytes(raw[0:2], "big")
    try:
        return datetime(  # noqa: DTZ001
            year, raw[2], raw[3], raw[4], raw[5], raw[6]
        )
    except ValueError:
        return None

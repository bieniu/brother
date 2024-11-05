"""Utils for Brother."""

import asyncio

from pysnmp.hlapi.v3arch.asyncio import SnmpEngine
from pysnmp.hlapi.varbinds import MibViewControllerManager


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

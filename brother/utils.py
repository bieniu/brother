"""Utils for Brother."""

import asyncio

from pysnmp.hlapi.asyncio import SnmpEngine
from pysnmp.hlapi.asyncio.cmdgen import vbProcessor
from pysnmp.smi.builder import MibBuilder


async def async_get_snmp_engine() -> SnmpEngine:
    """Get the SNMP engine."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _get_snmp_engine)


def _get_snmp_engine() -> SnmpEngine:
    """Return an instance of SnmpEngine."""
    engine = SnmpEngine()
    mib_controller = vbProcessor.getMibViewController(engine)
    # Actually load the MIBs from disk so we do
    # not do it in the event loop
    builder: MibBuilder = mib_controller.mibBuilder
    if "PYSNMP-MIB" not in builder.mibSymbols:
        builder.loadModules()

    return engine

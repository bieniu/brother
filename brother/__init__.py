"""
Python wrapper for getting data from Brother laser printers via snmp
"""
import logging

import pysnmp.hlapi.asyncio as hlapi
import sys
from pysnmp.hlapi.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    UsmUserData,
    getCmd,
)

OIDS = {
    "serial": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.1.0",
    "status": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.4.5.2.0",
    "sodel": "1.3.6.1.4.1.2435.2.4.3.2435.5.13.3.0",
    "firmware": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.17.0",
    "counters": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.10.0",
    "maintenance": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0",
    "nextcare": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.11.0",
    "replace": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.20.0",
}

_LOGGER = logging.getLogger(__name__)

class Brother:
    """Main class to perform snmp requests to printer."""

    def __init__(self, host):
        """Initialize."""
        self.data = {}
        self.host = host

    async def update(self):
        """Update data from printer."""


    @property
    def available(self):
        """Return True is data is available."""
        return bool(self.data)


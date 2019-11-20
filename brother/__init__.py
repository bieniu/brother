"""
Python wrapper for getting data from Brother laser and inkjet printers via snmp
"""
import logging

from pyasn1.type.univ import OctetString
import pysnmp.hlapi.asyncio as hlapi
from pysnmp.hlapi.asyncore.cmdgen import lcd
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
    "counters": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.10.0",
    "firmware": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.17.0",
    "maintenance": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0",
    "model": "1.3.6.1.4.1.2435.2.4.3.2435.5.13.3.0",
    "nextcare": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.11.0",
    "replace": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.20.0",
    "serial": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.1.0",
    "status": "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.4.5.2.0",
}

_LOGGER = logging.getLogger(__name__)

class Brother:
    """Main class to perform snmp requests to printer."""

    def __init__(self, host):
        """Initialize."""
        self.data = {}
        self.host = host
        _LOGGER.debug("Using host: %s", host)

        oids_list = []
        for value in OIDS.values():
            oids_list.append(ObjectType(ObjectIdentity(value)))

        self.oids = tuple(oids_list)

        self.SnmpEngine = SnmpEngine()

        self.request_args = [
            self.SnmpEngine,
            CommunityData("public", mpModel=1),
            UdpTransportTarget((host, 161)),
            ContextData(),
        ]

    async def update(self):
        """Update data from printer."""
        temp_data = {}
        errindication, errstatus, errindex, restable = await getCmd(*self.request_args, *self.oids)

        if errindication:
            print(f"SNMP error: {errindication}")
        elif errstatus:
            print(f"SNMP error: {errstatus}, {errindex}")
        else:
            lcd.unconfigure(self.SnmpEngine, None)
            for resrow in restable:
                if isinstance(resrow[-1], OctetString):
                    temp = resrow[-1].asOctets()
                    temp = ''.join(['%.2x' % x for x in temp])[0:-2]
                    temp = [temp[ind:ind+14] for ind in range(0, len(temp), 14)]
                    temp_data[str(resrow[0])] = temp
                else:
                    temp_data[str(resrow[0])] = str(resrow[-1])

        self.data = temp_data


    @property
    def available(self):
        """Return True is data is available."""
        return bool(self.data)


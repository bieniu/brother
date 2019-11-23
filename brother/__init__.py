"""
Python wrapper for getting data from Brother laser and inkjet printers via snmp
"""
import logging

import pysnmp.hlapi.asyncio as hlapi
from pyasn1.type.univ import OctetString
from pysnmp.hlapi.asyncore.cmdgen import lcd

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

HEX_OIDS = [
    "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.10.0",
    "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0",
    "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.11.0",
    "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.20.0",
]

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
            oids_list.append(hlapi.ObjectType(hlapi.ObjectIdentity(value)))

        self.oids = tuple(oids_list)

        self.SnmpEngine = hlapi.SnmpEngine()

        self.request_args = [
            self.SnmpEngine,
            hlapi.CommunityData("public", mpModel=1),
            hlapi.UdpTransportTarget((host, 161)),
            hlapi.ContextData(),
        ]

    async def update(self):
        """Update data from printer."""
        raw_data = await self._get_data()

        data = {}

        data["model"] = raw_data[OIDS["model"]][8:]
        data["serial"] = raw_data[OIDS["serial"]]
        data["status"] = raw_data[OIDS["status"]].strip().lower()
        data["firmware"] = raw_data[OIDS["firmware"]]
        # for key, value in raw_data.items():
        #     if key == '1.3.6.1.4.1.2435.2.4.3.2435.5.13.3.0':
        #         data["model"] = value[8:]
        #     if key == '1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.1.0':
        #         data["serial"] = value
        #     if key == '1.3.6.1.4.1.2435.2.3.9.4.2.1.5.4.5.2.0':
        #         data["status"] = value.strip().lower()
        #     if key == '1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.17.0':
        #         data["firmware"] = value

        self.data = data

    @property
    def available(self):
        """Return True is data is available."""
        return bool(self.data)

    # @property
    # def model(self):
    #     """Return printer's model."""
    #     if self.available:
    #         return self.data["model"]

    # @property
    # def serial(self):
    #     """Return printer's serial no."""
    #     if self.available:
    #         return self.data["serial"]

    # @property
    # def firmware(self):
    #     """Return printer's firmware version."""
    #     if self.available:
    #         return self.data["firmware"]

    # @property
    # def status(self):
    #     """Return printer's status."""
    #     if self.available:
    #         return self.data["status"]

    async def _get_data(self):
        """Retreive data from printer."""
        raw_data = {}

        errindication, errstatus, errindex, restable = await hlapi.getCmd(
            *self.request_args, *self.oids
        )

        if errindication:
            print(f"SNMP error: {errindication}")
        elif errstatus:
            print(f"SNMP error: {errstatus}, {errindex}")
        else:
            lcd.unconfigure(self.SnmpEngine, None)
            for resrow in restable:
                if str(resrow[0]) in HEX_OIDS:
                    temp = resrow[-1].asOctets()
                    temp = "".join(["%.2x" % x for x in temp])[0:-2]
                    temp = [temp[ind : ind + 14] for ind in range(0, len(temp), 14)]
                    raw_data[str(resrow[0])] = temp
                else:
                    raw_data[str(resrow[0])] = str(resrow[-1])
        return raw_data

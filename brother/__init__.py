"""
Python wrapper for getting data from Brother laser and inkjet printers via snmp
"""
import logging

import pysnmp.hlapi.asyncio as hlapi
from pyasn1.type.univ import OctetString
from pysnmp.hlapi.asyncore.cmdgen import lcd

ATTR_COUNTERS = "counters"
ATTR_FIRMWARE = "firmware"
ATTR_MAINTENANCE = "maintenance"
ATTR_MODEL = "model"
ATTR_NEXTCARE = "nextcare"
ATTR_SERIAL = "serial"
ATTR_STATUS = "status"

OIDS = {
    ATTR_COUNTERS: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.10.0",
    ATTR_FIRMWARE: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.17.0",
    ATTR_MAINTENANCE: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0",
    ATTR_MODEL: "1.3.6.1.4.1.2435.2.4.3.2435.5.13.3.0",
    ATTR_NEXTCARE: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.11.0",
    ATTR_SERIAL: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.1.0",
    ATTR_STATUS: "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.4.5.2.0",
}

VALUES_COUNTERS = {
    "00": "printer count",
    "01": "b/w count",
    "02": "color count",
    "12": "black count",
    "13": "cyan count",
    "14": "magenta count",
    "15": "yellow count",
    "16": "image count",
}

VALUES_MAINTENANCE = {
    "11": "drum count",
    "31": "toner status",
    "41": "drum remaining life",
    "63": "drum status",
    "69": "belt unit remaining life",
    "6a": "fuser remaining life",
    "6b": "laser remaining life",
    "6c": "pf kit mp remaining life",
    "6d": "pf kit 1 remaining life",
    "6f": "toner/ink remaining life",
    "81": "black toner/ink",
    "82": "cyan toner/ink",
    "83": "magenta toner/ink",
    "84": "yellow toner/ink",
}

VALUES_NEXTCARE = {
    "73": "laser unit remaining pages",
    "77": "pf kit 1 remaining pages",
    "82": "drum remaining pages",
    "86": "pf kit mp remaining pages",
    "88": "belt unit remaining pages",
    "89": "fuser unit remaining pages",
}

PERCENT_VALUES = [
    "drum remaining life",
    "belt unit remaining life",
    "fuser remaining life",
    "laser remaining life",
    "pf kit mp remaining life",
    "pf kit 1 remaining life",
    "toner/ink remaining life",
]

OIDS_HEX = [OIDS[ATTR_COUNTERS], OIDS[ATTR_MAINTENANCE], OIDS[ATTR_NEXTCARE]]

_LOGGER = logging.getLogger(__name__)


class Brother:
    """Main class to perform snmp requests to printer."""

    def __init__(self, host):
        """Initialize."""
        self.data = {}
        self.available = False
        self.host = host
        _LOGGER.debug("Using host: %s", host)

        self._oids = tuple(self._iterate_oids(OIDS.values()))

        self.snmp_engine = hlapi.SnmpEngine()

        self.request_args = [
            self.snmp_engine,
            hlapi.CommunityData("public", mpModel=1),
            hlapi.UdpTransportTarget((host, 161)),
            hlapi.ContextData(),
        ]

    async def update(self):
        """Update data from printer."""
        raw_data = await self._get_data()

        data = {}

        data[ATTR_MODEL] = raw_data[OIDS[ATTR_MODEL]][8:]
        data[ATTR_SERIAL] = raw_data[OIDS[ATTR_SERIAL]]
        data[ATTR_STATUS] = (
            raw_data[OIDS[ATTR_STATUS]].strip().lower()
        )  # sprawdzić znaki diakrytyczne
        data[ATTR_FIRMWARE] = raw_data[OIDS[ATTR_FIRMWARE]]

        data.update(
            dict(self._iterate_data(raw_data[OIDS[ATTR_COUNTERS]], VALUES_COUNTERS))
        )
        data.update(
            dict(
                self._iterate_data(raw_data[OIDS[ATTR_MAINTENANCE]], VALUES_MAINTENANCE)
            )
        )
        data.update(
            dict(self._iterate_data(raw_data[OIDS[ATTR_NEXTCARE]], VALUES_NEXTCARE))
        )

        self.data = data
        self.available = bool(self.data)

    async def _get_data(self):
        """Retreive data from printer."""
        raw_data = {}

        errindication, errstatus, errindex, restable = await hlapi.getCmd(
            *self.request_args, *self._oids
        )

        if errindication:
            print(f"SNMP error: {errindication}")
        elif errstatus:
            print(f"SNMP error: {errstatus}, {errindex}")
        else:
            for resrow in restable:
                if str(resrow[0]) in OIDS_HEX:
                    temp = resrow[-1].asOctets()
                    temp = "".join(["%.2x" % x for x in temp])[0:-2]
                    temp = [temp[ind : ind + 14] for ind in range(0, len(temp), 14)]
                    raw_data[str(resrow[0])] = temp
                else:
                    raw_data[str(resrow[0])] = str(resrow[-1])
        return raw_data

    @classmethod
    def _iterate_oids(cls, oids):
        """Iterate OIDS to retreive from printer."""
        for oid in oids:
            yield hlapi.ObjectType(hlapi.ObjectIdentity(oid))

    @classmethod
    def _iterate_data(cls, iterable, values_map):
        """Iterate data from hex words."""
        for item in iterable:
            if item[:2] in values_map:
                if values_map[item[:2]] in PERCENT_VALUES:
                    yield (values_map[item[:2]], round(int(item[-8:], 16) / 100))
                else:
                    yield (values_map[item[:2]], int(item[-8:], 16))

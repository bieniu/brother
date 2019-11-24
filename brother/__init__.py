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

OIDS_HEX = [OIDS["counters"], OIDS["maintenance"], OIDS["nextcare"], OIDS["replace"]]

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

        for word in raw_data[OIDS["maintenance"]]:
            if word[:2] == "11":
                data["drum counter"] = int(word[-8:], 16)
            if word[:2] == "63":
                data["drum status"] = int(word[-8:], 16)
            if word[:2] == "41":
                data["drum remaining life"] = round(int(word[-8:], 16) / 100)
            if word[:2] == "31":
                data["toner status"] = int(word[-8:], 16)
            if word[:2] == "69":
                data["belt unit remaining life"] = round(int(word[-8:], 16) / 100)
            if word[:2] == "6a":
                data["fuser remaining life"] = round(int(word[-8:], 16) / 100)
            if word[:2] == "6b":
                data["laser remaining life"] = round(int(word[-8:], 16) / 100)
            if word[:2] == "6c":
                data["pf kit mp remaining life"] = round(int(word[-8:], 16) / 100)
            if word[:2] == "6d":
                data["pf kit 1 remaining life"] = round(int(word[-8:], 16) / 100)
            if word[:2] == "6f":
                data["toner remaining life"] = round(int(word[-8:], 16) / 100)
            if word[:2] == "81":
                data["black toner"] = int(word[-8:], 16)
            if word[:2] == "82":
                data["cyan toner"] = int(word[-8:], 16)
            if word[:2] == "83":
                data["magenta toner"] = int(word[-8:], 16)
            if word[:2] == "84":
                data["yellow toner"] = int(word[-8:], 16)

        for word in raw_data[OIDS["nextcare"]]:
            if word[:2] == "82":
                data["drum remaining pages"] = int(word[-8:], 16)
            if word[:2] == "88":
                data["belt unit remaining pages"] = int(word[-8:], 16)
            if word[:2] == "89":
                data["fuser unit remaining pages"] = int(word[-8:], 16)
            if word[:2] == "73":
                data["laser unit remaining pages"] = int(word[-8:], 16)
            if word[:2] == "86":
                data["pf kit mp remaining pages"] = int(word[-8:], 16)
            if word[:2] == "77":
                data["pf kit 1 remaining pages"] = int(word[-8:], 16)

        for word in raw_data[OIDS["counters"]]:
            if word[:2] == "00":
                data["printer counter"] = int(word[-8:], 16)
            if word[:2] == "01":
                data["b/w page counter"] = int(word[-8:], 16)
            if word[:2] == "02":
                data["color page counter"] = int(word[-8:], 16)
            if word[:2] == "12":
                data["black counter"] = int(word[-8:], 16)
            if word[:2] == "13":
                data["cyan counter"] = int(word[-8:], 16)
            if word[:2] == "14":
                data["magenta counter"] = int(word[-8:], 16)
            if word[:2] == "15":
                data["yellow counter"] = int(word[-8:], 16)
            if word[:2] == "16":
                data["image counter"] = int(word[-8:], 16)

        self.data = data

    @property
    def available(self):
        """Return True is data is available."""
        return bool(self.data)

    @property
    def model(self):
        """Return printer's model."""
        if self.available:
            return self.data["model"]

    @property
    def serial(self):
        """Return printer's serial no."""
        if self.available:
            return self.data["serial"]

    @property
    def firmware(self):
        """Return printer's firmware version."""
        if self.available:
            return self.data["firmware"]

    @property
    def status(self):
        """Return printer's status."""
        if self.available:
            return self.data["status"]

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
                if str(resrow[0]) in OIDS_HEX:
                    temp = resrow[-1].asOctets()
                    temp = "".join(["%.2x" % x for x in temp])[0:-2]
                    temp = [temp[ind : ind + 14] for ind in range(0, len(temp), 14)]
                    raw_data[str(resrow[0])] = temp
                else:
                    raw_data[str(resrow[0])] = str(resrow[-1])
        return raw_data

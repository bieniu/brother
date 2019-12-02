"""
Python wrapper for getting data from Brother laser and inkjet printers via SNMP. Uses
the method of parsing data from: https://github.com/saper-2/BRN-Printer-sCounters-Info
"""
import logging

import pysnmp.hlapi.asyncio as hlapi
from pysnmp.error import PySnmpError
from pysnmp.hlapi.asyncore.cmdgen import lcd

from .const import *

_LOGGER = logging.getLogger(__name__)


class Brother:
    """Main class to perform snmp requests to printer."""

    def __init__(self, host, port=161):
        """Initialize."""
        self.data = {}

        self.firmware = None
        self.model = None
        self.serial = None
        self._host = host
        self._port = port

        self._oids = tuple(self._iterate_oids(OIDS.values()))

        _LOGGER.debug("Using host: %s", host)

    async def async_update(self):
        """Update data from printer."""

        raw_data = await self._get_data()

        if not raw_data:
            return

        data = {}

        try:
            self.model = (
                raw_data[OIDS[ATTR_MODEL]]
                .replace(" series", "")
                .replace("Brother ", "")
            )
            self.serial = raw_data[OIDS[ATTR_SERIAL]]
        except (TypeError, AttributeError):
            raise UnsupportedModel(
                "It seems that this printer model is not supported. Sorry."
            )
        try:
            self.firmware = raw_data[OIDS[ATTR_FIRMWARE]]
            data[ATTR_STATUS] = (
                raw_data[OIDS[ATTR_STATUS]]
                .strip()
                .encode("latin1")
                .decode("iso_8859_2")
                .lower()
            )
        except (TypeError, AttributeError):
            _LOGGER.warning("Incomplete data from printer.")
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

    @property
    def available(self):
        """Return True is data is available."""
        return bool(self.data)

    async def _get_data(self):
        """Retreive data from printer."""
        raw_data = {}
        snmp_engine = hlapi.SnmpEngine()

        try:
            request_args = [
                snmp_engine,
                hlapi.CommunityData("public", mpModel=1),
                hlapi.UdpTransportTarget((self._host, self._port)),
                hlapi.ContextData(),
            ]
            errindication, errstatus, errindex, restable = await hlapi.getCmd(
                *request_args, *self._oids
            )
        except PySnmpError as error:
            _LOGGER.error("Error: %s", error)
            return
        lcd.unconfigure(snmp_engine, None)
        if errindication:
            raise SnmpError(f"SNMP error: {errindication}")
        if errstatus:
            raise SnmpError(f"SNMP error: {errstatus}, {errindex}")
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


class SnmpError(Exception):
    """Raised when SNMP request ended in error."""

    def __init__(self, status):
        """Initialize."""
        super(SnmpError, self).__init__(status)
        self.status = status


class UnsupportedModel(Exception):
    """Raised when no model, serial no, firmware data."""

    def __init__(self, status):
        """Initialize."""
        super(UnsupportedModel, self).__init__(status)
        self.status = status

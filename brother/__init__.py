"""
Python wrapper for getting data from Brother laser and inkjet printers via SNMP. Uses
the method of parsing data from: https://github.com/saper-2/BRN-Printer-sCounters-Info
"""
import logging
import re

import chardet
from pysnmp.error import PySnmpError
import pysnmp.hlapi.asyncio as hlapi
from pysnmp.hlapi.asyncore.cmdgen import lcd

from .const import *

_LOGGER = logging.getLogger(__name__)

REGEX_MODEL_PATTERN = re.compile(r"MDL:(?P<model>[\w\-]+)")


class Brother:  # pylint:disable=too-many-instance-attributes
    """Main class to perform snmp requests to printer."""

    def __init__(self, host, port=161, kind="laser"):
        """Initialize."""
        if kind not in KINDS:
            _LOGGER.warning("Wrong kind argument. 'laser' was used.")
            self._kind = "laser"
        else:
            self._kind = kind
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
            self.data = {}
            return

        _LOGGER.debug("RAW data: %s", raw_data)

        data = {}

        try:
            self.model = re.search(
                REGEX_MODEL_PATTERN, raw_data[OIDS[ATTR_MODEL]]
            ).group("model")
            data[ATTR_MODEL] = self.model
            self.serial = raw_data[OIDS[ATTR_SERIAL]]
            data[ATTR_SERIAL] = self.serial
        except (TypeError, AttributeError):
            raise UnsupportedModel(
                "It seems that this printer model is not supported. Sorry."
            )
        try:
            self.firmware = raw_data[OIDS[ATTR_FIRMWARE]]
            data[ATTR_FIRMWARE] = self.firmware
            code_page = chardet.detect(raw_data[OIDS[ATTR_STATUS]].encode("latin1"))[
                "encoding"
            ]
            # chardet detects Polish as ISO-8859-1 but Polish should use ISO-8859-2
            if code_page == "ISO-8859-1":
                data[ATTR_STATUS] = (
                    raw_data[OIDS[ATTR_STATUS]]
                    .strip()
                    .encode("latin1")
                    .decode("iso_8859_2")
                    .lower()
                )
            else:
                data[ATTR_STATUS] = (
                    raw_data[OIDS[ATTR_STATUS]]
                    .strip()
                    .encode("latin1")
                    .decode(code_page)
                    .lower()
                )
        except (AttributeError, KeyError, TypeError):
            _LOGGER.debug("Incomplete data from printer.")
        if raw_data.get(OIDS[ATTR_PAGE_COUNT]):
            data[ATTR_PAGE_COUNT] = raw_data.get(OIDS[ATTR_PAGE_COUNT])
        try:
            data[ATTR_UPTIME] = round(int(raw_data.get(OIDS[ATTR_UPTIME])) / 8640000)
        except TypeError:
            pass
        if self._kind == "laser":
            data.update(
                dict(self._iterate_data(raw_data[OIDS[ATTR_COUNTERS]], VALUES_COUNTERS))
            )
            data.update(
                dict(
                    self._iterate_data(
                        raw_data[OIDS[ATTR_MAINTENANCE]], VALUES_LASER_MAINTENANCE
                    )
                )
            )
            data.update(
                dict(
                    self._iterate_data(
                        raw_data[OIDS[ATTR_NEXTCARE]], VALUES_LASER_NEXTCARE
                    )
                )
            )
        if self._kind == "ink":
            data.update(
                dict(self._iterate_data(raw_data[OIDS[ATTR_COUNTERS]], VALUES_COUNTERS))
            )
            data.update(
                dict(
                    self._iterate_data(
                        raw_data[OIDS[ATTR_MAINTENANCE]], VALUES_INK_MAINTENANCE
                    )
                )
            )

        _LOGGER.debug("Data: %s", data)
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
                hlapi.CommunityData("public", mpModel=0),
                hlapi.UdpTransportTarget(
                    (self._host, self._port), timeout=2, retries=10
                ),
                hlapi.ContextData(),
            ]
            errindication, errstatus, errindex, restable = await hlapi.getCmd(
                *request_args, *self._oids
            )
            # unconfigure SNMP engine
            lcd.unconfigure(snmp_engine, None)
        except PySnmpError as error:
            self.data = {}
            raise ConnectionError(error)
        if errindication:
            self.data = {}
            raise SnmpError(errindication)
        if errstatus:
            self.data = {}
            raise SnmpError(f"{errstatus}, {errindex}")
        for resrow in restable:
            if str(resrow[0]) in OIDS_HEX:
                # asOctet gives bytes data b'\x00\x01\x04\x00\x00\x03\xf6\xff'
                temp = resrow[-1].asOctets()
                # convert to string without checksum FF at the end, gives 000104000003f6
                temp = "".join(["%.2x" % x for x in temp])[0:-2]
                # split to 14 digits words in list, gives ['000104000003f6']
                temp = [temp[ind : ind + 14] for ind in range(0, len(temp), 14)]
                # map sensors names to OIDs
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
            # first byte means kind of sensor, last 4 bytes means value
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

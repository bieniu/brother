"""
Python wrapper for getting data from Brother laser and inkjet printers via SNMP. Uses
the method of parsing data from: https://github.com/saper-2/BRN-Printer-sCounters-Info
"""
import logging

import pysnmp.hlapi.asyncio as hlapi
from pysnmp.error import PySnmpError
from pysnmp.hlapi.asyncore.cmdgen import lcd

ATTR_COUNTERS = "counters"
ATTR_FIRMWARE = "firmware"
ATTR_MAINTENANCE = "maintenance"
ATTR_MODEL = "model"
ATTR_NEXTCARE = "nextcare"
ATTR_SERIAL = "serial"
ATTR_STATUS = "status"

VAL_BW_COUNT = "b/w_count"
VAL_BELT_REMAIN = "belt_unit_remaining_life"
VAL_BELT_REMAIN_PAGES = "belt_unit_remaining_pages"
VAL_BLACK_COUNT = "black_count"
VAL_BLACK_TONER = "black_toner"
VAL_BLACK_TONER_REMAIN = "black_toner_remaining"
VAL_BLACK_TONER_STATUS = "black_toner_status"
VAL_COLOR_COUNT = "color_count"
VAL_CYAN_COUNT = "cyan_count"
VAL_CYAN_TONER = "cyan_toner"
VAL_CYAN_TONER_REMAIN = "cyan_toner_remaining"
VAL_DRUM_COUNT = "drum_count"
VAL_DRUM_REMAIN = "drum_remaining_life"
VAL_DRUM_REMAIN_PAGES = "drum_remaining_pages"
VAL_DRUM_STATUS = "drum_status"
VAL_FUSER_REMAIN = "fuser_remaining_life"
VAL_FUSER_REMAIN_PAGES = "fuser_unit_remaining_pages"
VAL_IMAGE_COUNT = "image_count"
VAL_LASER_REMAIN = "laser_remaining_life"
VAL_LASER_REMAIN_PAGES = "laser_unit_remaining_pages"
VAL_MAGENTA_COUNT = "magenta_count"
VAL_MAGENTA_TONER = "magenta_toner"
VAL_MAGENTA_TONER_REMAIN = "magenta_toner_remaining"
VAL_PF_1_REMAIN = "pf_kit_1_remaining_life"
VAL_PF_1_REMAIN_PAGES = "pf_kit_1_remaining_pages"
VAL_PF_MP_REMAIN = "pf_kit_mp_remaining_life"
VAL_PF_MP_REMAIN_PAGES = "pf_kit_mp_remaining_pages"
VAL_PRINTER_COUNT = "printer_count"
VAL_YELLOW_COUNT = "yellow_count"
VAL_YELLOW_TONER = "yellow_toner"
VAL_YELLOW_TONER_REMAIN = "yellow_toner_remaining"

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
    "00": VAL_PRINTER_COUNT,
    "01": VAL_BW_COUNT,
    "02": VAL_COLOR_COUNT,
    "12": VAL_BLACK_COUNT,
    "13": VAL_CYAN_COUNT,
    "14": VAL_MAGENTA_COUNT,
    "15": VAL_YELLOW_COUNT,
    "16": VAL_IMAGE_COUNT,
}

VALUES_MAINTENANCE = {
    "11": VAL_DRUM_COUNT,
    "31": VAL_BLACK_TONER_STATUS,
    "41": VAL_DRUM_REMAIN,
    "63": VAL_DRUM_STATUS,
    "69": VAL_BELT_REMAIN,
    "6a": VAL_FUSER_REMAIN,
    "6b": VAL_LASER_REMAIN,
    "6c": VAL_PF_MP_REMAIN,
    "6d": VAL_PF_1_REMAIN,
    "6f": VAL_BLACK_TONER_REMAIN,
    "70": VAL_CYAN_TONER_REMAIN,
    "71": VAL_MAGENTA_TONER_REMAIN,
    "72": VAL_YELLOW_TONER_REMAIN,
    "81": VAL_BLACK_TONER,
    "82": VAL_CYAN_TONER,
    "83": VAL_MAGENTA_TONER,
    "84": VAL_YELLOW_TONER,
}

VALUES_NEXTCARE = {
    "73": VAL_LASER_REMAIN_PAGES,
    "77": VAL_PF_1_REMAIN_PAGES,
    "82": VAL_DRUM_REMAIN_PAGES,
    "86": VAL_PF_MP_REMAIN_PAGES,
    "88": VAL_BELT_REMAIN_PAGES,
    "89": VAL_FUSER_REMAIN_PAGES,
}

PERCENT_VALUES = [
    VAL_BELT_REMAIN,
    VAL_DRUM_REMAIN,
    VAL_FUSER_REMAIN,
    VAL_LASER_REMAIN,
    VAL_PF_1_REMAIN,
    VAL_PF_MP_REMAIN,
    VAL_BLACK_TONER_REMAIN,
    VAL_CYAN_TONER_REMAIN,
    VAL_MAGENTA_TONER_REMAIN,
    VAL_YELLOW_TONER_REMAIN,
]

OIDS_HEX = [OIDS[ATTR_COUNTERS], OIDS[ATTR_MAINTENANCE], OIDS[ATTR_NEXTCARE]]

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

    async def update(self):
        """Update data from printer."""

        raw_data = await self._get_data()

        if not raw_data:
            return

        data = {}

        try:
            self.model = raw_data[OIDS[ATTR_MODEL]][8:].replace(" series", "")
            self.serial = raw_data[OIDS[ATTR_SERIAL]]
        except TypeError:
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

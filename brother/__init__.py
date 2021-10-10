"""
Python wrapper for getting data from Brother laser and inkjet printers via SNMP. Uses
the method of parsing data from: https://github.com/saper-2/BRN-Printer-sCounters-Info
"""
from __future__ import annotations

import logging
import re
from collections.abc import Generator, Iterable
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import pysnmp.hlapi.asyncio as hlapi
from pysnmp.error import PySnmpError
from pysnmp.hlapi.asyncio.cmdgen import lcd

from .const import (
    ATTR_CHARSET,
    ATTR_COUNTERS,
    ATTR_FIRMWARE,
    ATTR_MAINTENANCE,
    ATTR_MODEL,
    ATTR_NEXTCARE,
    ATTR_PAGE_COUNT,
    ATTR_SERIAL,
    ATTR_STATUS,
    ATTR_UPTIME,
    CHARSET_MAP,
    KINDS,
    OIDS,
    OIDS_HEX,
    OIDS_WITHOUT_COUNTERS,
    PERCENT_VALUES,
    UNSUPPORTED_MODELS,
    VALUES_COUNTERS,
    VALUES_INK_MAINTENANCE,
    VALUES_LASER_MAINTENANCE,
    VALUES_LASER_NEXTCARE,
)

_LOGGER = logging.getLogger(__name__)

REGEX_MODEL_PATTERN = re.compile(r"MDL:(?P<model>[\w\-]+)")


class DictToObj(dict):
    """Dictionary to object class."""

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise AttributeError("No such attribute: " + name)


class Brother:
    """Main class to perform snmp requests to printer."""

    def __init__(
        self,
        host: str,
        port: int = 161,
        kind: str = "laser",
        snmp_engine: hlapi.SnmpEngine = None,
        model: str | None = None,
    ) -> None:
        """Initialize."""
        if model:
            _LOGGER.debug("model: %s", model)
            for unsupported_model in UNSUPPORTED_MODELS:
                if unsupported_model in model.lower():
                    raise UnsupportedModel(
                        "It seems that this printer model is not supported"
                    )

        if kind not in KINDS:
            _LOGGER.warning("Wrong kind argument, 'laser' was used")
            self._kind = "laser"
        else:
            self._kind = kind

        self._legacy = False

        self.firmware = None
        self.model = None
        self.serial = None
        self._host = host
        self._port = port
        self._last_uptime: datetime | None = None
        self._snmp_engine = snmp_engine
        self._need_init = True
        self._counters = True
        self._oids = tuple(self._iterate_oids(OIDS.values()))

        _LOGGER.debug("Using host: %s", host)

    async def async_update(self) -> DictToObj:
        """Update data from printer."""
        if not (raw_data := await self._get_data()):
            raise SnmpError("The printer did not return data")

        _LOGGER.debug("RAW data: %s", raw_data)

        data = DictToObj({})

        try:
            self.model = re.search(  # type: ignore[union-attr]
                REGEX_MODEL_PATTERN, raw_data[OIDS[ATTR_MODEL]]
            ).group("model")
            data[ATTR_MODEL] = self.model
            self.serial = raw_data[OIDS[ATTR_SERIAL]]
            data[ATTR_SERIAL] = self.serial
        except (TypeError, AttributeError) as err:
            raise UnsupportedModel(
                "It seems that this printer model is not supported"
            ) from err
        try:
            self.firmware = raw_data[OIDS[ATTR_FIRMWARE]]
            data[ATTR_FIRMWARE] = self.firmware

            # If no charset data from the printer use roman8 as default
            if raw_data.get(OIDS[ATTR_CHARSET]) in CHARSET_MAP:
                charset = CHARSET_MAP[raw_data[OIDS[ATTR_CHARSET]]]
            else:
                charset = "roman8"

            data[ATTR_STATUS] = (
                raw_data[OIDS[ATTR_STATUS]]
                .strip()
                .encode("latin1")
                .decode(charset)
                .lower()
            )
        except (AttributeError, KeyError, TypeError):
            _LOGGER.debug("Incomplete data from printer")
        try:
            uptime = int(cast(str, raw_data.get(OIDS[ATTR_UPTIME]))) / 100
        except TypeError:
            pass
        else:
            if self._last_uptime:
                new_uptime = (datetime.utcnow() - timedelta(seconds=uptime)).replace(
                    microsecond=0, tzinfo=timezone.utc
                )
                if abs((new_uptime - self._last_uptime).total_seconds()) > 5:
                    data[ATTR_UPTIME] = self._last_uptime = new_uptime
                else:
                    data[ATTR_UPTIME] = self._last_uptime
            else:
                data[ATTR_UPTIME] = self._last_uptime = (
                    datetime.utcnow() - timedelta(seconds=uptime)
                ).replace(microsecond=0, tzinfo=timezone.utc)
        if self._legacy:
            if self._kind == "laser":
                data.update(
                    dict(
                        self._iterate_data_legacy(
                            raw_data[OIDS[ATTR_MAINTENANCE]], VALUES_LASER_MAINTENANCE
                        )
                    )
                )
            if self._kind == "ink":
                data.update(
                    dict(
                        self._iterate_data_legacy(
                            raw_data[OIDS[ATTR_MAINTENANCE]], VALUES_INK_MAINTENANCE
                        )
                    )
                )
        else:
            if self._kind == "laser":
                if self._counters:
                    data.update(
                        dict(
                            self._iterate_data(
                                raw_data[OIDS[ATTR_COUNTERS]], VALUES_COUNTERS
                            )
                        )
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
                if self._counters:
                    data.update(
                        dict(
                            self._iterate_data(
                                raw_data[OIDS[ATTR_COUNTERS]], VALUES_COUNTERS
                            )
                        )
                    )
                data.update(
                    dict(
                        self._iterate_data(
                            raw_data[OIDS[ATTR_MAINTENANCE]], VALUES_INK_MAINTENANCE
                        )
                    )
                )
        # page counter for old printer models
        with suppress(ValueError):
            if not data.get(ATTR_PAGE_COUNT) and raw_data.get(OIDS[ATTR_PAGE_COUNT]):
                data[ATTR_PAGE_COUNT] = int(
                    cast(str, raw_data.get(OIDS[ATTR_PAGE_COUNT]))
                )

        _LOGGER.debug("Data: %s", data)
        return data

    def shutdown(self) -> None:
        """Unconfigure SNMP engine."""
        if self._snmp_engine:
            lcd.unconfigure(self._snmp_engine, None)

    async def _get_data(self) -> dict[str, Any]:
        """Retreive data from printer."""
        raw_data = {}

        if not self._snmp_engine:
            self._snmp_engine = hlapi.SnmpEngine()

        if self._need_init:
            await self._init_device()

        try:
            request_args = [
                self._snmp_engine,
                hlapi.CommunityData("public", mpModel=0),
                hlapi.UdpTransportTarget(
                    (self._host, self._port), timeout=2, retries=10
                ),
                hlapi.ContextData(),
            ]
            errindication, errstatus, errindex, restable = await hlapi.getCmd(
                *request_args, *self._oids
            )
        except PySnmpError as err:
            raise ConnectionError(err) from err
        if errindication:
            raise SnmpError(errindication)
        if errstatus:
            raise SnmpError(f"{errstatus}, {errindex}")
        for resrow in restable:
            if str(resrow[0]) in OIDS_HEX:
                # asOctets() gives bytes data b'c\x01\x04\x00\x00\x00\x01\x11\x01\x04\x00\
                # x00\x05,A\x01\x04\x00\x00"\xc41\x01\x04\x00\x00\x00\x01o\x01\x04\x00\
                # x00\x19\x00\x81\x01\x04\x00\x00\x00F\x86\x01\x04\x00\x00\x00\n\xff'
                temp = resrow[-1].asOctets()
                # convert to string without checksum FF at the end, gives
                # '630104000000011101040000052c410104000022c4310104000000016f01040000190
                #  0810104000000468601040000000a'
                temp = "".join(["%.2x" % x for x in temp])[0:-2]
                # split to 14 digits words in list, gives ['63010400000001',
                # '1101040000052c', '410104000022c4', '31010400000001',
                # '6f010400001900', '81010400000046', '8601040000000a']
                temp = [temp[ind : ind + 14] for ind in range(0, len(temp), 14)]
                # map sensors names to OIDs
                raw_data[str(resrow[0])] = temp
            else:
                raw_data[str(resrow[0])] = str(resrow[-1])
        # for legacy printers
        for resrow in restable:
            if str(resrow[0]) == OIDS[ATTR_MAINTENANCE]:
                # asOctets() gives bytes data
                temp = resrow[-1].asOctets()
                # convert to string without checksum FF at the end, gives
                # 'a101020414a201020c14a301020614a401020b14'
                temp = "".join(["%.2x" % x for x in temp])[0:-2]
                if self._legacy_printer(temp):
                    self._legacy = True
                    # split to 10 digits words in list, gives ['a101020414',
                    # 'a201020c14', 'a301020614', 'a401020b14']
                    temp = [temp[ind : ind + 10] for ind in range(0, len(temp), 10)]
                    # map sensors names to OIDs
                    raw_data[str(resrow[0])] = temp
                    break
        return raw_data

    async def _init_device(self) -> None:
        """Check if the device sends counters."""
        oids = tuple(self._iterate_oids(OIDS.values()))
        try:
            request_args = [
                self._snmp_engine,
                hlapi.CommunityData("public", mpModel=0),
                hlapi.UdpTransportTarget(
                    (self._host, self._port), timeout=2, retries=10
                ),
                hlapi.ContextData(),
            ]
        except PySnmpError as err:
            raise ConnectionError(err) from err
        errindication, errstatus, errindex, _ = await hlapi.getCmd(*request_args, *oids)
        if errindication:
            raise SnmpError(errindication)
        if errstatus:
            oids = tuple(self._iterate_oids(OIDS_WITHOUT_COUNTERS.values()))
            errindication, errstatus, errindex, _ = await hlapi.getCmd(
                *request_args, *oids
            )
            if errindication:
                raise SnmpError(errindication)
            if errstatus:
                raise SnmpError(f"{errstatus}, {errindex}")
            _LOGGER.debug("The printer %s doesn't send 'counters'", self._host)
            self._counters = False
            self._oids = oids
        self._need_init = False

    @classmethod
    def _legacy_printer(cls, string: str) -> bool:
        """Return True if printer is legacy."""
        length = len(string)
        nums = [x * 10 for x in range(length // 10)][1:]
        if results := [string[i - 2 : i] == "14" for i in nums]:
            return all(item for item in results)
        return False

    @classmethod
    def _iterate_oids(cls, oids: Iterable) -> Generator:
        """Iterate OIDS to retreive from printer."""
        for oid in oids:
            yield hlapi.ObjectType(hlapi.ObjectIdentity(oid))

    @classmethod
    def _iterate_data(cls, iterable: Iterable, values_map: dict) -> Generator:
        """Iterate data from hex words."""
        for item in iterable:
            # first byte means kind of sensor, last 4 bytes means value
            if item[:2] in values_map:
                if values_map[item[:2]] in PERCENT_VALUES:
                    yield (values_map[item[:2]], round(int(item[-8:], 16) / 100))
                else:
                    yield (values_map[item[:2]], int(item[-8:], 16))

    @classmethod
    def _iterate_data_legacy(cls, iterable: Iterable, values_map: dict) -> Generator:
        """Iterate data from hex words for legacy printers."""
        for item in iterable:
            # first byte means kind of sensor, last 4 bytes means value
            if item[:2] in values_map:
                yield (
                    values_map[item[:2]],
                    round(int(item[6:8], 16) / int(item[8:10], 16) * 100),
                )


class SnmpError(Exception):
    """Raised when SNMP request ended in error."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class UnsupportedModel(Exception):
    """Raised when no model, serial no, firmware data."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status

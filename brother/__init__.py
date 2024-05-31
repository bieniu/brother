"""Python wrapper for getting data from Brother laser and inkjet printers via SNMP."""

import logging
import re
from asyncio import timeout
from collections.abc import Generator, Iterable
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Self, cast

from dacite import from_dict
from pysnmp.error import PySnmpError
from pysnmp.hlapi.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
)
from pysnmp.hlapi.asyncio.cmdgen import lcd
from pysnmp.smi.rfc1902 import ObjectType

from .const import (
    ATTR_CHARSET,
    ATTR_COUNTERS,
    ATTR_FIRMWARE,
    ATTR_MAC,
    ATTR_MAINTENANCE,
    ATTR_MODEL,
    ATTR_NEXTCARE,
    ATTR_PAGE_COUNT,
    ATTR_SERIAL,
    ATTR_STATUS,
    ATTR_UPTIME,
    CHARSET_MAP,
    DEFAULT_TIMEOUT,
    OIDS,
    OIDS_HEX,
    PERCENT_VALUES,
    PRINTER_TYPES,
    RETRIES,
    UNSUPPORTED_MODELS,
    UPTIME_FLUCTUATION_SECONDS,
    VALUES_COUNTERS,
    VALUES_INK_MAINTENANCE,
    VALUES_LASER_MAINTENANCE,
    VALUES_LASER_NEXTCARE,
)
from .exceptions import SnmpError, UnsupportedModelError
from .model import BrotherSensors
from .utils import async_get_snmp_engine

_LOGGER = logging.getLogger(__name__)

REGEX_MODEL_PATTERN = re.compile(r"MDL:(?P<model>[\w\-]+)")
CHUNK_SIZE = 14
LEGACY_CHUNK_SIZE = 10


class Brother:
    """Main class to perform snmp requests to printer."""

    def __init__(
        self,
        host: str,
        port: int = 161,
        printer_type: str = "laser",
        model: str | None = None,
        snmp_engine: SnmpEngine = None,
    ) -> None:
        """Initialize."""
        if model and any(
            unsupported_model in model.lower()
            for unsupported_model in UNSUPPORTED_MODELS
        ):
            _LOGGER.debug("Model: %s", model)
            raise UnsupportedModelError(
                "It seems that this printer model is not supported"
            )

        if printer_type not in PRINTER_TYPES:
            _LOGGER.warning("Wrong printer_type argument, 'laser' was used")
            self._printer_type = "laser"
        else:
            self._printer_type = printer_type

        self._legacy = False

        self._firmware: str | None = None
        self.model: str
        self.serial: str
        self.mac: str
        self._host = host
        self._port = port
        self._last_uptime: datetime | None = None
        self._snmp_engine = snmp_engine
        self._oids: list[ObjectType] = []
        self._request_args: tuple[
            SnmpEngine, CommunityData, UdpTransportTarget, ContextData
        ]

    @property
    def firmware(self) -> str | None:
        """Return firmware version."""
        return self._firmware

    @property
    def host(self) -> str:
        """Return host."""
        return self._host

    @property
    def port(self) -> int:
        """Return port."""
        return self._port

    @classmethod
    async def create(
        cls,
        host: str,
        port: int = 161,
        printer_type: str = "laser",
        model: str | None = None,
        snmp_engine: SnmpEngine = None,
    ) -> Self:
        """Create a new device instance."""
        instance = cls(host, port, printer_type, model, snmp_engine)
        await instance.initialize()
        return instance

    async def initialize(self) -> None:
        """Initialize snmp_engine and check which OIDs are supported."""
        _LOGGER.debug("Initializing device %s", self._host)

        if not self._snmp_engine:
            self._snmp_engine = await async_get_snmp_engine()

        oids = list(self._iterate_oids(OIDS.values()))

        try:
            self._request_args = (
                self._snmp_engine,
                CommunityData("public", mpModel=0),
                UdpTransportTarget(
                    (self._host, self._port), timeout=DEFAULT_TIMEOUT, retries=RETRIES
                ),
                ContextData(),
            )
        except PySnmpError as err:
            raise ConnectionError(err) from err

        while True:
            async with timeout(DEFAULT_TIMEOUT * RETRIES):
                _, errstatus, errindex, _ = await getCmd(*self._request_args, *oids)

            if str(errstatus) == "noSuchName":
                # 5 and 8 are indexes from OIDS consts, model and serial are obligatory
                if errindex in (5, 8):
                    raise UnsupportedModelError(
                        "It seems that this printer model is not supported"
                    )

                oids.pop(errindex - 1)
                continue

            break

        self._oids = oids

    async def async_update(self) -> BrotherSensors:
        """Update data from printer."""
        if not (raw_data := await self._get_data()):
            raise SnmpError("The printer did not return data")

        _LOGGER.debug("RAW data: %s", raw_data)

        data: dict[str, Any] = {}

        try:
            model_match = re.search(REGEX_MODEL_PATTERN, raw_data[OIDS[ATTR_MODEL]])

            if TYPE_CHECKING:
                assert model_match is not None

            self.model = model_match.group("model")
            self.serial = raw_data[OIDS[ATTR_SERIAL]]
        except (TypeError, AttributeError) as err:
            raise UnsupportedModelError(
                "It seems that this printer model is not supported"
            ) from err

        self.mac = raw_data[OIDS[ATTR_MAC]]
        self._firmware = raw_data.get(OIDS[ATTR_FIRMWARE])

        if status := raw_data[OIDS[ATTR_STATUS]]:
            data[ATTR_STATUS] = self._cleanse_status(status.lower())

        try:
            uptime = int(cast(str, raw_data.get(OIDS[ATTR_UPTIME]))) / 100
        except TypeError:
            pass
        else:
            if self._last_uptime:
                new_uptime = (datetime.now(tz=UTC) - timedelta(seconds=uptime)).replace(
                    microsecond=0, tzinfo=UTC
                )
                if (
                    abs((new_uptime - self._last_uptime).total_seconds())
                    > UPTIME_FLUCTUATION_SECONDS
                ):
                    data[ATTR_UPTIME] = self._last_uptime = new_uptime
                else:
                    data[ATTR_UPTIME] = self._last_uptime
            else:
                data[ATTR_UPTIME] = self._last_uptime = (
                    datetime.now(tz=UTC) - timedelta(seconds=uptime)
                ).replace(microsecond=0, tzinfo=UTC)
        if self._legacy:
            if self._printer_type == "laser":
                data.update(
                    dict(
                        self._iterate_data_legacy(
                            raw_data.get(OIDS[ATTR_MAINTENANCE], {}),
                            VALUES_LASER_MAINTENANCE,
                        )
                    )
                )
            if self._printer_type == "ink":
                data.update(
                    dict(
                        self._iterate_data_legacy(
                            raw_data.get(OIDS[ATTR_MAINTENANCE], {}),
                            VALUES_INK_MAINTENANCE,
                        )
                    )
                )
        else:
            if self._printer_type == "laser":
                data.update(
                    dict(
                        self._iterate_data(
                            raw_data.get(OIDS[ATTR_COUNTERS], {}), VALUES_COUNTERS
                        )
                    )
                )
                data.update(
                    dict(
                        self._iterate_data(
                            raw_data.get(OIDS[ATTR_MAINTENANCE], {}),
                            VALUES_LASER_MAINTENANCE,
                        )
                    )
                )
                data.update(
                    dict(
                        self._iterate_data(
                            raw_data.get(OIDS[ATTR_NEXTCARE], {}), VALUES_LASER_NEXTCARE
                        )
                    )
                )
            if self._printer_type == "ink":
                data.update(
                    dict(
                        self._iterate_data(
                            raw_data.get(OIDS[ATTR_COUNTERS], {}), VALUES_COUNTERS
                        )
                    )
                )
                data.update(
                    dict(
                        self._iterate_data(
                            raw_data.get(OIDS[ATTR_MAINTENANCE], {}),
                            VALUES_INK_MAINTENANCE,
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

        result: BrotherSensors = from_dict(BrotherSensors, data)

        return result

    def shutdown(self) -> None:
        """Unconfigure SNMP engine."""
        if self._snmp_engine:
            lcd.unconfigure(self._snmp_engine, None)

    async def _get_data(self) -> dict[str, Any]:
        """Retrieve data from printer."""
        raw_data: dict[str, str | list[str]] = {}
        raw_status: bytes | None = None

        try:
            errindication, errstatus, errindex, restable = await getCmd(
                *self._request_args, *self._oids
            )
        except PySnmpError as err:
            raise ConnectionError(err) from err
        if errindication:
            raise SnmpError(errindication)
        if errstatus:
            msg = f"{errstatus}, {errindex}"
            raise SnmpError(msg)
        for resrow in restable:
            if str(resrow[0]) in OIDS_HEX:
                # asOctets gives bytes data b'c\x01\x04\x00\x00\x00\x01\x11\x01\x04\x00\
                # x00\x05,A\x01\x04\x00\x00"\xc41\x01\x04\x00\x00\x00\x01o\x01\x04\x00\
                # x00\x19\x00\x81\x01\x04\x00\x00\x00F\x86\x01\x04\x00\x00\x00\n\xff'
                data = resrow[-1].asOctets()
                # convert to string without checksum FF at the end, gives
                # '630104000000011101040000052c410104000022c4310104000000016f01040000190
                #  0810104000000468601040000000a'
                data_str = "".join([f"{x:02x}" for x in data])[0:-2]
                # split to 14 digits words in list, gives ['63010400000001',
                # '1101040000052c', '410104000022c4', '31010400000001',
                # '6f010400001900', '81010400000046', '8601040000000a']
                result = [
                    data_str[ind : ind + CHUNK_SIZE]
                    for ind in range(0, len(data_str), CHUNK_SIZE)
                ]
                # map sensors names to OIDs
                raw_data[str(resrow[0])] = result
            elif str(resrow[0]) == OIDS[ATTR_MAC]:
                data = resrow[-1].asOctets()
                raw_data[str(resrow[0])] = ":".join([f"{x:02x}" for x in data])
            elif str(resrow[0]) == OIDS[ATTR_STATUS]:
                raw_status = resrow[-1]._value  # noqa: SLF001
            else:
                raw_data[str(resrow[0])] = str(resrow[-1])

        if raw_status is not None:
            charset = raw_data.get(OIDS[ATTR_CHARSET], "unknown")

            if TYPE_CHECKING:
                assert isinstance(charset, str)

            encoding = CHARSET_MAP.get(charset, "roman8")
            if status := self._decode_status(raw_status, encoding):
                raw_data[OIDS[ATTR_STATUS]] = status

        # for legacy printers
        for resrow in restable:
            if str(resrow[0]) == OIDS[ATTR_MAINTENANCE]:
                # asOctets() gives bytes data
                data = resrow[-1].asOctets()
                # convert to string without checksum FF at the end, gives
                # 'a101020414a201020c14a301020614a401020b14'
                data_str = "".join([f"{x:02x}" for x in data])[0:-2]
                if self._legacy_printer(data_str):
                    self._legacy = True
                    # split to 10 digits words in list, gives ['a101020414',
                    # 'a201020c14', 'a301020614', 'a401020b14']
                    result = [
                        data_str[ind : ind + LEGACY_CHUNK_SIZE]
                        for ind in range(0, len(data_str), LEGACY_CHUNK_SIZE)
                    ]
                    # map sensors names to OIDs
                    raw_data[str(resrow[0])] = result
                    break
        return raw_data

    @staticmethod
    def _legacy_printer(string: str) -> bool:
        """Return True if printer is legacy."""
        length = len(string)
        nums = [x * 10 for x in range(length // 10)][1:]
        if results := [string[i - 2 : i] == "14" for i in nums]:
            return all(item for item in results)
        return False

    @staticmethod
    def _iterate_oids(oids: Iterable) -> Generator:
        """Iterate OIDS to retrieve from printer."""
        for oid in oids:
            yield ObjectType(ObjectIdentity(oid))

    @staticmethod
    def _iterate_data(iterable: Iterable, values_map: dict[str, str]) -> Generator:
        """Iterate data from hex words."""
        for item in iterable:
            # first byte means kind of sensor, last 4 bytes means value
            if item[:2] in values_map:
                if values_map[item[:2]] in PERCENT_VALUES:
                    yield (values_map[item[:2]], round(int(item[-8:], 16) / 100))
                else:
                    yield (values_map[item[:2]], int(item[-8:], 16))

    @staticmethod
    def _iterate_data_legacy(
        iterable: Iterable, values_map: dict[str, str]
    ) -> Generator:
        """Iterate data from hex words for legacy printers."""
        for item in iterable:
            # first byte means kind of sensor, last 4 bytes means value
            if item[:2] in values_map:
                yield (
                    values_map[item[:2]],
                    round(int(item[6:8], 16) / int(item[8:10], 16) * 100),
                )

    @staticmethod
    def _cleanse_status(status: str) -> str:
        """Cleanse and format status."""
        return " ".join(status.split()).strip()

    @staticmethod
    def _decode_status(status: bytes, encoding: str) -> str | None:
        """Decode status."""
        _LOGGER.debug("Status: %s, encoding: %s", status, encoding)
        try:
            result = status.decode(encoding)
        except UnicodeDecodeError:
            return None
        else:
            return result

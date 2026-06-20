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
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,
    set_cmd,
)
from pysnmp.hlapi.v3arch.asyncio.cmdgen import LCD
from pysnmp.proto.rfc1902 import OctetString
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
    DATETIME_SET_SUPPORTED_MODELS,
    DEFAULT_TIMEOUT,
    DEFAULT_WRITE_COMMUNITY,
    OID_DATETIME,
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
from .exceptions import MethodNotSupportedError, SnmpError, UnsupportedModelError
from .model import BrotherSensors
from .utils import (
    async_get_snmp_engine,
    build_dateandtime,
    bytes_to_hex_string,
    parse_dateandtime,
)

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
        community: str = "public",
        printer_type: str = "laser",
        model: str | None = None,
        snmp_engine: SnmpEngine | None = None,
        write_community: str = DEFAULT_WRITE_COMMUNITY,
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

        self._legacy: bool | None = None

        self._firmware: str | None = None
        self.model: str
        self.serial: str
        self.mac: str
        self._host = host
        self._port = port
        self._community = community
        self._write_community = write_community
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

    @property
    def community(self) -> str:
        """Return SNMP community."""
        return self._community

    @property
    def is_datetime_set_supported(self) -> bool:
        """Return True if the printer model supports setting the datetime via SNMP."""
        return any(m in self.model.lower() for m in DATETIME_SET_SUPPORTED_MODELS)

    @classmethod
    async def create(
        cls,
        host: str,
        port: int = 161,
        community: str = "public",
        printer_type: str = "laser",
        model: str | None = None,
        snmp_engine: SnmpEngine | None = None,
        write_community: str = DEFAULT_WRITE_COMMUNITY,
    ) -> Self:
        """Create a new device instance."""
        instance = cls(
            host=host,
            port=port,
            community=community,
            printer_type=printer_type,
            model=model,
            snmp_engine=snmp_engine,
            write_community=write_community,
        )
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
                CommunityData(self.community, mpModel=0),
                await UdpTransportTarget.create(
                    (self._host, self._port), timeout=DEFAULT_TIMEOUT, retries=RETRIES
                ),
                ContextData(),
            )
        except PySnmpError as err:
            raise ConnectionError(err) from err

        while True:
            async with timeout(DEFAULT_TIMEOUT * RETRIES):
                _, errstatus, errindex, _ = await get_cmd(*self._request_args, *oids)

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

        oids = OIDS

        try:
            model_match = REGEX_MODEL_PATTERN.search(raw_data[oids[ATTR_MODEL]])

            if TYPE_CHECKING:
                assert model_match is not None

            self.model = model_match.group("model")
            self.serial = raw_data[oids[ATTR_SERIAL]]
        except (TypeError, AttributeError) as err:
            raise UnsupportedModelError(
                "It seems that this printer model is not supported"
            ) from err

        self.mac = raw_data[oids[ATTR_MAC]]
        self._firmware = raw_data.get(oids[ATTR_FIRMWARE])

        if status := raw_data[oids[ATTR_STATUS]]:
            data[ATTR_STATUS] = self._cleanse_status(status.lower())

        try:
            uptime = int(cast(str, raw_data.get(oids[ATTR_UPTIME]))) / 100
        except TypeError:
            pass
        else:
            now = datetime.now(tz=UTC)
            if self._last_uptime:
                new_uptime = (now - timedelta(seconds=uptime)).replace(
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
                    now - timedelta(seconds=uptime)
                ).replace(microsecond=0, tzinfo=UTC)
        if self._legacy:
            if self._printer_type == "laser":
                data.update(
                    self._iterate_data_legacy(
                        raw_data.get(oids[ATTR_MAINTENANCE], {}),
                        VALUES_LASER_MAINTENANCE,
                    )
                )
            elif self._printer_type == "ink":
                data.update(
                    self._iterate_data_legacy(
                        raw_data.get(oids[ATTR_MAINTENANCE], {}),
                        VALUES_INK_MAINTENANCE,
                    )
                )
        else:
            data.update(
                self._iterate_data(
                    raw_data.get(oids[ATTR_COUNTERS], {}), VALUES_COUNTERS
                )
            )
            if self._printer_type == "laser":
                data.update(
                    self._iterate_data(
                        raw_data.get(oids[ATTR_MAINTENANCE], {}),
                        VALUES_LASER_MAINTENANCE,
                    )
                )
                data.update(
                    self._iterate_data(
                        raw_data.get(oids[ATTR_NEXTCARE], {}),
                        VALUES_LASER_NEXTCARE,
                    )
                )
            elif self._printer_type == "ink":
                data.update(
                    self._iterate_data(
                        raw_data.get(oids[ATTR_MAINTENANCE], {}),
                        VALUES_INK_MAINTENANCE,
                    )
                )
        with suppress(ValueError):
            if not data.get(ATTR_PAGE_COUNT) and raw_data.get(oids[ATTR_PAGE_COUNT]):
                data[ATTR_PAGE_COUNT] = int(
                    cast(str, raw_data.get(oids[ATTR_PAGE_COUNT]))
                )

        _LOGGER.debug("Data: %s", data)

        result: BrotherSensors = from_dict(BrotherSensors, data)

        return result

    def shutdown(self) -> None:
        """Unconfigure SNMP engine."""
        if self._snmp_engine:
            LCD.unconfigure(self._snmp_engine, None)

    async def async_get_datetime(self) -> datetime | None:
        """Return the printer's current date and time, or None if not available."""
        oid = ObjectType(ObjectIdentity(OID_DATETIME))

        try:
            async with timeout(DEFAULT_TIMEOUT * RETRIES):
                errindication, errstatus, errindex, restable = await get_cmd(
                    *self._request_args, oid
                )
        except TimeoutError as err:
            raise ConnectionError(err) from err
        except PySnmpError as err:
            raise ConnectionError(err) from err

        if errindication:
            raise SnmpError(str(errindication))
        if errstatus:
            if str(errstatus) == "noSuchName":
                return None
            msg = f"SNMP GET failed: {errstatus} at index {errindex}"
            raise SnmpError(msg)

        raw: bytes = restable[0][-1].asOctets()
        return parse_dateandtime(raw)

    async def async_set_datetime(self, dt: datetime | None = None) -> None:
        """Set the printer's date and time via SNMP."""
        if not self.is_datetime_set_supported:
            msg = f"Setting datetime is not supported on model {self.model}"
            raise MethodNotSupportedError(msg)

        if dt is None:
            dt = datetime.now(tz=UTC).astimezone()

        payload = OctetString(build_dateandtime(dt))
        oid = ObjectType(
            ObjectIdentity(OID_DATETIME),
            payload,
        )

        try:
            async with timeout(DEFAULT_TIMEOUT * RETRIES):
                errindication, errstatus, errindex, _ = await set_cmd(
                    *self._write_request_args(), oid
                )
        except TimeoutError as err:
            raise ConnectionError(err) from err
        except PySnmpError as err:
            raise ConnectionError(err) from err

        if errindication:
            raise SnmpError(str(errindication))
        if errstatus:
            msg = f"SNMP SET failed: {errstatus} at index {errindex}"
            raise SnmpError(msg)

        _LOGGER.debug("Printer datetime set to %s", dt.isoformat())

    def _write_request_args(
        self,
    ) -> tuple[SnmpEngine, CommunityData, UdpTransportTarget, ContextData]:
        """Return SNMP request args using the write community string."""
        return (
            self._request_args[0],
            CommunityData(self._write_community, mpModel=0),
            self._request_args[2],
            self._request_args[3],
        )

    async def _get_data(self) -> dict[str, Any]:
        """Retrieve data from printer."""
        raw_data: dict[str, str | list[str]] = {}
        raw_status: bytes | None = None

        try:
            async with timeout(DEFAULT_TIMEOUT * RETRIES):
                errindication, errstatus, errindex, restable = await get_cmd(
                    *self._request_args, *self._oids
                )
        except TimeoutError as err:
            raise ConnectionError(err) from err
        except PySnmpError as err:
            raise ConnectionError(err) from err
        if errindication:
            raise SnmpError(str(errindication))
        if errstatus:
            msg = f"{errstatus}, {errindex}"
            raise SnmpError(msg)

        oid_charset = OIDS[ATTR_CHARSET]
        oid_mac = OIDS[ATTR_MAC]
        oid_maintenance = OIDS[ATTR_MAINTENANCE]
        oid_status = OIDS[ATTR_STATUS]

        for resrow in restable:
            oid_str = str(resrow[0])
            if oid_str in OIDS_HEX:
                data = resrow[-1].asOctets()
                data_str = bytes_to_hex_string(data)
                if oid_str == oid_maintenance and self._legacy is not False:
                    if self._legacy is None:
                        self._legacy = self._legacy_printer(data_str)
                    if self._legacy:
                        result = [
                            data_str[ind : ind + LEGACY_CHUNK_SIZE]
                            for ind in range(0, len(data_str), LEGACY_CHUNK_SIZE)
                        ]
                        raw_data[oid_str] = result
                        continue
                result = [
                    data_str[ind : ind + CHUNK_SIZE]
                    for ind in range(0, len(data_str), CHUNK_SIZE)
                ]
                raw_data[oid_str] = result
            elif oid_str == oid_mac:
                data = resrow[-1].asOctets()
                raw_data[oid_str] = ":".join([f"{x:02x}" for x in data])
            elif oid_str == oid_status:
                raw_status = resrow[-1]._value  # noqa: SLF001
            else:
                raw_data[oid_str] = str(resrow[-1])

        if raw_status is not None:
            charset = raw_data.get(oid_charset, "unknown")

            if TYPE_CHECKING:
                assert isinstance(charset, str)

            encoding = CHARSET_MAP.get(charset, "roman8")
            if status := self._decode_status(raw_status, encoding):
                raw_data[oid_status] = status

        return raw_data

    @staticmethod
    def _legacy_printer(string: str) -> bool:
        """Return True if printer is legacy."""
        length = len(string)
        if length < LEGACY_CHUNK_SIZE * 2:
            return False
        return all(
            string[i - 2 : i] == "14"
            for i in range(LEGACY_CHUNK_SIZE, length, LEGACY_CHUNK_SIZE)
        )

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

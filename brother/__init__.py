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
_MANDATORY_OID_INDICES = frozenset(
    i for i, key in enumerate(OIDS, start=1) if key in {ATTR_MODEL, ATTR_SERIAL}
)
_IDX_ENGINE = 0
_IDX_TRANSPORT = 2
_IDX_CONTEXT = 3
_MAX_PORT = 65535


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
        if not host or not isinstance(host, str):
            msg = "host must be a non-empty string"
            raise ValueError(msg)
        if not isinstance(port, int) or not 1 <= port <= _MAX_PORT:
            msg = f"port must be an integer between 1 and {_MAX_PORT}, got {port}"
            raise ValueError(msg)

        if model:
            model_lower = model.casefold()
            if any(
                unsupported_model in model_lower
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
        model_lower = self.model.casefold()
        return any(m in model_lower for m in DATETIME_SET_SUPPORTED_MODELS)

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

        oids = [ObjectType(ObjectIdentity(oid)) for oid in OIDS.values()]

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

        max_retries = len(oids)
        while max_retries:
            max_retries -= 1
            async with timeout(DEFAULT_TIMEOUT * RETRIES):
                _, errstatus, errindex, _ = await get_cmd(*self._request_args, *oids)

            if str(errstatus) == "noSuchName":
                if errindex in _MANDATORY_OID_INDICES:
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

        self._extract_identity(raw_data)
        data: dict[str, Any] = {ATTR_STATUS: self._extract_status(raw_data)}
        if uptime := self._extract_uptime(raw_data):
            data[ATTR_UPTIME] = uptime
        data.update(self._extract_counters(raw_data))
        self._extract_page_count(raw_data, data)

        _LOGGER.debug("Data: %s", data)

        return from_dict(BrotherSensors, data)

    def _extract_identity(self, raw_data: dict[str, Any]) -> None:
        """Extract model, serial, mac and firmware from raw data."""
        try:
            model_match = REGEX_MODEL_PATTERN.search(raw_data[OIDS[ATTR_MODEL]])

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

    def _extract_status(self, raw_data: dict[str, Any]) -> str | None:
        """Extract and decode status from raw data."""
        if status := raw_data.get(OIDS[ATTR_STATUS]):
            return self._cleanse_status(status.lower())
        return None

    @staticmethod
    def _extract_uptime(raw_data: dict[str, Any]) -> datetime | None:
        """Extract and compute uptime datetime from raw data."""
        try:
            uptime = int(cast(str, raw_data.get(OIDS[ATTR_UPTIME]))) / 100
        except TypeError:
            return None
        return (datetime.now(tz=UTC) - timedelta(seconds=uptime)).replace(
            microsecond=0, tzinfo=UTC
        )

    def _extract_counters(self, raw_data: dict[str, Any]) -> dict[str, int]:
        """Extract sensor counters from raw data based on printer type."""
        data: dict[str, int] = {}
        if self._legacy:
            if self._printer_type == "laser":
                data.update(
                    self._iterate_data_legacy(
                        raw_data.get(OIDS[ATTR_MAINTENANCE], {}),
                        VALUES_LASER_MAINTENANCE,
                    )
                )
            elif self._printer_type == "ink":
                data.update(
                    self._iterate_data_legacy(
                        raw_data.get(OIDS[ATTR_MAINTENANCE], {}),
                        VALUES_INK_MAINTENANCE,
                    )
                )
        else:
            data.update(
                self._iterate_data(
                    raw_data.get(OIDS[ATTR_COUNTERS], {}), VALUES_COUNTERS
                )
            )
            if self._printer_type == "laser":
                data.update(
                    self._iterate_data(
                        raw_data.get(OIDS[ATTR_MAINTENANCE], {}),
                        VALUES_LASER_MAINTENANCE,
                    )
                )
                data.update(
                    self._iterate_data(
                        raw_data.get(OIDS[ATTR_NEXTCARE], {}), VALUES_LASER_NEXTCARE
                    )
                )
            elif self._printer_type == "ink":
                data.update(
                    self._iterate_data(
                        raw_data.get(OIDS[ATTR_MAINTENANCE], {}),
                        VALUES_INK_MAINTENANCE,
                    )
                )
        return data

    @staticmethod
    def _extract_page_count(raw_data: dict[str, Any], data: dict[str, Any]) -> None:
        """Extract page counter for old printer models."""
        with suppress(ValueError):
            if not data.get(ATTR_PAGE_COUNT):
                raw_page_count = raw_data.get(OIDS[ATTR_PAGE_COUNT])
                if raw_page_count:
                    data[ATTR_PAGE_COUNT] = int(cast(str, raw_page_count))

    def shutdown(self) -> None:
        """Unconfigure SNMP engine."""
        if self._snmp_engine:
            LCD.unconfigure(self._snmp_engine, None)

    async def async_get_datetime(self) -> datetime | None:
        """Return the printer's current date and time, or None if not available."""
        oid = ObjectType(ObjectIdentity(OID_DATETIME))

        try:
            errindication, errstatus, errindex, restable = await get_cmd(
                *self._request_args, oid
            )
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
            errindication, errstatus, errindex, _ = await set_cmd(
                *self._write_request_args(), oid
            )
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
            self._request_args[_IDX_ENGINE],
            CommunityData(self._write_community, mpModel=0),
            self._request_args[_IDX_TRANSPORT],
            self._request_args[_IDX_CONTEXT],
        )

    async def _get_data(self) -> dict[str, Any]:
        """Retrieve data from printer."""
        raw_data: dict[str, str | list[str]] = {}
        raw_status: bytes | None = None

        try:
            errindication, errstatus, errindex, restable = await get_cmd(
                *self._request_args, *self._oids
            )
        except PySnmpError as err:
            raise ConnectionError(err) from err
        if errindication:
            raise SnmpError(str(errindication))
        if errstatus:
            msg = f"{errstatus}, {errindex}"
            raise SnmpError(msg)
        for resrow in restable:
            oid_str = str(resrow[0])
            if oid_str in OIDS_HEX:
                # asOctets gives bytes data b'c\x01\x04\x00\x00\x00\x01\x11\x01\x04\x00\
                # x00\x05,A\x01\x04\x00\x00"\xc41\x01\x04\x00\x00\x00\x01o\x01\x04\x00\
                # x00\x19\x00\x81\x01\x04\x00\x00\x00F\x86\x01\x04\x00\x00\x00\n\xff'
                data = resrow[-1].asOctets()
                # convert to string without checksum FF at the end, gives
                # '630104000000011101040000052c410104000022c4310104000000016f01040000190
                #  0810104000000468601040000000a'
                data_str = bytes_to_hex_string(data)
                # split to 14 digits words in list, gives ['63010400000001',
                # '1101040000052c', '410104000022c4', '31010400000001',
                # '6f010400001900', '81010400000046', '8601040000000a']
                result = [
                    data_str[ind : ind + CHUNK_SIZE]
                    for ind in range(0, len(data_str), CHUNK_SIZE)
                ]
                # map sensors names to OIDs
                raw_data[oid_str] = result
            elif oid_str == OIDS[ATTR_MAC]:
                data = resrow[-1].asOctets()
                raw_data[oid_str] = ":".join(f"{x:02x}" for x in data)
            elif oid_str == OIDS[ATTR_STATUS]:
                try:
                    raw_status = resrow[-1].asOctets()
                except AttributeError:
                    raw_status = resrow[-1]._value  # noqa: SLF001
            else:
                raw_data[oid_str] = str(resrow[-1])

        if raw_status is not None:
            charset = raw_data.get(OIDS[ATTR_CHARSET], "unknown")

            if TYPE_CHECKING:
                assert isinstance(charset, str)

            encoding = CHARSET_MAP.get(charset, "roman8")
            if status := self._decode_status(raw_status, encoding):
                raw_data[OIDS[ATTR_STATUS]] = status

        if self._legacy is False:
            return raw_data

        # for legacy printers
        for resrow in restable:
            oid_str = str(resrow[0])
            if oid_str == OIDS[ATTR_MAINTENANCE]:
                # asOctets() gives bytes data
                data = resrow[-1].asOctets()
                # convert to string without checksum FF at the end, gives
                # 'a101020414a201020c14a301020614a401020b14'
                data_str = bytes_to_hex_string(data)
                if self._legacy is None:
                    self._legacy = self._legacy_printer(data_str)
                if self._legacy:
                    # split to 10 digits words in list, gives ['a101020414',
                    # 'a201020c14', 'a301020614', 'a401020b14']
                    result = [
                        data_str[ind : ind + LEGACY_CHUNK_SIZE]
                        for ind in range(0, len(data_str), LEGACY_CHUNK_SIZE)
                    ]
                    # map sensors names to OIDs
                    raw_data[oid_str] = result
                    break
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

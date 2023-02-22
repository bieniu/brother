"""Brother exceptions."""


class BrotherError(Exception):
    """Base class for brother errors."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class SnmpError(BrotherError):
    """Raised when SNMP request ended in error."""


class UnsupportedModelError(BrotherError):
    """Raised when no model, serial no, firmware data."""

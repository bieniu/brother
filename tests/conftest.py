"""Set up some common test helper things."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pysnmp.hlapi.v3arch.asyncio import CommunityData, ContextData, SnmpEngine
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.amber import AmberSnapshotExtension
from syrupy.location import PyTestLocation

from brother import Brother


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture."""
    return snapshot.use_extension(SnapshotExtension)


@pytest.fixture
def brother_with_request_args() -> Brother:
    """Return a Brother instance with fake _request_args for SNMP tests."""
    brother = Brother("localhost")
    brother._request_args = (
        MagicMock(spec=SnmpEngine),
        CommunityData("public", mpModel=0),
        MagicMock(),
        ContextData(),
    )
    return brother


class SnapshotExtension(AmberSnapshotExtension):
    """Extension for Syrupy."""

    @classmethod
    def dirname(cls, *, test_location: PyTestLocation) -> str:
        """Return the directory for the snapshot files."""
        test_dir = Path(test_location.filepath).parent
        return str(test_dir.joinpath("snapshots"))

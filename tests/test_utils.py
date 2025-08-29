"""Tests for brother utils."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from pysnmp.hlapi.v3arch.asyncio import SnmpEngine

from brother.utils import _get_snmp_engine, async_get_snmp_engine


def test_get_snmp_engine() -> None:
    """Test _get_snmp_engine function."""
    with patch("brother.utils.MibViewControllerManager") as mock_mib_manager:
        mock_mib_view_controller = MagicMock()
        mock_mib_view_controller.mibBuilder.mibSymbols = {}
        mock_mib_manager.get_mib_view_controller.return_value = mock_mib_view_controller

        engine = _get_snmp_engine()

    assert isinstance(engine, SnmpEngine)
    mock_mib_manager.get_mib_view_controller.assert_called_once()
    mock_mib_view_controller.mibBuilder.load_modules.assert_called_once()
    assert engine.cache["mibViewController"] == mock_mib_view_controller


def test_get_snmp_engine_with_existing_mibs() -> None:
    """Test _get_snmp_engine when MIBs are already loaded."""
    with patch("brother.utils.MibViewControllerManager") as mock_mib_manager:
        mock_mib_view_controller = MagicMock()
        # MIBs already loaded
        mock_mib_view_controller.mibBuilder.mibSymbols = {"PYSNMP-MIB": True}
        mock_mib_manager.get_mib_view_controller.return_value = mock_mib_view_controller

        engine = _get_snmp_engine()

    assert isinstance(engine, SnmpEngine)
    mock_mib_manager.get_mib_view_controller.assert_called_once()
    # load_modules should not be called since MIBs are already loaded
    mock_mib_view_controller.mibBuilder.load_modules.assert_not_called()
    assert engine.cache["mibViewController"] == mock_mib_view_controller


@pytest.mark.asyncio
async def test_async_get_snmp_engine() -> None:
    """Test async_get_snmp_engine function."""
    with patch("brother.utils._get_snmp_engine") as mock_get_engine:
        mock_engine = MagicMock(spec=SnmpEngine)
        mock_get_engine.return_value = mock_engine

        result = await async_get_snmp_engine()

    assert result == mock_engine
    mock_get_engine.assert_called_once()


@pytest.mark.asyncio
async def test_async_get_snmp_engine_uses_executor() -> None:
    """Test that async_get_snmp_engine uses executor properly."""
    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_engine = MagicMock(spec=SnmpEngine)
        mock_loop.run_in_executor.return_value = asyncio.Future()
        mock_loop.run_in_executor.return_value.set_result(mock_engine)

        result = await async_get_snmp_engine()

    assert result == mock_engine
    mock_get_loop.assert_called_once()
    mock_loop.run_in_executor.assert_called_once()
    args = mock_loop.run_in_executor.call_args[0]
    assert args[0] is None  # executor should be None (default)
    assert callable(args[1])  # second arg should be the _get_snmp_engine function

"""Tests for the generic read_register and write_register Device methods."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Patch ModbusHub before the device module is first imported so that it loads
# without a real Modbus connection.
_modbus_patcher = patch("homeassistant.components.modbus.modbus.ModbusHub")
_modbus_patcher.start()

from custom_components.nilan.device import Device  # noqa: E402
from custom_components.nilan.registers import RegisterTable  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    """Stop the module-level patcher when the test session ends."""
    _modbus_patcher.stop()


def _make_device():
    """Create a Device instance with a mocked modbus hub."""
    mock_hub = MagicMock()
    hass = MagicMock()
    device = Device(hass, "TestDevice", "tcp", "192.168.1.1", 502, 1)
    device._modbus = mock_hub
    return device, mock_hub


# ---------------------------------------------------------------------------
# read_register tests
# ---------------------------------------------------------------------------


class TestReadRegister:
    def setup_method(self):
        self.device, self.mock_modbus = _make_device()

    @pytest.mark.asyncio
    async def test_read_input_register_returns_value(self):
        mock_result = MagicMock()
        mock_result.registers = [1234]
        self.mock_modbus.async_pb_call = AsyncMock(return_value=mock_result)

        value = await self.device.read_register("input", 200)

        assert value == 1234
        self.mock_modbus.async_pb_call.assert_awaited_once_with(1, 200, 1, "input")

    @pytest.mark.asyncio
    async def test_read_holding_register_returns_value(self):
        mock_result = MagicMock()
        mock_result.registers = [42]
        self.mock_modbus.async_pb_call = AsyncMock(return_value=mock_result)

        value = await self.device.read_register("holding", 1002)

        assert value == 42
        self.mock_modbus.async_pb_call.assert_awaited_once_with(1, 1002, 1, "holding")

    @pytest.mark.asyncio
    async def test_read_register_with_enum_table(self):
        mock_result = MagicMock()
        mock_result.registers = [7]
        self.mock_modbus.async_pb_call = AsyncMock(return_value=mock_result)

        value = await self.device.read_register(RegisterTable.INPUT, 100)

        assert value == 7
        self.mock_modbus.async_pb_call.assert_awaited_once_with(1, 100, 1, "input")

    @pytest.mark.asyncio
    async def test_read_register_uppercase_string(self):
        """Table string should be case-insensitive."""
        mock_result = MagicMock()
        mock_result.registers = [0]
        self.mock_modbus.async_pb_call = AsyncMock(return_value=mock_result)

        value = await self.device.read_register("INPUT", 0)

        assert value == 0

    @pytest.mark.asyncio
    async def test_read_register_returns_none_on_modbus_failure(self):
        self.mock_modbus.async_pb_call = AsyncMock(return_value=None)

        value = await self.device.read_register("input", 200)

        assert value is None

    @pytest.mark.asyncio
    async def test_read_register_invalid_table_string_raises(self):
        with pytest.raises(ValueError, match="Invalid table"):
            await self.device.read_register("coils", 0)

    @pytest.mark.asyncio
    async def test_read_register_invalid_table_type_raises(self):
        with pytest.raises(ValueError, match="Invalid table type"):
            await self.device.read_register(123, 0)

    @pytest.mark.asyncio
    async def test_read_register_negative_address_raises(self):
        with pytest.raises(ValueError, match="Invalid address"):
            await self.device.read_register("input", -1)

    @pytest.mark.asyncio
    async def test_read_register_non_int_address_raises(self):
        with pytest.raises(ValueError, match="Invalid address"):
            await self.device.read_register("input", "200")


# ---------------------------------------------------------------------------
# write_register tests
# ---------------------------------------------------------------------------


class TestWriteRegister:
    def setup_method(self):
        self.device, self.mock_modbus = _make_device()

    @pytest.mark.asyncio
    async def test_write_register_returns_true(self):
        self.mock_modbus.async_pb_call = AsyncMock(return_value=MagicMock())

        result = await self.device.write_register(1002, 3)

        assert result is True
        self.mock_modbus.async_pb_call.assert_awaited_once_with(
            1, 1002, [3], "write_registers"
        )

    @pytest.mark.asyncio
    async def test_write_register_zero_value(self):
        self.mock_modbus.async_pb_call = AsyncMock(return_value=MagicMock())

        result = await self.device.write_register(1001, 0)

        assert result is True

    @pytest.mark.asyncio
    async def test_write_register_max_value(self):
        self.mock_modbus.async_pb_call = AsyncMock(return_value=MagicMock())

        result = await self.device.write_register(300, 65535)

        assert result is True
        self.mock_modbus.async_pb_call.assert_awaited_once_with(
            1, 300, [65535], "write_registers"
        )

    @pytest.mark.asyncio
    async def test_write_register_negative_value_raises(self):
        with pytest.raises(ValueError, match="Invalid value"):
            await self.device.write_register(1002, -1)

    @pytest.mark.asyncio
    async def test_write_register_overflow_value_raises(self):
        with pytest.raises(ValueError, match="Invalid value"):
            await self.device.write_register(1002, 65536)

    @pytest.mark.asyncio
    async def test_write_register_negative_address_raises(self):
        with pytest.raises(ValueError, match="Invalid address"):
            await self.device.write_register(-1, 0)

    @pytest.mark.asyncio
    async def test_write_register_non_int_address_raises(self):
        with pytest.raises(ValueError, match="Invalid address"):
            await self.device.write_register("1002", 0)

    @pytest.mark.asyncio
    async def test_write_register_non_int_value_raises(self):
        with pytest.raises(ValueError, match="Invalid value"):
            await self.device.write_register(1002, 3.5)

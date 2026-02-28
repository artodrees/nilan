"""The Nilan integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .device import Device

PLATFORMS = [
    "binary_sensor",
    "button",
    "climate",
    "number",
    "select",
    "sensor",
    "switch",
    "water_heater",
]

SERVICE_READ_REGISTER = "read_register"
SERVICE_WRITE_REGISTER = "write_register"

SERVICE_READ_REGISTER_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("address"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("table"): vol.In(["input", "holding"]),
    }
)

SERVICE_WRITE_REGISTER_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("address"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("value"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
    }
)

_LOGGER = logging.getLogger(__name__)


def _get_device(hass: HomeAssistant, entry_id: str | None) -> Device | None:
    """Return the Device instance for the given entry_id, or the first available one."""
    domain_data = hass.data.get(DOMAIN, {})
    if entry_id is not None:
        device = domain_data.get(entry_id)
        if not isinstance(device, Device):
            _LOGGER.error("No Nilan device found for entry_id '%s'", entry_id)
            return None
        return device
    for device in domain_data.values():
        if isinstance(device, Device):
            return device
    _LOGGER.error("No Nilan device found")
    return None


def _register_services(hass: HomeAssistant) -> None:
    """Register nilan services."""

    async def handle_read_register(call: ServiceCall) -> dict:
        """Handle the nilan.read_register service call.

        Returns a dict with key 'value' containing the raw 16-bit register
        value, or None if the read failed.
        """
        entry_id = call.data.get("entry_id")
        address = call.data["address"]
        table = call.data["table"]
        device = _get_device(hass, entry_id)
        if device is None:
            return {"value": None}
        result = await device.read_register(table, address)
        _LOGGER.info(
            "nilan.read_register table=%s address=%d -> %s", table, address, result
        )
        return {"value": result}

    async def handle_write_register(call: ServiceCall) -> None:
        """Handle the nilan.write_register service call.

        Writes a raw 16-bit unsigned integer value to a holding register.
        """
        entry_id = call.data.get("entry_id")
        address = call.data["address"]
        value = call.data["value"]
        device = _get_device(hass, entry_id)
        if device is None:
            return
        await device.write_register(address, value)
        _LOGGER.info("nilan.write_register address=%d value=%d", address, value)

    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_REGISTER,
        handle_read_register,
        schema=SERVICE_READ_REGISTER_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_WRITE_REGISTER,
        handle_write_register,
        schema=SERVICE_WRITE_REGISTER_SCHEMA,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nilan CTS602 Modbus TCP from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    name = entry.data["name"]
    host_port = entry.data["host_port"]
    unit_id = entry.data["unit_id"]
    com_type = entry.data["com_type"]
    host_ip = entry.data["host_ip"]
    # board_type = entry.data["board_type"]

    device = Device(hass, name, com_type, host_ip, host_port, unit_id)
    try:
        await device.setup()
    except ValueError as ex:
        raise ConfigEntryNotReady(f"Timeout while connecting {host_ip}") from ex
    hass.data[DOMAIN][entry.entry_id] = device

    if not hass.services.has_service(DOMAIN, SERVICE_READ_REGISTER):
        _register_services(hass)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        new.update({"com_type": "tcp"})
        new.update({"board_type": "CTS602"})
        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    elif config_entry.version == 2:
        new = {**config_entry.data}
        new.update({"board_type": "CTS602"})
        config_entry.version = 3
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_READ_REGISTER)
        hass.services.async_remove(DOMAIN, SERVICE_WRITE_REGISTER)

    return unload_ok


class NilanEntity(Entity):
    """Nilan Entity."""

    def __init__(self, device: Device) -> None:
        """Initialize the instance."""
        self._device = device

    @property
    def device_info(self):
        """Device Info."""
        unique_id = self._device.get_device_name + self._device.get_device_type

        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, unique_id),
            },
            "name": self._device.get_device_name,
            "manufacturer": "Nilan",
            "model": self._device.get_device_type,
            "sw_version": self._device.get_device_sw_version,
            "hw_version": self._device.get_device_hw_version,
            "suggested_area": "Boiler Room",
        }

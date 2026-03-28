"""The Milesight Gateway integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_GATEWAY_URL, DOMAIN
from .coordinator import MilesightGatewayCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type MilesightGatewayConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Runtime data stored on the config entry."""

    coordinator: DataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: MilesightGatewayConfigEntry
) -> bool:
    """Set up Milesight Gateway from a config entry."""
    coordinator = MilesightGatewayCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.api.connected:
        raise ConfigEntryNotReady

    # Register the gateway itself as a device so sensor devices can link to it via via_device.
    gateway_url = entry.data[CONF_GATEWAY_URL]
    port = entry.data[CONF_PORT]
    gateway_id = f"{gateway_url}:{port}"
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, gateway_id)},
        name=f"Milesight Gateway ({gateway_url})",
        manufacturer="Milesight",
        model="LoRaWAN Gateway",
        configuration_url=gateway_url,
    )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    entry.runtime_data = RuntimeData(coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: MilesightGatewayConfigEntry
) -> None:
    """Reload the integration when config options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: MilesightGatewayConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow a device to be removed from the UI."""
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: MilesightGatewayConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

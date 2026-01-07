"""Home Assistant integration for indevolt device."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import IndevoltCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("power"): cv.positive_int,
    }
)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the indevolt integration component.

    This function is called when the integration is added to the Home Assistant configuration.
    No component-level setup needed.
    """
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up indevolt from a config entry.

    This is the main setup function called when a config entry is added.
    It initializes the coordinator and sets up platforms.
    """
    hass.data.setdefault(DOMAIN, {})

    try:
        # Setup coordinator and perform initial data refresh
        coordinator = IndevoltCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()

        # Store coordinator (for platform access) and setup platforms
        hass.data[DOMAIN][entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    except Exception as err:
        _LOGGER.exception("Unexpected error occurred while setting config entry")

        # Clean up partially created resources
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            del hass.data[DOMAIN][entry.entry_id]

        raise ConfigEntryNotReady from err

    else:
        return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up resources.

    This is called when the integration is removed or reloaded.
    """
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.debug("Config entry %s not loaded or already unloaded", entry.entry_id)
        return True

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok

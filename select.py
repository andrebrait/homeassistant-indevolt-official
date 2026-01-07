"""Select platform for Indevolt integration."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IndevoltCoordinator

_LOGGER = logging.getLogger(__name__)

# Mapping of integer values to display strings
WORKING_MODE_OPTIONS = {
    1: "Self-consumed prioritized",
    2: "Charge/Discharge schedule",
    3: "Real-time control",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities from a config entry."""
    coordinator: IndevoltCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [
            WorkingModeSelect(coordinator, config_entry),
        ]
    )


class IndevoltSelectEntity(CoordinatorEntity, SelectEntity):
    """Base class for Indevolt select entities."""

    def __init__(self, coordinator: IndevoltCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_{self._get_cjson_point()}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"Indevolt {coordinator.config['device_model']}",
        }

    def _get_cjson_point(self) -> str:
        """Get the cJson Point for this entity."""
        raise NotImplementedError

    def _get_command_value(self, value: str) -> list:
        """Convert the selected value to the command format."""
        raise NotImplementedError

    async def async_select_option(self, option: str) -> None:
        """Update the selected option on the device."""
        try:
            command_value = self._get_command_value(option)
            await self.coordinator.async_push_data(self._get_cjson_point(), command_value)
            self._attr_current_option = option
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set %s: %s", self.name, err)
            raise


class WorkingModeSelect(IndevoltSelectEntity):
    """Select entity for Working Mode."""

    _attr_name = "Working Mode"
    _attr_options = list(WORKING_MODE_OPTIONS.values())
    _attr_icon = "mdi:cog"

    def __init__(self, coordinator: IndevoltCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, config_entry)
        self._attr_current_option = None

    def _get_cjson_point(self) -> str:
        """Get the cJson Point for Working Mode."""
        return "47005"

    def _get_command_value(self, value: str) -> list:
        """Convert option string to integer command format."""
        for key, option in WORKING_MODE_OPTIONS.items():
            if option == value:
                return [key]
        return [1]

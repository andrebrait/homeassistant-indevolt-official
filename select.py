"""Select platform for indevolt integration."""

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

ENERGY_MODE_MAP = {
    1: "Self-consumed Prioritized",
    4: "Real-time Control",
    5: "Charge/discharge Schedule",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform for Indevolt.

    This function is called by Home Assistant when the integration is set up.
    It creates select entities for the Energy Mode.
    """
    coordinator: IndevoltCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([IndevoltEnergyModeSelect(coordinator)])


class IndevoltEnergyModeSelect(CoordinatorEntity[IndevoltCoordinator], SelectEntity):
    """Select entity for Energy Mode selection."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: IndevoltCoordinator) -> None:
        """Initialize the Energy Mode select."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_energy_mode"
        self._attr_name = "Energy mode"
        self._attr_options = list(ENERGY_MODE_MAP.values())
        self._attr_device_info = coordinator.device_info

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self.coordinator.data is None:
            return None

        mode_value = self.coordinator.data.get("7101")

        if mode_value is None:
            return None

        # Convert to int if it's a string number
        try:
            mode_int = int(mode_value) if isinstance(mode_value, str) else mode_value
        except (ValueError, TypeError):
            _LOGGER.error("Invalid energy mode value: %s (type: %s)", mode_value, type(mode_value))
            return None

        option = ENERGY_MODE_MAP.get(mode_int)
        if option is None:
            _LOGGER.warning(
                "Mode value %s not found in map. Valid values: %s",
                mode_int,
                list(ENERGY_MODE_MAP.keys()),
            )

        return option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        mode_value = next(
            (key for key, value in ENERGY_MODE_MAP.items() if value == option),
            None,
        )

        if mode_value is None:
            _LOGGER.error("Invalid energy mode option: %s", option)
            return

        try:
            await self.coordinator.async_push_data("47005", mode_value)
            await self.coordinator.async_request_refresh()

        except Exception:
            _LOGGER.exception("Failed to set energy mode to %s", option)
            raise

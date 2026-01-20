"""Select platform for Indevolt integration."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import IndevoltCoordinator, IndevoltConfigEntry
from .entity import IndevoltEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class IndevoltSelectEntityDescription(SelectEntityDescription):
    """Custom entity description class for Indevolt select entities."""

    read_key: str
    write_key: str
    value_mapping: dict[int, str] = field(default_factory=dict)
    generation: list[int] = field(default_factory=lambda: [1, 2])


SELECTS: Final = (
    IndevoltSelectEntityDescription(
        key="working_mode",
        translation_key="working_mode",
        generation=[2],
        read_key="7101",
        write_key="47005",
        value_mapping={
            1: "self_consumed_prioritized",
            4: "real_time_control",
            5: "charge_discharge_schedule",
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IndevoltConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform for Indevolt."""
    coordinator = entry.runtime_data
    device_gen = coordinator.device_info_data.get("generation", 1)

    # Initialize select values (first fetch)
    initial_keys = [
        description.read_key
        for description in SELECTS
        if device_gen in description.generation
    ]
    coordinator.set_initial_sensor_keys(initial_keys)
    await coordinator.async_config_entry_first_refresh()

    # Add select entities based on device generation
    async_add_entities(
        [
            IndevoltSelectEntity(coordinator=coordinator, description=description)
            for description in SELECTS
            if device_gen in description.generation
        ]
    )


class IndevoltSelectEntity(IndevoltEntity, SelectEntity):
    """Represents a select entity for Indevolt devices."""

    entity_description: IndevoltSelectEntityDescription

    def __init__(
        self,
        coordinator: IndevoltCoordinator,
        description: IndevoltSelectEntityDescription,
    ) -> None:
        """Initialize the Indevolt select entity."""
        super().__init__(coordinator, context=description.read_key)

        self.entity_description = description
        self._attr_unique_id = f"{self.serial_number}_{description.key}"
        self._attr_options = list(description.value_mapping.values())

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self.coordinator.data is None:
            return None

        raw_value = self.coordinator.data.get(self.entity_description.read_key)
        if raw_value is None:
            return None

        value_int = int(raw_value) if isinstance(raw_value, str) else raw_value
        option = self.entity_description.value_mapping.get(value_int)
        return option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        value_int = next(
            (key for key, value in self.entity_description.value_mapping.items() if value == option),
            None,
        )

        if value_int is None:
            return

        try:
            await self.coordinator.async_push_data(self.entity_description.write_key, value_int)
            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error("Failed to set %s to %s: %s", self.entity_description.key, option, err)
            raise

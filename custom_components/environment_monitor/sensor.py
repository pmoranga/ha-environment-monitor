"""Status sensors for Environment Monitor."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    METRIC_HUMIDITY,
    METRIC_TEMPERATURE,
    STATUS_HIGH,
    STATUS_LOW,
    STATUS_OPTIMAL,
    STATUS_UNAVAILABLE,
)
from .entity import EnvironmentMonitorEntity
from .manager import EnvironmentMonitorManager

ICONS = {
    STATUS_OPTIMAL: "mdi:check-circle",
    "acceptable": "mdi:alert-circle-outline",
    STATUS_LOW: "mdi:arrow-down-circle",
    STATUS_HIGH: "mdi:arrow-up-circle",
    STATUS_UNAVAILABLE: "mdi:help-circle-outline",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up status sensors."""
    manager: EnvironmentMonitorManager = entry.runtime_data
    entities: list[SensorEntity] = [EnvironmentOverallStatusSensor(manager)]
    entities.extend(EnvironmentMetricStatusSensor(manager, metric) for metric in manager.metrics)
    async_add_entities(entities)


class EnvironmentMetricStatusSensor(EnvironmentMonitorEntity, SensorEntity):
    """Status of a configured source metric."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["optimal", "acceptable", "low", "high"]
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: EnvironmentMonitorManager, metric: str) -> None:
        """Initialize a metric status sensor."""
        super().__init__(manager, f"{metric}_status")
        self.metric = metric
        self._attr_translation_key = f"{metric}_status"
        self._attr_suggested_object_id = (
            f"environment_monitor_{entry_slug(manager.name)}_{metric}_status"
        )

    @property
    def available(self) -> bool:
        """Report whether the source has a usable value."""
        return self.manager.value(self.metric) is not None

    @property
    def native_value(self) -> str | None:
        """Return the classified source state."""
        return self.manager.status(self.metric) if self.available else None

    @property
    def icon(self) -> str:
        """Return an icon matching the current status."""
        return ICONS[self.manager.status(self.metric)]

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Identify the monitored source."""
        return {"source_entity_id": self.manager.source_entity(self.metric)}


class EnvironmentOverallStatusSensor(EnvironmentMonitorEntity, SensorEntity):
    """Combined status of all enabled metrics."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["optimal", "acceptable", "low", "high"]
    _attr_translation_key = "overall_status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: EnvironmentMonitorManager) -> None:
        """Initialize the overall status sensor."""
        super().__init__(manager, "overall_status")
        self._attr_suggested_object_id = (
            f"environment_monitor_{entry_slug(manager.name)}_overall_status"
        )

    @property
    def available(self) -> bool:
        """Report whether every configured source is available."""
        return self.manager.overall_status != STATUS_UNAVAILABLE

    @property
    def native_value(self) -> str | None:
        """Return the combined state."""
        return self.manager.overall_status if self.available else None

    @property
    def icon(self) -> str:
        """Return an icon matching the current status."""
        return ICONS[self.manager.overall_status]

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Expose each component status."""
        return {
            f"{metric}_status": self.manager.status(metric)
            for metric in self.manager.metrics
        }


def entry_slug(value: str) -> str:
    """Create a readable entity ID suggestion."""
    normalized = "".join(
        character if character.isalnum() else " " for character in value.lower()
    )
    return "_".join(normalized.split())

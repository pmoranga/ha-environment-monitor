"""Editable settings for Environment Monitor."""

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import METRIC_HUMIDITY, METRIC_TEMPERATURE
from .entity import EnvironmentMonitorEntity
from .manager import EnvironmentMonitorManager
from .sensor import entry_slug


@dataclass(frozen=True, kw_only=True)
class SettingDescription:
    """Describe one editable number."""

    key: str
    minimum: float
    maximum: float
    step: float
    unit: str
    device_class: NumberDeviceClass | None = None


def metric_descriptions(metric: str) -> list[SettingDescription]:
    """Build descriptions for one enabled metric."""
    if metric == METRIC_TEMPERATURE:
        values = [
            SettingDescription(
                key=f"{metric}_{suffix}",
                minimum=-100,
                maximum=1000,
                step=0.1,
                unit=UnitOfTemperature.CELSIUS,
                device_class=NumberDeviceClass.TEMPERATURE,
            )
            for suffix in ("low", "optimal_min", "optimal_max", "high")
        ]
        values.extend(
            SettingDescription(
                key=f"{metric}_chart_{bound}",
                minimum=-100,
                maximum=1000,
                step=1,
                unit=UnitOfTemperature.CELSIUS,
                device_class=NumberDeviceClass.TEMPERATURE,
            )
            for bound in ("min", "max")
        )
    else:
        values = [
            SettingDescription(
                key=f"{metric}_{suffix}",
                minimum=0,
                maximum=100,
                step=1,
                unit="%",
            )
            for suffix in ("low", "optimal_min", "optimal_max", "high")
        ]
    values.extend(
        SettingDescription(
            key=f"{metric}_{state}_alert_minutes",
            minimum=1,
            maximum=120,
            step=1,
            unit=UnitOfTime.MINUTES,
        )
        for state in ("low", "high")
    )
    return values


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up editable setting numbers."""
    manager: EnvironmentMonitorManager = entry.runtime_data
    async_add_entities(
        EnvironmentSettingNumber(manager, description)
        for metric in manager.metrics
        for description in metric_descriptions(metric)
    )


class EnvironmentSettingNumber(EnvironmentMonitorEntity, NumberEntity):
    """A persisted threshold, chart bound, or alert delay."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, manager: EnvironmentMonitorManager, description: SettingDescription
    ) -> None:
        """Initialize the setting."""
        super().__init__(manager, description.key)
        self.key = description.key
        self._attr_translation_key = description.key
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum
        self._attr_native_step = description.step
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class
        self._attr_suggested_object_id = (
            f"environment_monitor_{entry_slug(manager.name)}_{description.key}"
        )

    @property
    def native_value(self) -> float:
        """Return the configured value."""
        return float(self.manager.config[self.key])

    async def async_set_native_value(self, value: float) -> None:
        """Persist a changed value."""
        await self.manager.async_set_setting(self.key, value)

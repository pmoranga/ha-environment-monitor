"""Alert switch for Environment Monitor."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_ALERTS_ENABLED
from .entity import EnvironmentMonitorEntity
from .manager import EnvironmentMonitorManager
from .sensor import entry_slug


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the alerts switch."""
    async_add_entities([EnvironmentAlertsSwitch(entry.runtime_data)])


class EnvironmentAlertsSwitch(EnvironmentMonitorEntity, SwitchEntity):
    """Enable or disable delayed persistent notifications."""

    _attr_translation_key = "alerts"
    _attr_icon = "mdi:bell-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, manager: EnvironmentMonitorManager) -> None:
        """Initialize the switch."""
        super().__init__(manager, "alerts_enabled")
        self._attr_suggested_object_id = (
            f"environment_monitor_{entry_slug(manager.name)}_alerts_enabled"
        )

    @property
    def is_on(self) -> bool:
        """Return whether alerts are enabled."""
        return self.manager.alerts_enabled

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable alerts."""
        await self.manager.async_set_setting(CONF_ALERTS_ENABLED, True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable alerts."""
        await self.manager.async_set_setting(CONF_ALERTS_ENABLED, False)

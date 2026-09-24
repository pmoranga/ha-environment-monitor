"""Shared Environment Monitor entity."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .manager import EnvironmentMonitorManager


class EnvironmentMonitorEntity(Entity):
    """Base entity tied to a monitor manager."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: EnvironmentMonitorManager, key: str) -> None:
        """Initialize the entity."""
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, manager.entry.entry_id)},
            name=manager.name,
            manufacturer="Environment Monitor",
            model="Environmental zone",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to manager changes."""
        self.async_on_remove(self.manager.async_add_listener(self.async_write_ha_state))

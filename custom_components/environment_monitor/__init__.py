"""Environment Monitor integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .manager import EnvironmentMonitorManager

type EnvironmentMonitorConfigEntry = ConfigEntry[EnvironmentMonitorManager]


async def async_setup_entry(
    hass: HomeAssistant, entry: EnvironmentMonitorConfigEntry
) -> bool:
    """Set up Environment Monitor from a config entry."""
    manager = EnvironmentMonitorManager(hass, entry)
    entry.runtime_data = manager
    await manager.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EnvironmentMonitorConfigEntry
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_stop()
    return unload_ok

"""Runtime state and alert handling for Environment Monitor."""

from collections.abc import Callable
from contextlib import suppress
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, UnitOfTemperature
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import (
    CONF_ALERTS_ENABLED,
    CONF_HUMIDITY_ENTITY,
    CONF_NAME,
    CONF_TEMPERATURE_ENTITY,
    DEFAULTS,
    METRIC_HUMIDITY,
    METRIC_TEMPERATURE,
    STATUS_HIGH,
    STATUS_LOW,
)
from .helpers import limits_are_valid, metric_status, overall_status

Listener = Callable[[], None]


class EnvironmentMonitorManager:
    """Manage one configured environmental zone."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the manager."""
        self.hass = hass
        self.entry = entry
        self.config: dict[str, Any] = {**DEFAULTS, **entry.options}
        self.name: str = self.config[CONF_NAME]
        self._listeners: set[Listener] = set()
        self._remove_source_listener: Callable[[], None] | None = None
        self._timers: dict[str, Callable[[], None]] = {}
        self._conditions: dict[str, str] = {}
        self._notified: set[tuple[str, str]] = set()

    @property
    def metrics(self) -> tuple[str, ...]:
        """Return enabled metrics."""
        return tuple(
            metric
            for metric, key in (
                (METRIC_TEMPERATURE, CONF_TEMPERATURE_ENTITY),
                (METRIC_HUMIDITY, CONF_HUMIDITY_ENTITY),
            )
            if self.config.get(key)
        )

    def source_entity(self, metric: str) -> str:
        """Return a metric source entity ID."""
        key = (
            CONF_TEMPERATURE_ENTITY
            if metric == METRIC_TEMPERATURE
            else CONF_HUMIDITY_ENTITY
        )
        return self.config[key]

    def value(self, metric: str) -> float | None:
        """Return a numeric source value, normalized to Celsius for temperature."""
        state = self.hass.states.get(self.source_entity(metric))
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        with suppress(ValueError, TypeError):
            value = float(state.state)
            if metric == METRIC_TEMPERATURE:
                unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
                if unit and unit != UnitOfTemperature.CELSIUS:
                    value = TemperatureConverter.convert(
                        value, unit, UnitOfTemperature.CELSIUS
                    )
            return value
        return None

    def status(self, metric: str) -> str:
        """Return the status for one metric."""
        return metric_status(self.value(metric), metric, self.config)

    @property
    def overall_status(self) -> str:
        """Return the overall zone status."""
        return overall_status([self.status(metric) for metric in self.metrics])

    @property
    def alerts_enabled(self) -> bool:
        """Return whether notifications are enabled."""
        return bool(self.config[CONF_ALERTS_ENABLED])

    async def async_start(self) -> None:
        """Start tracking source entities."""
        entities = [self.source_entity(metric) for metric in self.metrics]
        self._remove_source_listener = async_track_state_change_event(
            self.hass, entities, self._async_source_changed
        )
        self._refresh()

    async def async_stop(self) -> None:
        """Stop listeners and pending alert timers."""
        if self._remove_source_listener:
            self._remove_source_listener()
        for cancel in self._timers.values():
            cancel()
        self._timers.clear()

    @callback
    def async_add_listener(self, listener: Listener) -> Callable[[], None]:
        """Register an entity update listener."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    async def async_set_setting(self, key: str, value: float | bool) -> None:
        """Validate, persist, and apply a setting from an entity."""
        new_config = {**self.config, key: value}
        metric = key.split("_", 1)[0]
        if metric in self.metrics and not limits_are_valid(new_config, metric):
            raise HomeAssistantError(
                "Limits must satisfy low ≤ optimal minimum ≤ optimal maximum ≤ high, "
                "and the chart range must contain all temperature limits"
            )
        self.config = new_config
        options = {**self.entry.options, key: value}
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        if key.endswith("_alert_minutes"):
            if cancel := self._timers.pop(metric, None):
                cancel()
        self._refresh()

    @callback
    def _async_source_changed(self, event: Event[dict[str, Any]]) -> None:
        """Handle a source entity state change."""
        self._refresh()

    @callback
    def _refresh(self) -> None:
        """Update entities and alert timers."""
        for metric in self.metrics:
            self._sync_alert(metric, self.status(metric))
        for listener in self._listeners:
            listener()

    @callback
    def _sync_alert(self, metric: str, status: str) -> None:
        """Start or cancel a delayed notification for a metric."""
        previous = self._conditions.get(metric)
        self._conditions[metric] = status
        if previous != status:
            if cancel := self._timers.pop(metric, None):
                cancel()
            self._notified = {item for item in self._notified if item[0] != metric}

        if not self.alerts_enabled or status not in (STATUS_LOW, STATUS_HIGH):
            if cancel := self._timers.pop(metric, None):
                cancel()
            return
        if metric in self._timers or (metric, status) in self._notified:
            return

        delay = float(self.config[f"{metric}_{status}_alert_minutes"]) * 60
        self._timers[metric] = async_call_later(
            self.hass,
            delay,
            lambda _now: self._async_send_alert(metric, status),
        )

    @callback
    def _async_send_alert(self, metric: str, status: str) -> None:
        """Create a notification if an alert condition still applies."""
        self._timers.pop(metric, None)
        if not self.alerts_enabled or self.status(metric) != status:
            return
        self._notified.add((metric, status))
        value = self.value(metric)
        unit = "°C" if metric == METRIC_TEMPERATURE else "%"
        limit = self.config[f"{metric}_{status}"]
        direction = "above" if status == STATUS_HIGH else "below"
        label = metric.capitalize()
        persistent_notification.async_create(
            self.hass,
            f"{value:g} {unit} is {direction} {limit:g} {unit}.",
            title=f"{self.name} — {label} {status}",
            notification_id=f"environment_monitor_{self.entry.entry_id}_{metric}_{status}",
        )

"""Config flow for Environment Monitor."""

from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlowWithReload
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)
from homeassistant.util import slugify

from .const import (
    CONF_ALERTS_ENABLED,
    CONF_HUMIDITY_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    DEFAULTS,
    DOMAIN,
    METRIC_HUMIDITY,
    METRIC_TEMPERATURE,
)
from .helpers import limits_are_valid


def suggested(key: str, values: dict[str, Any]) -> vol.Marker:
    """Return a field with a default or a suggested existing value."""
    if key in values:
        return vol.Required(key, description={"suggested_value": values[key]})
    if key in DEFAULTS:
        return vol.Required(key, default=DEFAULTS[key])
    return vol.Required(key)


def basic_schema(values: dict[str, Any]) -> vol.Schema:
    """Build the zone/source schema."""
    temperature = EntitySelector(
        EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.TEMPERATURE)
    )
    humidity = EntitySelector(
        EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.HUMIDITY)
    )
    fields: dict[vol.Marker, Any] = {
        suggested(CONF_NAME, values): TextSelector(),
        vol.Optional(
            CONF_TEMPERATURE_ENTITY,
            description={"suggested_value": values.get(CONF_TEMPERATURE_ENTITY)},
        ): temperature,
        vol.Optional(
            CONF_HUMIDITY_ENTITY,
            description={"suggested_value": values.get(CONF_HUMIDITY_ENTITY)},
        ): humidity,
        suggested(CONF_ALERTS_ENABLED, values): BooleanSelector(),
    }
    return vol.Schema(fields)


def metric_schema(metric: str, values: dict[str, Any]) -> vol.Schema:
    """Build a threshold and delay schema for a metric."""
    unit = "°C" if metric == METRIC_TEMPERATURE else "%"
    minimum, maximum, step = (
        (-100.0, 1000.0, 0.1)
        if metric == METRIC_TEMPERATURE
        else (0.0, 100.0, 1.0)
    )
    limit_selector = NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            unit_of_measurement=unit,
            mode=NumberSelectorMode.BOX,
        )
    )
    fields: dict[vol.Marker, Any] = {
        suggested(f"{metric}_{suffix}", values): limit_selector
        for suffix in ("low", "optimal_min", "optimal_max", "high")
    }
    if metric == METRIC_TEMPERATURE:
        fields.update(
            {
                suggested(f"temperature_chart_{bound}", values): limit_selector
                for bound in ("min", "max")
            }
        )
    delay_selector = NumberSelector(
        NumberSelectorConfig(
            min=1,
            max=120,
            step=1,
            unit_of_measurement="min",
            mode=NumberSelectorMode.BOX,
        )
    )
    fields.update(
        {
            suggested(f"{metric}_{state}_alert_minutes", values): delay_selector
            for state in ("low", "high")
        }
    )
    return vol.Schema(fields)


class FlowSteps:
    """Shared wizard steps for setup and editing."""

    values: dict[str, Any]

    async def _async_basic_step(
        self, step_id: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Collect the zone name and sources."""
        errors: dict[str, str] = {}
        if user_input is not None:
            name = str(user_input.get(CONF_NAME, "")).strip()
            if not name:
                errors[CONF_NAME] = "invalid_name"
            elif not user_input.get(CONF_TEMPERATURE_ENTITY) and not user_input.get(
                CONF_HUMIDITY_ENTITY
            ):
                errors["base"] = "no_sources"
            else:
                user_input[CONF_NAME] = name
                self.values.update(user_input)
                if not user_input.get(CONF_TEMPERATURE_ENTITY):
                    self.values.pop(CONF_TEMPERATURE_ENTITY, None)
                if not user_input.get(CONF_HUMIDITY_ENTITY):
                    self.values.pop(CONF_HUMIDITY_ENTITY, None)
                if user_input.get(CONF_TEMPERATURE_ENTITY):
                    return await self.async_step_temperature()
                return await self.async_step_humidity()
        return self.async_show_form(
            step_id=step_id,
            data_schema=basic_schema(self.values),
            errors=errors,
        )

    async def async_step_temperature(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect temperature limits."""
        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = {**self.values, **user_input}
            if limits_are_valid(candidate, METRIC_TEMPERATURE):
                self.values.update(user_input)
                if self.values.get(CONF_HUMIDITY_ENTITY):
                    return await self.async_step_humidity()
                return await self._async_finish()
            errors["base"] = "invalid_limits"
        return self.async_show_form(
            step_id="temperature",
            data_schema=metric_schema(METRIC_TEMPERATURE, self.values),
            errors=errors,
        )

    async def async_step_humidity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect humidity limits."""
        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = {**self.values, **user_input}
            if limits_are_valid(candidate, METRIC_HUMIDITY):
                self.values.update(user_input)
                return await self._async_finish()
            errors["base"] = "invalid_limits"
        return self.async_show_form(
            step_id="humidity",
            data_schema=metric_schema(METRIC_HUMIDITY, self.values),
            errors=errors,
        )

    async def _async_finish(self) -> ConfigFlowResult:
        """Finish the active flow."""
        raise NotImplementedError


class EnvironmentMonitorConfigFlow(FlowSteps, ConfigFlow, domain=DOMAIN):
    """Configure an Environment Monitor zone."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize a new setup flow."""
        self.values = dict(DEFAULTS)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start the setup wizard."""
        return await self._async_basic_step("user", user_input)

    async def _async_finish(self) -> ConfigFlowResult:
        """Create the zone config entry."""
        await self.async_set_unique_id(slugify(self.values[CONF_NAME]))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=self.values[CONF_NAME], data={}, options=self.values
        )

    @staticmethod
    def async_get_options_flow(config_entry: Any) -> "EnvironmentMonitorOptionsFlow":
        """Return the options flow handler."""
        return EnvironmentMonitorOptionsFlow()


class EnvironmentMonitorOptionsFlow(FlowSteps, OptionsFlowWithReload):
    """Edit an existing Environment Monitor zone."""

    def __init__(self) -> None:
        """Initialize the options flow."""
        self.values = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start the editing wizard."""
        if not self.values:
            self.values = {**DEFAULTS, **self.config_entry.options}
        return await self._async_basic_step("init", user_input)

    async def _async_finish(self) -> ConfigFlowResult:
        """Save updated options and reload the integration."""
        self.hass.config_entries.async_update_entry(
            self.config_entry, title=self.values[CONF_NAME]
        )
        return self.async_create_entry(data=self.values)

"""Constants for Environment Monitor."""

from typing import Final

DOMAIN: Final = "environment_monitor"
PLATFORMS: Final = ["number", "sensor", "switch"]

CONF_NAME: Final = "name"
CONF_TEMPERATURE_ENTITY: Final = "temperature_entity"
CONF_HUMIDITY_ENTITY: Final = "humidity_entity"
CONF_ALERTS_ENABLED: Final = "alerts_enabled"

METRIC_TEMPERATURE: Final = "temperature"
METRIC_HUMIDITY: Final = "humidity"
METRICS: Final = (METRIC_TEMPERATURE, METRIC_HUMIDITY)

STATUS_OPTIMAL: Final = "optimal"
STATUS_ACCEPTABLE: Final = "acceptable"
STATUS_LOW: Final = "low"
STATUS_HIGH: Final = "high"
STATUS_UNAVAILABLE: Final = "unavailable"
STATUS_OPTIONS: Final = [
    STATUS_OPTIMAL,
    STATUS_ACCEPTABLE,
    STATUS_LOW,
    STATUS_HIGH,
    STATUS_UNAVAILABLE,
]

DEFAULTS: Final = {
    CONF_ALERTS_ENABLED: False,
    "temperature_low": 14.0,
    "temperature_optimal_min": 16.0,
    "temperature_optimal_max": 20.0,
    "temperature_high": 22.0,
    "temperature_chart_min": 10.0,
    "temperature_chart_max": 30.0,
    "temperature_low_alert_minutes": 15.0,
    "temperature_high_alert_minutes": 10.0,
    "humidity_low": 30.0,
    "humidity_optimal_min": 35.0,
    "humidity_optimal_max": 50.0,
    "humidity_high": 60.0,
    "humidity_low_alert_minutes": 15.0,
    "humidity_high_alert_minutes": 15.0,
}

LIMIT_SUFFIXES: Final = ("low", "optimal_min", "optimal_max", "high")

"""Pure helpers for Environment Monitor."""

from collections.abc import Mapping
from typing import Any

from .const import (
    LIMIT_SUFFIXES,
    STATUS_ACCEPTABLE,
    STATUS_HIGH,
    STATUS_LOW,
    STATUS_OPTIMAL,
    STATUS_UNAVAILABLE,
)


def metric_status(value: float | None, metric: str, config: Mapping[str, Any]) -> str:
    """Classify a metric value using its configured limits."""
    if value is None:
        return STATUS_UNAVAILABLE
    low, optimal_min, optimal_max, high = (
        float(config[f"{metric}_{suffix}"]) for suffix in LIMIT_SUFFIXES
    )
    if value < low:
        return STATUS_LOW
    if value > high:
        return STATUS_HIGH
    if optimal_min <= value <= optimal_max:
        return STATUS_OPTIMAL
    return STATUS_ACCEPTABLE


def overall_status(statuses: list[str]) -> str:
    """Return the most important state across enabled metrics."""
    for state in (STATUS_HIGH, STATUS_LOW, STATUS_UNAVAILABLE, STATUS_ACCEPTABLE):
        if state in statuses:
            return state
    return STATUS_OPTIMAL


def limits_are_valid(config: Mapping[str, Any], metric: str) -> bool:
    """Validate ordered limits and the optional temperature chart range."""
    limits = [float(config[f"{metric}_{suffix}"]) for suffix in LIMIT_SUFFIXES]
    if limits != sorted(limits):
        return False
    if metric == "temperature":
        return (
            float(config["temperature_chart_min"]) <= limits[0]
            and float(config["temperature_chart_max"]) >= limits[-1]
        )
    return True

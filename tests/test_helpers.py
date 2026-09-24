"""Tests for the integration's dependency-free status helpers."""

import importlib
from pathlib import Path
import sys
from types import ModuleType
import unittest


ROOT = Path(__file__).parents[1]
PACKAGE_PATH = ROOT / "custom_components" / "environment_monitor"

# Load the pure modules without importing the Home Assistant-dependent package
# initializer, keeping these tests lightweight for contributors.
custom_components = ModuleType("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]
environment_monitor = ModuleType("custom_components.environment_monitor")
environment_monitor.__path__ = [str(PACKAGE_PATH)]
sys.modules.setdefault("custom_components", custom_components)
sys.modules.setdefault("custom_components.environment_monitor", environment_monitor)

const = importlib.import_module("custom_components.environment_monitor.const")
helpers = importlib.import_module("custom_components.environment_monitor.helpers")


class HelpersTest(unittest.TestCase):
    """Exercise classification and validation behavior."""

    def setUp(self) -> None:
        """Create an independent default configuration."""
        self.config = dict(const.DEFAULTS)

    def test_metric_status_classifies_all_bands(self) -> None:
        """Temperature readings map to all expected bands."""
        cases = {
            13.9: const.STATUS_LOW,
            14.0: const.STATUS_ACCEPTABLE,
            16.0: const.STATUS_OPTIMAL,
            20.0: const.STATUS_OPTIMAL,
            20.1: const.STATUS_ACCEPTABLE,
            22.1: const.STATUS_HIGH,
            None: const.STATUS_UNAVAILABLE,
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(
                    helpers.metric_status(value, const.METRIC_TEMPERATURE, self.config),
                    expected,
                )

    def test_overall_status_uses_documented_priority(self) -> None:
        """A more important condition wins across metrics."""
        self.assertEqual(
            helpers.overall_status([const.STATUS_LOW, const.STATUS_HIGH]),
            const.STATUS_HIGH,
        )
        self.assertEqual(
            helpers.overall_status(
                [const.STATUS_ACCEPTABLE, const.STATUS_UNAVAILABLE]
            ),
            const.STATUS_UNAVAILABLE,
        )
        self.assertEqual(
            helpers.overall_status([const.STATUS_OPTIMAL, const.STATUS_ACCEPTABLE]),
            const.STATUS_ACCEPTABLE,
        )

    def test_limits_must_be_ordered(self) -> None:
        """Reject crossed threshold bands."""
        self.assertTrue(helpers.limits_are_valid(self.config, "temperature"))
        self.config["temperature_optimal_min"] = 23
        self.assertFalse(helpers.limits_are_valid(self.config, "temperature"))

    def test_temperature_chart_contains_limits(self) -> None:
        """Reject chart bounds that clip thresholds."""
        self.config["temperature_chart_min"] = 15
        self.assertFalse(helpers.limits_are_valid(self.config, "temperature"))


if __name__ == "__main__":
    unittest.main()

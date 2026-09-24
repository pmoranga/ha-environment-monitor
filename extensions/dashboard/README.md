# Optional Lovelace dashboard

This extension visualizes the core's two source entities over the last 24 hours
with configurable colour bands.

## Dependencies

Install these cards with HACS, then add their resources in Home Assistant:

1. ApexCharts Card
2. Config Template Card
3. Mushroom

## Install

Choose one approach:

- Add `card.yaml` as a Manual card; or
- Create a YAML dashboard, copy `card.yaml` to
  `/config/dashboards/environment-monitor-card.yaml`, and adapt
  `dashboard.yaml` to the dashboard's actual include path.

The core must be installed first. Changing its Helpers immediately updates the
card's bands and alert controls.

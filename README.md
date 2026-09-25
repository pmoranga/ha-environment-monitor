# Home Assistant Environment Monitor

[![GitHub Release](https://img.shields.io/github/v/release/pmoranga/ha-environment-monitor?style=for-the-badge)](https://github.com/pmoranga/ha-environment-monitor/releases)
[![Validation](https://img.shields.io/github/actions/workflow/status/pmoranga/ha-environment-monitor/validate.yml?branch=main&style=for-the-badge&label=validation)](https://github.com/pmoranga/ha-environment-monitor/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/pmoranga/ha-environment-monitor)](LICENSE)

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz)
[![Maintained](https://img.shields.io/badge/maintained-yes-brightgreen?style=for-the-badge)](https://github.com/pmoranga/ha-environment-monitor/commits/main)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.9%2B-blue?style=for-the-badge)](https://www.home-assistant.io/)

A Home Assistant custom integration that classifies temperature and humidity for
independent rooms, zones, or sensing points. It is installed and configured from
the Home Assistant UI—there is no YAML generator or package to maintain.

Each zone can monitor temperature, humidity, or both. The integration creates a
device for the zone containing status sensors, editable threshold and delay
numbers, and an alerts switch.

## Install

### HACS

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pmoranga&repository=ha-environment-monitor&category=integration)

1. In HACS, open **Integrations**.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add `https://github.com/pmoranga/ha-environment-monitor` as an
   **Integration** repository.
4. Install **Environment Monitor** and restart Home Assistant.

### Manual

Copy `custom_components/environment_monitor` into the matching directory under
your Home Assistant configuration folder:

```text
/config/custom_components/environment_monitor
```

Restart Home Assistant after the initial installation.

## Add a zone with the installation wizard

[![Open your Home Assistant instance and start setting up Environment Monitor.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=environment_monitor)

1. Go to **Settings → Devices & services**.
2. Choose **Add integration** and search for **Environment Monitor**.
3. Name the zone and select a temperature sensor, a humidity sensor, or both.
4. Review the threshold bands and notification delays.
5. Repeat **Add integration** for every additional zone.

Temperature sources may use °C or °F. Values are normalized to °C internally,
and Home Assistant displays temperature settings in the user's configured unit.

## Status model

The four thresholds must remain ordered:

```text
low ≤ optimal minimum ≤ optimal maximum ≤ high
```

A reading is classified as:

- **low** below the low limit;
- **acceptable** between a low/high limit and the optimal band;
- **optimal** inside the optimal band (inclusive);
- **high** above the high limit;
- unavailable when the selected source has no numeric value.

The overall sensor prioritizes `high`, then `low`, unavailable, `acceptable`,
and finally `optimal` across the enabled metrics.

## Entities

Every zone has:

- an **Overall status** sensor;
- a **Temperature status** and/or **Humidity status** sensor;
- editable numbers for the enabled metric's limits and alert delays;
- temperature chart minimum/maximum numbers for dashboard use;
- an **Alerts** switch.

When alerts are enabled and a metric remains low or high for its configured
delay, the integration creates one persistent notification. A new notification
can occur after that metric returns to another state and later becomes low or
high again.

Use **Configure** on an Environment Monitor integration entry to change its
name, source sensors, thresholds, delays, or initial alert setting. Number and
switch entities can also be changed directly from a dashboard or automation.

## Migrating from the YAML generator

1. Install this integration and create a wizard entry for each former zone.
2. Recreate any dashboard references or automations with the new entity IDs
   shown on the zone device page.
3. Remove the old generated package from `/config/packages`.
4. Restart Home Assistant once to remove the old package entities.

Do not keep both implementations active for the same zone: they will create
duplicate status entities and notifications.

## Development

The dependency-free unit tests cover threshold validation and status priority:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q custom_components tests
```

## License

Environment Monitor is available under the [MIT License](LICENSE).

# Home Assistant Environment Monitor

Reusable, vendor-neutral monitoring for one temperature entity and one humidity
entity. The repository is deliberately split into a small core and optional
frontend extensions.

## Layout

- [`core/`](core/) — Helpers, calculated status entities and alert automations.
  This is the only component installed in Home Assistant today.
- [`extensions/dashboard/`](extensions/dashboard/) — an optional 24-hour
  Lovelace dashboard with configurable colour bands. It requires HACS cards
  and is not installed by the core.

No database, history, Home Assistant `.storage` data, credentials, or
`secrets.yaml` belongs in this repository.

## Install the core

1. Create `/config/packages/` if necessary.
2. Copy [`core/environment_monitor.yaml`](core/environment_monitor.yaml) to
   `/config/packages/environment_monitor.yaml`.
3. Ensure `configuration.yaml` contains the following inside its existing
   `homeassistant:` section:

   ```yaml
   packages: !include_dir_named packages
   ```

4. Validate the configuration and restart Home Assistant.
5. In **Settings → Devices & services → Helpers**, set:

   - **Temperature source** to the source `sensor.*` entity ID.
   - **Humidity source** to the source `sensor.*` entity ID.

The default example entity IDs are inert until replaced. The initial values are
applied once; Helper changes persist across restarts.

## Entities provided by the core

- `sensor.environment_temperature_status`
- `sensor.environment_humidity_status`
- `sensor.environment_overall_status`

Their machine-readable states are `optimal`, `acceptable`, `low`, `high`, and
`unavailable`. Add these entities to any native Lovelace Entities or Tile card.
The source Helpers are configuration fields; they are not status entities.

## Configure bands and alerts

All limits and alert delays are `input_number` Helpers. `Alertas ativados`
is an on/off switch for all four alerts and starts **off**. Keep the limits in
ascending order:

```text
chart minimum ≤ low limit ≤ optimal minimum ≤ optimal maximum ≤ high limit ≤ chart maximum
```

The default bands target a baby's bedroom:

- Temperature: `14 / 16 / 20 / 22 °C`. This makes 16–20 °C optimal,
  14–16 °C and 20–22 °C acceptable, and values outside 14–22 °C low/high.
- Humidity: `30 / 35 / 50 / 60 %`. This makes 35–50% optimal, 30–35% and
  50–60% acceptable, and values outside 30–60% low/high.

When alerts are enabled, four automations create persistent Home Assistant
notifications when values remain low or high longer than the configured delay.

## Optional dashboard

See [`extensions/dashboard/README.md`](extensions/dashboard/README.md) only
when you want the richer, colour-banded 24-hour dashboard. It has separate
frontend dependencies and does not affect the core installation.

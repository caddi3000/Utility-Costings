# Home Assistant Utility Cost — v0.5.0

A Home Assistant package + Lovelace card for time-of-use electricity cost accounting.

## What v0.5 adds

- True **TOU dollar accumulation**: each tracked device is costed using the tariff active at the time it consumed energy.
- **Today / Month / Bill cycle / Year** energy and dollar meters.
- Whole-bill estimate: **grid import cost + daily supply charge − solar export credit**.
- Tiered daily FIT: first configured kWh/day at Tier 1, remaining export at Tier 2.
- Tracked and **Other / Untracked** load cost views.
- Rate changes preserve historical accumulated dollars. Change the helpers and only future consumption uses the new rates.
- Device list remains generated from one file: `config/devices.yaml`.

## Current defaults

The supplied defaults are EnergyAustralia Solar Max: peak 0.581713 AUD/kWh, shoulder 0.210584, off-peak 0.348018, supply 1.260600 AUD/day, FIT 0.08 for the first 10 kWh/day then 0.03.

## Install

1. Copy `packages/utility_cost.yaml` to your HA `packages` directory and ensure packages are enabled in `configuration.yaml`.
2. Copy both files in `www/` to `/config/www/`.
3. Add `/local/utility-cost-devices.js` and `/local/utility-cost-card.js` as Lovelace JavaScript module resources, in that order.
4. Restart Home Assistant.
5. Add the card shown in `examples/lovelace.yaml`.

## Changing electricity plan later

Change these HA helpers; do **not** edit the card:

- `input_text.utility_plan_name`
- `input_number.utility_peak_rate`
- `input_number.utility_shoulder_rate`
- `input_number.utility_offpeak_rate`
- `input_number.utility_supply_daily`
- `input_number.utility_fit_tier1`
- `input_number.utility_fit_tier2`
- `input_number.utility_fit_threshold`

The cost ledger integrates live cost flow, so accumulated historical costs stay at their old tariff and new usage is charged at the new tariff.

## Bill cycle

The generated bill meter currently resets at midnight on the same day-of-month as `bill_cycle_start`, every three months anchored to its month. With the supplied `2026-09-05` start this generates `0 0 5 3,6,9,12 *` (5 Mar/Jun/Sep/Dec). If your retailer changes the billing-cycle anchor, edit `config/tariff_defaults.yaml` and rerun `python3 tools/generate.py`.

## Add/remove devices

Edit only `config/devices.yaml`, then run:

```bash
python3 tools/generate.py
```

The generator creates energy integrations, period meters, TOU cost integrations and the Lovelace device registry.

## Accuracy notes

The **net bill** is the retailer-style estimate and uses grid import, supply charge and FIT. Individual appliance costs are useful TOU-equivalent attribution. A device powered by self-consumed solar cannot be uniquely assigned a retailer grid cost without circuit/source-level energy-flow attribution.

FIT tier switching is based on the daily export meter. Around the exact tier threshold there can be a very small integration-step discrepancy depending on source update frequency.

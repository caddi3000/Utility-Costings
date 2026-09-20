# Utility Cost v1.2.1

Home Assistant custom integration for electricity bill estimation and per-device time-of-use costing.

## What's new in 1.2.1
- Correct daily supply charge: one full configured daily charge is posted per active billing day instead of accruing it hourly.
- Per-device Peak / Shoulder / Off-peak kWh and cost accumulation.
- Expandable device breakdown in both bundled Lovelace cards.
- Editable tariff rates, daily supply charge, FIT, tariff time windows, bill-cycle start, system entities and tracked devices through **Settings → Devices & services → Integrations → Utility Cost → Configure**.
- Weekly, monthly, bill-period and yearly accounting retained.
- Bill cycle now advances in 3-calendar-month periods from the configured cycle start rather than a fixed 91-day approximation.

## HACS repository layout
This repository is an **Integration** repository. `custom_components/utility_cost` must be directly under the repository root.

## Frontend resources
The integration serves:
- `/utility_cost_static/utility-cost-card.js?v=121`
- `/utility_cost_static/utility-bill-card.js?v=121`

If your HA installation does not auto-load the bundled cards, add those two URLs under **Settings → Dashboards → Resources** as **JavaScript module** resources.

## Cards
```yaml
type: custom:utility-cost-card
```

```yaml
type: custom:utility-bill-card
default_period: bill
```

## Cost meaning
The top bill estimate is retailer-style: grid import charges + supply charge − solar FIT credit.

Tracked-device totals are **tariff costs**: each device's measured energy is accumulated against the Peak, Shoulder or Off-peak rate active at that moment. Because whole-home solar data cannot identify which individual appliance consumed each unit of self-generated solar, device tariff cost is intentionally kept separate from the retailer bill estimate.


## v1.2.1

Maintenance release for upgrades from earlier Utility Cost versions. Adds the Home Assistant config-entry migration handler required to upgrade existing installations to schema version 2 without deleting and recreating the integration. Existing entity selections, tariffs and options are preserved; newly introduced settings receive defaults only when missing.

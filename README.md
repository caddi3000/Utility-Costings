# Utility Cost v1.2.2 — unified release

One HACS **Integration** containing the Utility Cost accounting backend and both Lovelace cards. This is the only repository required.

## Included
- Retailer-style bill estimate: grid import charges + daily supply charge − solar FIT credit.
- Full daily supply charge posted once per active billing day.
- Peak / Shoulder / Off-peak accounting.
- Per-device TOU kWh and tariff-cost breakdown for Today, Week, Month, Bill Period and Year.
- Editable plan, tariffs, FIT tiers, tariff windows, bill-cycle start, source entities and tracked devices through the integration Configure flow.
- Config-entry migration for installations created with earlier Utility Cost versions.
- Both bundled cards: `utility-cost-card` and `utility-bill-card`.

## HACS
Add `caddi3000/Utility-Costings` as an **Integration**. `custom_components/utility_cost` must be directly under the repository root. Do not install a separate Electricity-Bill-Cost dashboard repository for this release.

## Lovelace cards
```yaml
type: custom:utility-cost-card
```

```yaml
type: custom:utility-bill-card
default_period: bill
```

The integration serves the frontend at:
- `/utility_cost_static/utility-cost-card.js?v=122`
- `/utility_cost_static/utility-bill-card.js?v=122`

If your Home Assistant installation does not auto-load them, add both under **Settings → Dashboards → Resources** as JavaScript modules.

## Configuration
Use **Settings → Devices & services → Integrations → Utility Cost → Configure**. Entity IDs are selected in Home Assistant; they are not hard-coded into the integration.

## Device cost meaning
Device totals are **tariff costs**. Each tracked device's measured energy is assigned to the Peak, Shoulder or Off-peak rate active during that interval. These figures are kept separate from the retailer bill estimate because whole-house solar metering cannot determine the exact solar/grid source of energy consumed by each individual device.

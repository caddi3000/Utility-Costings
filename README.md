# Utility Cost v1.3.0

Unified Home Assistant custom integration and Lovelace cards for electricity bill estimation and per-device costing.

## v1.3.0
- Repairs per-device Peak / Shoulder / Off-peak accumulation for all new samples.
- Older device energy that predates TOU buckets is shown explicitly as **Before TOU tracking** rather than incorrectly appearing as zero-use tariff rows.
- Adds estimated per-device bill impact using the whole-property net Fronius/grid-meter supply mix at each one-minute interval.
- Tracks estimated grid-supplied kWh, solar-supplied kWh, grid cost, lost FIT opportunity cost, bill impact, solar supplied %, and estimated solar saving.
- The attribution is deliberately phase-balanced: it uses the net whole-property import position, not an individual electrical phase.
- Adds an inline **Rates** editor to the Utility Cost dashboard card for Peak, Shoulder, Off-peak, supply, FIT tiers and FIT threshold. Changes apply to future accumulation; historical costs are not repriced.
- Keeps the full Home Assistant Configure flow for entities, tariff windows and bill-cycle settings.
- Both `utility-cost-card` and `utility-bill-card` remain bundled in this one HACS Integration.

## Cards
```yaml
type: custom:utility-cost-card
```

```yaml
type: custom:utility-bill-card
default_period: bill
```

If manually registering resources, use:
- `/utility_cost_static/utility-cost-card.js?v=130`
- `/utility_cost_static/utility-bill-card.js?v=130`

## Important accounting note
Per-device grid/solar attribution is an accounting estimate based on the whole-house supply mix at each interval. It is appropriate for a net-metered three-phase property, but it is not physical circuit-level tracing. Solar opportunity cost uses the applicable FIT tier estimate at that interval.

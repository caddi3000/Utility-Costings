# Utility Cost Card

Home Assistant electricity-cost dashboard with time-of-use accounting, solar FIT, supply charges, bill-cycle totals and per-device tracking.

## HACS installation

This repository is structured as a HACS **Dashboard** (Lovelace/plugin) repository. The installable frontend file is `utility-cost-card.js` at the repository root.

1. Put this repository on GitHub.
2. In HACS, add the GitHub repository as a **Dashboard** custom repository.
3. Install **Utility Cost Card**.
4. HACS should register the frontend resource automatically. If your HACS version asks you to add it manually, use the HACS-provided `/hacsfiles/.../utility-cost-card.js` module path rather than `/local/`.
5. Add the card:

```yaml
type: custom:utility-cost-card
title: Utility Cost
```

## Backend (one-time Home Assistant setup)

HACS Dashboard installation installs the frontend card only. The accounting backend is deliberately kept as a Home Assistant package in `packages/utility_cost.yaml`.

Copy `packages/utility_cost.yaml` to your HA `/config/packages/utility_cost.yaml` and ensure packages are enabled in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Restart Home Assistant after checking configuration.

The backend contains the TOU accumulators, supply charge, tiered FIT, Today/Month/Bill/Year totals and plan/rate helpers. Rates can be changed later in Home Assistant without modifying the card source.

## Device configuration

Source definitions live in `config/devices.yaml`. `tools/generate.py` remains in the repository for regenerating the backend when tracked entities are added or changed. The generated device registry is bundled into `utility-cost-card.js`, so HACS only has one frontend asset to install.

## Current Solar Max defaults

- Peak: $0.581713/kWh
- Shoulder: $0.210584/kWh
- Off peak: $0.348018/kWh
- Supply: $1.260600/day
- FIT tier 1: $0.08/kWh for first 10 kWh/day
- FIT tier 2: $0.03/kWh thereafter

## Repository layout

```text
utility-cost-card.js        HACS-installed Lovelace card (single bundled asset)
hacs.json                   HACS metadata
packages/utility_cost.yaml  HA accounting backend
config/                     source configuration
tools/generate.py           generator
examples/lovelace.yaml      card example
```

## Upgrading from v0.5.0

Remove the old custom repository entry if HACS marked it non-compliant, then add the corrected GitHub repository again as category **Dashboard**. Do not add `www/utility-cost-devices.js` as a separate resource; v0.6.0 bundles it into the main card.

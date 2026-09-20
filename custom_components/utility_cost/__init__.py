"""Utility Cost integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path
import voluptuous as vol

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, PLATFORMS, CONF_PEAK, CONF_SHOULDER, CONF_OFFPEAK, CONF_SUPPLY, CONF_FIT1, CONF_FIT2, CONF_FIT_LIMIT
from .engine import CostEngine

_LOGGER = logging.getLogger(__name__)
CARD_VERSION = "1.3.0"
CARD_PATH = Path(__file__).parent / "frontend" / "utility-cost-card.js"
BILL_CARD_PATH = Path(__file__).parent / "frontend" / "utility-bill-card.js"
CARD_URL = "/utility_cost_static/utility-cost-card.js"
BILL_CARD_URL = "/utility_cost_static/utility-bill-card.js"
CARD_MODULE_URL = f"{CARD_URL}?v={CARD_VERSION.replace('.', '')}"
BILL_CARD_MODULE_URL = f"{BILL_CARD_URL}?v={CARD_VERSION.replace('.', '')}"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Utility Cost and expose the bundled Lovelace card."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), False), StaticPathConfig(BILL_CARD_URL, str(BILL_CARD_PATH), False)]
    )
    # Load the bundled card globally. This is intentionally independent of
    # Lovelace storage resources, so it also works with YAML dashboards.
    add_extra_js_url(hass, CARD_MODULE_URL)
    add_extra_js_url(hass, BILL_CARD_MODULE_URL)
    _LOGGER.info("Utility Cost card registered at %s", CARD_MODULE_URL)

    async def _update_rates(call):
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        entry = entries[0]
        options = dict(entry.options)
        for key in (CONF_PEAK, CONF_SHOULDER, CONF_OFFPEAK, CONF_SUPPLY, CONF_FIT1, CONF_FIT2, CONF_FIT_LIMIT):
            if key in call.data:
                options[key] = float(call.data[key])
        hass.config_entries.async_update_entry(entry, options=options)

    if not hass.services.has_service(DOMAIN, "update_rates"):
        hass.services.async_register(
            DOMAIN, "update_rates", _update_rates,
            schema=vol.Schema({
                vol.Optional(CONF_PEAK): vol.Coerce(float), vol.Optional(CONF_SHOULDER): vol.Coerce(float),
                vol.Optional(CONF_OFFPEAK): vol.Coerce(float), vol.Optional(CONF_SUPPLY): vol.Coerce(float),
                vol.Optional(CONF_FIT1): vol.Coerce(float), vol.Optional(CONF_FIT2): vol.Coerce(float),
                vol.Optional(CONF_FIT_LIMIT): vol.Coerce(float),
            })
        )
    return True


async def async_migrate_entry(hass: HomeAssistant, entry) -> bool:
    """Migrate older Utility Cost config entries to the current schema."""
    _LOGGER.info(
        "Migrating Utility Cost config entry %s from version %s",
        entry.entry_id,
        entry.version,
    )

    if entry.version > 2:
        _LOGGER.error(
            "Cannot migrate Utility Cost config entry %s from future version %s",
            entry.entry_id,
            entry.version,
        )
        return False

    data = dict(entry.data)

    if entry.version < 2:
        # v2 added editable TOU windows and a configurable bill-cycle anchor.
        # Keep every value/entity selected by the user and only add fields that
        # did not exist in the older entry. Options are intentionally left
        # untouched and continue to override entry.data.
        from .const import DEFAULTS

        for key, value in DEFAULTS.items():
            data.setdefault(key, value)

        hass.config_entries.async_update_entry(entry, data=data, version=2)

    _LOGGER.info(
        "Utility Cost config entry %s migration complete; version=%s",
        entry.entry_id,
        entry.version,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up a Utility Cost config entry."""
    eng = CostEngine(hass, entry)
    await eng.load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = eng

    async def _tick(now):
        await eng.tick(now)

    entry.async_on_unload(
        async_track_time_interval(hass, _tick, timedelta(minutes=1))
    )
    entry.async_on_unload(entry.add_update_listener(_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _reload(hass: HomeAssistant, entry) -> None:
    """Reload after options/config changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a Utility Cost config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return ok

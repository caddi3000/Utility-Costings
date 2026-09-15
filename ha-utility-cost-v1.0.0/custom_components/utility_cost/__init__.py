from pathlib import Path
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from .const import DOMAIN, PLATFORMS
from .engine import CostEngine

CARD_URL="/utility_cost/utility-cost-card.js"
async def async_setup(hass, config):
    path=Path(__file__).parent/"frontend"/"utility-cost-card.js"
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL,str(path),False)])
    return True
async def async_setup_entry(hass, entry):
    eng=CostEngine(hass,entry); await eng.load(); hass.data.setdefault(DOMAIN,{})[entry.entry_id]=eng
    async def _tick(now): await eng.tick(now)
    entry.async_on_unload(async_track_time_interval(hass,_tick,timedelta(minutes=1)))
    entry.async_on_unload(entry.add_update_listener(_reload))
    await hass.config_entries.async_forward_entry_setups(entry,PLATFORMS)
    await _register_card(hass)
    return True
async def _register_card(hass):
    try:
        resources=hass.data.get("lovelace",{}).get("resources")
        if resources and hasattr(resources,"async_create_item"):
            items=resources.async_items()
            if not any(i.get("url","").startswith(CARD_URL) for i in items): await resources.async_create_item({"res_type":"module","url":CARD_URL})
    except Exception: pass
async def _reload(hass,entry): await hass.config_entries.async_reload(entry.entry_id)
async def async_unload_entry(hass,entry):
    ok=await hass.config_entries.async_unload_platforms(entry,PLATFORMS)
    if ok:hass.data[DOMAIN].pop(entry.entry_id,None)
    return ok

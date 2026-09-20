from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *

POWER = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power"))
POWER_MULTI = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power", multiple=True))

def system_schema(defaults=None):
    d = defaults or {}
    schema = {}
    for key, sel in (
        (CONF_GRID_IMPORT, POWER),
        (CONF_GRID_EXPORT, POWER),
        (CONF_HOUSE_POWER, POWER),
    ):
        if d.get(key):
            schema[vol.Required(key, default=d[key])] = sel
        else:
            schema[vol.Required(key)] = sel
    if d.get(CONF_SOLAR_POWER):
        schema[vol.Optional(CONF_SOLAR_POWER, default=d[CONF_SOLAR_POWER])] = POWER
    else:
        schema[vol.Optional(CONF_SOLAR_POWER)] = POWER
    if d.get(CONF_TRACKED):
        schema[vol.Optional(CONF_TRACKED, default=d[CONF_TRACKED])] = POWER_MULTI
    else:
        schema[vol.Optional(CONF_TRACKED)] = POWER_MULTI
    return vol.Schema(schema)

def tariff_schema(defaults=None):
    d = {**DEFAULTS, **(defaults or {})}
    return vol.Schema({
        vol.Required(CONF_PLAN, default=d[CONF_PLAN]): selector.TextSelector(),
        vol.Required(CONF_PEAK, default=d[CONF_PEAK]): vol.Coerce(float),
        vol.Required(CONF_SHOULDER, default=d[CONF_SHOULDER]): vol.Coerce(float),
        vol.Required(CONF_OFFPEAK, default=d[CONF_OFFPEAK]): vol.Coerce(float),
        vol.Required(CONF_SUPPLY, default=d[CONF_SUPPLY]): vol.Coerce(float),
        vol.Required(CONF_FIT1, default=d[CONF_FIT1]): vol.Coerce(float),
        vol.Required(CONF_FIT2, default=d[CONF_FIT2]): vol.Coerce(float),
        vol.Required(CONF_FIT_LIMIT, default=d[CONF_FIT_LIMIT]): vol.Coerce(float),
        vol.Required(CONF_BILL_START, default=d[CONF_BILL_START]): selector.DateSelector(),
        vol.Required(CONF_PEAK_AM_START, default=d[CONF_PEAK_AM_START]): selector.TimeSelector(),
        vol.Required(CONF_PEAK_AM_END, default=d[CONF_PEAK_AM_END]): selector.TimeSelector(),
        vol.Required(CONF_SHOULDER_START, default=d[CONF_SHOULDER_START]): selector.TimeSelector(),
        vol.Required(CONF_SHOULDER_END, default=d[CONF_SHOULDER_END]): selector.TimeSelector(),
        vol.Required(CONF_PEAK_PM_START, default=d[CONF_PEAK_PM_START]): selector.TimeSelector(),
        vol.Required(CONF_PEAK_PM_END, default=d[CONF_PEAK_PM_END]): selector.TimeSelector(),
    })

class UtilityCostConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2
    def __init__(self): self._data = {}
    async def async_step_user(self, user_input=None):
        if self._async_current_entries(): return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            self._data.update(user_input); return await self.async_step_tariffs()
        return self.async_show_form(step_id="user", data_schema=system_schema())
    async def async_step_tariffs(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input); return self.async_create_entry(title="Utility Cost", data=self._data)
        return self.async_show_form(step_id="tariffs", data_schema=tariff_schema())
    @staticmethod
    def async_get_options_flow(config_entry): return UtilityCostOptionsFlow(config_entry)

class UtilityCostOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry): self.entry=entry; self._data={}
    async def async_step_init(self,user_input=None):
        current={**self.entry.data,**self.entry.options}
        if user_input is not None:
            self._data.update(user_input); return await self.async_step_tariffs()
        return self.async_show_form(step_id="init",data_schema=system_schema(current),description_placeholders={"hint":"Select which entities Utility Cost should monitor."})
    async def async_step_tariffs(self,user_input=None):
        current={**self.entry.data,**self.entry.options,**self._data}
        if user_input is not None:
            self._data.update(user_input); return self.async_create_entry(title="",data=self._data)
        return self.async_show_form(step_id="tariffs",data_schema=tariff_schema(current))

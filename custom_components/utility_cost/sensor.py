from __future__ import annotations
import re
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    eng=hass.data[DOMAIN][entry.entry_id]
    entities=[]
    for p in ("today","week","month","bill","year"):
        entities += [BillSensor(eng,p,"net"),BillSensor(eng,p,"grid"),BillSensor(eng,p,"supply"),BillSensor(eng,p,"fit")]
    for eid in eng.cfg.get("tracked_power_entities",[]):
        for p in ("today","week","month","bill","year"): entities.append(DeviceCostSensor(eng,p,eid))
    entities += [ActiveTariffSensor(eng), UntrackedPowerSensor(eng)]
    async_add_entities(entities)

class Base(SensorEntity):
    _attr_has_entity_name=True
    def __init__(self,eng): self.eng=eng; eng.listeners.append(self.async_write_ha_state)
    @property
    def device_info(self): return DeviceInfo(identifiers={(DOMAIN,self.eng.entry.entry_id)},name="Utility Cost",manufacturer="Custom",model="Utility bill accounting")

class BillSensor(Base):
    _attr_native_unit_of_measurement="AUD"; _attr_device_class=SensorDeviceClass.MONETARY; _attr_state_class=SensorStateClass.TOTAL
    def __init__(self,eng,p,kind):
        super().__init__(eng); self.p=p; self.kind=kind; self._attr_unique_id=f"utility_cost_{p}_{kind}"; self._attr_name=f"{p.title()} {kind.title()} Cost"
    @property
    def native_value(self):
        x=self.eng.period(self.p); v=x[self.kind] if self.kind!="net" else x["grid"]+x["supply"]-x["fit"]; return round(v,2)
    @property
    def extra_state_attributes(self):
        x=self.eng.period(self.p)
        return {"utility_cost_role":self.kind,"period":self.p,"period_key":x.get("key"),"plan":self.eng.cfg.get("plan_name"),"grid_cost":round(x.get("grid",0),4),"supply_cost":round(x.get("supply",0),4),"solar_credit":round(x.get("fit",0),4),"house_kwh":round(x.get("house_kwh",0),3),"tracked_kwh":round(x.get("tracked_kwh",0),3),"grid_kwh":round(x.get("grid_kwh",0),3),"export_kwh":round(x.get("export_kwh",0),3),"solar_kwh":round(x.get("solar_kwh",0),3),"tariff_kwh":x.get("tariff_kwh",{}),"tariff_cost":x.get("tariff_cost",{}),"rates":{"peak_rate":self.eng.cfg.get("peak_rate"),"shoulder_rate":self.eng.cfg.get("shoulder_rate"),"offpeak_rate":self.eng.cfg.get("offpeak_rate"),"supply_daily":self.eng.cfg.get("supply_daily"),"fit_tier1":self.eng.cfg.get("fit_tier1"),"fit_tier2":self.eng.cfg.get("fit_tier2"),"fit_daily_limit":self.eng.cfg.get("fit_daily_limit")},"data_since":self.eng.data.get("started_at")}

def _display_name(st,eid):
    name=(st.attributes.get("friendly_name") if st else None) or eid.split(".",1)[-1].replace("_"," ").title()
    name=re.sub(r"^Utility Cost\s+", "", name, flags=re.I)
    name=re.sub(r"^sensor[.:_\s-]+", "", name, flags=re.I)
    name=re.sub(r"^\[evcc\]\s*", "EV ", name, flags=re.I)
    return name.strip()

class DeviceCostSensor(Base):
    _attr_native_unit_of_measurement="AUD"; _attr_device_class=SensorDeviceClass.MONETARY; _attr_state_class=SensorStateClass.TOTAL
    def __init__(self,eng,p,eid):
        super().__init__(eng); self.p=p; self.eid=eid; slug=eid.replace(".","_"); self._attr_unique_id=f"utility_cost_{p}_{slug}"; self.display_name=_display_name(eng.hass.states.get(eid),eid); self._attr_name=f"{self.display_name} {p.title()} Cost"
    @property
    def native_value(self): return round(self.eng.period(self.p).get("devices",{}).get(self.eid,0),2)
    @property
    def extra_state_attributes(self):
        x=self.eng.period(self.p)
        
        energy=x.get("device_kwh",{}).get(self.eid,0); tk=x.get("device_tariff_kwh",{}).get(self.eid,{"peak":0.0,"shoulder":0.0,"offpeak":0.0}); tc=x.get("device_tariff_cost",{}).get(self.eid,{"peak":0.0,"shoulder":0.0,"offpeak":0.0})
        allocated=sum(float(tk.get(t,0) or 0) for t in ("peak","shoulder","offpeak")); legacy=max(0.0,energy-allocated)
        tariff_total=x.get("devices",{}).get(self.eid,0); allocated_cost=sum(float(tc.get(t,0) or 0) for t in ("peak","shoulder","offpeak")); legacy_cost=max(0.0,tariff_total-allocated_cost)
        grid_kwh=x.get("device_grid_kwh",{}).get(self.eid,0); solar_kwh=x.get("device_solar_kwh",{}).get(self.eid,0); grid_cost=x.get("device_grid_cost",{}).get(self.eid,0); opp=x.get("device_solar_opportunity_cost",{}).get(self.eid,0); impact=x.get("device_bill_impact",{}).get(self.eid,0)
        return {"source_entity":self.eid,"period":self.p,"display_name":self.display_name,"energy_kwh":round(energy,3),"tariff_kwh":tk,"tariff_cost":tc,"legacy_unallocated_kwh":round(legacy,3),"legacy_unallocated_cost":round(legacy_cost,4),"estimated_grid_kwh":round(grid_kwh,3),"estimated_solar_kwh":round(solar_kwh,3),"estimated_grid_cost":round(grid_cost,4),"solar_opportunity_cost":round(opp,4),"estimated_bill_impact":round(impact,4),"solar_saving":round(max(0.0,tariff_total-impact-legacy_cost),4),"solar_supplied_percent":round((solar_kwh/(grid_kwh+solar_kwh)*100) if grid_kwh+solar_kwh>0 else 0,1),"cost_type":"tariff_cost","data_since":self.eng.data.get("started_at")}

class ActiveTariffSensor(Base):
    def __init__(self,eng): super().__init__(eng); self._attr_unique_id="utility_cost_active_tariff"; self._attr_name="Active Tariff"
    @property
    def native_value(self): return self.eng.tariff(__import__('homeassistant').util.dt.now())[0]
    @property
    def extra_state_attributes(self): return {"rate":self.eng.tariff(__import__('homeassistant').util.dt.now())[1],"unit":"AUD/kWh","plan":self.eng.cfg.get("plan_name")}

class UntrackedPowerSensor(Base):
    _attr_native_unit_of_measurement="W"; _attr_device_class=SensorDeviceClass.POWER; _attr_state_class=SensorStateClass.MEASUREMENT
    def __init__(self,eng): super().__init__(eng); self._attr_unique_id="utility_cost_untracked_power"; self._attr_name="Untracked Power"
    @property
    def native_value(self):
        c=self.eng.cfg; house=self.eng._power_kw(c["house_power"]); tracked=sum(self.eng._power_kw(e) for e in c.get("tracked_power_entities",[])); return round(max(0,house-tracked)*1000,1)

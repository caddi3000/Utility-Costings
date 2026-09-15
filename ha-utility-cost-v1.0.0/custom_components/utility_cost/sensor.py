from __future__ import annotations
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_registry import async_get
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    eng=hass.data[DOMAIN][entry.entry_id]
    entities=[]
    for p in ("today","month","bill","year"):
        entities += [BillSensor(eng,p,"net"),BillSensor(eng,p,"grid"),BillSensor(eng,p,"supply"),BillSensor(eng,p,"fit")]
    for eid in eng.cfg.get("tracked_power_entities",[]):
        for p in ("today","month","bill","year"): entities.append(DeviceCostSensor(eng,p,eid))
    entities += [ActiveTariffSensor(eng), UntrackedPowerSensor(eng)]
    async_add_entities(entities)

class Base(SensorEntity):
    _attr_has_entity_name=True
    def __init__(self,eng): self.eng=eng; eng.listeners.append(self.async_write_ha_state)
    @property
    def device_info(self): return DeviceInfo(identifiers={(DOMAIN,self.eng.entry.entry_id)},name="Utility Cost",manufacturer="Custom",model="Utility bill accounting")

class BillSensor(Base):
    _attr_native_unit_of_measurement="AUD"; _attr_device_class=SensorDeviceClass.MONETARY; _attr_state_class=SensorStateClass.TOTAL
    def __init__(self,eng,p,kind): super().__init__(eng); self.p=p; self.kind=kind; self._attr_unique_id=f"utility_cost_{p}_{kind}"; self._attr_name=f"{p.title()} {kind.title()} Cost"
    @property
    def native_value(self):
        x=self.eng.period(self.p); v=x[self.kind] if self.kind!="net" else x["grid"]+x["supply"]-x["fit"]; return round(v,2)
    @property
    def extra_state_attributes(self):
        x=self.eng.period(self.p); return {"period_key":x.get("key"),"plan":self.eng.cfg.get("plan_name"),"grid_cost":round(x.get("grid",0),4),"supply_cost":round(x.get("supply",0),4),"solar_credit":round(x.get("fit",0),4)}

class DeviceCostSensor(Base):
    _attr_native_unit_of_measurement="AUD"; _attr_device_class=SensorDeviceClass.MONETARY; _attr_state_class=SensorStateClass.TOTAL
    def __init__(self,eng,p,eid):
        super().__init__(eng); self.p=p; self.eid=eid; slug=eid.replace(".","_"); self._attr_unique_id=f"utility_cost_{p}_{slug}"; st=eng.hass.states.get(eid); name=(st.attributes.get("friendly_name") if st else eid); self._attr_name=f"{name} {p.title()} Cost"
    @property
    def native_value(self): return round(self.eng.period(self.p).get("devices",{}).get(self.eid,0),2)
    @property
    def extra_state_attributes(self): return {"source_entity":self.eid,"period":self.p}

class ActiveTariffSensor(Base):
    def __init__(self,eng): super().__init__(eng); self._attr_unique_id="utility_cost_active_tariff"; self._attr_name="Active Tariff"
    @property
    def native_value(self): return self.eng.tariff(__import__('homeassistant').util.dt.now())[0]
    @property
    def extra_state_attributes(self): return {"rate":self.eng.tariff(__import__('homeassistant').util.dt.now())[1],"unit":"AUD/kWh"}

class UntrackedPowerSensor(Base):
    _attr_native_unit_of_measurement="W"; _attr_device_class=SensorDeviceClass.POWER; _attr_state_class=SensorStateClass.MEASUREMENT
    def __init__(self,eng): super().__init__(eng); self._attr_unique_id="utility_cost_untracked_power"; self._attr_name="Untracked Power"
    @property
    def native_value(self):
        c=self.eng.cfg; house=self.eng._power_kw(c["house_power"]); tracked=sum(self.eng._power_kw(e) for e in c.get("tracked_power_entities",[])); return round(max(0,house-tracked)*1000,1)

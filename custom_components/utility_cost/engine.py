from __future__ import annotations
from datetime import date, datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from .const import *

PERIODS=("today","week","month","bill","year")
TARIFFS=("peak","shoulder","offpeak")

class UtilityCostStore(Store):
    """Persistent store with Home Assistant-compatible storage migration."""

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict
    ) -> dict:
        """Preserve older Utility Cost data while upgrading the store wrapper.

        Field/schema normalization is deliberately handled by CostEngine.load(),
        where the current tariff/device defaults are available. Home Assistant
        will re-save the returned data using this store's current version.
        """
        if old_major_version > self.version:
            raise NotImplementedError(
                f"Cannot migrate Utility Cost storage from future version "
                f"{old_major_version}.{old_minor_version}"
            )
        return dict(old_data or {})


class CostEngine:
    def __init__(self,hass:HomeAssistant,entry):
        self.hass=hass; self.entry=entry; self.store=UtilityCostStore(hass,3,"utility_cost_state", minor_version=1)
        self.data={}; self.last=None; self.listeners=[]
    @property
    def cfg(self): return {**DEFAULTS,**self.entry.data,**self.entry.options}

    async def load(self):
        self.data=await self.store.async_load() or {"periods":{},"fit_day_kwh":0.0,"fit_day":None}
        self.data.setdefault("periods",{}); self.data.setdefault("started_at",dt_util.now().isoformat())
        self.data.setdefault("supply_posted_day",None); self.data.setdefault("schema_version",1)
        self._ensure_periods(dt_util.now())
        if self.data.get("schema_version",1)<3:
            self._migrate_supply(dt_util.now()); self.data["schema_version"]=3; await self.store.async_save(self.data)
    def _add_months(self,d:date,n:int)->date:
        m=d.month-1+n; y=d.year+m//12; m=m%12+1
        import calendar
        return date(y,m,min(d.day,calendar.monthrange(y,m)[1]))
    def _bill_bounds(self,now):
        anchor=dt_util.parse_date(str(self.cfg[CONF_BILL_START])) or now.date()
        if now.date()<anchor:return anchor,self._add_months(anchor,3)-timedelta(days=1)
        cur=anchor
        while self._add_months(cur,3)<=now.date(): cur=self._add_months(cur,3)
        return cur,self._add_months(cur,3)-timedelta(days=1)
    def _keys(self,now):
        week_start=now.date()-timedelta(days=now.weekday()); bill_start,_=self._bill_bounds(now)
        return {"today":now.date().isoformat(),"week":week_start.isoformat(),"month":now.strftime("%Y-%m"),"year":str(now.year),"bill":bill_start.isoformat()}
    def _blank(self):
        return {"grid":0.0,"grid_kwh":0.0,"supply":0.0,"fit":0.0,"export_kwh":0.0,"solar_kwh":0.0,"devices":{},"device_kwh":{},"device_tariff_kwh":{},"device_tariff_cost":{},"tracked_kwh":0.0,"house_kwh":0.0,"tariff_kwh":{t:0.0 for t in TARIFFS},"tariff_cost":{t:0.0 for t in TARIFFS}}
    def _ensure_periods(self,now):
        keys=self._keys(now)
        for p,k in keys.items():
            item=self.data["periods"].get(p)
            if not item or item.get("key")!=k:self.data["periods"][p]={"key":k,**self._blank()}
            else:
                for key,val in self._blank().items(): item.setdefault(key,val.copy() if isinstance(val,dict) else val)
        day=now.date().isoformat()
        if self.data.get("fit_day")!=day:self.data["fit_day"]=day;self.data["fit_day_kwh"]=0.0
    def _active_days(self,p,now):
        try: started=dt_util.parse_datetime(self.data.get("started_at","")) or now
        except Exception: started=now
        start=max(started.date(),now.date()) if p=="today" else started.date()
        if p=="week": start=max(start,now.date()-timedelta(days=now.weekday()))
        elif p=="month": start=max(start,now.date().replace(day=1))
        elif p=="year": start=max(start,date(now.year,1,1))
        elif p=="bill": start=max(start,self._bill_bounds(now)[0])
        return max(1,(now.date()-start).days+1)
    def _migrate_supply(self,now):
        rate=float(self.cfg[CONF_SUPPLY])
        for p in PERIODS:
            if p in self.data["periods"]: self.data["periods"][p]["supply"]=self._active_days(p,now)*rate
        self.data["supply_posted_day"]=now.date().isoformat()
    def _post_daily_supply(self,now):
        day=now.date().isoformat()
        if self.data.get("supply_posted_day")==day:return
        rate=float(self.cfg[CONF_SUPPLY])
        for p in PERIODS:self.data["periods"][p]["supply"]+=rate
        self.data["supply_posted_day"]=day
    @staticmethod
    def _mins(v):
        s=str(v); parts=s.split(":"); return int(parts[0])*60+int(parts[1])
    @staticmethod
    def _in_window(m,start,end):
        if start==end:return False
        return start<=m<end if start<end else (m>=start or m<end)
    def tariff(self,now):
        m=now.hour*60+now.minute;c=self.cfg
        if self._in_window(m,self._mins(c[CONF_PEAK_AM_START]),self._mins(c[CONF_PEAK_AM_END])) or self._in_window(m,self._mins(c[CONF_PEAK_PM_START]),self._mins(c[CONF_PEAK_PM_END])):return "peak",float(c[CONF_PEAK])
        if self._in_window(m,self._mins(c[CONF_SHOULDER_START]),self._mins(c[CONF_SHOULDER_END])):return "shoulder",float(c[CONF_SHOULDER])
        return "offpeak",float(c[CONF_OFFPEAK])
    def _power_kw(self,eid):
        st=self.hass.states.get(eid)
        if not st:return 0.0
        try:v=float(st.state)
        except (ValueError,TypeError):return 0.0
        unit=st.attributes.get("unit_of_measurement","")
        if unit=="kW":return v
        if unit=="MW":return v*1000
        return v/1000.0
    async def tick(self,now=None):
        now=now or dt_util.now();self._ensure_periods(now);self._post_daily_supply(now)
        if self.last is None:self.last=now;await self.store.async_save(self.data);return
        hours=max(0,min((now-self.last).total_seconds()/3600,0.1));self.last=now
        if not hours:return
        tariff,rate=self.tariff(now);c=self.cfg
        imp=max(0,self._power_kw(c[CONF_GRID_IMPORT]));exp=max(0,self._power_kw(c[CONF_GRID_EXPORT]));house=max(0,self._power_kw(c[CONF_HOUSE_POWER]));solar=max(0,self._power_kw(c.get(CONF_SOLAR_POWER,"")))
        tracked=list(c.get(CONF_TRACKED) or []);dev={e:max(0,self._power_kw(e)) for e in tracked}
        import_kwh=imp*hours;export_kwh=exp*hours;used=float(self.data.get("fit_day_kwh",0));lim=float(c[CONF_FIT_LIMIT]);tier1=max(0,min(export_kwh,lim-used));tier2=max(0,export_kwh-tier1);fit=tier1*float(c[CONF_FIT1])+tier2*float(c[CONF_FIT2]);self.data["fit_day_kwh"]=used+export_kwh
        for p in PERIODS:
            x=self.data["periods"][p];x["grid"]+=import_kwh*rate;x["grid_kwh"]+=import_kwh;x["fit"]+=fit;x["export_kwh"]+=export_kwh;x["house_kwh"]+=house*hours;x["solar_kwh"]+=solar*hours;x["tariff_kwh"][tariff]+=import_kwh;x["tariff_cost"][tariff]+=import_kwh*rate
            for e,kw in dev.items():
                kwh=kw*hours; cost=kwh*rate
                x["devices"][e]=x["devices"].get(e,0)+cost;x["device_kwh"][e]=x["device_kwh"].get(e,0)+kwh;x["tracked_kwh"]+=kwh
                x["device_tariff_kwh"].setdefault(e,{t:0.0 for t in TARIFFS});x["device_tariff_cost"].setdefault(e,{t:0.0 for t in TARIFFS})
                x["device_tariff_kwh"][e][tariff]+=kwh;x["device_tariff_cost"][e][tariff]+=cost
        await self.store.async_save(self.data)
        for cb in list(self.listeners):cb()
    def period(self,p):return self.data["periods"].get(p,self._blank())

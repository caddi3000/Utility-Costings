DOMAIN = "utility_cost"
PLATFORMS = ["sensor"]
CONF_GRID_IMPORT = "grid_import_power"
CONF_GRID_EXPORT = "grid_export_power"
CONF_HOUSE_POWER = "house_power"
CONF_SOLAR_POWER = "solar_power"
CONF_TRACKED = "tracked_power_entities"
CONF_PLAN = "plan_name"
CONF_PEAK = "peak_rate"
CONF_SHOULDER = "shoulder_rate"
CONF_OFFPEAK = "offpeak_rate"
CONF_SUPPLY = "supply_daily"
CONF_FIT1 = "fit_tier1"
CONF_FIT2 = "fit_tier2"
CONF_FIT_LIMIT = "fit_daily_limit"
CONF_BILL_START = "bill_cycle_start"
CONF_PEAK_AM_START = "peak_am_start"
CONF_PEAK_AM_END = "peak_am_end"
CONF_SHOULDER_START = "shoulder_start"
CONF_SHOULDER_END = "shoulder_end"
CONF_PEAK_PM_START = "peak_pm_start"
CONF_PEAK_PM_END = "peak_pm_end"
DEFAULTS = {
    CONF_PLAN: "EnergyAustralia Solar Max",
    CONF_PEAK: 0.581713,
    CONF_SHOULDER: 0.210584,
    CONF_OFFPEAK: 0.348018,
    CONF_SUPPLY: 1.260600,
    CONF_FIT1: 0.08,
    CONF_FIT2: 0.03,
    CONF_FIT_LIMIT: 10.0,
    CONF_BILL_START: "2026-09-05",
    CONF_PEAK_AM_START: "06:00:00",
    CONF_PEAK_AM_END: "10:00:00",
    CONF_SHOULDER_START: "10:00:00",
    CONF_SHOULDER_END: "16:00:00",
    CONF_PEAK_PM_START: "16:00:00",
    CONF_PEAK_PM_END: "00:00:00",
}

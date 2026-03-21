"""
Configuration constants for the Microgrid Simulation.
Standardizes physical limits and simulation parameters.
"""

# Temporal Parameters
START_DATE = "2025-01-01 00:00:00"
END_DATE = "2025-12-31 23:55:00"
FREQ = "5min"

# Physical Constants (Scaled Microgrid)
# PV: 100 kWp nominal (practical peak typically 75–85 kW under non-ideal conditions)
P_MAX_SOLAR = 100_000.0   # Watts

# Base loads (W). These are anchors; profiles in models.py shape the curve.
HOSTEL_BASE_LOAD_W = 100_000.0
DEPT_BASE_LOAD_W = 15_000.0

# HVAC sensitivity (W/°C above threshold) — tuned per building in models.py
AC_COEFFICIENT_HOSTEL = 2_500.0
AC_COEFFICIENT_DEPT = 3_500.0

# Environmental Constants
CLOUD_SMOOTHING = 24  # Rolling window for cloud persistence

# Warangal, Telangana (India) — month-wise diurnal temperature model parameters.
# Notes:
# - Values are approximate climatology intended for realistic synthetic data.
# - t_mean roughly follows average daily mean; t_amp sets typical diurnal swing.
# - You can refine these numbers if you have a preferred source/table.
WARANGAL_MONTHLY_T = {
	1: {"t_mean": 23.0, "t_amp": 10.0},
	2: {"t_mean": 26.0, "t_amp": 11.0},
	3: {"t_mean": 30.0, "t_amp": 12.0},
	4: {"t_mean": 33.0, "t_amp": 12.0},
	5: {"t_mean": 37.0, "t_amp": 11.0},
	6: {"t_mean": 31.0, "t_amp": 9.0},
	7: {"t_mean": 28.0, "t_amp": 7.0},
	8: {"t_mean": 27.5, "t_amp": 7.0},
	9: {"t_mean": 27.5, "t_amp": 7.0},
	10: {"t_mean": 27.0, "t_amp": 8.0},
	11: {"t_mean": 24.5, "t_amp": 9.0},
	12: {"t_mean": 22.0, "t_amp": 9.0},
}

# Monsoon months for Warangal (Jul–Sep) bias clouds and humidity.
MONSOON_MONTHS = {7, 8, 9}

# Humidity model (percent).
HUMIDITY_NON_MONSOON_BASE = 55.0
HUMIDITY_MONSOON_BASE = 82.0
HUMIDITY_CLOUD_COEFF_NON_MONSOON = 15.0
HUMIDITY_CLOUD_COEFF_MONSOON = 18.0
HUMIDITY_NOISE_STD = 4.0

# Academic calendar (default approximations for 2025).
# is_academic_day is intended to capture term vs breaks/exams/major festival week.
SUMMER_BREAK = ("2025-05-15", "2025-06-30")
EXAM_WEEKS = [
	("2025-04-21", "2025-05-05"),
	("2025-11-17", "2025-12-01"),
]
DIWALI_WEEK = ("2025-10-18", "2025-10-26")

# National holiday flags (YYYY-MM-DD). Add/remove as needed.
NATIONAL_HOLIDAYS_2025 = {
	"2025-01-26": "Republic Day",
	"2025-08-15": "Independence Day",
	"2025-10-02": "Gandhi Jayanti",
}

# Battery model parameters (for rolling SoC feature).
BATTERY_CAPACITY_WH = 250_000.0
BATTERY_MAX_CHARGE_W = 100_000.0
BATTERY_MAX_DISCHARGE_W = 100_000.0
BATTERY_CHARGE_EFF = 0.95
BATTERY_DISCHARGE_EFF = 0.95
BATTERY_INITIAL_SOC = 0.5

# PV derating (temperature, dust, wiring losses etc.) applied at peak.
PV_DERATE = 0.82

# Load curve parameters (hostel)
HOSTEL_MORNING_PEAK_W = 180_000.0   # 07:00–09:00 extra above base
HOSTEL_EVENING_PEAK_W = 220_000.0   # 19:00–23:00 extra above base (drives ~400 kW peak)
HOSTEL_DAYTIME_REDUCTION_W = 0.0    # optional reduction during 10:00–17:00

# Load curve parameters (department)
DEPT_WORKDAY_PEAK_W = 120_000.0     # 10:00–17:00 peak above base
DEPT_OFFHOURS_W = 8_000.0           # additional non-work baseload for security/IT
DEPT_WEEKEND_SCALE = 0.55
DEPT_HOLIDAY_SCALE = 0.45

# Academic/break scaling
HOSTEL_NON_ACADEMIC_SCALE = 0.78
DEPT_NON_ACADEMIC_SCALE = 0.60

# Exam week effects
HOSTEL_EXAM_LATE_NIGHT_W = 45_000.0

# Humidity HVAC bump (W per %RH above threshold) for each building
HUMIDITY_HVAC_W_PER_PCT_HOSTEL = 350.0
HUMIDITY_HVAC_W_PER_PCT_DEPT = 500.0
HUMIDITY_THRESHOLD_PCT = 75.0

# Temperature HVAC threshold (°C)
TEMP_HVAC_THRESHOLD_C = 30.0

# Export formatting
TRUNCATE_DECIMALS = 3

# High-Frequency Parameters
FS = 20               # 20Hz Sampling
DURATION_NORMAL = 3600 # 1 Hour
DURATION_FAULT = 300   # 5 Minutes

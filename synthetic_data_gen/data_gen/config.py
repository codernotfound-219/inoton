"""
Configuration constants for the Microgrid Simulation.
Standardizes physical limits and simulation parameters.
"""

# Temporal Parameters
START_DATE = "2026-04-01 00:00:00"
END_DATE = "2026-04-30 23:55:00"
FREQ = "5min"

# Physical Constants (Tabletop Scale)
P_MAX_SOLAR = 500.0   # Watts
BASE_LOAD = 50.0      # Watts
AC_COEFFICIENT = 20.0 # W/°C spike above 30°C

# Environmental Constants
T_MEAN = 32.5         # Mean temperature in °C
T_AMP = 12.5          # Diurnal temperature swing
CLOUD_SMOOTHING = 24  # Rolling window for cloud persistence

# High-Frequency Parameters
FS = 20               # 20Hz Sampling
DURATION_NORMAL = 3600 # 1 Hour
DURATION_FAULT = 300   # 5 Minutes

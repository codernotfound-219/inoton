import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

start_dt = "2026-04-01 00:00:00"
end_dt = "2026-04-30 23:55:00"

time_index = pd.date_range(start=start_dt, end=end_dt, freq="5min")
df = pd.DataFrame(index=time_index)

df['timestamp'] = df.index.astype('datetime64[s]').astype(np.int64)
df['time_of_day'] = df.index.hour
df['day_of_week'] = df.index.dayofweek

delta = df['timestamp'].iloc[1] - df['timestamp'].iloc[0]
if delta != 300:
    raise ValueError("WHAT")

# print(f"Dataset Shape: {df.shape}")
# print(df.head())

# 1. Cloud Cover: Smoothed Random Walk
np.random.seed(42)  # For reproducibility during the hackathon
raw_noise = np.random.rand(len(df))
df['cloud_cover'] = pd.Series(raw_noise).rolling(window=24, min_periods=1, center=True).mean().values

# 2. Temperature: Diurnal Sine Wave + Cloud Correlation
hours = df.index.hour + df.index.minute / 60
T_mean = 32.5
T_amp = 12.5

# Base Sine Wave (peaking at 15:00 / 3 PM)
df['temperature_c'] = T_mean + T_amp * np.sin(2 * np.pi * (hours - 9) / 24)

# Apply Cloud Penalty and Gaussian Noise
df['temperature_c'] -= (df['cloud_cover'] * 5.0) 
df['temperature_c'] += np.random.normal(0, 0.5, len(df))

# Ensure temperature stays within your specified 20-45 range
df['temperature_c'] = df['temperature_c'].clip(20, 45)

# Plot first 48 hours to see two full cycles
df_plot = df.iloc[:288*2] 

fig, ax1 = plt.subplots(figsize=(12, 5))

ax1.set_xlabel('Time')
ax1.set_ylabel('Temperature (C)', color='tab:red')
ax1.plot(df_plot.index, df_plot['temperature_c'], color='tab:red', label='Temp')

ax2 = ax1.twinx()
ax2.set_ylabel('Cloud Cover (0-1)', color='tab:blue')
ax2.fill_between(df_plot.index, df_plot['cloud_cover'], color='tab:blue', alpha=0.3, label='Cloud')

plt.title("Environmental Variable Correlation (48 Hour Sample)")
plt.show()

# Constants for a tabletop-scale microgrid
P_MAX_SOLAR = 500.0  # Watts
BASE_LOAD = 50.0     # Watts
AC_COEFFICIENT = 20.0 # Watts per Degree Celsius above 30C

# Ensure 'hours' is calculated with floating-point precision for smooth transitions
hours = df.index.hour + df.index.minute / 60.0

# 1. Solar Irradiance (W)
# Model: Cosine curve centered at 12:00 (Noon) attenuated by Cloud Cover
df['solar_irradiance_w'] = P_MAX_SOLAR * np.maximum(0, np.cos(np.pi * (hours - 12) / 12))
df['solar_irradiance_w'] *= (1 - 0.75 * df['cloud_cover'])

# 2. Department Load (W)
# Logic: Base Load + Workday Activity (09:00 - 17:00) + AC Surge based on Temperature
df['dept_load_w'] = BASE_LOAD
work_mask = (df.index.hour >= 9) & (df.index.hour <= 17)
df.loc[work_mask, 'dept_load_w'] += 400.0
# AC Spike: Triggered only when Temp > 30C during work hours
ac_spike = np.maximum(0, df['temperature_c'] - 30.0) * AC_COEFFICIENT
df.loc[work_mask, 'dept_load_w'] += ac_spike

# 3. Hostel Load (W)
# Logic: Base Load + Evening/Night Usage (18:00 - 02:00)
df['hostel_load_w'] = BASE_LOAD
hostel_mask = (df.index.hour >= 18) | (df.index.hour < 2)
df.loc[hostel_mask, 'hostel_load_w'] += 450.0

# Add Stochastic Noise (5%) to simulate real-world sensor fluctuations
cols_to_noise = ['solar_irradiance_w', 'dept_load_w', 'hostel_load_w']
for col in cols_to_noise:
    noise = np.random.normal(0, df[col].mean() * 0.05, len(df))
    df[col] = (df[col] + noise).clip(lower=0)

# Calculate Total Demand for verification
df['total_load_w'] = df['dept_load_w'] + df['hostel_load_w']

plt.figure(figsize=(14, 6))
# Plotting the first 48 hours
df_sample = df.iloc[:288*2]

plt.plot(df_sample.index, df_sample['solar_irradiance_w'], label='Solar Supply (W)', color='orange', linewidth=2)
plt.plot(df_sample.index, df_sample['total_load_w'], label='Total Load Demand (W)', color='black', linestyle='--')
plt.fill_between(df_sample.index, df_sample['solar_irradiance_w'], df_sample['total_load_w'], 
                 where=(df_sample['total_load_w'] > df_sample['solar_irradiance_w']),
                 color='red', alpha=0.2, label='Energy Deficit (Battery/Grid Needed)')

plt.title("Microgrid Power Balance: Supply vs Demand (48 Hour Sample)")
plt.ylabel("Power (Watts)")
plt.legend()
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.show()

# # Final step: Save the dataset
# df.to_csv("synthetic_energy_data.csv")
# print("Dataset successfully exported to synthetic_energy_data.csv")

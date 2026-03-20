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

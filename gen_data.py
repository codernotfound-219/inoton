import pandas as pd
import numpy as np

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

print(f"Dataset Shape: {df.shape}")
print(df.head())

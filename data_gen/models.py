import pandas as pd
import numpy as np
from .config import *

def generate_base_df():
    """Initializes the temporal structure and extracts features."""
    time_index = pd.date_range(start=START_DATE, end=END_DATE, freq=FREQ)
    df = pd.DataFrame(index=time_index)
    df['timestamp'] = df.index.astype('datetime64[s]').astype(np.int64)
    df['time_of_day'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek
    return df

def apply_environmental_models(df):
    """Models Cloud Cover and Temperature with physical coupling."""
    np.random.seed(42)
    hours = df.index.hour + df.index.minute / 60.0
    
    # Cloud Cover: Smoothed Random Walk
    raw_noise = np.random.rand(len(df))
    df['cloud_cover'] = pd.Series(raw_noise).rolling(
        window=CLOUD_SMOOTHING, min_periods=1, center=True).mean().values
    
    # Temperature: Sinusoidal + Cloud Penalty
    df['temperature_c'] = T_MEAN + T_AMP * np.sin(2 * np.pi * (hours - 9) / 24)
    df['temperature_c'] -= (df['cloud_cover'] * 5.0)
    df['temperature_c'] += np.random.normal(0, 0.5, len(df))
    df['temperature_c'] = df['temperature_c'].clip(20, 45)
    return df

def apply_power_metrics(df):
    """Derives power supply and demand based on environmental state."""
    hours = df.index.hour + df.index.minute / 60.0
    
    # Solar Supply
    df['solar_irradiance_w'] = P_MAX_SOLAR * np.maximum(0, np.cos(np.pi * (hours - 12) / 12))
    df['solar_irradiance_w'] *= (1 - 0.75 * df['cloud_cover'])
    
    # Department Load
    df['dept_load_w'] = BASE_LOAD
    work_mask = (df.index.hour >= 9) & (df.index.hour <= 17)
    df.loc[work_mask, 'dept_load_w'] += 400.0
    ac_spike = np.maximum(0, df['temperature_c'] - 30.0) * AC_COEFFICIENT
    df.loc[work_mask, 'dept_load_w'] += ac_spike
    
    # Hostel Load
    df['hostel_load_w'] = BASE_LOAD
    hostel_mask = (df.index.hour >= 18) | (df.index.hour < 2)
    df.loc[hostel_mask, 'hostel_load_w'] += 450.0
    
    # Noise Injection & Total
    for col in ['solar_irradiance_w', 'dept_load_w', 'hostel_load_w']:
        noise = np.random.normal(0, df[col].mean() * 0.05, len(df))
        df[col] = (df[col] + noise).clip(lower=0)
    
    df['total_load_w'] = df['dept_load_w'] + df['hostel_load_w']
    return df

def generate_hf_waveform(duration, is_anomaly=False):
    """Generates 20Hz current signals for Autoencoder training."""
    t = np.linspace(0, duration, int(FS * duration))
    if not is_anomaly:
        signal = 5.0 + 0.2 * np.sin(2 * np.pi * 0.5 * t) + np.random.normal(0, 0.1, len(t))
    else:
        signal = 5.0 + np.random.normal(0, 5.0, len(t)) + np.random.choice([0, 20], len(t), p=[0.9, 0.1])
    return np.clip(signal, 0, None)

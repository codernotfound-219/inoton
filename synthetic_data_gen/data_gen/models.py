import pandas as pd
import numpy as np
from .config import *


def _truncate_floats_inplace(df: pd.DataFrame, decimals: int) -> pd.DataFrame:
    if decimals is None:
        return df
    factor = 10 ** int(decimals)
    float_cols = df.select_dtypes(include=["float", "float32", "float64"]).columns
    if len(float_cols) == 0:
        return df
    df[float_cols] = np.trunc(df[float_cols].to_numpy() * factor) / factor
    return df


def _parse_date_range(date_range):
    start_s, end_s = date_range
    return pd.Timestamp(start_s), pd.Timestamp(end_s)


def _is_in_ranges(dti: pd.DatetimeIndex, ranges) -> np.ndarray:
    mask = np.zeros(len(dti), dtype=bool)
    for start_s, end_s in ranges:
        start, end = _parse_date_range((start_s, end_s))
        mask |= (dti >= start) & (dti <= end)
    return mask

def generate_base_df():
    """Initializes the temporal structure and extracts features."""
    time_index = pd.date_range(start=START_DATE, end=END_DATE, freq=FREQ)
    df = pd.DataFrame(index=time_index)
    df['timestamp'] = df.index.astype('datetime64[s]').astype(np.int64)
    df['time_of_day'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek

    # Calendar flags
    dates = df.index
    df["month"] = dates.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Holidays
    holiday_dates = set(pd.to_datetime(list(NATIONAL_HOLIDAYS_2025.keys())).normalize())
    df["is_holiday"] = pd.Index(dates.normalize()).isin(holiday_dates).astype(int)

    # Academic day encoding: 1 for typical academic days, 0 for breaks/exams/Diwali-week/holidays.
    summer_start, summer_end = _parse_date_range(SUMMER_BREAK)
    diwali_start, diwali_end = _parse_date_range(DIWALI_WEEK)
    is_summer_break = (dates >= summer_start) & (dates <= summer_end)
    is_diwali_week = (dates >= diwali_start) & (dates <= diwali_end)
    is_exam_week = _is_in_ranges(dates, EXAM_WEEKS)

    df["is_academic_day"] = (~(is_summer_break | is_diwali_week | is_exam_week | (df["is_holiday"] == 1))).astype(int)
    return df

def apply_environmental_models(df):
    """Models Cloud Cover and Temperature with physical coupling."""
    np.random.seed(42)
    hours = df.index.hour + df.index.minute / 60.0

    months = df.index.month

    # Cloud Cover: month-biased noise + persistence
    # Higher cloud probability during monsoon months (Jul–Sep).
    is_monsoon = np.isin(months, list(MONSOON_MONTHS))
    raw_noise = np.empty(len(df), dtype=float)
    n = len(df)
    # Non-monsoon: lower average cloudiness
    raw_noise[~is_monsoon] = np.random.beta(2.0, 5.0, size=int((~is_monsoon).sum()))
    # Monsoon: higher average cloudiness
    raw_noise[is_monsoon] = np.random.beta(5.0, 2.0, size=int(is_monsoon.sum()))
    df['cloud_cover'] = pd.Series(raw_noise).rolling(
        window=CLOUD_SMOOTHING, min_periods=1, center=True).mean().values
    df['cloud_cover'] = np.clip(df['cloud_cover'], 0.0, 1.0)

    # Temperature: month-wise sinusoidal + cloud penalty
    t_mean_map = {m: v["t_mean"] for m, v in WARANGAL_MONTHLY_T.items()}
    t_amp_map = {m: v["t_amp"] for m, v in WARANGAL_MONTHLY_T.items()}
    t_mean = pd.Series(months).map(t_mean_map).to_numpy(dtype=float)
    t_amp = pd.Series(months).map(t_amp_map).to_numpy(dtype=float)

    df['temperature_c'] = t_mean + t_amp * np.sin(2 * np.pi * (hours - 9) / 24)
    df['temperature_c'] -= (df['cloud_cover'] * 5.0)
    df['temperature_c'] += np.random.normal(0, 0.5, len(df))

    # Humidity (%): correlated with cloud cover, especially during monsoon
    humidity_base = np.where(is_monsoon, HUMIDITY_MONSOON_BASE, HUMIDITY_NON_MONSOON_BASE)
    humidity_coeff = np.where(is_monsoon, HUMIDITY_CLOUD_COEFF_MONSOON, HUMIDITY_CLOUD_COEFF_NON_MONSOON)
    df["humidity_pct"] = humidity_base + humidity_coeff * df["cloud_cover"].to_numpy()
    df["humidity_pct"] += np.random.normal(0, HUMIDITY_NOISE_STD, len(df))
    df["humidity_pct"] = df["humidity_pct"].clip(25.0, 100.0)

    df['temperature_c'] = df['temperature_c'].clip(18, 45)
    return df

def apply_power_metrics(df):
    """Derives power supply and demand based on environmental state."""
    hours = df.index.hour + df.index.minute / 60.0
    
    # Solar Supply
    # Cosine curve centered at noon, with practical derating.
    df['solar_irradiance_w'] = (P_MAX_SOLAR * PV_DERATE) * np.maximum(0, np.cos(np.pi * (hours - 12) / 12))
    df['solar_irradiance_w'] *= (1 - 0.75 * df['cloud_cover'])
    
    # Department Load
    work_mask = (df.index.hour >= 10) & (df.index.hour <= 17)
    dept = np.full(len(df), float(DEPT_BASE_LOAD_W + DEPT_OFFHOURS_W), dtype=float)
    dept[work_mask] += float(DEPT_WORKDAY_PEAK_W)

    # Calendar scaling (weekend/holiday/non-academic)
    if "is_weekend" in df.columns:
        dept *= np.where(df["is_weekend"].to_numpy() == 1, float(DEPT_WEEKEND_SCALE), 1.0)
    if "is_holiday" in df.columns:
        dept *= np.where(df["is_holiday"].to_numpy() == 1, float(DEPT_HOLIDAY_SCALE), 1.0)
    if "is_academic_day" in df.columns:
        dept *= np.where(df["is_academic_day"].to_numpy() == 1, 1.0, float(DEPT_NON_ACADEMIC_SCALE))

    # Temperature-driven HVAC for department (mostly daytime)
    temp_excess = np.maximum(0, df["temperature_c"].to_numpy() - float(TEMP_HVAC_THRESHOLD_C))
    dept_hvac = temp_excess * float(AC_COEFFICIENT_DEPT)
    dept[work_mask] += dept_hvac[work_mask]

    df['dept_load_w'] = dept

    # Humidity-driven HVAC bump (secondary effect, stronger in monsoon)
    if "humidity_pct" in df.columns:
        humidity_excess = np.maximum(0, df["humidity_pct"].to_numpy() - float(HUMIDITY_THRESHOLD_PCT))
        is_monsoon = np.isin(df.index.month, list(MONSOON_MONTHS))
        monsoon_coeff = np.where(is_monsoon, 1.25, 1.0)
        bump_dept = humidity_excess * float(HUMIDITY_HVAC_W_PER_PCT_DEPT) * monsoon_coeff
        mask = np.asarray(work_mask, dtype=bool)
        df.loc[mask, 'dept_load_w'] += bump_dept[mask]

    # Hostel Load
    hostel = np.full(len(df), float(HOSTEL_BASE_LOAD_W), dtype=float)

    # Dual-peak hostel behavior: morning (07–09) and evening/night (19–23)
    morning = (df.index.hour >= 7) & (df.index.hour <= 9)
    evening = (df.index.hour >= 19) & (df.index.hour <= 23)
    hostel[morning] += float(HOSTEL_MORNING_PEAK_W)
    hostel[evening] += float(HOSTEL_EVENING_PEAK_W)

    # Daytime is typically lower than peaks (optional reduction term)
    daytime = (df.index.hour >= 10) & (df.index.hour <= 17)
    if float(HOSTEL_DAYTIME_REDUCTION_W) != 0.0:
        hostel[daytime] = np.maximum(float(HOSTEL_BASE_LOAD_W), hostel[daytime] - float(HOSTEL_DAYTIME_REDUCTION_W))

    # Temperature-driven HVAC for hostel (distributed across day/evening)
    temp_excess = np.maximum(0, df["temperature_c"].to_numpy() - float(TEMP_HVAC_THRESHOLD_C))
    hostel += temp_excess * float(AC_COEFFICIENT_HOSTEL)

    df['hostel_load_w'] = hostel

    # Hostel yearly cycle: academic term vs breaks/holidays/exam weeks.
    # Heuristic: during summer break & major holiday week, hostel occupancy and load drop.
    # During exam weeks, night-time load increases (late-night study).
    if "is_academic_day" in df.columns:
        # Base multiplier: lower on non-academic days.
        multiplier = np.where(df["is_academic_day"].to_numpy() == 1, 1.0, float(HOSTEL_NON_ACADEMIC_SCALE))
        # Holidays additionally reduce typical hostel usage.
        if "is_holiday" in df.columns:
            multiplier = np.where(df["is_holiday"].to_numpy() == 1, multiplier * 0.80, multiplier)
        df['hostel_load_w'] = df['hostel_load_w'] * multiplier

    # Exam weeks: increase late-night usage (20:00–01:00)
    exam_mask = _is_in_ranges(df.index, EXAM_WEEKS)
    late_night = (df.index.hour >= 20) | (df.index.hour <= 1)
    df.loc[exam_mask & late_night, 'hostel_load_w'] += 120.0

    # Humidity bump for hostel HVAC (more latent cooling load)
    if "humidity_pct" in df.columns:
        humidity_excess = np.maximum(0, df["humidity_pct"].to_numpy() - float(HUMIDITY_THRESHOLD_PCT))
        is_monsoon = np.isin(df.index.month, list(MONSOON_MONTHS))
        monsoon_coeff = np.where(is_monsoon, 1.25, 1.0)
        bump_hostel = humidity_excess * float(HUMIDITY_HVAC_W_PER_PCT_HOSTEL) * monsoon_coeff
        df['hostel_load_w'] = df['hostel_load_w'] + bump_hostel

    # Weekends: modestly higher hostel usage in evenings
    if "is_weekend" in df.columns:
        weekend_evening = (df["is_weekend"] == 1) & ((df.index.hour >= 18) & (df.index.hour <= 23))
        df.loc[weekend_evening, 'hostel_load_w'] += 12_000.0
    
    # Noise Injection & Total
    for col in ['solar_irradiance_w', 'dept_load_w', 'hostel_load_w']:
        noise = np.random.normal(0, df[col].mean() * 0.05, len(df))
        df[col] = (df[col] + noise).clip(lower=0)
    
    df['total_load_w'] = df['dept_load_w'] + df['hostel_load_w']

    # Rolling battery SoC (stateful feature)
    dt_hours = pd.Timedelta(FREQ).total_seconds() / 3600.0
    soc = np.zeros(len(df), dtype=float)
    soc[0] = float(BATTERY_INITIAL_SOC)
    capacity_wh = float(BATTERY_CAPACITY_WH)
    max_ch_w = float(BATTERY_MAX_CHARGE_W)
    max_dis_w = float(BATTERY_MAX_DISCHARGE_W)
    ch_eff = float(BATTERY_CHARGE_EFF)
    dis_eff = float(BATTERY_DISCHARGE_EFF)

    solar = df["solar_irradiance_w"].to_numpy(dtype=float)
    load = df["total_load_w"].to_numpy(dtype=float)
    for i in range(1, len(df)):
        # Behind-the-meter flow:
        # 1) PV supplies load first
        # 2) Surplus PV charges battery (limited by max charge power)
        # 3) Remaining deficit discharges battery (limited by max discharge power and available SoC)
        pv_w = solar[i - 1]
        demand_w = load[i - 1]

        pv_to_load_w = min(pv_w, demand_w)
        surplus_w = pv_w - pv_to_load_w
        deficit_w = demand_w - pv_to_load_w

        # Charge
        ch_w = min(max(surplus_w, 0.0), max_ch_w)
        delta_wh_ch = ch_w * dt_hours * ch_eff

        # Discharge (also limited by available energy)
        # Available DC energy in battery at current SoC:
        available_wh = soc[i - 1] * capacity_wh
        max_dis_wh = available_wh * dis_eff
        max_dis_w_energy_limited = (max_dis_wh / dt_hours) if dt_hours > 0 else 0.0
        dis_w = min(max(deficit_w, 0.0), max_dis_w, max_dis_w_energy_limited)
        delta_wh_dis = (dis_w * dt_hours) / max(dis_eff, 1e-9)

        soc[i] = soc[i - 1] + (delta_wh_ch - delta_wh_dis) / capacity_wh
        soc[i] = min(1.0, max(0.0, soc[i]))
    df["battery_soc"] = soc

    _truncate_floats_inplace(df, TRUNCATE_DECIMALS)
    return df

def generate_hf_waveform(duration, is_anomaly=False):
    """Generates 20Hz current signals for Autoencoder training."""
    t = np.linspace(0, duration, int(FS * duration))
    if not is_anomaly:
        signal = 5.0 + 0.2 * np.sin(2 * np.pi * 0.5 * t) + np.random.normal(0, 0.1, len(t))
    else:
        signal = 5.0 + np.random.normal(0, 5.0, len(t)) + np.random.choice([0, 20], len(t), p=[0.9, 0.1])
    return np.clip(signal, 0, None)

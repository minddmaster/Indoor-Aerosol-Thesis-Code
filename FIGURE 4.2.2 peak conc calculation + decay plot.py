# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 19:21:21 2026

@author: papkp
"""

# Ref No: THESIS-DECAY-COMBINED-NaCl-1510-1600-2026-03-05
# Combined decay fit using all OFF periods within 15:10–16:00
# Excludes ON periods and excludes ventilation ± buffer.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress

SMPS_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 1 ELPI VS SMPS/DAY1 SMPS DATA_COM32.xlsx"
time_col = "corrected time"

ANALYSIS_START = "15:10:00"
ANALYSIS_END   = "16:00:00"

# ON periods (to EXCLUDE from decay data)
AEROSOL_ON_PERIODS = [
    ("15:12:00", "15:17:00"),
    ("15:30:00", "15:35:00"),
    ("15:47:00", "15:52:00"),
]

# OFF decay segments to INCLUDE (between OFF and next ON / end)
DECAY_SEGMENTS = [
    ("15:17:00", "15:30:00"),  # after R1 OFF, before R2 ON
    ("15:35:00", "15:47:00"),  # after R2 OFF, before R3 ON
    ("15:52:00", "16:00:00"),  # after R3 OFF, until end of window
]

VENTILATION_TIMES = ["15:22:00", "15:40:00", "15:57:00"]
EXCLUDE_VENT_SEC = 60
MIN_POINTS = 6  # pooled fit; aim for at least 6 points


# ---------- Helpers ----------
def load_best_smps_sheet(path: str, time_col: str):
    xls = pd.ExcelFile(path)
    best_sh, best_df, best_n = None, None, -1
    for sh in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sh)
        if time_col in df.columns:
            n = df[time_col].notna().sum()
            if n > best_n:
                best_sh, best_df, best_n = sh, df, n
    if best_df is None:
        raise ValueError(f"No sheet contains '{time_col}'. Sheets: {xls.sheet_names}")
    print(f"Auto-selected sheet: {best_sh} (rows with '{time_col}' = {best_n})")
    return best_df

def make_T(base_ts: pd.Timestamp, hhmmss: str) -> pd.Timestamp:
    t = pd.to_datetime(hhmmss).time()
    return base_ts.replace(hour=t.hour, minute=t.minute, second=t.second)

def compute_total_conc(df: pd.DataFrame, time_col: str):
    bin_cols = [c for c in df.columns if c != time_col]
    diam_nm = np.array([float(c) for c in bin_cols], dtype=float)
    order = np.argsort(diam_nm)
    diam_nm = diam_nm[order]
    bin_cols = [bin_cols[i] for i in order]
    Y = df[bin_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    dlog10 = np.gradient(np.log10(diam_nm))
    return np.nansum(Y * dlog10, axis=1)


# ---------- Load ----------
df = load_best_smps_sheet(SMPS_PATH, time_col=time_col)

df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
df = df.dropna(subset=[time_col]).sort_values(time_col).reset_index(drop=True)

base = df[time_col].iloc[0]
N_total = compute_total_conc(df, time_col=time_col)

# Restrict to analysis window
t_start = make_T(base, ANALYSIS_START)
t_end = make_T(base, ANALYSIS_END)
mask = (df[time_col] >= t_start) & (df[time_col] <= t_end)

df_win = df.loc[mask].copy().reset_index(drop=True)
N_win = N_total[mask.to_numpy()]

# ---------- Build combined decay dataset ----------
combined_idx = []

# Include decay segments
for (a, b) in DECAY_SEGMENTS:
    ta = make_T(base, a)
    tb = make_T(base, b)
    seg_mask = (df_win[time_col] >= ta) & (df_win[time_col] <= tb)
    combined_idx.extend(df_win.index[seg_mask].tolist())

combined_idx = sorted(set(combined_idx))

# Exclude ON periods (safety)
for (a, b) in AEROSOL_ON_PERIODS:
    ta = make_T(base, a)
    tb = make_T(base, b)
    on_mask = (df_win[time_col] >= ta) & (df_win[time_col] <= tb)
    on_idx = set(df_win.index[on_mask].tolist())
    combined_idx = [i for i in combined_idx if i not in on_idx]

# Exclude ventilation ± buffer
if EXCLUDE_VENT_SEC:
    drop = set()
    for vt in VENTILATION_TIMES:
        tv = make_T(base, vt)
        lower = tv - pd.Timedelta(seconds=EXCLUDE_VENT_SEC)
        upper = tv + pd.Timedelta(seconds=EXCLUDE_VENT_SEC)
        vent_mask = (df_win[time_col] >= lower) & (df_win[time_col] <= upper)
        drop.update(df_win.index[vent_mask].tolist())
    combined_idx = [i for i in combined_idx if i not in drop]

# Extract time + concentration
decay_times = df_win.loc[combined_idx, time_col].copy()
decay_conc = N_win[np.array(combined_idx, dtype=int)].astype(float)

# Remove invalid
ok = np.isfinite(decay_conc) & (decay_conc > 0)

decay_times = decay_times.loc[ok]
decay_conc = decay_conc[ok]

print(f"\nCombined decay points used: {len(decay_conc)}")

if len(decay_conc) < MIN_POINTS:
    raise ValueError(f"Not enough points for combined decay fit (n={len(decay_conc)}). Increase analysis window or reduce MIN_POINTS.")

# Convert to seconds since first decay point
tsec = (decay_times - decay_times.iloc[0]).dt.total_seconds().to_numpy()
logC = np.log(decay_conc)

# Fit
slope, intercept, r_value, p_value, std_err = linregress(tsec, logC)
lambda_decay = -slope
r2 = r_value**2
ACH = lambda_decay * 3600
half_life_min = (np.log(2) / lambda_decay) / 60 if lambda_decay > 0 else np.nan

print("\nCombined decay fit (all OFF periods within 15:10–16:00)")
print("-------------------------------------------------------")
print(f"λ = {lambda_decay:.6f} s⁻¹")
print(f"R² = {r2:.3f}")
print(f"ACH = {ACH:.2f} h⁻¹")
print(f"Half-life = {half_life_min:.1f} min")

# Plot
fit = np.exp(intercept + slope * tsec)

plt.figure(figsize=(7.0, 4.4))
plt.scatter(tsec, decay_conc, label="Decay points (pooled)")
plt.plot(tsec, fit, label="Exponential fit")
plt.xlabel("Time since first decay point (s)")
plt.ylabel("Total particle number concentration (cm$^{-3}$)")
plt.title("Pooled aerosol decay fit (NaCl, SMPS, 15:10–16:00)")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend(frameon=False)
plt.tight_layout()
plt.show()
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 17:51:10 2026

@author: papkp
"""

# Ref No: THESIS-FIG-4.2-NaCl-Timeseries-SMPS-2026-03-05
# Time series of total particle number concentration computed from SMPS size distributions
# Uses "corrected time" and diameter-bin columns, with shaded aerosol ON periods.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SMPS_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 1 ELPI VS SMPS/DAY1 SMPS DATA_COM32.xlsx"
SHEET_NAME = "EDIT1 (2)"   # change if needed

time_col = "corrected time"

# Timeline (Day 1)
AEROSOL_PERIODS = [
    ("15:12:00", "15:17:00"),
    ("15:30:00", "15:35:00"),
    ("15:47:00", "15:52:00"),
]
VENTILATION_TIMES = ["15:22:00", "15:40:00", "15:57:00"]

# Load
df = pd.read_excel(SMPS_PATH, sheet_name=SHEET_NAME)

# Convert time
df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
df = df.dropna(subset=[time_col]).sort_values(time_col)

# Identify diameter bins (all numeric columns except time)
bin_cols = [c for c in df.columns if c != time_col]
diam_nm = np.array([float(c) for c in bin_cols], dtype=float)

# Sort bins ascending (important)
order = np.argsort(diam_nm)
diam_nm = diam_nm[order]
bin_cols = [bin_cols[i] for i in order]

# Extract distributions
Y = df[bin_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)  # shape (t, bins)

# Compute Δlog10(D) for integration
dlog10 = np.gradient(np.log10(diam_nm))  # same length as bins

# Total number concentration time series:
# If Y is dN/dlog10D, then N = sum(Y * dlog10)
N_total = np.nansum(Y * dlog10, axis=1)

# Plot
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df[time_col], N_total, linewidth=1.4)

# Shade aerosol generation periods
for i, (t0, t1) in enumerate(AEROSOL_PERIODS):
    start = pd.to_datetime(t0).time()
    end = pd.to_datetime(t1).time()
    # Use same date as data by taking any timestamp date; compare by time-of-day
    ax.axvspan(
        df[time_col].iloc[0].replace(hour=start.hour, minute=start.minute, second=start.second),
        df[time_col].iloc[0].replace(hour=end.hour, minute=end.minute, second=end.second),
        alpha=0.18,
        label="Aerosol generation" if i == 0 else None
    )

# Ventilation markers
for i, vt in enumerate(VENTILATION_TIMES):
    v = pd.to_datetime(vt).time()
    ax.axvline(
        df[time_col].iloc[0].replace(hour=v.hour, minute=v.minute, second=v.second),
        linestyle="--",
        linewidth=1.2,
        label="Ventilation" if i == 0 else None
    )

ax.set_xlabel("Time")
ax.set_ylabel("Total particle number concentration (particles cm$^{-3}$)")
ax.set_title("Figure 4.2. SMPS total particle number concentration during NaCl aerosol generation (Day 1, SPHERE House)")
ax.grid(True, which="both", linestyle="--", linewidth=0.5)
ax.legend(frameon=False)

plt.tight_layout()
plt.show()
# Filter to timeline window 15:10–16:00
t_start = df[time_col].iloc[0].replace(hour=15, minute=10, second=0)
t_end   = df[time_col].iloc[0].replace(hour=16, minute=0,  second=0)
df = df[(df[time_col] >= t_start) & (df[time_col] <= t_end)]
print("Peak concentration:", np.nanmax(N_total))
print("Mean concentration:", np.nanmean(N_total))
print("Background concentration:", np.nanmin(N_total))
from scipy.stats import linregress
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------
# SETTINGS
# --------------------------
MIN_POINTS = 4
EXPAND_END = "17:00:00"          # allow expansion up to 17:00
EXCLUDE_VENT_SEC = 60            # exclude ±60 s around ventilation line
USE_REPEAT = "R3"                # try "R1", "R2", or "R3"

REPEATS = {
    "R1": {"off": "15:17:00", "vent": "15:22:00"},
    "R2": {"off": "15:35:00", "vent": "15:40:00"},
    "R3": {"off": "15:52:00", "vent": "15:57:00"},
}

base = df[time_col].iloc[0]
def T(hhmmss: str):
    t = pd.to_datetime(hhmmss).time()
    return base.replace(hour=t.hour, minute=t.minute, second=t.second)

off_t = T(REPEATS[USE_REPEAT]["off"])
vent_t = T(REPEATS[USE_REPEAT]["vent"])
expand_end_t = T(EXPAND_END)

# Initial window: OFF -> VENT
win_start = off_t
win_end = vent_t

decay_df = df[(df[time_col] >= win_start) & (df[time_col] <= win_end)].copy()
print(f"{USE_REPEAT}: points in OFF→VENT window ({win_start.time()}–{win_end.time()}): {decay_df.shape[0]}")

# Expand window automatically until we have enough points (max 18:00)
max_end = T("18:00:00")
candidate_end = vent_t  # start with OFF->VENT

while True:
    decay_df = df[(df[time_col] >= win_start) & (df[time_col] <= candidate_end)].copy()

    if decay_df.shape[0] >= MIN_POINTS:
        win_end = candidate_end
        break

    # extend by 10 minutes each loop
    candidate_end = candidate_end + pd.Timedelta(minutes=10)

    if candidate_end > max_end:
        win_end = max_end
        break

# Recompute decay_df with final chosen end
decay_df = df[(df[time_col] >= win_start) & (df[time_col] <= win_end)].copy()
print(f"Auto-extended window end: {win_end.time()}")
print(f"Number of SMPS points in window: {decay_df.shape[0]}")

# Exclude ventilation ± buffer (optional but recommended)
if EXCLUDE_VENT_SEC and decay_df.shape[0] > 0:
    lower = vent_t - pd.Timedelta(seconds=EXCLUDE_VENT_SEC)
    upper = vent_t + pd.Timedelta(seconds=EXCLUDE_VENT_SEC)
    before = decay_df.shape[0]
    decay_df = decay_df[(decay_df[time_col] < lower) | (decay_df[time_col] > upper)].copy()
    after = decay_df.shape[0]
    print(f"Excluded ventilation ±{EXCLUDE_VENT_SEC}s: {before} -> {after} points")

print(f"Decay window used: {win_start.time()}–{win_end.time()}")
print(f"Number of SMPS points in window: {decay_df.shape[0]}")

# Build arrays
decay_conc = N_total[decay_df.index].astype(float)
tsec = (decay_df[time_col] - decay_df[time_col].iloc[0]).dt.total_seconds().to_numpy()

mask = np.isfinite(tsec) & np.isfinite(decay_conc) & (decay_conc > 0)
tsec = tsec[mask]
decay_conc = decay_conc[mask]

if len(tsec) < MIN_POINTS or np.allclose(tsec, tsec[0]):
    raise ValueError(
        f"Not enough valid points for decay fit (n={len(tsec)}). "
        f"Try USE_REPEAT='R3' and/or increase EXPAND_END beyond 16:00, or reduce MIN_POINTS."
    )

logC = np.log(decay_conc)
slope, intercept, r_value, p_value, std_err = linregress(tsec, logC)

lambda_decay = -slope
r2 = r_value**2
ACH = lambda_decay * 3600
half_life_min = (np.log(2) / lambda_decay) / 60

print("\nAerosol decay analysis")
print("----------------------")
print(f"Repeat used: {USE_REPEAT}")
print(f"Decay constant λ: {lambda_decay:.6f} s⁻¹")
print(f"R² of exponential fit: {r2:.3f}")
print(f"Equivalent removal rate (λ×3600): {ACH:.2f} h⁻¹")
print(f"Half-life: {half_life_min:.1f} min")

# Plot
fit = np.exp(intercept + slope * tsec)

plt.figure(figsize=(6.8, 4.2))
plt.scatter(tsec, decay_conc, label="Measured")
plt.plot(tsec, fit, label="Exponential fit")
plt.xlabel("Time since start of decay window (s)")
plt.ylabel("Total particle number concentration (cm$^{-3}$)")
plt.title(f"Aerosol decay fit ({USE_REPEAT})")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend(frameon=False)
plt.tight_layout()
plt.show()
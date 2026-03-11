# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 22:42:58 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# Figure 8.3.1
# Semi-log decay comparison using SMPS total number concentration
# Onion-ring frying, Day 4, Hood OFF vs Hood ON
# ============================================================

smps_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 8.x, 9.x/DAY4 SMPS DATA_COM32.xlsx"
output_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 8.x, 9.x/Figure_8_3_1_SMPS_semilog_decay.png"

experiments = [
    {"label": "OFF_R1", "condition": "Hood OFF", "start": "12:41:15", "end": "13:03:15"},
    {"label": "ON_R1",  "condition": "Hood ON",  "start": "13:13:33", "end": "13:35:40"},
    {"label": "OFF_R2", "condition": "Hood OFF", "start": "13:41:30", "end": "14:03:40"},
    {"label": "ON_R2",  "condition": "Hood ON",  "start": "14:10:20", "end": "14:32:25"},
    {"label": "OFF_R3", "condition": "Hood OFF", "start": "14:39:13", "end": "15:01:20"},
    {"label": "ON_R3",  "condition": "Hood ON",  "start": "15:06:40", "end": "15:28:55"},
]

decay_minutes = 10
rolling_window = 3

# ------------------------------------------------------------
# Load SMPS
# ------------------------------------------------------------
raw = pd.read_excel(smps_file)
raw.columns = [str(c).strip() for c in raw.columns]

print("SMPS columns:")
print(raw.columns.tolist())

if "Time" not in raw.columns:
    raise ValueError("Could not find 'Time' column in SMPS file.")

# numeric bin columns
bin_cols = []
for col in raw.columns:
    if col == "Time":
        continue
    try:
        float(col)
        bin_cols.append(col)
    except ValueError:
        pass

if not bin_cols:
    raise ValueError("No numeric SMPS size-bin columns found.")

print(f"Using {len(bin_cols)} SMPS size bins.")

df = raw[["Time"] + bin_cols].copy()
df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

for col in bin_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["Total_Number"] = df[bin_cols].sum(axis=1, skipna=True)
df = df.dropna(subset=["Time", "Total_Number"]).copy()
df = df.sort_values("Time").reset_index(drop=True)

# keep time-of-day only
df["Clock"] = df["Time"].dt.strftime("%H:%M:%S")
df["Time"] = pd.to_datetime("2025-01-01 " + df["Clock"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

# ------------------------------------------------------------
# Extract decay
# ------------------------------------------------------------
def extract_decay(data, start_time, end_time, label):
    start_dt = pd.to_datetime("2025-01-01 " + start_time, format="%Y-%m-%d %H:%M:%S")
    end_dt   = pd.to_datetime("2025-01-01 " + end_time,   format="%Y-%m-%d %H:%M:%S")
    window_end = end_dt + pd.Timedelta(minutes=decay_minutes)

    subset = data[(data["Time"] >= start_dt) & (data["Time"] <= window_end)].copy()
    exp_only = subset[(subset["Time"] >= start_dt) & (subset["Time"] <= end_dt)].copy()

    if subset.empty or exp_only.empty:
        raise ValueError(f"No usable data for {label}")

    peak_idx = exp_only["Total_Number"].idxmax()
    peak_time = data.loc[peak_idx, "Time"]
    peak_val = data.loc[peak_idx, "Total_Number"]

    decay = subset[subset["Time"] >= peak_time].copy().reset_index(drop=True)
    decay["Time_min"] = (decay["Time"] - peak_time).dt.total_seconds() / 60
    decay = decay[decay["Time_min"] <= decay_minutes].copy().reset_index(drop=True)

    # background from final 3 points
    background = decay["Total_Number"].tail(3).mean()
    decay["Decay"] = (decay["Total_Number"] - background).clip(lower=0)

    # smooth
    decay["Decay_smooth"] = decay["Decay"].rolling(rolling_window, center=True, min_periods=1).mean()

    c0 = decay["Decay_smooth"].iloc[0]
    if c0 <= 0:
        raise ValueError(f"Non-positive starting value for {label}")

    decay["Normalised"] = decay["Decay_smooth"] / c0
    decay["ln_Normalised"] = np.log(decay["Normalised"].replace(0, np.nan))

    return decay, peak_val

segments = []
for exp in experiments:
    try:
        decay, peak_val = extract_decay(df, exp["start"], exp["end"], exp["label"])
        decay["Condition"] = exp["condition"]
        decay["Repeat"] = exp["label"]
        segments.append(decay)
        print(f"{exp['label']}: peak = {peak_val:,.0f} particles cm^-3")
    except Exception as e:
        print(f"{exp['label']} skipped: {e}")

all_decay = pd.concat(segments, ignore_index=True)

# average by condition/time
all_decay["Time_bin"] = all_decay["Time_min"].round(2)
summary = (
    all_decay.groupby(["Condition", "Time_bin"])["ln_Normalised"]
    .agg(["mean", "std", "count"])
    .reset_index()
)

summary["sem"] = summary["std"] / np.sqrt(summary["count"])
summary["upper"] = summary["mean"] + summary["sem"].fillna(0)
summary["lower"] = summary["mean"] - summary["sem"].fillna(0)

off = summary[summary["Condition"] == "Hood OFF"].copy()
on  = summary[summary["Condition"] == "Hood ON"].copy()

# linear fit to ln(C/C0) = -kt
def fit_decay(curve_df):
    fit_df = curve_df.dropna(subset=["mean"]).copy()
    fit_df = fit_df[np.isfinite(fit_df["mean"])]
    if len(fit_df) < 2:
        return np.nan, np.nan
    slope, intercept = np.polyfit(fit_df["Time_bin"], fit_df["mean"], 1)
    return slope, intercept

slope_off, intercept_off = fit_decay(off)
slope_on, intercept_on = fit_decay(on)

print(f"Hood OFF slope: {slope_off:.4f} min^-1")
print(f"Hood ON slope: {slope_on:.4f} min^-1")

# ------------------------------------------------------------
# Plot
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 6))

ax.plot(off["Time_bin"], off["mean"], linewidth=2.5, label="Hood OFF")
ax.fill_between(off["Time_bin"], off["lower"], off["upper"], alpha=0.20)

ax.plot(on["Time_bin"], on["mean"], linewidth=2.5, linestyle="--", label="Hood ON")
ax.fill_between(on["Time_bin"], on["lower"], on["upper"], alpha=0.20)

# fitted lines
if np.isfinite(slope_off):
    ax.plot(off["Time_bin"], slope_off * off["Time_bin"] + intercept_off, linewidth=1.5)
if np.isfinite(slope_on):
    ax.plot(on["Time_bin"], slope_on * on["Time_bin"] + intercept_on, linewidth=1.5, linestyle=":")

ax.set_xlabel("Time since peak (min)")
ax.set_ylabel("ln(C/C$_0$)")
ax.set_xlim(0, decay_minutes)
ax.legend(loc="upper right", frameon=True)

plt.tight_layout()
plt.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()
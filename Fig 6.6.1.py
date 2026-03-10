# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 19:07:42 2026

@author: papkp
"""

# =========================================================
# SECTION 6.6 – VENTILATION REMOVAL RATE CONSTANT
# Fit C(t) = C0 * exp(-k t) to ELPI decay data
# =========================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ---------------------------------------------------------
# FILE
# ---------------------------------------------------------
elpi_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/day4 elpi data.xlsx"
)

# ---------------------------------------------------------
# TIME WINDOWS
# ---------------------------------------------------------
EXP1_NO_FAN = ("12:41:15", "13:03:15")
EXP2_FAN    = ("13:13:33", "13:35:40")
EXP7_NO_FAN = ("16:09:30", "16:40:30")
EXP8_FAN    = ("16:48:50", "17:18:50")

# ---------------------------------------------------------
# LOAD ELPI
# ---------------------------------------------------------
df = pd.read_excel(elpi_file)
df.columns = [str(c).strip() for c in df.columns]

time_col = "Time" if "Time" in df.columns else "corrected time"
df["DateTime"] = pd.to_datetime(df[time_col], errors="coerce")
df["Total"] = pd.to_numeric(df["Concentration value"], errors="coerce")
df = df.dropna(subset=["DateTime", "Total"]).copy()

df["TimeOnly"] = pd.to_datetime(
    "2000-01-01 " + df["DateTime"].dt.strftime("%H:%M:%S"),
    errors="coerce"
)

# ---------------------------------------------------------
# EXTRACT DECAY
# ---------------------------------------------------------
def extract_decay(df, start, end, smooth_window=5, max_minutes=15, min_fraction=0.05):
    start_dt = pd.to_datetime("2000-01-01 " + start)
    end_dt   = pd.to_datetime("2000-01-01 " + end)

    block = df[(df["TimeOnly"] >= start_dt) & (df["TimeOnly"] <= end_dt)].copy()
    block = block.sort_values("TimeOnly").reset_index(drop=True)

    block["Smooth"] = block["Total"].rolling(smooth_window, center=True, min_periods=1).mean()

    peak_idx = block["Smooth"].idxmax()
    decay = block.loc[peak_idx:].copy().reset_index(drop=True)

    decay["Minutes"] = (
        (decay["TimeOnly"] - decay["TimeOnly"].iloc[0]).dt.total_seconds() / 60
    )
    decay["Norm"] = decay["Smooth"] / decay["Smooth"].iloc[0]

    decay = decay[decay["Minutes"] <= max_minutes].copy()
    decay = decay[decay["Norm"] > min_fraction].copy()

    return decay

# ---------------------------------------------------------
# FIT EXPONENTIAL DECAY
# ln(C/C0) = -k t
# ---------------------------------------------------------
def fit_decay_constant(decay_df):
    x = decay_df["Minutes"].values
    y = np.log(decay_df["Norm"].values)

    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]
    intercept = coeffs[1]

    k = -slope
    y_fit = slope * x + intercept

    # R^2
    ss_res = np.sum((y - y_fit) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

    return k, intercept, r2

# ---------------------------------------------------------
# BUILD DATASETS
# ---------------------------------------------------------
datasets = {
    "Deep fry – no fan": extract_decay(df, *EXP1_NO_FAN),
    "Deep fry – fan":    extract_decay(df, *EXP2_FAN),
    "Stir fry – no fan": extract_decay(df, *EXP7_NO_FAN),
    "Stir fry – fan":    extract_decay(df, *EXP8_FAN),
}

# ---------------------------------------------------------
# FIT + PRINT RESULTS
# ---------------------------------------------------------
results = []

for name, decay in datasets.items():
    k, intercept, r2 = fit_decay_constant(decay)
    results.append({
        "Experiment": name,
        "k (min^-1)": k,
        "R^2": r2,
        "Half-life (min)": np.log(2) / k if k > 0 else np.nan
    })

results_df = pd.DataFrame(results)
print("\n================ REMOVAL RATE CONSTANTS ================\n")
print(results_df)
print("\n========================================================\n")

# ---------------------------------------------------------
# PLOT LOG-LINEAR DECAY FITS
# ---------------------------------------------------------
plt.figure(figsize=(8, 5))

for name, decay in datasets.items():
    k, intercept, r2 = fit_decay_constant(decay)

    x = decay["Minutes"].values
    y = np.log(decay["Norm"].values)
    y_fit = -k * x + intercept

    plt.plot(x, y, linewidth=2, label=f"{name} (k={k:.3f} min$^{{-1}}$)")
    plt.plot(x, y_fit, linestyle="--", linewidth=1)

plt.xlabel("Time after peak (minutes)")
plt.ylabel("ln(C/Cmax)")
plt.title("Figure 6.5 – Removal rate constants with and without kitchen exhaust ventilation")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend()
plt.tight_layout()
plt.show()
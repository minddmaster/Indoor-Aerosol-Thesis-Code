# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 19:43:20 2026

@author: papkp
"""

# =========================================================
# FIGURE 6.7 – Full-day SMPS time series under natural ventilation
# Kitchen vs master bedroom
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# ---------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------
kitchen_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.2.1/DAY5 SMPS DATA_COM33_Kitchen.xlsx"
)

bedroom_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.2.1/DAY5 SMPS DATA_COM32_MBed.xlsx"
)

# ---------------------------------------------------------
# BACON FRYING PERIODS WITHIN AVAILABLE DATA
# ---------------------------------------------------------
BACON_PERIODS = [
    ("Bacon fry 1", "12:57:40", "13:22:30"),
    ("Bacon fry 2", "13:23:30", "13:46:40"),
]

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------
smooth_window = 3
merge_tolerance = "3min"
use_log_y = True

phase_alpha = 0.10
phase_color = "#ead1dc"

# ---------------------------------------------------------
# LOAD SMPS TOTAL
# ---------------------------------------------------------
def load_smps_total(filepath, label):
    df = pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    print(f"\nLoaded: {filepath.name}")
    print("Columns:", list(df.columns))

    if "corrected time" not in df.columns:
        raise ValueError(f"'corrected time' column not found in {filepath.name}")

    df["DateTime"] = pd.to_datetime(df["corrected time"], errors="coerce")
    df = df.dropna(subset=["DateTime"]).copy()

    # Use time-of-day only
    df["TimeOnly"] = pd.to_datetime(
        "2000-01-01 " + df["DateTime"].dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

    conc_cols = [c for c in df.columns if c not in ["corrected time", "DateTime", "TimeOnly"]]
    df[conc_cols] = df[conc_cols].apply(pd.to_numeric, errors="coerce")
    df["Total"] = df[conc_cols].sum(axis=1, skipna=True)

    out = df[["TimeOnly", "Total"]].copy()
    out = out.rename(columns={"Total": label})
    out = out.sort_values("TimeOnly").reset_index(drop=True)

    print(f"Rows kept: {len(out)}")
    print(f"Time range: {out['TimeOnly'].min()} to {out['TimeOnly'].max()}")

    return out

# ---------------------------------------------------------
# LOAD FILES
# ---------------------------------------------------------
kitchen = load_smps_total(kitchen_file, "Kitchen")
bedroom = load_smps_total(bedroom_file, "Master bedroom")

# ---------------------------------------------------------
# MERGE BY NEAREST TIME
# ---------------------------------------------------------
ts = pd.merge_asof(
    kitchen.sort_values("TimeOnly"),
    bedroom.sort_values("TimeOnly"),
    on="TimeOnly",
    direction="nearest",
    tolerance=pd.Timedelta(merge_tolerance)
)

ts = ts.dropna(subset=["Master bedroom"]).copy()

if ts.empty:
    raise ValueError("Merged SMPS dataset is empty. Increase merge_tolerance or inspect timestamps.")

# ---------------------------------------------------------
# SMOOTHING
# ---------------------------------------------------------
ts["Kitchen_smooth"] = ts["Kitchen"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

ts["Bedroom_smooth"] = ts["Master bedroom"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

# ---------------------------------------------------------
# PLOT FULL DAY
# ---------------------------------------------------------
plt.figure(figsize=(11, 5))

plt.plot(
    ts["TimeOnly"],
    ts["Kitchen_smooth"],
    linewidth=1.5,
    marker="o",
    markersize=3,
    label="Kitchen SMPS"
)

plt.plot(
    ts["TimeOnly"],
    ts["Bedroom_smooth"],
    linewidth=1.5,
    marker="s",
    markersize=3,
    linestyle="--",
    label="Master bedroom SMPS"
)

# Shade bacon frying periods
for label, start_str, end_str in BACON_PERIODS:
    start_dt = pd.to_datetime("2000-01-01 " + start_str)
    end_dt   = pd.to_datetime("2000-01-01 " + end_str)

    plt.axvspan(start_dt, end_dt, alpha=phase_alpha, color=phase_color)

plt.xlabel("Time")
plt.ylabel("Particle number concentration (particles cm$^{-3}$)")
plt.title(
    "Figure 6.7 – Full-day particle number concentration measured in the kitchen and "
    "master bedroom under natural ventilation"
)

plt.legend()
plt.grid(True, linestyle="--", linewidth=0.5)

if use_log_y:
    plt.yscale("log")
    plt.ylim(2e2, 3e5)

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()

plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PRINT SUMMARY FOR BACON PERIODS
# ---------------------------------------------------------
print("\n================ BACON NATURAL VENTILATION SUMMARY ================\n")
for label, start_str, end_str in BACON_PERIODS:
    start_dt = pd.to_datetime("2000-01-01 " + start_str)
    end_dt   = pd.to_datetime("2000-01-01 " + end_str)

    block = ts[(ts["TimeOnly"] >= start_dt) & (ts["TimeOnly"] <= end_dt)].copy()

    if not block.empty:
        k_idx = block["Kitchen_smooth"].idxmax()
        b_idx = block["Bedroom_smooth"].idxmax()

        print(label)
        print("  Kitchen peak:", round(ts.loc[k_idx, "Kitchen_smooth"], 0),
              "at", ts.loc[k_idx, "TimeOnly"].strftime("%H:%M:%S"))
        print("  Bedroom peak:", round(ts.loc[b_idx, "Bedroom_smooth"], 0),
              "at", ts.loc[b_idx, "TimeOnly"].strftime("%H:%M:%S"))
        print()

print("===================================================================\n")
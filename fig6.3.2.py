# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 18:27:42 2026

@author: papkp
"""

# =========================================================
# FIGURE 6.3.2 – SMPS time series during bacon frying
# Kitchen vs Master Bedroom
# Updated thesis-quality version
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# ---------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------
kitchen_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/DAY5 SMPS DATA_COM33_Kitchen.xlsx"
)

bedroom_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/DAY5 SMPS DATA_COM32_MBed.xlsx"
)

# ---------------------------------------------------------
# BACON COOKING TIMELINE
# ---------------------------------------------------------
BACON_TIMELINE = [
    ("Heat",        "12:57:40", "13:02:40"),
    ("Fry",         "13:02:40", "13:08:40"),
    ("Decay",       "13:08:40", "13:13:58"),
    ("Ventilation", "13:13:58", "13:22:30"),

    ("Heat",        "13:23:30", "13:28:30"),
    ("Fry",         "13:28:30", "13:34:30"),
    ("Decay",       "13:34:30", "13:39:30"),
    ("Ventilation", "13:39:30", "13:46:40"),

    ("Heat",        "13:48:50", "13:53:50"),
    ("Fry",         "13:53:50", "13:59:50"),
    ("Decay",       "13:59:50", "14:04:50"),
    ("Ventilation", "14:04:50", "14:11:50"),
]

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------
merge_tolerance = "3min"
smooth_window = 3
use_log_y = True

# plot only the bacon experiment window
plot_start = "12:55:00"
plot_end   = "14:12:00"

# lighter shading for cleaner figure
phase_colors = {
    "Heat": "orange",
    "Fry": "red",
    "Decay": "blue",
    "Ventilation": "green"
}
phase_alpha = 0.07

# ---------------------------------------------------------
# LOAD SMPS TOTAL CONCENTRATION
# ---------------------------------------------------------
def load_smps_total(filepath, room_name):
    df = pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    if "corrected time" not in df.columns:
        raise ValueError(f"'corrected time' column not found in {filepath.name}")

    df["DateTime"] = pd.to_datetime(df["corrected time"], errors="coerce")
    df = df.dropna(subset=["DateTime"]).copy()

    # Ignore inconsistent original dates; use time of day only
    df["TimeOnly"] = pd.to_datetime(
        "2000-01-01 " + df["DateTime"].dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

    conc_cols = [c for c in df.columns if c not in ["corrected time", "DateTime", "TimeOnly"]]
    df[conc_cols] = df[conc_cols].apply(pd.to_numeric, errors="coerce")

    df["Total"] = df[conc_cols].sum(axis=1, skipna=True)

    out = df[["TimeOnly", "Total"]].copy()
    out = out.rename(columns={"Total": room_name})
    out = out.sort_values("TimeOnly").reset_index(drop=True)

    return out

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
kitchen = load_smps_total(kitchen_file, "Kitchen")
bedroom = load_smps_total(bedroom_file, "Master bedroom")

print("Kitchen range:", kitchen["TimeOnly"].min(), "to", kitchen["TimeOnly"].max())
print("Bedroom range:", bedroom["TimeOnly"].min(), "to", bedroom["TimeOnly"].max())

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
    raise ValueError("Merged dataset is empty. Increase merge_tolerance or inspect timestamps.")

# ---------------------------------------------------------
# FILTER BACON WINDOW
# ---------------------------------------------------------
plot_start_dt = pd.to_datetime("2000-01-01 " + plot_start)
plot_end_dt   = pd.to_datetime("2000-01-01 " + plot_end)

ts = ts[(ts["TimeOnly"] >= plot_start_dt) & (ts["TimeOnly"] <= plot_end_dt)].copy()

if ts.empty:
    raise ValueError("No data found in the selected bacon frying time window.")

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
# OPTIONAL PEAK SUMMARY
# ---------------------------------------------------------
k_idx = ts["Kitchen_smooth"].idxmax()
b_idx = ts["Bedroom_smooth"].idxmax()

k_peak_time = ts.loc[k_idx, "TimeOnly"]
b_peak_time = ts.loc[b_idx, "TimeOnly"]

k_peak_value = ts.loc[k_idx, "Kitchen_smooth"]
b_peak_value = ts.loc[b_idx, "Bedroom_smooth"]

delay_min = (b_peak_time - k_peak_time).total_seconds() / 60
fraction_pct = (b_peak_value / k_peak_value) * 100

print("\n================ FIGURE 6.3.2 SUMMARY ================")
print("Kitchen peak time:", k_peak_time.strftime("%H:%M:%S"))
print("Kitchen peak concentration (cm^-3):", round(k_peak_value, 0))
print("Master bedroom peak time:", b_peak_time.strftime("%H:%M:%S"))
print("Master bedroom peak concentration (cm^-3):", round(b_peak_value, 0))
print("Bedroom peak as % of kitchen peak:", round(fraction_pct, 1))
print("Approx. delay (min):", round(delay_min, 2))
print("======================================================\n")

# ---------------------------------------------------------
# PLOT
# ---------------------------------------------------------
plt.figure(figsize=(11, 5))

plt.plot(
    ts["TimeOnly"],
    ts["Kitchen_smooth"],
    linewidth=2,
    label="Kitchen"
)

plt.plot(
    ts["TimeOnly"],
    ts["Bedroom_smooth"],
    linewidth=2,
    linestyle="--",
    label="Master bedroom"
)

# Shade experiment phases
for phase, start, end in BACON_TIMELINE:
    start_dt = pd.to_datetime("2000-01-01 " + start)
    end_dt   = pd.to_datetime("2000-01-01 " + end)

    plt.axvspan(
        start_dt,
        end_dt,
        alpha=phase_alpha,
        color=phase_colors[phase]
    )

# Optional labels for first cycle only
plt.text(pd.to_datetime("2000-01-01 12:59:30"), 1.4e5, "Heat", fontsize=9)
plt.text(pd.to_datetime("2000-01-01 13:04:30"), 1.4e5, "Fry", fontsize=9)
plt.text(pd.to_datetime("2000-01-01 13:10:00"), 1.4e5, "Decay", fontsize=9)
plt.text(pd.to_datetime("2000-01-01 13:16:00"), 1.4e5, "Ventilation", fontsize=9)

plt.xlabel("Time")
plt.ylabel("Particle number concentration (cm$^{-3}$)")
plt.title(
    "Figure 6.3.2 Time series of particle number concentration measured in the kitchen "
    "and master bedroom during bacon frying"
)

plt.legend()
plt.grid(True, linestyle="--", linewidth=0.5)

if use_log_y:
    plt.yscale("log")
    plt.ylim(2e2, 2e5)

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()

plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------
output_dir = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.2"
)
output_dir.mkdir(parents=True, exist_ok=True)

png_file = output_dir / "Figure_6_3_2_SMPS_Bacon_Kitchen_vs_MasterBedroom.png"
tiff_file = output_dir / "Figure_6_3_2_SMPS_Bacon_Kitchen_vs_MasterBedroom.tiff"

plt.figure(1)
plt.savefig(png_file, dpi=600, bbox_inches="tight")
plt.savefig(tiff_file, dpi=600, bbox_inches="tight")

print("Saved PNG:", png_file)
print("Saved TIFF:", tiff_file)
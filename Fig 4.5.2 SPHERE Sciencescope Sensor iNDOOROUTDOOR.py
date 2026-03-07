# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 09:44:23 2026

@author: papkp
"""

# =========================================================
# SCIENCESCOPE COMPARISON SCRIPT
# SPHERE House experiments: Kitchen vs Outdoor
# Period: 26 Feb 2025 12:00 to 28 Feb 2025 13:00
# 30-minute interval data
# =========================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# =========================
# USER INPUT
# =========================
outdoor_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 4.5.2 SPHERE 28 FEB/26 feb 16.30 - 28 Feb 10.30 2025 SPHERE X22e outdoor.csv"
kitchen_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 4.5.2 SPHERE 28 FEB/26 feb 16.30 - 28 Feb 10.30 2025 SPHERE X223 Kitchen.csv"

output_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 4.5.2 SPHERE 28 FEB/outputs")
output_dir.mkdir(parents=True, exist_ok=True)

# =========================
# EXPERIMENT WINDOWS
# =========================
# Broad block shading suitable for 30-minute sensor resolution

experiment_windows = [
    # 26 Feb 2025
    ("26/02/2025 12:34:30", "26/02/2025 13:16:45", "Exp 9: Fan off"),
    ("26/02/2025 14:19:15", "26/02/2025 14:54:40", "Exp 10: Fan max"),
    ("26/02/2025 17:02:00", "26/02/2025 17:38:30", "Exp 11: Fan min"),

    # 27 Feb 2025 - Onion ring deep fry
    ("27/02/2025 12:41:15", "27/02/2025 13:03:15", "Exp 1: Deep fry no fan"),
    ("27/02/2025 13:13:33", "27/02/2025 13:35:40", "Exp 2: Deep fry fan"),
    ("27/02/2025 13:41:30", "27/02/2025 14:03:40", "Exp 3: Deep fry no fan"),
    ("27/02/2025 14:10:20", "27/02/2025 14:32:25", "Exp 4: Deep fry fan"),
    ("27/02/2025 14:39:13", "27/02/2025 15:01:20", "Exp 5: Deep fry no fan"),
    ("27/02/2025 15:06:40", "27/02/2025 15:28:55", "Exp 6: Deep fry fan"),

    # 27 Feb 2025 - Stir fry
    ("27/02/2025 16:09:30", "27/02/2025 16:40:30", "Exp 7: Stir fry no fan"),
    ("27/02/2025 16:48:50", "27/02/2025 17:18:50", "Exp 8: Stir fry fan"),

    # 28 Feb 2025 - 5% NaCl
    ("28/02/2025 09:46:30", "28/02/2025 10:06:31", "Exp 1: NaCl 10 min"),
    ("28/02/2025 10:11:45", "28/02/2025 11:02:30", "Exp 2: NaCl 20 min"),
    ("28/02/2025 11:04:25", "28/02/2025 11:52:10", "Exp 3: NaCl 20 min"),
    ("28/02/2025 12:00:40", "28/02/2025 12:56:31", "Exp 4: NaCl 20 min"),
]

# Daily grouped windows for cleaner figure shading
daily_blocks = [
    ("26/02/2025 12:34:30", "26/02/2025 17:38:30", "26 Feb ventilation tests"),
    ("27/02/2025 12:41:15", "27/02/2025 17:18:50", "27 Feb cooking experiments"),
    ("28/02/2025 09:46:30", "28/02/2025 12:56:31", "28 Feb NaCl experiments"),
]

# Optional repeat/event markers for zoomed plots
event_markers = [
    # 27 Feb onion ring + stir fry
    ("27/02/2025 12:41:15", "Exp1 start"),
    ("27/02/2025 13:03:15", "Exp1 end"),
    ("27/02/2025 13:13:33", "Exp2 start"),
    ("27/02/2025 13:35:40", "Exp2 end"),
    ("27/02/2025 13:41:30", "Exp3 start"),
    ("27/02/2025 14:03:40", "Exp3 end"),
    ("27/02/2025 14:10:20", "Exp4 start"),
    ("27/02/2025 14:32:25", "Exp4 end"),
    ("27/02/2025 14:39:13", "Exp5 start"),
    ("27/02/2025 15:01:20", "Exp5 end"),
    ("27/02/2025 15:06:40", "Exp6 start"),
    ("27/02/2025 15:28:55", "Exp6 end"),
    ("27/02/2025 16:09:30", "Exp7 start"),
    ("27/02/2025 16:40:30", "Exp7 end"),
    ("27/02/2025 16:48:50", "Exp8 start"),
    ("27/02/2025 17:18:50", "Exp8 end"),

    # 28 Feb NaCl
    ("28/02/2025 09:46:30", "Exp1 gen"),
    ("28/02/2025 10:06:31", "Exp1 vent"),
    ("28/02/2025 10:11:45", "Exp2 gen"),
    ("28/02/2025 11:02:30", "Exp2 end"),
    ("28/02/2025 11:04:25", "Exp3 gen"),
    ("28/02/2025 11:52:10", "Exp3 end"),
    ("28/02/2025 12:00:40", "Exp4 gen"),
    ("28/02/2025 12:56:31", "Exp4 end"),
]

# =========================
# LOAD FUNCTION
# =========================
def load_sciencescope_csv(filepath, location_name):
    raw = pd.read_csv(filepath, header=None)
    records = []
    ncols = raw.shape[1]

    for start in range(0, ncols, 7):
        if start + 3 >= ncols:
            continue

        dt_col = raw.iloc[:, start]
        value_col = raw.iloc[:, start + 1]
        param_col = raw.iloc[:, start + 3]

        param_name = param_col.dropna().astype(str).str.strip().replace("", np.nan).dropna()
        if param_name.empty:
            continue
        param_name = param_name.iloc[0]

        temp = pd.DataFrame({
            "datetime": pd.to_datetime(dt_col, dayfirst=True, errors="coerce"),
            "value": pd.to_numeric(value_col, errors="coerce")
        }).dropna(subset=["datetime"])

        temp = temp[temp["datetime"].dt.year >= 2020]
        temp["parameter"] = param_name
        records.append(temp)

    tidy = pd.concat(records, ignore_index=True)

    wide = tidy.pivot_table(
        index="datetime",
        columns="parameter",
        values="value",
        aggfunc="mean"
    ).reset_index()

    rename_map = {
        "AQ CO": "CO",
        "AQ CO2 Concentration": "CO2",
        "AQ PM1.0": "PM1",
        "AQ PM2.5": "PM2_5",
        "AQ PM10.0": "PM10",
        "AQ VOC": "VOC",
        "AQ VOC ": "VOC",
        "AQ Temperature": "Temperature",
        "AQ Sound Level": "Sound",
        "AQ RSSI": "RSSI"
    }

    wide = wide.rename(columns=rename_map)
    wide.columns.name = None

    new_cols = ["datetime"] + [f"{c}_{location_name}" for c in wide.columns if c != "datetime"]
    wide.columns = new_cols

    wide = wide.sort_values("datetime").drop_duplicates(subset="datetime").reset_index(drop=True)
    return wide

# =========================
# SUPPORT FUNCTIONS
# =========================
def add_shading(ax, windows, alpha=0.12, text_y=0.9):
    for start, end, label in windows:
        start_dt = pd.to_datetime(start, dayfirst=True)
        end_dt = pd.to_datetime(end, dayfirst=True)
        ax.axvspan(start_dt, end_dt, alpha=alpha)
        ymax = ax.get_ylim()[1]
        ax.text(
            start_dt + (end_dt - start_dt) / 2,
            ymax * text_y,
            label,
            ha="center",
            va="top",
            fontsize=8,
            rotation=90
        )

def add_event_lines(ax, markers):
    for t, label in markers:
        tt = pd.to_datetime(t, dayfirst=True)
        ax.axvline(tt, linestyle=":", linewidth=0.8)

# =========================
# LOAD DATA
# =========================
outdoor = load_sciencescope_csv(outdoor_file, "Outdoor")
kitchen = load_sciencescope_csv(kitchen_file, "Kitchen")

df = pd.merge(outdoor, kitchen, on="datetime", how="outer").sort_values("datetime").reset_index(drop=True)

# IMPORTANT:
# Your uploaded files start at 26 Feb 16:30, so anything before 16:30 on 26 Feb
# cannot actually be plotted unless you have an earlier export.
start_time = pd.to_datetime("26/02/2025 16:30", dayfirst=True)
end_time = pd.to_datetime("28/02/2025 10:30", dayfirst=True)

df = df[(df["datetime"] >= start_time) & (df["datetime"] <= end_time)].copy()

# =========================
# DERIVED VARIABLES
# =========================
for pollutant in ["PM1", "PM2_5", "PM10", "CO", "VOC", "CO2"]:
    k = f"{pollutant}_Kitchen"
    o = f"{pollutant}_Outdoor"
    if k in df.columns and o in df.columns:
        df[f"{pollutant}_difference"] = df[k] - df[o]
        df[f"{pollutant}_ratio"] = np.where(df[o] > 0, df[k] / df[o], np.nan)

df.to_csv(output_dir / "sciencescope_kitchen_outdoor_merged.csv", index=False)

# =========================
# STYLE
# =========================
plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 11
})

date_fmt = mdates.DateFormatter("%d %b\n%H:%M")

# =========================
# FIGURE 1: MAIN PM FIGURE
# =========================
fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

pollutants = [
    ("PM1", "PM$_1$ (µg m$^{-3}$)"),
    ("PM2_5", "PM$_{2.5}$ (µg m$^{-3}$)"),
    ("PM10", "PM$_{10}$ (µg m$^{-3}$)")
]

for ax, (pol, ylabel) in zip(axes, pollutants):
    k = f"{pol}_Kitchen"
    o = f"{pol}_Outdoor"

    if k in df.columns:
        ax.plot(df["datetime"], df[k], linewidth=2, marker="o", markersize=3, label="Kitchen")
    if o in df.columns:
        ax.plot(df["datetime"], df[o], linewidth=2, linestyle="--", marker="s", markersize=3, label="Outdoor")

    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", linewidth=0.5)
    add_shading(ax, daily_blocks, alpha=0.10, text_y=0.88)
    ax.legend(frameon=False, loc="upper right")

axes[0].set_title(
    "ScienceScope particle concentrations during SPHERE House experiments:\nKitchen versus outdoor measurements"
)
axes[-1].set_xlabel("Date and time")
axes[-1].xaxis.set_major_formatter(date_fmt)
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "Figure_4_5_2_PM_comparison_kitchen_vs_outdoor.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================
# FIGURE 2: PM DIFFERENCE
# =========================
fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

diff_info = [
    ("PM1_difference", "Kitchen - Outdoor PM$_1$"),
    ("PM2_5_difference", "Kitchen - Outdoor PM$_{2.5}$"),
    ("PM10_difference", "Kitchen - Outdoor PM$_{10}$")
]

for ax, (col, ylabel) in zip(axes, diff_info):
    if col in df.columns:
        ax.plot(df["datetime"], df[col], linewidth=2, marker="o", markersize=3)
        ax.axhline(0, linestyle="--", linewidth=1)

    ax.set_ylabel(ylabel + "\n(µg m$^{-3}$)")
    ax.grid(True, linestyle="--", linewidth=0.5)
    add_shading(ax, daily_blocks, alpha=0.10, text_y=0.88)

axes[0].set_title("Indoor-outdoor particle concentration difference during SPHERE House experiments")
axes[-1].set_xlabel("Date and time")
axes[-1].xaxis.set_major_formatter(date_fmt)
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "Figure_4_5_2_PM_difference.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================
# FIGURE 3: PM RATIO
# =========================
fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

ratio_info = [
    ("PM1_ratio", "PM$_1$ I/O ratio"),
    ("PM2_5_ratio", "PM$_{2.5}$ I/O ratio"),
    ("PM10_ratio", "PM$_{10}$ I/O ratio")
]

for ax, (col, ylabel) in zip(axes, ratio_info):
    if col in df.columns:
        ax.plot(df["datetime"], df[col], linewidth=2, marker="o", markersize=3)
        ax.axhline(1, linestyle="--", linewidth=1)

    ax.set_ylabel(ylabel)
    ax.set_yscale("log")
    ax.grid(True, linestyle="--", linewidth=0.5)
    add_shading(ax, daily_blocks, alpha=0.10, text_y=0.88)

axes[0].set_title("Indoor/outdoor particle ratios during SPHERE House experiments")
axes[-1].set_xlabel("Date and time")
axes[-1].xaxis.set_major_formatter(date_fmt)
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "Figure_4_5_2_PM_ratio.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================
# FIGURE 4: 27 FEB ZOOMED COOKING PLOT
# =========================
df_27 = df[
    (df["datetime"] >= pd.to_datetime("27/02/2025 12:00", dayfirst=True)) &
    (df["datetime"] <= pd.to_datetime("27/02/2025 18:00", dayfirst=True))
].copy()

fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

for ax, (pol, ylabel) in zip(axes, pollutants):
    k = f"{pol}_Kitchen"
    o = f"{pol}_Outdoor"

    if k in df_27.columns:
        ax.plot(df_27["datetime"], df_27[k], linewidth=2, marker="o", markersize=4, label="Kitchen")
    if o in df_27.columns:
        ax.plot(df_27["datetime"], df_27[o], linewidth=2, linestyle="--", marker="s", markersize=4, label="Outdoor")

    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", linewidth=0.5)
    add_shading(ax, [w for w in experiment_windows if pd.to_datetime(w[0], dayfirst=True).date() == pd.Timestamp("2025-02-27").date()], alpha=0.12, text_y=0.88)
    add_event_lines(ax, [m for m in event_markers if pd.to_datetime(m[0], dayfirst=True).date() == pd.Timestamp("2025-02-27").date()])
    ax.legend(frameon=False, loc="upper right")

axes[0].set_title(
    "ScienceScope particle measurements on 27 February 2025:\nOnion ring deep frying and stir-fry experiments"
)
axes[-1].set_xlabel("Time")
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "Figure_4_5_2_27Feb_zoomed_PM.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================
# FIGURE 5: 28 FEB ZOOMED NaCl PLOT
# =========================
df_28 = df[
    (df["datetime"] >= pd.to_datetime("28/02/2025 09:30", dayfirst=True)) &
    (df["datetime"] <= pd.to_datetime("28/02/2025 13:00", dayfirst=True))
].copy()

fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

for ax, (pol, ylabel) in zip(axes, pollutants):
    k = f"{pol}_Kitchen"
    o = f"{pol}_Outdoor"

    if k in df_28.columns:
        ax.plot(df_28["datetime"], df_28[k], linewidth=2, marker="o", markersize=4, label="Kitchen")
    if o in df_28.columns:
        ax.plot(df_28["datetime"], df_28[o], linewidth=2, linestyle="--", marker="s", markersize=4, label="Outdoor")

    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", linewidth=0.5)
    add_shading(ax, [w for w in experiment_windows if pd.to_datetime(w[0], dayfirst=True).date() == pd.Timestamp("2025-02-28").date()], alpha=0.12, text_y=0.88)
    add_event_lines(ax, [m for m in event_markers if pd.to_datetime(m[0], dayfirst=True).date() == pd.Timestamp("2025-02-28").date()])
    ax.legend(frameon=False, loc="upper right")

axes[0].set_title(
    "ScienceScope particle measurements on 28 February 2025:\n5% NaCl aerosol experiments"
)
axes[-1].set_xlabel("Time")
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "Figure_4_5_2_28Feb_zoomed_PM.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================
# SUMMARY TABLE
# =========================
summary_cols = [c for c in df.columns if c != "datetime"]
summary = df[summary_cols].describe().T
summary["median"] = df[summary_cols].median()
summary.to_csv(output_dir / "Figure_4_5_2_summary_statistics.csv")

# =========================
# PEAK EVENTS TABLE
# =========================
peak_records = []

for variable in ["PM1_Kitchen", "PM2_5_Kitchen", "PM10_Kitchen", "CO_Kitchen", "VOC_Kitchen", "CO2_Kitchen"]:
    if variable in df.columns and df[variable].notna().any():
        idx = df[variable].idxmax()
        peak_records.append({
            "variable": variable,
            "peak_value": df.loc[idx, variable],
            "peak_time": df.loc[idx, "datetime"]
        })

peaks_df = pd.DataFrame(peak_records)
peaks_df.to_csv(output_dir / "Figure_4_5_2_peak_events.csv", index=False)

print("Done. Outputs saved to:")
print(output_dir)
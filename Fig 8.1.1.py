# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 21:39:16 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# --------------------------------------------------
# File paths
# --------------------------------------------------
outside_bathroom_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 8.x/CPC DAY 4 OUTSIDE BATH_EXCEL.csv"
master_bedroom_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 8.x/cpc012_Master Bedroom_Day4.csv"

# --------------------------------------------------
# Read files
# --------------------------------------------------
outside_bathroom = pd.read_csv(outside_bathroom_file, encoding="latin1", engine="python")
master_bedroom = pd.read_csv(master_bedroom_file, encoding="latin1", engine="python")

# Clean column names
outside_bathroom.columns = outside_bathroom.columns.str.strip()
master_bedroom.columns = master_bedroom.columns.str.strip()

print("Outside bathroom columns:", outside_bathroom.columns)
print("Master bedroom columns:", master_bedroom.columns)

# Rename concentration columns
outside_bathroom = outside_bathroom.rename(columns={"Concentration (#/cm³)": "Outside_Bathroom"})
master_bedroom = master_bedroom.rename(columns={"Concentration (#/cm³)": "Master_Bedroom"})

# --------------------------------------------------
# Parse time
# --------------------------------------------------
outside_bathroom["Time"] = pd.to_datetime(outside_bathroom["Time"], errors="coerce")
master_bedroom["Time"] = pd.to_datetime(master_bedroom["Time"], errors="coerce")

# Drop invalid rows
outside_bathroom = outside_bathroom.dropna(subset=["Time", "Outside_Bathroom"]).copy()
master_bedroom = master_bedroom.dropna(subset=["Time", "Master_Bedroom"]).copy()

# Ensure numeric concentration
outside_bathroom["Outside_Bathroom"] = pd.to_numeric(outside_bathroom["Outside_Bathroom"], errors="coerce")
master_bedroom["Master_Bedroom"] = pd.to_numeric(master_bedroom["Master_Bedroom"], errors="coerce")

outside_bathroom = outside_bathroom.dropna(subset=["Outside_Bathroom"]).copy()
master_bedroom = master_bedroom.dropna(subset=["Master_Bedroom"]).copy()

# Sort by time
outside_bathroom = outside_bathroom.sort_values("Time").reset_index(drop=True)
master_bedroom = master_bedroom.sort_values("Time").reset_index(drop=True)

# --------------------------------------------------
# Create 1-minute time base from master bedroom CPC
# --------------------------------------------------
master_bedroom = master_bedroom[["Time", "Master_Bedroom"]].copy()

# Resample outside bathroom CPC to 1-minute resolution
outside_bathroom_resampled = (
    outside_bathroom.set_index("Time")[["Outside_Bathroom"]]
    .resample("1min")
    .interpolate(method="time")
    .reset_index()
)

# Also keep original 5-minute outside bathroom data for step plotting
outside_bathroom_original = outside_bathroom[["Time", "Outside_Bathroom"]].copy()

# Merge resampled outside bathroom onto master bedroom time base
df = pd.merge(
    master_bedroom,
    outside_bathroom_resampled,
    on="Time",
    how="left"
)

# Fill any remaining missing values
df["Outside_Bathroom"] = df["Outside_Bathroom"].interpolate(method="linear")

# --------------------------------------------------
# Calculate cumulative exposure using master bedroom CPC only
# --------------------------------------------------
df["dt"] = df["Time"].diff().dt.total_seconds()
df.loc[df.index[0], "dt"] = 0

df["Cumulative_Exposure"] = np.cumsum(df["Master_Bedroom"] * df["dt"])

# Relative time in minutes
df["Time_min"] = (df["Time"] - df["Time"].iloc[0]).dt.total_seconds() / 60
outside_bathroom_original["Time_min"] = (
    outside_bathroom_original["Time"] - df["Time"].iloc[0]
).dt.total_seconds() / 60

# Peak master bedroom concentration
peak_idx = df["Master_Bedroom"].idxmax()
peak_val = df.loc[peak_idx, "Master_Bedroom"]
peak_time = df.loc[peak_idx, "Time_min"]

print(f"Peak master bedroom concentration: {peak_val:,.0f} particles cm^-3")
print(f"Peak time: {peak_time:.1f} min")
print(f"Final cumulative exposure: {df['Cumulative_Exposure'].iloc[-1]:.3e} particles s cm^-3")

# --------------------------------------------------
# Plot
# --------------------------------------------------
fig, ax1 = plt.subplots(figsize=(10, 6))

# Master bedroom CPC (1-minute)
ax1.plot(
    df["Time_min"],
    df["Master_Bedroom"],
    linewidth=1.6,
    label="Master bedroom CPC"
)

# Outside bathroom CPC shown as original 5-minute step data
ax1.step(
    outside_bathroom_original["Time_min"],
    outside_bathroom_original["Outside_Bathroom"],
    where="mid",
    linewidth=2.2,
    label="Outside bathroom CPC"
)

# Peak marker and annotation
ax1.scatter(peak_time, peak_val, s=45, color="black", zorder=5)
ax1.annotate(
    f"Peak = {peak_val:,.0f}",
    xy=(peak_time, peak_val),
    xytext=(peak_time + 15, peak_val * 0.8),
    arrowprops=dict(arrowstyle="->", lw=1),
    fontsize=10
)

ax1.set_xlabel("Time (min)")
ax1.set_ylabel("Particle concentration (particles cm$^{-3}$)")
ax1.set_xlim(left=0)

# Cumulative exposure
ax2 = ax1.twinx()
ax2.plot(
    df["Time_min"],
    df["Cumulative_Exposure"],
    linestyle="--",
    linewidth=1.6,
    label="Cumulative exposure (master bedroom)"
)
ax2.set_ylabel("Cumulative exposure (particles s cm$^{-3}$)")

# Format right axis
formatter = ScalarFormatter(useMathText=True)
formatter.set_powerlimits((0, 0))
ax2.yaxis.set_major_formatter(formatter)

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper center", frameon=True)

plt.tight_layout()
plt.savefig("Figure_8_1_1_peak_vs_cumulative_final.png", dpi=300, bbox_inches="tight")
plt.show()
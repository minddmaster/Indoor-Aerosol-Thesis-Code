# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 21:56:15 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------
# File paths
# --------------------------------------------------
cpc_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 8.x, 9.x/cpc012_Master Bedroom_Day4.csv"
drx_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 8.x, 9.x/sphereday4_drX.csv"

# --------------------------------------------------
# Read files
# --------------------------------------------------
cpc = pd.read_csv(cpc_file, encoding="latin1", engine="python")
drx = pd.read_csv(drx_file, encoding="latin1", engine="python")

# Clean column names
cpc.columns = cpc.columns.str.strip()
drx.columns = drx.columns.str.strip()

print("CPC columns:", cpc.columns.tolist())
print("DRX columns:", drx.columns.tolist())

# --------------------------------------------------
# Rename CPC columns
# --------------------------------------------------
cpc = cpc.rename(columns={"Concentration (#/cm³)": "CPC_Number"})

# --------------------------------------------------
# Parse time
# Adjust format if needed
# --------------------------------------------------
cpc["Time"] = pd.to_datetime(cpc["Time"], errors="coerce")
drx["Time"] = pd.to_datetime(drx["Time"], errors="coerce")

# --------------------------------------------------
# Choose DRX mass column manually
# --------------------------------------------------
drx_mass_col = "PM2.5 [ug/m3]"

# Convert to numeric
cpc["CPC_Number"] = pd.to_numeric(cpc["CPC_Number"], errors="coerce")
drx[drx_mass_col] = pd.to_numeric(drx[drx_mass_col], errors="coerce")

# Drop invalid rows
cpc = cpc.dropna(subset=["Time", "CPC_Number"]).copy()
drx = drx.dropna(subset=["Time", drx_mass_col]).copy()

# Sort by time
cpc = cpc.sort_values("Time").reset_index(drop=True)
drx = drx.sort_values("Time").reset_index(drop=True)

# --------------------------------------------------
# Resample both to 1-minute means
# --------------------------------------------------
cpc_1min = (
    cpc.set_index("Time")[["CPC_Number"]]
    .resample("1min")
    .mean()
    .reset_index()
)

drx_1min = (
    drx.set_index("Time")[[drx_mass_col]]
    .resample("1min")
    .mean()
    .reset_index()
)

# --------------------------------------------------
# Merge
# --------------------------------------------------
df = pd.merge(cpc_1min, drx_1min, on="Time", how="inner")
df = df.dropna(subset=["CPC_Number", drx_mass_col]).copy()

# Relative time in minutes
df["Time_min"] = (df["Time"] - df["Time"].iloc[0]).dt.total_seconds() / 60

# Peaks
cpc_peak_idx = df["CPC_Number"].idxmax()
cpc_peak_val = df.loc[cpc_peak_idx, "CPC_Number"]
cpc_peak_time = df.loc[cpc_peak_idx, "Time_min"]

drx_peak_idx = df[drx_mass_col].idxmax()
drx_peak_val = df.loc[drx_peak_idx, drx_mass_col]
drx_peak_time = df.loc[drx_peak_idx, "Time_min"]

print(f"CPC peak: {cpc_peak_val:,.0f} particles cm^-3 at {cpc_peak_time:.1f} min")
print(f"DRX peak: {drx_peak_val:,.2f} ug/m3 at {drx_peak_time:.1f} min")

# --------------------------------------------------
# Plot
# --------------------------------------------------
fig, ax1 = plt.subplots(figsize=(10, 6))

# CPC number concentration
ax1.plot(
    df["Time_min"],
    df["CPC_Number"],
    linewidth=1.6,
    label="CPC number concentration"
)
ax1.set_xlabel("Time (min)")
ax1.set_ylabel("Particle number concentration (particles cm$^{-3}$)")
ax1.set_xlim(left=0)

# CPC peak annotation
ax1.scatter(cpc_peak_time, cpc_peak_val, s=35, color="black", zorder=5)
ax1.annotate(
    f"CPC peak = {cpc_peak_val:,.0f}",
    xy=(cpc_peak_time, cpc_peak_val),
    xytext=(cpc_peak_time + 18, cpc_peak_val * 0.75),
    arrowprops=dict(arrowstyle="->", lw=1),
    fontsize=9
)

# DRX mass concentration
ax2 = ax1.twinx()
ax2.plot(
    df["Time_min"],
    df[drx_mass_col],
    linestyle="--",
    linewidth=2.2,
    label="DRX PM2.5 mass concentration"
)
ax2.set_ylabel("Particle mass concentration (µg m$^{-3}$)")

# DRX peak annotation
ax2.scatter(drx_peak_time, drx_peak_val, s=35, color="black", zorder=5)
ax2.annotate(
    f"DRX peak = {drx_peak_val:,.1f}",
    xy=(drx_peak_time, drx_peak_val),
    xytext=(drx_peak_time + 12, drx_peak_val * 0.85),
    arrowprops=dict(arrowstyle="->", lw=1),
    fontsize=9
)

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", frameon=True)

plt.tight_layout()
plt.savefig("Figure_8_2_1_number_vs_mass.png", dpi=300, bbox_inches="tight")
plt.show()
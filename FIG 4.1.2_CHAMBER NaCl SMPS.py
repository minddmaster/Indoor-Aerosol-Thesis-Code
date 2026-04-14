# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 20:38:14 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =========================
# File path
# =========================
file_path = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/fig 4.1.2- Chamber Nacl SMPS/260423_0.2%nacl_smpswithAM241_DRYER.raw")

# =========================
# Read raw file
# =========================
with open(file_path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

# Split header and data
header = lines[0].strip().split("\t")
data_lines = [line.strip().split("\t") for line in lines[1:] if line.strip()]

# Create dataframe
df = pd.DataFrame(data_lines, columns=header)

# Rename first column to datetime
df = df.rename(columns={df.columns[0]: "datetime"})

# Parse datetime
df["datetime"] = pd.to_datetime(df["datetime"], format="%d/%m/%Y %H:%M:%S", errors="coerce")

# Convert remaining columns to numeric where possible
for col in df.columns[1:]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# =========================
# Detect particle diameter columns
# =========================
diameter_cols = []
for col in df.columns[1:]:
    try:
        float(col)
        diameter_cols.append(col)
    except ValueError:
        break

diameters = np.array([float(c) for c in diameter_cols])

print("Number of scans:", len(df))
print("Number of diameter bins:", len(diameter_cols))
print("Diameter range (nm):", diameters.min(), "to", diameters.max())

# =========================
# Distribution matrix
# =========================
dist = df[diameter_cols].copy()

# Total concentration
df["total_conc"] = dist.sum(axis=1)

# Peak diameter
peak_idx = np.nanargmax(dist.values, axis=1)
df["peak_diameter_nm"] = diameters[peak_idx]

# =========================
# Calculate GMD and GSD
# =========================
log_dp = np.log(diameters)

def calc_gmd_gsd(row_values):
    values = np.array(row_values, dtype=float)
    values = np.nan_to_num(values, nan=0.0)

    if values.sum() <= 0:
        return np.nan, np.nan

    weights = values / values.sum()
    mean_log = np.sum(weights * log_dp)
    var_log = np.sum(weights * (log_dp - mean_log) ** 2)

    gmd = np.exp(mean_log)
    gsd = np.exp(np.sqrt(var_log))
    return gmd, gsd

gmd_list = []
gsd_list = []

for _, row in dist.iterrows():
    gmd, gsd = calc_gmd_gsd(row.values)
    gmd_list.append(gmd)
    gsd_list.append(gsd)

df["GMD_nm"] = gmd_list
df["GSD"] = gsd_list

# =========================
# Choose stable period
# Adjust if needed
# =========================
stable_df = df.iloc[1:].copy()
stable_dist = stable_df[diameter_cols]

mean_dist = stable_dist.mean(axis=0)
std_dist = stable_dist.std(axis=0)

# =========================
# Figure 4.1.2 Mean size distribution
# =========================
plt.figure(figsize=(7, 5))
plt.plot(diameters, mean_dist.values, marker="o")
plt.xscale("log")
plt.xlabel("Particle diameter (nm)")
plt.ylabel("Number concentration")
plt.title("Mean SMPS Size Distribution\n26 April 2023, 0.2% NaCl, Am-241, dryer")
plt.grid(True, which="both", alpha=0.3)
plt.tight_layout()
plt.savefig(file_path.parent / "Figure_4_1_2_SMPS_size_distribution.png", dpi=300, bbox_inches="tight")
plt.show()

# =========================
# Figure 4.1.3 GMD vs time
# =========================
plt.figure(figsize=(8, 5))
plt.plot(df["datetime"], df["GMD_nm"], marker="o")
plt.xlabel("Time")
plt.ylabel("Geometric mean diameter (nm)")
plt.title("GMD Over Time")
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(file_path.parent / "Figure_4_1_3_GMD_vs_time.png", dpi=300, bbox_inches="tight")
plt.show()

# =========================
# Optional: total concentration vs time
# =========================
plt.figure(figsize=(8, 5))
plt.plot(df["datetime"], df["total_conc"], marker="o")
plt.xlabel("Time")
plt.ylabel("Total number concentration")
plt.title("Total Concentration Over Time")
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(file_path.parent / "Figure_4_1_3_total_concentration_vs_time.png", dpi=300, bbox_inches="tight")
plt.show()

# =========================
# Summary statistics
# =========================
print("\nSummary statistics:")
print(df[["GMD_nm", "GSD", "total_conc", "peak_diameter_nm"]].describe())

print("\nFiles saved to:")
print(file_path.parent)
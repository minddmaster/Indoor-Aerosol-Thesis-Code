# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 05:36:57 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 12:46:21 2026

Updated for Figure 6.3:
Comparison of baseline-corrected PM2.5 concentrations across outdoor,
ground floor (indoor), and first floor (indoor) locations in the BDFI office.

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# FILE PATHS
# =====================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_UPDATED.xlsx"

output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Figure_6_5_MultiFloor_PM25_BaselineCorrected.png"
# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_excel(file_path)
df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
df = df.dropna(subset=["Time"])

# =====================================================
# APPLY BASELINE CORRECTION
# =====================================================

baseline_ff = 11.0
baseline_gf = 14.0
baseline_out = 11.0

df["First Floor_corr"] = df["First Floor"] - baseline_ff
df["Ground Floor_corr"] = df["Ground Floor"] - baseline_gf
df["Outdoor_corr"] = df["Outdoor"] - baseline_out

# Keep only positive corrected values for summary comparison
df_plot = df[
    (df["Outdoor_corr"] > 0) &
    (df["Ground Floor_corr"] > 0) &
    (df["First Floor_corr"] > 0)
].copy()

# =====================================================
# CALCULATE MEAN AND STD
# =====================================================

means = [
    df_plot["Outdoor_corr"].mean(),
    df_plot["Ground Floor_corr"].mean(),
    df_plot["First Floor_corr"].mean()
]

stds = [
    df_plot["Outdoor_corr"].std(),
    df_plot["Ground Floor_corr"].std(),
    df_plot["First Floor_corr"].std()
]

labels = ["Outdoor", "Ground floor (indoor)", "First floor (indoor)"]

# =====================================================
# COLOUR SCHEME
# =====================================================

colors = ["#4C72B0", "#DD8452", "#55A868"]
# Blue = Outdoor, Orange = Ground floor, Green = First floor

# =====================================================
# PLOT
# =====================================================

plt.figure(figsize=(9, 6))

bars = plt.bar(
    labels,
    means,
    yerr=stds,
    capsize=8,
    color=colors,
    edgecolor="black",
    linewidth=1.2
)

# Labels and title
plt.ylabel("PM$_{2.5}$ concentration (µg m$^{-3}$)", fontsize=12, fontweight="bold")
plt.title(
    "Comparison of baseline-corrected PM$_{2.5}$ concentrations across outdoor, ground floor (indoor), and first floor (indoor) locations in the BDFI office",
    fontsize=13
)
   

# Add mean values above bars
for i, (mean, std) in enumerate(zip(means, stds)):
    plt.text(i, mean + std + 0.1, f"{mean:.2f}", ha="center", fontsize=10)

# Grid
plt.grid(axis="y", linestyle="--", alpha=0.5)

# Tight layout
plt.tight_layout()

# Save figure
plt.savefig(output_path, dpi=600, bbox_inches="tight")

# Show plot
plt.show()

# =====================================================
# PRINT VALUES FOR THESIS
# =====================================================

print("\n=== FINAL VALUES FOR FIGURE 6.3 ===")
for lab, mean_val, std_val in zip(labels, means, stds):
    print(f"{lab}: mean = {mean_val:.2f}, SD = {std_val:.2f}")

print("\nFigure saved to:")
print(output_path)
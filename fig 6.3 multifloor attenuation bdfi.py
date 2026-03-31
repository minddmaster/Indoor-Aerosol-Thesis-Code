# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 12:46:21 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# =====================================================
# FILE PATHS
# =====================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_BiasCorrected.xlsx"

output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Figure_7_3_1_MultiFloor_PM25_BiasCorrected_COLOURED.png"

# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_excel(file_path)
df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
df = df.dropna(subset=["Time"])

# =====================================================
# CALCULATE MEAN AND STD
# =====================================================

means = [
    df["Outdoor"].mean(),
    df["Ground Floor"].mean(),
    df["First Floor"].mean()
]

stds = [
    df["Outdoor"].std(),
    df["Ground Floor"].std(),
    df["First Floor"].std()
]

labels = ["Outdoor", "Ground Floor", "First Floor"]

# =====================================================
# COLOUR SCHEME (BEST FOR THESIS)
# =====================================================

colors = ["#4C72B0", "#DD8452", "#55A868"]  
# Blue (Outdoor), Orange (Ground), Green (First Floor)

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
    edgecolor='black',
    linewidth=1.2
)

# Labels & title
plt.ylabel("Mean PM$_{2.5}$ Concentration (µg m$^{-3}$)", fontsize=12)
plt.title("Mean PM$_{2.5}$ concentrations across BDFI monitoring locations", fontsize=13)

for i, (mean, std) in enumerate(zip(means, stds)):
    plt.text(i, mean + std + 0.1, f"{mean:.2f}", ha='center', fontsize=10)

# Grid (subtle, professional)
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Tight layout
plt.tight_layout()

# Save figure
plt.savefig(output_path, dpi=600)

# Show plot
plt.show()

# =====================================================
# PRINT VALUES FOR THESIS
# =====================================================

print("\n=== FINAL VALUES FOR FIGURE ===")
for lab, mean_val, std_val in zip(labels, means, stds):
    print(f"{lab}: mean = {mean_val:.2f}, SD = {std_val:.2f}")

print("\nFigure saved to:")
print(output_path)
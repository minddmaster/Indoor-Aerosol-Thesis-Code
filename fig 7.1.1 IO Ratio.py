# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 11:16:04 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# =====================================================
# 1. LOAD MERGED DATA
# =====================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data.xlsx"

df = pd.read_excel(file_path)

# convert time
df["Time"] = pd.to_datetime(df["Time"])

# =====================================================
# 2. CALCULATE I/O RATIOS
# =====================================================

df["FF_IO"] = df["First Floor"] / df["Outdoor"]
df["GF_IO"] = df["Ground Floor"] / df["Outdoor"]

# remove extreme values
df = df[(df["FF_IO"] > 0) & (df["GF_IO"] > 0)]
df = df[(df["FF_IO"] < 5) & (df["GF_IO"] < 5)]

# =====================================================
# 3. CREATE BOX PLOT
# =====================================================

fig, ax = plt.subplots(figsize=(8,6))

data = [df["FF_IO"], df["GF_IO"]]

ax.boxplot(
    data,
    patch_artist=True,
    widths=0.5,
    showfliers=False
)

colors = ["steelblue", "darkorange"]

for patch, color in zip(ax.artists, colors):
    patch.set_facecolor(color)

ax.set_xticklabels(["First Floor", "Ground Floor"], fontsize=12)

ax.set_ylabel("Indoor / Outdoor PM2.5 Ratio", fontsize=12)
ax.set_title(
    "Distribution of Indoor–Outdoor PM2.5 Ratios in the BDFI Building",
    fontsize=13
)

ax.axhline(1, linestyle="--", linewidth=1.5)

ax.grid(True, alpha=0.3)

plt.tight_layout()

# =====================================================
# 4. SAVE FIGURE
# =====================================================

output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Figure_7_2_1_IO_Boxplot.png"

plt.savefig(output_path, dpi=600)

plt.show()

print("Figure saved to:")
print(output_path)
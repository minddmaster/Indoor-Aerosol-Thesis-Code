# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 05:19:01 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Figure: Outdoor vs Ground Floor vs First Floor PM2.5 (baseline-corrected)
@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# 1. LOAD DATA
# =====================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_UPDATED.xlsx"

df = pd.read_excel(file_path)

df["Time"] = pd.to_datetime(df["Time"])

# =====================================================
# 2. BASELINE CORRECTION
# =====================================================

baseline_ff = 11.0
baseline_gf = 14.0
baseline_out = 11.0

df["FF_corr"] = df["First Floor"] - baseline_ff
df["GF_corr"] = df["Ground Floor"] - baseline_gf
df["OUT_corr"] = df["Outdoor"] - baseline_out

# Remove negative values after correction
df = df[(df["FF_corr"] > 0) & (df["GF_corr"] > 0) & (df["OUT_corr"] > 0)]

# =====================================================
# 3. CREATE BOXPLOT
# =====================================================

fig, ax = plt.subplots(figsize=(8,6))

data = [
    df["OUT_corr"],
    df["GF_corr"],
    df["FF_corr"]
]

box = ax.boxplot(
    data,
    patch_artist=True,
    widths=0.5,
    showfliers=False
)

# Colors
colors = ["green", "darkorange", "steelblue"]

for patch, color in zip(box["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)

# Median styling
for median in box["medians"]:
    median.set_color("black")
    median.set_linewidth(1.5)

# Labels
ax.set_xticklabels(
    ["Outdoor", "Ground floor (indoor)", "First floor (indoor)"],
    fontsize=11
)

ax.set_ylabel("PM$_{2.5}$ concentration (µg m$^{-3}$)", fontsize=12, fontweight="bold")

ax.set_title(
    "Comparison of baseline-corrected PM$_{2.5}$ concentrations across outdoor and indoor locations",
    fontsize=13
)

ax.grid(True, linestyle="--", alpha=0.3)

plt.tight_layout()

# =====================================================
# 4. SAVE
# =====================================================

output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Figure_6_X_IndoorOutdoor_Boxplot.png"

plt.savefig(output_path, dpi=600, bbox_inches="tight")

plt.show()

print("Figure saved to:")
print(output_path)

# =====================================================
# 5. SUMMARY STATS (VERY USEFUL FOR THESIS TEXT)
# =====================================================

print("\nMean values (µg/m³):")
print("Outdoor:", df["OUT_corr"].mean())
print("Ground floor:", df["GF_corr"].mean())
print("First floor:", df["FF_corr"].mean())
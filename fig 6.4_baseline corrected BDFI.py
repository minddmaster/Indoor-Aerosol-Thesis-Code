# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 05:13:53 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 11:16:04 2026

Updated for baseline-corrected I/O ratios in Figure 6.3
@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# 1. LOAD MERGED DATA
# =====================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_UPDATED.xlsx"

df = pd.read_excel(file_path)

# Convert time
df["Time"] = pd.to_datetime(df["Time"])

# =====================================================
# 2. APPLY BASELINE CORRECTION
# =====================================================

baseline_ff = 11.0
baseline_gf = 14.0
baseline_out = 11.0

df["First Floor_corrected"] = df["First Floor"] - baseline_ff
df["Ground Floor_corrected"] = df["Ground Floor"] - baseline_gf
df["Outdoor_corrected"] = df["Outdoor"] - baseline_out

# =====================================================
# 3. CALCULATE I/O RATIOS
# =====================================================

# Avoid division by zero or negative outdoor values
df = df[df["Outdoor_corrected"] > 0].copy()

df["FF_IO"] = df["First Floor_corrected"] / df["Outdoor_corrected"]
df["GF_IO"] = df["Ground Floor_corrected"] / df["Outdoor_corrected"]

# Remove negative and extreme values
df = df[(df["FF_IO"] > 0) & (df["GF_IO"] > 0)]
df = df[(df["FF_IO"] < 5) & (df["GF_IO"] < 5)]

# =====================================================
# 4. CREATE BOX PLOT
# =====================================================

fig, ax = plt.subplots(figsize=(8, 6))

data = [df["FF_IO"].dropna(), df["GF_IO"].dropna()]

box = ax.boxplot(
    data,
    patch_artist=True,
    widths=0.5,
    showfliers=False
)

colors = ["steelblue", "darkorange"]

for patch, color in zip(box["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)

for median in box["medians"]:
    median.set_color("black")
    median.set_linewidth(1.5)

ax.set_xticklabels(["First floor", "Ground floor"], fontsize=12)
ax.set_ylabel("Indoor / Outdoor PM$_{2.5}$ ratio", fontsize=12, fontweight="bold")
ax.set_title(
    "Distribution of baseline-corrected indoor–outdoor PM$_{2.5}$ ratios in the BDFI office",
    fontsize=13
)

ax.axhline(1, linestyle="--", linewidth=1.5, color="grey")
ax.grid(True, linestyle="--", alpha=0.3)

plt.tight_layout()

# =====================================================
# 5. SAVE FIGURE
# =====================================================

output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Figure_6_3_IO_Boxplot_corrected.png"

plt.savefig(output_path, dpi=600, bbox_inches="tight")
plt.show()

print("Figure saved to:")
print(output_path)

# Optional: print medians for reporting
print("\nMedian FF/O ratio:", df["FF_IO"].median())
print("Median GF/O ratio:", df["GF_IO"].median())
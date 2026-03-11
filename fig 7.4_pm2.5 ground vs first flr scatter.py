# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 12:09:22 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ======================================================
# 1. LOAD DATA
# ======================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_co2/Merged_BDFI_CO2_PM25.xlsx"

df = pd.read_excel(file_path)

# ======================================================
# 2. CLEAN DATA
# ======================================================

df = df.dropna(subset=["Ground Floor PM2.5", "First Floor PM2.5"])

df = df[(df["Ground Floor PM2.5"] >= 0)]
df = df[(df["First Floor PM2.5"] >= 0)]

x = df["Ground Floor PM2.5"]
y = df["First Floor PM2.5"]

# ======================================================
# 3. CREATE SCATTER PLOT
# ======================================================

plt.figure(figsize=(8,6))

plt.scatter(
    x,
    y,
    alpha=0.35,
    s=18,
    color="steelblue"
)

# ======================================================
# 4. ADD 1:1 LINE
# ======================================================

max_val = max(x.max(), y.max())

plt.plot(
    [0, max_val],
    [0, max_val],
    linestyle="--",
    color="red",
    linewidth=2,
    label="1:1 line"
)

# ======================================================
# 5. LABELS
# ======================================================

plt.xlabel("Ground floor PM₂.₅ concentration (μg m$^{-3}$)")
plt.ylabel("First floor PM₂.₅ concentration (μg m$^{-3}$)")

plt.title(
    "Figure 7.5 – Comparison of ground floor and first floor PM₂.₅ concentrations"
)

plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()

# ======================================================
# 6. SAVE FIGURE
# ======================================================

output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_co2/Figure_7_5_PM25_Floor_Comparison.png"

plt.savefig(output_path, dpi=600)

plt.show()

print("Figure saved to:")
print(output_path)
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 12:21:30 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

# ======================================================
# LOAD DATA
# ======================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_co2/Merged_BDFI_CO2_PM25.xlsx"

df = pd.read_excel(file_path)

# ======================================================
# CLEAN DATA
# ======================================================

df = df.dropna(subset=["Outdoor PM2.5","Ground Floor PM2.5"])

df = df[(df["Outdoor PM2.5"] >= 0)]
df = df[(df["Ground Floor PM2.5"] >= 0)]

x = df["Outdoor PM2.5"]
y = df["Ground Floor PM2.5"]

# ======================================================
# REGRESSION
# ======================================================

slope, intercept, r_value, p_value, std_err = linregress(x, y)

Finf = slope
r2 = r_value**2

# ======================================================
# SCATTER
# ======================================================

plt.figure(figsize=(8,6))

plt.scatter(
    x,
    y,
    alpha=0.35,
    s=18,
    color="steelblue"
)

# regression line
x_line = np.linspace(x.min(), x.max(), 100)
y_line = slope * x_line + intercept

plt.plot(
    x_line,
    y_line,
    color="red",
    linewidth=2
)

# ======================================================
# LABELS
# ======================================================

plt.xlabel("Outdoor PM₂.₅ concentration (μg m$^{-3}$)")
plt.ylabel("Ground floor PM₂.₅ concentration (μg m$^{-3}$)")

plt.title(
    "Figure 7.6 – Outdoor vs ground floor PM₂.₅ concentrations"
)

plt.grid(alpha=0.3)

# ======================================================
# DISPLAY RESULTS
# ======================================================

text = f"F_inf ≈ {Finf:.2f}\n$R^2$ = {r2:.2f}"

plt.text(
    0.05,
    0.95,
    text,
    transform=plt.gca().transAxes,
    fontsize=11,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
)

plt.tight_layout()

# ======================================================
# SAVE
# ======================================================

output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_co2/Figure_7_6_Outdoor_vs_GroundFloor_PM25.png"

plt.savefig(output_path, dpi=600)

plt.show()

print("Estimated infiltration factor:", Finf)
print("R²:", r2)
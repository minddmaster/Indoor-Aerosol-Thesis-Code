# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 11:59:34 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

# ======================================================
# 1. LOAD MERGED DATASET
# ======================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_co2/Merged_BDFI_CO2_PM25.xlsx"

df = pd.read_excel(file_path)

# ======================================================
# 2. CLEAN DATA
# ======================================================

df = df.dropna(subset=["Ground Floor CO2", "Ground Floor PM2.5"])

# Remove impossible values
df = df[(df["Ground Floor CO2"] > 300) & (df["Ground Floor CO2"] < 2000)]
df = df[(df["Ground Floor PM2.5"] >= 0)]

# ======================================================
# 3. REGRESSION ANALYSIS
# ======================================================

x = df["Ground Floor CO2"]
y = df["Ground Floor PM2.5"]

slope, intercept, r_value, p_value, std_err = linregress(x, y)

r2 = r_value**2

# ======================================================
# 4. CREATE SCATTER PLOT
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
# 5. LABELS
# ======================================================

plt.xlabel("Ground floor CO₂ concentration (ppm)", fontsize=12)
plt.ylabel("Ground floor PM₂.₅ concentration (μg m$^{-3}$)", fontsize=12)

plt.title(
    "Figure 7.4.1 – Relationship between ground floor CO₂ and PM₂.₅",
    fontsize=13
)

plt.grid(alpha=0.3)

# ======================================================
# 6. DISPLAY REGRESSION EQUATION + R2
# ======================================================

equation_text = f"PM₂.₅ = {slope:.3f} × CO₂ + {intercept:.2f}\n$R^2$ = {r2:.3f}"

plt.text(
    0.05,
    0.95,
    equation_text,
    transform=plt.gca().transAxes,
    fontsize=11,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
)

plt.tight_layout()

# ======================================================
# 7. SAVE FIGURE
# ======================================================

output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_co2/Figure_7_4_1_CO2_vs_PM25.png"

plt.savefig(output_path, dpi=600)

plt.show()

# ======================================================
# 8. PRINT STATISTICS
# ======================================================

print("Regression results:")
print("Slope:", slope)
print("Intercept:", intercept)
print("R²:", r2)
print("p-value:", p_value)

print("\nFigure saved to:")
print(output_path)
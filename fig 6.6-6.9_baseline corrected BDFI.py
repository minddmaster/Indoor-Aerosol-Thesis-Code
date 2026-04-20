# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 05:57:15 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Updated for Chapter 6:
Figures 6.6 – 6.9 (CO2–PM relationships and inter-floor dynamics)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# =====================================================
# FILE PATHS
# =====================================================

pm_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_UPDATED.xlsx"
co2_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_CO2_Data.xlsx"

output_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Figure_6_6_to_6_9_outputs")
output_dir.mkdir(parents=True, exist_ok=True)

# =====================================================
# SETTINGS
# =====================================================

plt.rcParams["figure.figsize"] = (8, 6)
plt.rcParams["font.size"] = 11

COL_OUTDOOR = "#4C72B0"
COL_GROUND = "#DD8452"
COL_FIRST = "#55A868"
COL_LINE = "black"

# =====================================================
# LOAD DATA
# =====================================================

pm = pd.read_excel(pm_file)
pm["Time"] = pd.to_datetime(pm["Time"], errors="coerce")
pm = pm.dropna(subset=["Time"]).sort_values("Time")

co2 = pd.read_excel(co2_file)
co2["Time"] = pd.to_datetime(co2["Time"], errors="coerce")
co2 = co2.dropna(subset=["Time"]).sort_values("Time")

df = pm.merge(co2, on="Time", how="inner").sort_values("Time")

# =====================================================
# BASELINE CORRECTION
# =====================================================

df["First Floor_corr"] = df["First Floor"] - 11
df["Ground Floor_corr"] = df["Ground Floor"] - 14
df["Outdoor_corr"] = df["Outdoor"] - 11

# =====================================================
# HELPER FUNCTION
# =====================================================

def regression_plot(x, y, xlabel, ylabel, title, color, save_path):
    temp = pd.DataFrame({"x": x, "y": y}).dropna()
    temp = temp[(temp["y"] > 0)]

    X = temp["x"].values.reshape(-1, 1)
    Y = temp["y"].values

    model = LinearRegression()
    model.fit(X, Y)
    y_pred = model.predict(X)

    slope = model.coef_[0]
    intercept = model.intercept_
    r2 = r2_score(Y, y_pred)

    plt.figure()
    plt.scatter(temp["x"], temp["y"], alpha=0.35, color=color)
    order = np.argsort(temp["x"].values)
    plt.plot(temp["x"].values[order], y_pred[order], color=COL_LINE, linewidth=2)

    plt.xlabel(xlabel, fontweight="bold")
    plt.ylabel(ylabel, fontweight="bold")
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=600)
    plt.show()

    print(f"\n{title}")
    print(f"y = {slope:.4f}x + {intercept:.2f}, R² = {r2:.3f}")

    return slope, intercept, r2

# =====================================================
# FIGURE 6.6
# =====================================================

regression_plot(
    df["Ground Floor CO2"],
    df["Ground Floor_corr"],
    "Ground floor CO$_2$ (ppm)",
    "Ground floor PM$_{2.5}$ (µg m$^{-3}$)",
    "Figure 6.6 Relationship between ground-floor CO$_2$ and baseline-corrected PM$_{2.5}$",
    COL_GROUND,
    output_dir / "Figure_6_6.png"
)

# =====================================================
# FIGURE 6.7
# =====================================================

regression_plot(
    df["First Floor CO2"],
    df["First Floor_corr"],
    "First floor CO$_2$ (ppm)",
    "First floor PM$_{2.5}$ (µg m$^{-3}$)",
    "Figure 6.7 Relationship between first-floor CO$_2$ and baseline-corrected PM$_{2.5}$",
    COL_FIRST,
    output_dir / "Figure_6_7.png"
)

# =====================================================
# FIGURE 6.8
# =====================================================

temp = df[["Ground Floor_corr", "First Floor_corr"]].dropna()
temp = temp[(temp > 0).all(axis=1)]

plt.figure()
plt.scatter(temp["Ground Floor_corr"], temp["First Floor_corr"], alpha=0.35, color=COL_FIRST)

mx = max(temp.max())
plt.plot([0, mx], [0, mx], linestyle="--", color=COL_LINE)

plt.xlabel("Ground floor PM$_{2.5}$ (µg m$^{-3}$)", fontweight="bold")
plt.ylabel("First floor PM$_{2.5}$ (µg m$^{-3}$)", fontweight="bold")
plt.title("Figure 6.8 Comparison of ground-floor and first-floor baseline-corrected PM$_{2.5}$")
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir / "Figure_6_8.png", dpi=600)
plt.show()

# =====================================================
# FIGURE 6.9
# =====================================================

regression_plot(
    df["Outdoor_corr"],
    df["Ground Floor_corr"],
    "Outdoor PM$_{2.5}$ (µg m$^{-3}$)",
    "Ground floor PM$_{2.5}$ (µg m$^{-3}$)",
    "Figure 6.9 Relationship between outdoor and ground-floor baseline-corrected PM$_{2.5}$",
    COL_OUTDOOR,
    output_dir / "Figure_6_9.png"
)
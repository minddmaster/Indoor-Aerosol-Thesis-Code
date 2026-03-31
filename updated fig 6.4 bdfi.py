# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 13:22:19 2026

@author: papkp
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

pm_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_BiasCorrected.xlsx"
co2_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_CO2_Data.xlsx"

output_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Figure_6_4_outputs")
output_dir.mkdir(parents=True, exist_ok=True)

# =====================================================
# SETTINGS
# =====================================================

plt.rcParams["figure.figsize"] = (8, 6)
plt.rcParams["font.size"] = 11

COL_OUTDOOR = "#4C72B0"   # blue
COL_GROUND = "#DD8452"    # orange
COL_FIRST = "#55A868"     # green
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

print("Merged rows:", len(df))
print("Date range:", df["Time"].min(), "to", df["Time"].max())
print("Columns:", df.columns.tolist())

# =====================================================
# HELPER FUNCTION
# =====================================================

def regression_plot(x, y, xlabel, ylabel, title, color, save_path):
    temp = pd.DataFrame({"x": x, "y": y}).dropna()

    X = temp["x"].values.reshape(-1, 1)
    Y = temp["y"].values

    model = LinearRegression()
    model.fit(X, Y)
    y_pred = model.predict(X)

    slope = model.coef_[0]
    intercept = model.intercept_
    r2 = r2_score(Y, y_pred)

    plt.figure()
    plt.scatter(temp["x"], temp["y"], alpha=0.35, color=color, edgecolor="none")
    order = np.argsort(temp["x"].values)
    plt.plot(temp["x"].values[order], y_pred[order], color=COL_LINE, linewidth=2)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=600)
    plt.show()

    print(f"\n{title}")
    print(f"Equation: y = {slope:.4f}x + {intercept:.2f}")
    print(f"R² = {r2:.3f}")

    return slope, intercept, r2

# =====================================================
# FIGURE 6.4.1
# =====================================================

gf_slope, gf_intercept, gf_r2 = regression_plot(
    x=df["Ground Floor CO2"],
    y=df["Ground Floor"],
    xlabel="Ground Floor CO$_2$ (ppm)",
    ylabel="Ground Floor PM$_{2.5}$ (µg m$^{-3}$)",
    title="Figure 6.4.1 Relationship between ground-floor CO$_2$ and PM$_{2.5}$",
    color=COL_GROUND,
    save_path=output_dir / "Figure_6_4_1_GroundFloor_CO2_vs_PM25.png"
)

# =====================================================
# FIGURE 6.4.2
# =====================================================

ff_slope, ff_intercept, ff_r2 = regression_plot(
    x=df["First Floor CO2"],
    y=df["First Floor"],
    xlabel="First Floor CO$_2$ (ppm)",
    ylabel="First Floor PM$_{2.5}$ (µg m$^{-3}$)",
    title="Figure 6.4.2 Relationship between first-floor CO$_2$ and PM$_{2.5}$",
    color=COL_FIRST,
    save_path=output_dir / "Figure_6_4_2_FirstFloor_CO2_vs_PM25.png"
)

# =====================================================
# FIGURE 6.4.3
# =====================================================

temp_floor = df[["Ground Floor", "First Floor"]].dropna()

plt.figure()
plt.scatter(temp_floor["Ground Floor"], temp_floor["First Floor"],
            alpha=0.35, color=COL_FIRST, edgecolor="none")

mx = max(temp_floor["Ground Floor"].max(), temp_floor["First Floor"].max())
plt.plot([0, mx], [0, mx], linestyle="--", color=COL_LINE, linewidth=1.5)

plt.xlabel("Ground Floor PM$_{2.5}$ (µg m$^{-3}$)")
plt.ylabel("First Floor PM$_{2.5}$ (µg m$^{-3}$)")
plt.title("Figure 6.4.3 Comparison of ground-floor and first-floor PM$_{2.5}$ concentrations")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir / "Figure_6_4_3_Ground_vs_First_PM25.png", dpi=600)
plt.show()

floor_r = temp_floor["Ground Floor"].corr(temp_floor["First Floor"])
floor_r2 = floor_r**2 if pd.notna(floor_r) else np.nan

print("\nFigure 6.4.3 Comparison of ground-floor and first-floor PM2.5 concentrations")
print(f"Correlation coefficient r = {floor_r:.3f}")
print(f"R² = {floor_r2:.3f}")

# =====================================================
# FIGURE 6.4.4
# =====================================================

out_slope, out_intercept, out_r2 = regression_plot(
    x=df["Outdoor"],
    y=df["Ground Floor"],
    xlabel="Outdoor PM$_{2.5}$ (µg m$^{-3}$)",
    ylabel="Ground Floor PM$_{2.5}$ (µg m$^{-3}$)",
    title="Figure 6.4.4 Relationship between outdoor and ground-floor PM$_{2.5}$ concentrations",
    color=COL_OUTDOOR,
    save_path=output_dir / "Figure_6_4_4_Outdoor_vs_Ground_PM25.png"
)

# =====================================================
# SUMMARY TABLE
# =====================================================

summary = pd.DataFrame({
    "Analysis": [
        "Ground Floor CO2 vs PM2.5",
        "First Floor CO2 vs PM2.5",
        "Ground Floor vs First Floor PM2.5",
        "Outdoor vs Ground Floor PM2.5"
    ],
    "Slope / r": [
        gf_slope,
        ff_slope,
        floor_r,
        out_slope
    ],
    "Intercept": [
        gf_intercept,
        ff_intercept,
        np.nan,
        out_intercept
    ],
    "R2": [
        gf_r2,
        ff_r2,
        floor_r2,
        out_r2
    ]
}).round(3)

summary.to_excel(output_dir / "Figure_6_4_summary_metrics.xlsx", index=False)

print("\nSummary table saved to:")
print(output_dir / "Figure_6_4_summary_metrics.xlsx")
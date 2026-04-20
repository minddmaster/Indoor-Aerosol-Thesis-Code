# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 07:09:25 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
CO tracer analysis for BDFI
Purpose:
- Assess whether CO behaves as an outdoor tracer
- Compare outdoor CO with indoor CO on ground and first floor
- Quantify lagged relationships between outdoor and indoor CO

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# =====================================================
# FILE PATHS
# =====================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_CO_Data.xlsx"

output_dir = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/CO_Tracer_Analysis"
)
output_dir.mkdir(parents=True, exist_ok=True)

# =====================================================
# SETTINGS
# =====================================================

plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 11

COL_OUT = "#4C72B0"   # blue
COL_GF = "#DD8452"    # orange
COL_FF = "#55A868"    # green
COL_LINE = "black"

# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_excel(file_path)
df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
df = df.dropna(subset=["Time"]).sort_values("Time").reset_index(drop=True)

# Convert columns to numeric safely
for col in ["Outdoor CO", "Ground Floor CO", "First Floor CO"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print("Rows:", len(df))
print("Date range:", df["Time"].min(), "to", df["Time"].max())
print("Missing values:")
print(df[["Outdoor CO", "Ground Floor CO", "First Floor CO"]].isna().sum())

# =====================================================
# OPTIONAL DAILY AVERAGES FOR LONG-TERM OVERVIEW
# =====================================================

daily = (
    df.set_index("Time")[["Outdoor CO", "Ground Floor CO", "First Floor CO"]]
    .resample("D")
    .mean()
    .reset_index()
)

# =====================================================
# FIGURE 1: DAILY TIME SERIES
# =====================================================

plt.figure(figsize=(12, 6))
plt.plot(daily["Time"], daily["Outdoor CO"], label="Outdoor CO", color=COL_OUT, linewidth=1.5)
plt.plot(daily["Time"], daily["Ground Floor CO"], label="Ground floor CO", color=COL_GF, linewidth=1.5)
plt.plot(daily["Time"], daily["First Floor CO"], label="First floor CO", color=COL_FF, linewidth=1.5)

plt.xlabel("Time", fontweight="bold")
plt.ylabel("CO concentration (ppm)", fontweight="bold")
plt.title("Figure CO.1 Daily averaged outdoor and indoor CO concentrations in the BDFI office")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir / "Figure_CO_1_Daily_Timeseries.png", dpi=600, bbox_inches="tight")
plt.show()

# =====================================================
# HELPER: REGRESSION PLOT
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

    plt.figure(figsize=(8, 6))
    plt.scatter(temp["x"], temp["y"], alpha=0.35, color=color, edgecolor="none")

    order = np.argsort(temp["x"].values)
    plt.plot(temp["x"].values[order], y_pred[order], color=COL_LINE, linewidth=2)

    plt.xlabel(xlabel, fontweight="bold")
    plt.ylabel(ylabel, fontweight="bold")
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=600, bbox_inches="tight")
    plt.show()

    print(f"\n{title}")
    print(f"Equation: y = {slope:.4f}x + {intercept:.4f}")
    print(f"R² = {r2:.3f}")
    print(f"n = {len(temp)}")

    return slope, intercept, r2

# =====================================================
# FIGURE 2: OUTDOOR CO vs GROUND FLOOR CO
# =====================================================

gf_slope, gf_intercept, gf_r2 = regression_plot(
    x=df["Outdoor CO"],
    y=df["Ground Floor CO"],
    xlabel="Outdoor CO (ppm)",
    ylabel="Ground floor CO (ppm)",
    title="Figure CO.2 Relationship between outdoor and ground-floor CO concentrations",
    color=COL_GF,
    save_path=output_dir / "Figure_CO_2_Outdoor_vs_Ground_CO.png"
)

# =====================================================
# FIGURE 3: OUTDOOR CO vs FIRST FLOOR CO
# =====================================================

ff_slope, ff_intercept, ff_r2 = regression_plot(
    x=df["Outdoor CO"],
    y=df["First Floor CO"],
    xlabel="Outdoor CO (ppm)",
    ylabel="First floor CO (ppm)",
    title="Figure CO.3 Relationship between outdoor and first-floor CO concentrations",
    color=COL_FF,
    save_path=output_dir / "Figure_CO_3_Outdoor_vs_First_CO.png"
)

# =====================================================
# FIGURE 4: GROUND FLOOR vs FIRST FLOOR CO
# =====================================================

temp_floor = df[["Ground Floor CO", "First Floor CO"]].dropna()

plt.figure(figsize=(8, 6))
plt.scatter(
    temp_floor["Ground Floor CO"],
    temp_floor["First Floor CO"],
    alpha=0.35,
    color=COL_FF,
    edgecolor="none"
)

mx = max(temp_floor["Ground Floor CO"].max(), temp_floor["First Floor CO"].max())
plt.plot([0, mx], [0, mx], linestyle="--", color=COL_LINE, linewidth=1.5)

plt.xlabel("Ground floor CO (ppm)", fontweight="bold")
plt.ylabel("First floor CO (ppm)", fontweight="bold")
plt.title("Figure CO.4 Comparison of ground-floor and first-floor CO concentrations")
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir / "Figure_CO_4_Ground_vs_First_CO.png", dpi=600, bbox_inches="tight")
plt.show()

floor_r = temp_floor["Ground Floor CO"].corr(temp_floor["First Floor CO"])
floor_r2 = floor_r**2 if pd.notna(floor_r) else np.nan

print("\nFigure CO.4 Comparison of ground-floor and first-floor CO concentrations")
print(f"Correlation coefficient r = {floor_r:.3f}")
print(f"R² = {floor_r2:.3f}")
print(f"n = {len(temp_floor)}")

# =====================================================
# LAG ANALYSIS: OUTDOOR CO vs INDOOR CO
# 30-minute steps, 0 to 6 hours
# =====================================================

results = []

for lag_steps in range(0, 13):  # 0 to 6 hours in 30-min steps
    temp = df.copy()
    temp["Outdoor_CO_lag"] = temp["Outdoor CO"].shift(lag_steps)

    gf = temp[["Outdoor_CO_lag", "Ground Floor CO"]].dropna()
    ff = temp[["Outdoor_CO_lag", "First Floor CO"]].dropna()

    gf_r = gf["Outdoor_CO_lag"].corr(gf["Ground Floor CO"]) if len(gf) > 2 else np.nan
    ff_r = ff["Outdoor_CO_lag"].corr(ff["First Floor CO"]) if len(ff) > 2 else np.nan

    results.append({
        "Lag_steps": lag_steps,
        "Lag_hours": lag_steps * 0.5,
        "GF_r": gf_r,
        "GF_R2": gf_r**2 if pd.notna(gf_r) else np.nan,
        "FF_r": ff_r,
        "FF_R2": ff_r**2 if pd.notna(ff_r) else np.nan
    })

lag_df = pd.DataFrame(results)

best_gf = lag_df.loc[lag_df["GF_R2"].idxmax()]
best_ff = lag_df.loc[lag_df["FF_R2"].idxmax()]

# =====================================================
# FIGURE 5: LAGGED CO CORRELATION
# =====================================================

plt.figure(figsize=(8, 5))
plt.plot(lag_df["Lag_hours"], lag_df["GF_R2"], marker="o", label="Ground floor R²", color=COL_GF)
plt.plot(lag_df["Lag_hours"], lag_df["FF_R2"], marker="o", label="First floor R²", color=COL_FF)

plt.xlabel("Lag (hours)", fontweight="bold")
plt.ylabel("R²", fontweight="bold")
plt.title("Figure CO.5 Lagged outdoor–indoor CO correlation in the BDFI office")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir / "Figure_CO_5_Lagged_CO_Correlation.png", dpi=600, bbox_inches="tight")
plt.show()

# =====================================================
# SAVE OUTPUT TABLES
# =====================================================

summary = pd.DataFrame({
    "Analysis": [
        "Outdoor vs Ground Floor CO",
        "Outdoor vs First Floor CO",
        "Ground Floor vs First Floor CO",
        "Best Ground Floor CO lag",
        "Best First Floor CO lag"
    ],
    "Metric": [
        "R²",
        "R²",
        "R²",
        "Lag hours / R²",
        "Lag hours / R²"
    ],
    "Value": [
        gf_r2,
        ff_r2,
        floor_r2,
        f"{best_gf['Lag_hours']:.1f} h / {best_gf['GF_R2']:.3f}",
        f"{best_ff['Lag_hours']:.1f} h / {best_ff['FF_R2']:.3f}"
    ]
})

summary.to_excel(output_dir / "CO_Tracer_Summary.xlsx", index=False)
lag_df.to_excel(output_dir / "CO_Lag_Analysis.xlsx", index=False)
daily.to_excel(output_dir / "CO_Daily_Averages.xlsx", index=False)

# =====================================================
# PRINT RESULTS
# =====================================================

print("\n=== CO TRACER SUMMARY ===")
print(summary.to_string(index=False))

print("\n=== CO LAG ANALYSIS ===")
print(lag_df.to_string(index=False))

print("\nBest Ground Floor CO lag:")
print(best_gf)

print("\nBest First Floor CO lag:")
print(best_ff)

print(f"\nSaved outputs to:\n{output_dir}")
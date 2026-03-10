# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 23:12:05 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =========================================================
# Load merged BDFI dataset
# Must contain columns: Time, Outdoor, Indoor_GF, Indoor_FF
# =========================================================
file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/merged_BDFI_PM25.csv"

df = pd.read_csv(file_path)
df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
df = df.dropna(subset=["Time"]).sort_values("Time").reset_index(drop=True)

for col in ["Outdoor", "Indoor_GF", "Indoor_FF"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Outdoor", "Indoor_GF", "Indoor_FF"]).copy()
df = df[df["Outdoor"] > 0].copy()

# =========================================================
# Bonfire Night event window
# =========================================================
start = pd.Timestamp("2023-11-04 12:00:00")
end   = pd.Timestamp("2023-11-06 12:00:00")

event = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()

if event.empty:
    raise ValueError("No data found in Bonfire Night window.")

# =========================================================
# Calculate I/O ratios
# =========================================================
event["IO_GF"] = event["Indoor_GF"] / event["Outdoor"]
event["IO_FF"] = event["Indoor_FF"] / event["Outdoor"]

# =========================================================
# Peak detection
# Bonfire peak = max outdoor concentration in event window
# =========================================================
peak_idx = event["Outdoor"].idxmax()
peak_time = event.loc[peak_idx, "Time"]
peak_outdoor = event.loc[peak_idx, "Outdoor"]

# =========================================================
# Lag analysis (30-minute steps up to 3 hours)
# =========================================================
results = []

for lag_steps in range(0, 7):   # 0 to 6 = 0 to 3 hr
    temp = event.copy()
    temp["Outdoor_lag"] = temp["Outdoor"].shift(lag_steps)

    gf = temp[["Outdoor_lag", "Indoor_GF"]].dropna()
    ff = temp[["Outdoor_lag", "Indoor_FF"]].dropna()

    gf_r = gf["Outdoor_lag"].corr(gf["Indoor_GF"]) if len(gf) > 2 else np.nan
    ff_r = ff["Outdoor_lag"].corr(ff["Indoor_FF"]) if len(ff) > 2 else np.nan

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

# =========================================================
# Event summary
# =========================================================
summary = pd.DataFrame({
    "Location": ["Outdoor", "Ground Floor", "First Floor"],
    "Peak_PM25": [
        event["Outdoor"].max(),
        event["Indoor_GF"].max(),
        event["Indoor_FF"].max()
    ],
    "Mean_PM25": [
        event["Outdoor"].mean(),
        event["Indoor_GF"].mean(),
        event["Indoor_FF"].mean()
    ],
    "Peak_Time": [
        event.loc[event["Outdoor"].idxmax(), "Time"],
        event.loc[event["Indoor_GF"].idxmax(), "Time"],
        event.loc[event["Indoor_FF"].idxmax(), "Time"]
    ]
})

summary["Peak_to_Outdoor_Peak_Ratio"] = [
    1.0,
    event["Indoor_GF"].max() / event["Outdoor"].max(),
    event["Indoor_FF"].max() / event["Outdoor"].max()
]

# =========================================================
# Print outputs
# =========================================================
print("\n=== BONFIRE NIGHT EVENT SUMMARY ===")
print(f"Outdoor peak on: {peak_time}")
print(f"Outdoor peak PM2.5: {peak_outdoor:.2f} µg/m³\n")

print(summary.to_string(index=False))

print("\n=== LAG ANALYSIS ===")
print(lag_df.to_string(index=False))

print("\nBest Ground Floor lag:")
print(best_gf)

print("\nBest First Floor lag:")
print(best_ff)

# =========================================================
# Save outputs
# =========================================================
outdir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Bonfire_Night_Event")
outdir.mkdir(parents=True, exist_ok=True)

summary.to_csv(outdir / "bonfire_summary.csv", index=False)
lag_df.to_csv(outdir / "bonfire_lag_analysis.csv", index=False)
event.to_csv(outdir / "bonfire_window_data.csv", index=False)

# =========================================================
# Plot 1: Time series
# =========================================================
plt.figure(figsize=(12, 6))
plt.plot(event["Time"], event["Outdoor"], label="Outdoor PM2.5")
plt.plot(event["Time"], event["Indoor_GF"], label="Ground Floor PM2.5")
plt.plot(event["Time"], event["Indoor_FF"], label="First Floor PM2.5")
plt.axvline(pd.Timestamp("2023-11-05 18:00:00"), linestyle="--", linewidth=1)
plt.axvline(pd.Timestamp("2023-11-05 23:59:00"), linestyle="--", linewidth=1)
plt.xlabel("Time")
plt.ylabel("PM2.5 (µg/m³)")
plt.title("Bonfire Night PM2.5 Event: Outdoor and Indoor Concentrations")
plt.legend()
plt.tight_layout()
plt.savefig(outdir / "bonfire_timeseries.png", dpi=300)
plt.show()

# =========================================================
# Plot 2: Indoor/Outdoor ratios
# =========================================================
plt.figure(figsize=(12, 5))
plt.plot(event["Time"], event["IO_GF"], label="Ground Floor I/O")
plt.plot(event["Time"], event["IO_FF"], label="First Floor I/O")
plt.axhline(1.0, linestyle="--", linewidth=1)
plt.axhline(1.2, linestyle="--", linewidth=1)
plt.xlabel("Time")
plt.ylabel("Indoor / Outdoor Ratio")
plt.title("Bonfire Night PM2.5 Event: Indoor/Outdoor Ratios")
plt.legend()
plt.tight_layout()
plt.savefig(outdir / "bonfire_io_ratio.png", dpi=300)
plt.show()

# =========================================================
# Plot 3: Lag-R²
# =========================================================
plt.figure(figsize=(8, 5))
plt.plot(lag_df["Lag_hours"], lag_df["GF_R2"], marker="o", label="Ground Floor R²")
plt.plot(lag_df["Lag_hours"], lag_df["FF_R2"], marker="o", label="First Floor R²")
plt.xlabel("Lag (hours)")
plt.ylabel("R²")
plt.title("Lagged Indoor-Outdoor Correlation During Bonfire Night")
plt.legend()
plt.tight_layout()
plt.savefig(outdir / "bonfire_lag_r2.png", dpi=300)
plt.show()

print(f"\nSaved outputs to:\n{outdir}")
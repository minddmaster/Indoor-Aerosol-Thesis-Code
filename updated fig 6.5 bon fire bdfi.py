# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 21:36:47 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Updated Bonfire Night analysis using bias-corrected PM2.5 dataset
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =========================================================
# Load bias-corrected BDFI dataset
# Must contain columns: Time, Outdoor, Ground Floor, First Floor
# =========================================================
file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_BiasCorrected.xlsx"

df = pd.read_excel(file_path)
df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
df = df.dropna(subset=["Time"]).sort_values("Time").reset_index(drop=True)

for col in ["Outdoor", "Ground Floor", "First Floor"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Outdoor", "Ground Floor", "First Floor"]).copy()
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
event["IO_GF"] = event["Ground Floor"] / event["Outdoor"]
event["IO_FF"] = event["First Floor"] / event["Outdoor"]

# =========================================================
# Peak detection
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

    gf = temp[["Outdoor_lag", "Ground Floor"]].dropna()
    ff = temp[["Outdoor_lag", "First Floor"]].dropna()

    gf_r = gf["Outdoor_lag"].corr(gf["Ground Floor"]) if len(gf) > 2 else np.nan
    ff_r = ff["Outdoor_lag"].corr(ff["First Floor"]) if len(ff) > 2 else np.nan

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
        event["Ground Floor"].max(),
        event["First Floor"].max()
    ],
    "Mean_PM25": [
        event["Outdoor"].mean(),
        event["Ground Floor"].mean(),
        event["First Floor"].mean()
    ],
    "Peak_Time": [
        event.loc[event["Outdoor"].idxmax(), "Time"],
        event.loc[event["Ground Floor"].idxmax(), "Time"],
        event.loc[event["First Floor"].idxmax(), "Time"]
    ]
})

summary["Peak_to_Outdoor_Peak_Ratio"] = [
    1.0,
    event["Ground Floor"].max() / event["Outdoor"].max(),
    event["First Floor"].max() / event["Outdoor"].max()
]

# =========================================================
# Print outputs
# =========================================================
print("\n=== BONFIRE NIGHT EVENT SUMMARY (Bias-corrected PM2.5) ===")
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
outdir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Bonfire_Night_Event_BiasCorrected")
outdir.mkdir(parents=True, exist_ok=True)

summary.to_csv(outdir / "bonfire_summary_bias_corrected.csv", index=False)
lag_df.to_csv(outdir / "bonfire_lag_analysis_bias_corrected.csv", index=False)
event.to_csv(outdir / "bonfire_window_data_bias_corrected.csv", index=False)

# =========================================================
# Plot 1: Time series
# =========================================================
plt.figure(figsize=(12, 6))
plt.plot(event["Time"], event["Outdoor"], label="Outdoor PM$_{2.5}$", color="#4C72B0")
plt.plot(event["Time"], event["Ground Floor"], label="Ground Floor PM$_{2.5}$", color="#DD8452")
plt.plot(event["Time"], event["First Floor"], label="First Floor PM$_{2.5}$", color="#55A868")
plt.axvline(pd.Timestamp("2023-11-05 18:00:00"), linestyle="--", linewidth=1, color="black")
plt.axvline(pd.Timestamp("2023-11-05 23:59:00"), linestyle="--", linewidth=1, color="black")
plt.xlabel("Time")
plt.ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
plt.title("Figure 6.5.1 Outdoor/Indoor PM$_{2.5}$ concentrations during the Bonfire Night event")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(outdir / "Figure_6_5_1_bonfire_timeseries_bias_corrected.png", dpi=600)
plt.show()

# =========================================================
# Plot 2: Indoor/Outdoor ratios
# =========================================================
plt.figure(figsize=(12, 5))
plt.plot(event["Time"], event["IO_GF"], label="Ground Floor I/O", color="#DD8452")
plt.plot(event["Time"], event["IO_FF"], label="First Floor I/O", color="#55A868")
plt.axhline(1.0, linestyle="--", linewidth=1, color="black")
plt.axhline(1.2, linestyle="--", linewidth=1, color="grey")
plt.xlabel("Time")
plt.ylabel("Indoor / Outdoor Ratio")
plt.title("Figure 6.5.2 Outdoor/Indoor PM$_{2.5}$ ratios during the Bonfire Night event")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(outdir / "Figure_6_5_2_bonfire_io_ratio_bias_corrected.png", dpi=600)
plt.show()

# =========================================================
# Plot 3: Lag-R²
# =========================================================
plt.figure(figsize=(8, 5))
plt.plot(lag_df["Lag_hours"], lag_df["GF_R2"], marker="o", label="Ground Floor R²", color="#DD8452")
plt.plot(lag_df["Lag_hours"], lag_df["FF_R2"], marker="o", label="First Floor R²", color="#55A868")
plt.xlabel("Lag (hours)")
plt.ylabel("R²")
plt.title("Figure 6.5.3 Lagged indoor–outdoor correlation during Bonfire Night")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(outdir / "Figure_6_5_3_bonfire_lag_r2_bias_corrected.png", dpi=600)
plt.show()

print(f"\nSaved outputs to:\n{outdir}")
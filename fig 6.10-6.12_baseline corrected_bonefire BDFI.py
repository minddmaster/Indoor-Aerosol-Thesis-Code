# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 06:27:56 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 1 21:55:00 2026

Updated for baseline-corrected Bonfire Night analysis
Relabelled to Figures 6.10–6.12

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =====================================================
# FILE PATHS
# =====================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_UPDATED.xlsx"

outdir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Bonfire_Night_Event_BaselineCorrected")
outdir.mkdir(parents=True, exist_ok=True)

# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_excel(file_path)
df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
df = df.dropna(subset=["Time"]).sort_values("Time").reset_index(drop=True)

for col in ["Outdoor", "Ground Floor", "First Floor"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Outdoor", "Ground Floor", "First Floor"]).copy()

# =====================================================
# APPLY BASELINE CORRECTION
# =====================================================

baseline_out = 11.0
baseline_gf = 14.0
baseline_ff = 11.0

df["Outdoor_corr"] = df["Outdoor"] - baseline_out
df["Ground Floor_corr"] = df["Ground Floor"] - baseline_gf
df["First Floor_corr"] = df["First Floor"] - baseline_ff

# Keep corrected values in dataset, but require positive outdoor for ratio analysis
df_ratio = df[df["Outdoor_corr"] > 0].copy()

# =====================================================
# BONFIRE NIGHT WINDOW
# =====================================================

start = pd.Timestamp("2023-11-04 12:00:00")
end   = pd.Timestamp("2023-11-06 12:00:00")

event = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()
event_ratio = df_ratio[(df_ratio["Time"] >= start) & (df_ratio["Time"] <= end)].copy()

if event.empty:
    raise ValueError("No data found in Bonfire Night window.")

# =====================================================
# CALCULATE I/O RATIOS
# =====================================================

event_ratio["IO_GF"] = event_ratio["Ground Floor_corr"] / event_ratio["Outdoor_corr"]
event_ratio["IO_FF"] = event_ratio["First Floor_corr"] / event_ratio["Outdoor_corr"]

# Remove negative and extreme ratios for interpretability
event_ratio = event_ratio[
    (event_ratio["IO_GF"] > 0) & (event_ratio["IO_FF"] > 0) &
    (event_ratio["IO_GF"] < 5) & (event_ratio["IO_FF"] < 5)
].copy()

# =====================================================
# EVENT SUMMARY
# =====================================================

summary = pd.DataFrame({
    "Location": ["Outdoor", "Ground Floor", "First Floor"],
    "Peak_PM25": [
        event["Outdoor_corr"].max(),
        event["Ground Floor_corr"].max(),
        event["First Floor_corr"].max()
    ],
    "Mean_PM25": [
        event["Outdoor_corr"].mean(),
        event["Ground Floor_corr"].mean(),
        event["First Floor_corr"].mean()
    ],
    "Peak_Time": [
        event.loc[event["Outdoor_corr"].idxmax(), "Time"],
        event.loc[event["Ground Floor_corr"].idxmax(), "Time"],
        event.loc[event["First Floor_corr"].idxmax(), "Time"]
    ]
})

summary["Peak_to_Outdoor_Peak_Ratio"] = [
    1.0,
    event["Ground Floor_corr"].max() / event["Outdoor_corr"].max() if event["Outdoor_corr"].max() > 0 else np.nan,
    event["First Floor_corr"].max() / event["Outdoor_corr"].max() if event["Outdoor_corr"].max() > 0 else np.nan
]

# =====================================================
# LAG ANALYSIS: 30-MIN STEPS, 0-3 HOURS
# =====================================================

results = []

for lag_steps in range(0, 7):
    temp = event.copy()
    temp["Outdoor_lag"] = temp["Outdoor_corr"].shift(lag_steps)

    gf = temp[["Outdoor_lag", "Ground Floor_corr"]].dropna()
    ff = temp[["Outdoor_lag", "First Floor_corr"]].dropna()

    # Keep only positive corrected values for lag-correlation analysis
    gf = gf[(gf["Outdoor_lag"] > 0) & (gf["Ground Floor_corr"] > 0)]
    ff = ff[(ff["Outdoor_lag"] > 0) & (ff["First Floor_corr"] > 0)]

    gf_r = gf["Outdoor_lag"].corr(gf["Ground Floor_corr"]) if len(gf) > 2 else np.nan
    ff_r = ff["Outdoor_lag"].corr(ff["First Floor_corr"]) if len(ff) > 2 else np.nan

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
# SAVE TABLE OUTPUTS
# =====================================================

summary.to_excel(outdir / "Bonfire_Summary_BaselineCorrected.xlsx", index=False)
lag_df.to_excel(outdir / "Bonfire_Lag_Analysis_BaselineCorrected.xlsx", index=False)
event.to_excel(outdir / "Bonfire_Window_Data_BaselineCorrected.xlsx", index=False)

# =====================================================
# PLOT: FIGURE 6.10
# =====================================================

plt.figure(figsize=(12, 6))
plt.plot(event["Time"], event["Outdoor_corr"], label="Outdoor PM$_{2.5}$", color="#4C72B0", linewidth=1.5)
plt.plot(event["Time"], event["Ground Floor_corr"], label="Ground floor PM$_{2.5}$", color="#DD8452", linewidth=1.5)
plt.plot(event["Time"], event["First Floor_corr"], label="First floor PM$_{2.5}$", color="#55A868", linewidth=1.5)

# Main Bonfire period markers
plt.axvline(pd.Timestamp("2023-11-05 18:00:00"), linestyle="--", linewidth=1, color="black")
plt.axvline(pd.Timestamp("2023-11-05 23:59:00"), linestyle="--", linewidth=1, color="black")

plt.xlabel("Time", fontweight="bold")
plt.ylabel("PM$_{2.5}$ concentration (µg m$^{-3}$)", fontweight="bold")
plt.title("Figure 6.10 Baseline-corrected outdoor and indoor PM$_{2.5}$ concentrations during the Bonfire Night event")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(outdir / "Figure_6_10_Bonfire_Timeseries_BaselineCorrected.png", dpi=600, bbox_inches="tight")
plt.show()

# =====================================================
# PLOT: FIGURE 6.11
# =====================================================

plt.figure(figsize=(12, 5))
plt.plot(event_ratio["Time"], event_ratio["IO_GF"], label="Ground floor I/O", color="#DD8452", linewidth=1.5)
plt.plot(event_ratio["Time"], event_ratio["IO_FF"], label="First floor I/O", color="#55A868", linewidth=1.5)

plt.axhline(1.0, linestyle="--", linewidth=1, color="black")
plt.axhline(1.2, linestyle="--", linewidth=1, color="grey")

plt.xlabel("Time", fontweight="bold")
plt.ylabel("Indoor / Outdoor ratio", fontweight="bold")
plt.title("Figure 6.11 Baseline-corrected indoor–outdoor PM$_{2.5}$ ratios during the Bonfire Night event")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(outdir / "Figure_6_11_Bonfire_IO_Ratio_BaselineCorrected.png", dpi=600, bbox_inches="tight")
plt.show()

# =====================================================
# PLOT: FIGURE 6.12
# =====================================================

plt.figure(figsize=(8, 5))
plt.plot(lag_df["Lag_hours"], lag_df["GF_R2"], marker="o", label="Ground floor R$^2$", color="#DD8452")
plt.plot(lag_df["Lag_hours"], lag_df["FF_R2"], marker="o", label="First floor R$^2$", color="#55A868")

plt.xlabel("Lag (hours)", fontweight="bold")
plt.ylabel("R$^2$", fontweight="bold")
plt.title("Figure 6.12 Lagged indoor–outdoor PM$_{2.5}$ correlation during the Bonfire Night event")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(outdir / "Figure_6_12_Bonfire_Lag_Correlation_BaselineCorrected.png", dpi=600, bbox_inches="tight")
plt.show()

# =====================================================
# PRINT RESULTS
# =====================================================

print("\n=== BONFIRE NIGHT EVENT SUMMARY (Baseline-corrected PM2.5) ===")
print(summary.to_string(index=False))

print("\n=== LAG ANALYSIS ===")
print(lag_df.to_string(index=False))

print("\nBest Ground Floor lag:")
print(best_gf)

print("\nBest First Floor lag:")
print(best_ff)

print(f"\nSaved outputs to:\n{outdir}")
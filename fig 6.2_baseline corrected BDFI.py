# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 04:41:09 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt

# File path
file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_PM25_Data_UPDATED.xlsx"

# Read data
df = pd.read_excel(file_path)

# Check column names if needed
print(df.columns.tolist())

# Parse datetime
df["Time"] = pd.to_datetime(df["Time"])

# Baseline offsets from 5th percentile assessment
baseline_ff = 11.0
baseline_gf = 14.0
baseline_out = 11.0

# Apply baseline correction
df["First Floor_corrected"] = df["First Floor"] - baseline_ff
df["Ground Floor_corrected"] = df["Ground Floor"] - baseline_gf
df["Outdoor_corrected"] = df["Outdoor"] - baseline_out

# Keep negative values in the dataset for transparency,
# but clip to zero for plotting to avoid distracting negative artefacts
plot_df = df.copy()
plot_df["First Floor_corrected"] = plot_df["First Floor_corrected"].clip(lower=0)
plot_df["Ground Floor_corrected"] = plot_df["Ground Floor_corrected"].clip(lower=0)
plot_df["Outdoor_corrected"] = plot_df["Outdoor_corrected"].clip(lower=0)

# Daily averages
daily = (
    plot_df.set_index("Time")[
        ["First Floor_corrected", "Ground Floor_corrected", "Outdoor_corrected"]
    ]
    .resample("D")
    .mean()
)

# Plot
plt.figure(figsize=(12, 6))
plt.plot(
    daily.index,
    daily["First Floor_corrected"],
    label="First floor (indoor)",
    linewidth=1.5,
    alpha=0.9
)
plt.plot(
    daily.index,
    daily["Ground Floor_corrected"],
    label="Ground floor (indoor)",
    linewidth=1.5,
    alpha=0.9
)
plt.plot(
    daily.index,
    daily["Outdoor_corrected"],
    label="Outdoor",
    linewidth=1.5,
    alpha=0.9
)

plt.xlabel("Time", fontweight="bold")
plt.ylabel("PM$_{2.5}$ concentration (µg m$^{-3}$)", fontweight="bold")
plt.title("Daily averaged baseline-corrected indoor and outdoor PM$_{2.5}$ concentrations in the BDFI office (June 2023–March 2026)")
plt.ylim(bottom=0)
plt.legend(loc="upper right", frameon=True)
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()

# Save figure
output_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Figure_6_2_baseline_corrected_PM25.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.show()

print(f"Figure saved to: {output_path}")
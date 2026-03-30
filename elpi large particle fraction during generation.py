# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 21:53:09 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Charge state analysis/elpi day1.xlsx"
OUTPUT_DIR = os.path.dirname(FILE)

FORCED_DATE = "2025-02-24"

GEN_WINDOWS = [
    ("baseline", "Repeat1", "15:12:00", "15:17:00"),
    ("baseline", "Repeat2", "15:30:00", "15:35:00"),
    ("baseline", "Repeat3", "15:47:00", "15:52:00"),

    ("corona", "Repeat1", "16:11:10", "16:16:10"),
    ("corona", "Repeat2", "16:26:30", "16:31:30"),
    ("corona", "Repeat3", "16:40:40", "16:45:40"),

    ("ionizer", "Repeat1", "16:59:10", "17:04:10"),
    ("ionizer", "Repeat2", "17:11:30", "17:16:30"),
    ("ionizer", "Repeat3", "17:25:30", "17:30:30"),
]

def dt(hms):
    return pd.to_datetime(f"{FORCED_DATE} {hms}")

# Load ELPI
df = pd.read_excel(FILE, skiprows=40, header=None)

time = pd.to_datetime(df.iloc[:, 0], errors="coerce")
data = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
data = data.dropna(axis=1, how="all")

mask = time.notna()
time = time[mask]
data = data[mask]

n_stages = data.shape[1]

# Approximate ELPI stage diameters (log-spaced if exact diameters unavailable)
diameters = np.logspace(np.log10(0.03), np.log10(10), n_stages)

rows = []

for condition, repeat_name, start_hms, end_hms in GEN_WINDOWS:
    sub = data[(time >= dt(start_hms)) & (time <= dt(end_hms))]
    if len(sub) == 0:
        continue

    mean_dist = sub.mean(axis=0).to_numpy(dtype=float)
    total = np.nansum(mean_dist)

    small = np.nansum(mean_dist[diameters < 0.1])
    medium = np.nansum(mean_dist[(diameters >= 0.1) & (diameters < 0.2)])
    large150 = np.nansum(mean_dist[diameters >= 0.15])
    large200 = np.nansum(mean_dist[diameters >= 0.2])

    rows.append({
        "condition": condition,
        "repeat": repeat_name,
        "frac_lt100nm": small / total if total > 0 else np.nan,
        "frac_100_200nm": medium / total if total > 0 else np.nan,
        "frac_gt150nm": large150 / total if total > 0 else np.nan,
        "frac_gt200nm": large200 / total if total > 0 else np.nan,
        "total": total
    })

run_df = pd.DataFrame(rows)
run_path = os.path.join(OUTPUT_DIR, "Table_ELPI_generation_size_fractions_run.csv")
run_df.to_csv(run_path, index=False)

print("\nRun-level ELPI generation fractions:")
print(run_df)

summary_df = run_df.groupby("condition").agg(
    frac_lt100nm_mean=("frac_lt100nm", "mean"),
    frac_lt100nm_std=("frac_lt100nm", "std"),
    frac_100_200nm_mean=("frac_100_200nm", "mean"),
    frac_100_200nm_std=("frac_100_200nm", "std"),
    frac_gt150nm_mean=("frac_gt150nm", "mean"),
    frac_gt150nm_std=("frac_gt150nm", "std"),
    frac_gt200nm_mean=("frac_gt200nm", "mean"),
    frac_gt200nm_std=("frac_gt200nm", "std"),
    total_mean=("total", "mean"),
    total_std=("total", "std"),
).reset_index()

summary_path = os.path.join(OUTPUT_DIR, "Table_ELPI_generation_size_fractions_summary.csv")
summary_df.to_csv(summary_path, index=False)

print("\nCondition summary:")
print(summary_df)

# Plot large-particle fractions
x = np.arange(len(summary_df))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - width/2, summary_df["frac_gt150nm_mean"], width,
       yerr=summary_df["frac_gt150nm_std"], capsize=4, label="Fraction >150 nm")
ax.bar(x + width/2, summary_df["frac_gt200nm_mean"], width,
       yerr=summary_df["frac_gt200nm_std"], capsize=4, label="Fraction >200 nm")

ax.set_xticks(x)
ax.set_xticklabels(summary_df["condition"])
ax.set_ylabel("Fraction of size distribution during generation")
ax.set_title("ELPI large-particle fractions during generation")
ax.legend()
ax.grid(True, axis="y", linestyle="--", linewidth=0.5)

plt.tight_layout()
fig_path = os.path.join(OUTPUT_DIR, "Figure_ELPI_generation_large_particle_fractions.png")
plt.savefig(fig_path, dpi=300, bbox_inches="tight")
plt.show()

print("\nSaved:")
print(run_path)
print(summary_path)
print(fig_path)
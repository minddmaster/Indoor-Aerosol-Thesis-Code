# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 17:00:21 2026

@author: papkp
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================================================
# USER INPUTS
# =========================================================

file_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.4.1/21012025.xlsx"

output_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.4.1")
output_dir.mkdir(parents=True, exist_ok=True)

time_windows = {
    "R2": ("2025-01-21 16:17:00", "2025-01-21 16:19:00"),
    "R3": ("2025-01-21 16:24:00", "2025-01-21 16:26:00"),
    "R4": ("2025-01-21 16:31:00", "2025-01-21 16:33:00"),
}

stage_diameters_nm = np.array([20.8, 38.9, 70.9, 120.1, 201.5, 315.9, 482.9, 761.3, 1230.9, 1955.5, 3088.1])

# =========================================================
# HELPERS
# =========================================================

def coefficient_of_variation(values):
    values = np.asarray(values, dtype=float)
    mean = np.nanmean(values)
    std = np.nanstd(values, ddof=1)
    if mean == 0:
        return np.nan
    return (std / mean) * 100

def geometric_mean_diameter(stage_values, diameters_nm):
    stage_values = np.asarray(stage_values, dtype=float)
    diameters_nm = np.asarray(diameters_nm, dtype=float)

    mask = np.isfinite(stage_values) & (stage_values > 0)
    if mask.sum() == 0:
        return np.nan

    weights = stage_values[mask]
    dp = diameters_nm[mask]

    return np.exp(np.sum(weights * np.log(dp)) / np.sum(weights))

def subset_window(df, start_str, end_str):
    start = pd.to_datetime(start_str)
    end = pd.to_datetime(end_str)
    return df[(df["Time"] >= start) & (df["Time"] <= end)].copy()

def find_header_row(filepath, max_rows=80):
    raw = pd.read_excel(filepath, header=None)
    for i in range(min(max_rows, len(raw))):
        row_vals = [str(v).strip().lower() for v in raw.iloc[i].values if pd.notna(v)]
        joined = " ".join(row_vals)
        if "stage1" in joined and "stage11" in joined:
            return i
    return None

# =========================================================
# READ ELPI FILE
# =========================================================

header_row = find_header_row(file_path)
if header_row is None:
    raise ValueError("Could not identify the ELPI header row in 21012025.xlsx")

df = pd.read_excel(file_path, header=header_row)

time_col = df.columns[0]

stage_cols = [c for c in df.columns if str(c).strip().lower().startswith("stage")]
stage_cols = sorted(stage_cols, key=lambda x: int("".join(filter(str.isdigit, str(x))) or 0))

if len(stage_cols) < 11:
    raise ValueError(f"Expected Stage1–Stage11 columns, found: {stage_cols}")

total_col = None
for c in df.columns:
    c_low = str(c).strip().lower()
    if c_low == "unnamed: 32" or c_low == "concentration" or c_low == "total":
        total_col = c
        break

keep_cols = [time_col] + stage_cols + ([total_col] if total_col else [])
elpi = df[keep_cols].copy()
elpi = elpi.rename(columns={time_col: "Time"})

if total_col:
    elpi = elpi.rename(columns={total_col: "Total"})
else:
    elpi["Total"] = elpi[stage_cols].sum(axis=1)

# safer datetime parsing
elpi["Time"] = pd.to_datetime(elpi["Time"], errors="coerce")

for c in stage_cols + ["Total"]:
    elpi[c] = pd.to_numeric(elpi[c], errors="coerce")

elpi = elpi.dropna(subset=["Time", "Total"]).reset_index(drop=True)

print("Loaded rows:", len(elpi))
print("Stage columns:", stage_cols)
print("Time range:", elpi["Time"].min(), "to", elpi["Time"].max())

# =========================================================
# EXTRACT REPEATS
# =========================================================

repeats = {}
for run, (start_t, end_t) in time_windows.items():
    sub = subset_window(elpi, start_t, end_t)
    if len(sub) > 0:
        sub = sub.copy()
        sub["Time_since_start_s"] = (sub["Time"] - sub["Time"].iloc[0]).dt.total_seconds()
        sub["Time_since_start_min"] = sub["Time_since_start_s"] / 60.0
    repeats[run] = sub
    print(f"{run}: {len(sub)} rows")

# =========================================================
# FIGURE 5.4.1 – ALIGNED REPEATABILITY PLOT
# =========================================================

plt.figure(figsize=(9, 5))

for run, sub in repeats.items():
    if len(sub) == 0:
        continue
    plt.plot(
        sub["Time_since_start_min"],
        sub["Total"],
        linewidth=2,
        label=run
    )

plt.xlabel("Time since start of repeat (min)", fontsize=12)
plt.ylabel("Total number concentration (cm$^{-3}$)", fontsize=12)
plt.title("Figure 5.4.1. Repeatability of aerosol generation across three runs", fontsize=13)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(fontsize=10)
plt.tight_layout()
plt.savefig(output_dir / "Figure_5_4_1_repeatability_ELPI_aligned.png", dpi=300, bbox_inches="tight")
plt.show()

# =========================================================
# FIGURE 5.4.2 – MEAN SIZE DISTRIBUTION ACROSS REPEATS
# =========================================================

plt.figure(figsize=(8, 5))

peak_vals = []
total_vals = []
gmd_vals = []
run_summary = []

for run, sub in repeats.items():
    if len(sub) == 0:
        continue

    mean_dist = sub[stage_cols].mean(axis=0)

    plt.plot(
        stage_diameters_nm,
        mean_dist.values,
        marker="o",
        linewidth=2,
        label=run
    )

    peak_conc = sub["Total"].max()
    total_conc = sub["Total"].mean()
    gmd = geometric_mean_diameter(mean_dist.values, stage_diameters_nm)

    peak_vals.append(peak_conc)
    total_vals.append(total_conc)
    gmd_vals.append(gmd)

    run_summary.append([run, peak_conc, total_conc, gmd])

plt.xscale("log")
plt.xlabel("Particle diameter (nm)", fontsize=12)
plt.ylabel("Mean ELPI concentration", fontsize=12)
plt.title("Figure 5.4.2. Mean size distribution across repeats", fontsize=13)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(fontsize=10)
plt.tight_layout()
plt.savefig(output_dir / "Figure_5_4_2_mean_size_distribution_ELPI.png", dpi=300, bbox_inches="tight")
plt.show()

# =========================================================
# TABLE 5.4.1 – REPRODUCIBILITY METRICS
# =========================================================

table_541 = pd.DataFrame({
    "Parameter": [
        "Peak concentration (cm^-3)",
        "Geometric mean diameter (nm)",
        "Total number concentration (cm^-3)"
    ],
    "Mean": [
        np.mean(peak_vals) if peak_vals else np.nan,
        np.mean(gmd_vals) if gmd_vals else np.nan,
        np.mean(total_vals) if total_vals else np.nan
    ],
    "Std Dev": [
        np.std(peak_vals, ddof=1) if len(peak_vals) > 1 else np.nan,
        np.std(gmd_vals, ddof=1) if len(gmd_vals) > 1 else np.nan,
        np.std(total_vals, ddof=1) if len(total_vals) > 1 else np.nan
    ],
    "CV (%)": [
        coefficient_of_variation(peak_vals) if len(peak_vals) > 1 else np.nan,
        coefficient_of_variation(gmd_vals) if len(gmd_vals) > 1 else np.nan,
        coefficient_of_variation(total_vals) if len(total_vals) > 1 else np.nan
    ]
})

print("\nTable 5.4.1")
print(table_541)

run_summary_df = pd.DataFrame(
    run_summary,
    columns=["Run", "Peak concentration (cm^-3)", "Mean total concentration (cm^-3)", "GMD (nm)"]
)

print("\nRun summary")
print(run_summary_df)

table_541.to_csv(output_dir / "Table_5_4_1_reproducibility_metrics.csv", index=False)
table_541.to_excel(output_dir / "Table_5_4_1_reproducibility_metrics.xlsx", index=False)

run_summary_df.to_csv(output_dir / "Run_summary_R2_R3_R4.csv", index=False)
run_summary_df.to_excel(output_dir / "Run_summary_R2_R3_R4.xlsx", index=False)

print(f"\nAll outputs saved to:\n{output_dir}")
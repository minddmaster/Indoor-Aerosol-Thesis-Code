# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 18:35:12 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Size-band analysis for charge-state experiments
SPHERE House Day 1 (24-02-2025)

Quantifies whether larger-particle fractions are suppressed under charged conditions.

Outputs:
- Table_6_2_10_size_band_run_summary.csv
- Table_6_2_11_size_band_condition_summary.csv
- Figure_6_2_5_large_particle_fraction.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# FILE PATHS
# =========================================================
SMPS_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Charge state analysis/DAY1 SMPS DATA_COM32.xlsx"
OUTPUT_DIR = os.path.join(os.path.dirname(SMPS_FILE), "charge_state_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FORCED_DATE = "2025-02-24"


# =========================================================
# GENERATION WINDOWS ONLY (n = 3 per main condition)
# =========================================================
DIST_WINDOWS = [
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


# =========================================================
# HELPERS
# =========================================================
def dt(hms: str) -> pd.Timestamp:
    return pd.to_datetime(f"{FORCED_DATE} {hms}")

def extract_time_from_string(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.extract(r"(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})")[0]

def parse_time_series(raw: pd.Series, forced_date: str) -> pd.Series:
    if np.issubdtype(raw.dtype, np.number):
        parsed = pd.to_datetime(raw, unit="d", origin="1899-12-30", errors="coerce")
        return pd.to_datetime(forced_date + " " + parsed.dt.strftime("%H:%M:%S"), errors="coerce")

    raw_str = raw.astype(str).str.strip()

    parsed = pd.to_datetime(raw_str, format="%H:%M:%S", errors="coerce")
    if parsed.notna().sum() < 5:
        parsed = pd.to_datetime(raw_str, format="%H:%M", errors="coerce")

    if parsed.notna().sum() < 5:
        extracted = extract_time_from_string(raw_str)
        parsed = pd.to_datetime(extracted, format="%H:%M:%S", errors="coerce")
        if parsed.notna().sum() < 5:
            parsed = pd.to_datetime(extracted, format="%H:%M", errors="coerce")

    if parsed.notna().sum() < 5:
        parsed = pd.to_datetime(raw_str, errors="coerce")

    return pd.to_datetime(forced_date + " " + parsed.dt.strftime("%H:%M:%S"), errors="coerce")


# =========================================================
# LOAD SMPS SIZE DISTRIBUTION
# =========================================================
def load_smps_size_distribution(file, forced_date=FORCED_DATE):
    xls = pd.ExcelFile(file)
    sheet = xls.sheet_names[0]
    last_error = None

    for skip in [0, 10, 20, 30, 40]:
        try:
            df = pd.read_excel(file, sheet_name=sheet, skiprows=skip)
            df.columns = [str(c).strip() for c in df.columns]

            time_col = None
            for c in df.columns:
                c_str = str(c).lower().strip()
                if "corrected time" in c_str or c_str == "time" or "time" in c_str:
                    time_col = c
                    break
            if time_col is None:
                continue

            size_cols = []
            size_vals = []
            for c in df.columns:
                if c == time_col:
                    continue
                try:
                    dp = float(str(c).strip())
                    size_cols.append(c)
                    size_vals.append(dp)
                except Exception:
                    pass

            if len(size_cols) < 5:
                continue

            out = pd.DataFrame()
            out["Time"] = parse_time_series(df[time_col], forced_date)

            for c in size_cols:
                out[str(c)] = pd.to_numeric(df[c], errors="coerce")

            out = out.dropna(subset=["Time"]).sort_values("Time").reset_index(drop=True)

            print(f"Loaded {os.path.basename(file)} with {len(size_cols)} size bins using skiprows={skip}")
            print(out[["Time"]].head())
            return out, np.array(size_vals, dtype=float), [str(c) for c in size_cols]

        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to load SMPS size distribution. Last error: {last_error}")


# =========================================================
# BAND METRICS
# =========================================================
def integrate_band(dist, diameters, lower=None, upper=None):
    mask = np.ones_like(diameters, dtype=bool)
    if lower is not None:
        mask &= diameters >= lower
    if upper is not None:
        mask &= diameters < upper

    vals = np.asarray(dist, dtype=float)[mask]
    if vals.size == 0:
        return np.nan
    return np.nansum(vals)

def summarise_distribution(dist, diameters):
    total = integrate_band(dist, diameters, lower=None, upper=None)
    band_10_50 = integrate_band(dist, diameters, lower=10, upper=50)
    band_50_150 = integrate_band(dist, diameters, lower=50, upper=150)
    band_gt150 = integrate_band(dist, diameters, lower=150, upper=None)
    band_gt200 = integrate_band(dist, diameters, lower=200, upper=None)

    frac_gt150 = band_gt150 / total if pd.notna(total) and total > 0 else np.nan
    frac_gt200 = band_gt200 / total if pd.notna(total) and total > 0 else np.nan

    return {
        "total_integrated": total,
        "band_10_50": band_10_50,
        "band_50_150": band_50_150,
        "band_gt150": band_gt150,
        "band_gt200": band_gt200,
        "frac_gt150": frac_gt150,
        "frac_gt200": frac_gt200,
    }


# =========================================================
# MAIN
# =========================================================
print("Loading SMPS size distribution...")
df, diameters, size_cols = load_smps_size_distribution(SMPS_FILE)

rows = []

for condition, repeat_name, start_hms, end_hms in DIST_WINDOWS:
    sub = df[(df["Time"] >= dt(start_hms)) & (df["Time"] <= dt(end_hms))].copy()
    print(f"{condition} {repeat_name}: {len(sub)} rows")

    if len(sub) == 0:
        continue

    mean_dist = sub[size_cols].mean(axis=0).to_numpy(dtype=float)
    metrics = summarise_distribution(mean_dist, diameters)

    rows.append({
        "condition": condition,
        "repeat": repeat_name,
        "start_time": start_hms,
        "end_time": end_hms,
        **metrics
    })

run_df = pd.DataFrame(rows)

run_path = os.path.join(OUTPUT_DIR, "Table_6_2_10_size_band_run_summary.csv")
run_df.to_csv(run_path, index=False)

print("\nRun-level size-band summary:")
print(run_df)

# Condition summary
condition_summary = run_df.groupby("condition").agg(
    total_integrated_mean=("total_integrated", "mean"),
    total_integrated_std=("total_integrated", "std"),
    frac_gt150_mean=("frac_gt150", "mean"),
    frac_gt150_std=("frac_gt150", "std"),
    frac_gt200_mean=("frac_gt200", "mean"),
    frac_gt200_std=("frac_gt200", "std"),
    band_gt150_mean=("band_gt150", "mean"),
    band_gt150_std=("band_gt150", "std"),
    band_gt200_mean=("band_gt200", "mean"),
    band_gt200_std=("band_gt200", "std"),
).reset_index()

summary_path = os.path.join(OUTPUT_DIR, "Table_6_2_11_size_band_condition_summary.csv")
condition_summary.to_csv(summary_path, index=False)

print("\nCondition summary:")
print(condition_summary)

# Plot fractions >150 nm and >200 nm
x = np.arange(len(condition_summary))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 5))

ax.bar(
    x - width/2,
    condition_summary["frac_gt150_mean"],
    width,
    yerr=condition_summary["frac_gt150_std"],
    capsize=4,
    label="Fraction >150 nm"
)

ax.bar(
    x + width/2,
    condition_summary["frac_gt200_mean"],
    width,
    yerr=condition_summary["frac_gt200_std"],
    capsize=4,
    label="Fraction >200 nm"
)

ax.set_xticks(x)
ax.set_xticklabels(condition_summary["condition"])
ax.set_ylabel("Fraction of integrated size distribution")
ax.set_title("Figure 6.2.5. Large-particle fractions under electrostatic conditions")
ax.legend()
ax.grid(True, axis="y", linestyle="--", linewidth=0.5)

plt.tight_layout()

fig_path = os.path.join(OUTPUT_DIR, "Figure_6_2_5_large_particle_fraction.png")
plt.savefig(fig_path, dpi=300, bbox_inches="tight")
plt.show()

print("\nSaved:")
print(run_path)
print(summary_path)
print(fig_path)

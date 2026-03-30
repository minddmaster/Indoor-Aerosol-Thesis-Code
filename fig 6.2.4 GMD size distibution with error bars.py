# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 18:20:50 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Figure 6.2.4 — Mean size distributions under electrostatic conditions
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Charge state analysis/DAY1 SMPS DATA_COM32.xlsx"
OUTPUT_DIR = os.path.join(os.path.dirname(FILE), "charge_state_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FORCED_DATE = "2025-02-24"

# Generation windows
WINDOWS = [
    ("baseline", "14:50:01", "14:56:00"),
    ("baseline", "15:12:00", "15:17:00"),
    ("baseline", "15:30:00", "15:35:00"),

    ("corona", "16:11:10", "16:16:10"),
    ("corona", "16:26:30", "16:31:30"),
    ("corona", "16:40:40", "16:45:40"),

    ("ionizer", "16:59:10", "17:04:10"),
    ("ionizer", "17:11:30", "17:16:30"),
    ("ionizer", "17:25:30", "17:30:30"),
]

def dt(hms):
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

# Load data
df, diameters, size_cols = load_smps_size_distribution(FILE)

# Store distributions
data = {"baseline": [], "corona": [], "ionizer": []}

for cond, start, end in WINDOWS:
    sub = df[(df["Time"] >= dt(start)) & (df["Time"] <= dt(end))].copy()

    print(f"{cond}: {start} to {end} -> {len(sub)} rows")

    if len(sub) == 0:
        continue

    dist = sub[size_cols].mean(axis=0).to_numpy(dtype=float)

    if len(dist) == len(diameters):
        data[cond].append(dist)

# Compute mean + std safely
mean_std = {}
for cond in data:
    if len(data[cond]) == 0:
        print(f"Warning: no valid distributions found for {cond}")
        continue

    arr = np.vstack(data[cond])

    mean_std[cond] = {
        "mean": np.nanmean(arr, axis=0),
        "std": np.nanstd(arr, axis=0)
    }

    print(f"{cond}: {arr.shape[0]} distributions averaged")

# Plot
plt.figure(figsize=(8, 6))

labels = {
    "baseline": "Baseline",
    "corona": "Corona charger",
    "ionizer": "Corona charger + ionizer"
}

for cond in ["baseline", "corona", "ionizer"]:
    if cond not in mean_std:
        continue

    mean = mean_std[cond]["mean"]
    std = mean_std[cond]["std"]

    plt.plot(diameters, mean, label=labels[cond], linewidth=2)
    plt.fill_between(diameters, mean - std, mean + std, alpha=0.2)

plt.xscale("log")
plt.xlabel("Particle diameter (nm)")
plt.ylabel("dN/dlogDp")
plt.title("Figure 6.2.4. Mean particle size distributions under electrostatic conditions")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend()
plt.tight_layout()

out_path = os.path.join(OUTPUT_DIR, "Figure_6_2_4_size_distribution.png")
plt.savefig(out_path, dpi=300, bbox_inches="tight")
plt.show()

print("\nSaved:")
print(out_path)
plt.figure(figsize=(8,6))

labels = {
    "baseline": "Baseline",
    "corona": "Corona charger",
    "ionizer": "Corona charger + ionizer"
}

colors = {
    "baseline": "blue",
    "corona": "orange",
    "ionizer": "green"
}

for cond in ["baseline", "corona", "ionizer"]:
    if cond not in mean_std:
        continue

    mean = mean_std[cond]["mean"]
    std = mean_std[cond]["std"]

    # main line
    plt.plot(diameters, mean, label=labels[cond], color=colors[cond], linewidth=2)

    # shaded region (already good)
    plt.fill_between(diameters, mean - std, mean + std,
                     color=colors[cond], alpha=0.2)

    # ADD ERROR BARS (sample every few bins to avoid clutter)
    step = 3  # adjust (2–4 works well)
    idx = np.arange(0, len(diameters), step)

    plt.errorbar(diameters[idx],
                 mean[idx],
                 yerr=std[idx],
                 fmt='o',
                 color=colors[cond],
                 capsize=3,
                 markersize=4,
                 alpha=0.8)

plt.xscale("log")
plt.xlabel("Particle diameter (nm)")
plt.ylabel("dN/dlogDp")
plt.title("Figure 6.2.4. Mean particle size distributions under electrostatic conditions")

plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend()
plt.tight_layout()

plt.savefig(os.path.join(OUTPUT_DIR, "Figure_6_2_4_size_distribution_with_errorbars.png"),
            dpi=300, bbox_inches="tight")

plt.show()
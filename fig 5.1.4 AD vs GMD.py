# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 23:10:25 2026

@author: papkp
"""

# ============================================================
# FIGURE 5.1.4 – CHARACTERISTIC DIAMETER COMPARISON
# Computes GMD and mode diameter from your already-generated
# summary tables, then plots a comparison figure.
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# INPUT FILES
# Use the summary CSVs created from your previous scripts
# ============================================================
files = {
    "Water": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/COMPARISON_21JAN_AND_060224/Water_21Jan_summary.csv",
    "Sodium iodide": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/COMPARISON_21JAN_AND_060224/Sodium_iodide_21Jan_summary.csv",
    "NaCl (21 Jan)": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/COMPARISON_21JAN_AND_060224/NaCl_(21_Jan)_21Jan_summary.csv",
    "NaCl (6 Feb)": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/COMPARISON_21JAN_AND_060224/NaCl_(6_Feb)_060224_summary.csv",
    "Sucrose": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/COMPARISON_21JAN_AND_060224/Sucrose_060224_summary.csv",
    "KCl": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/COMPARISON_21JAN_AND_060224/KCl_060224_summary.csv",
}

output_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/COMPARISON_21JAN_AND_060224")
output_dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# FUNCTIONS
# ============================================================
def compute_gmd(diam_nm, weights):
    """
    Geometric mean diameter using positive weights.
    """
    diam_nm = np.asarray(diam_nm, dtype=float)
    weights = np.asarray(weights, dtype=float)

    mask = np.isfinite(diam_nm) & np.isfinite(weights) & (diam_nm > 0) & (weights > 0)
    diam_nm = diam_nm[mask]
    weights = weights[mask]

    if len(diam_nm) == 0 or np.sum(weights) <= 0:
        return np.nan

    return np.exp(np.sum(weights * np.log(diam_nm)) / np.sum(weights))


def compute_mode_diameter(diam_nm, weights):
    """
    Diameter at maximum mean distribution.
    """
    diam_nm = np.asarray(diam_nm, dtype=float)
    weights = np.asarray(weights, dtype=float)

    mask = np.isfinite(diam_nm) & np.isfinite(weights)
    diam_nm = diam_nm[mask]
    weights = weights[mask]

    if len(diam_nm) == 0:
        return np.nan

    return diam_nm[np.argmax(weights)]


# ============================================================
# CALCULATE METRICS
# ============================================================
rows = []

for aerosol, path in files.items():
    df = pd.read_csv(path)

    diam = df["diameter_nm"].values
    mean_vals = df["mean"].values

    gmd = compute_gmd(diam, mean_vals)
    mode = compute_mode_diameter(diam, mean_vals)

    rows.append({
        "Aerosol": aerosol,
        "GMD_nm": gmd,
        "Mode_nm": mode
    })

summary_df = pd.DataFrame(rows)

# Save table
summary_path = output_dir / "Table_5_1_Aerosol_Characteristic_Diameters.csv"
summary_df.to_csv(summary_path, index=False)

print(summary_df)

# ============================================================
# PLOT – GMD AND MODE DIAMETER COMPARISON
# ============================================================
x = np.arange(len(summary_df))

plt.figure(figsize=(10, 5.5))
plt.plot(x, summary_df["GMD_nm"], marker="o", linewidth=2, label="Geometric mean diameter")
plt.plot(x, summary_df["Mode_nm"], marker="s", linewidth=2, label="Mode diameter")

plt.xticks(x, summary_df["Aerosol"], rotation=30, ha="right")
plt.ylabel("Diameter (nm)")
plt.title("Figure 5.1.4. Comparison of characteristic particle diameters across chamber aerosols")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend()
plt.tight_layout()

fig_path = output_dir / "Figure_5_1_4_GMD_Mode_Comparison.png"
plt.savefig(fig_path, dpi=600, bbox_inches="tight")
plt.show()

print(f"\nSaved table to: {summary_path}")
print(f"Saved figure to: {fig_path}")
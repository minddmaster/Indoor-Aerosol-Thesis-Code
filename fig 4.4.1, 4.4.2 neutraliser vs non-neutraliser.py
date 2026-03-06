# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 17:12:14 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Ref No: THESIS-FIG4.4-COMPLETE-CLEANFILES-2026-03-05
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================
# FILE PATHS
# =========================================================
NEUTRALISED_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 1 Am241 vs no neutraliser/neutraliser_DAY1 SMPS DATA_COM32.xlsx"
NON_NEUTRALISED_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 1 Am241 vs no neutraliser/non-neutraliser_ DAY1 SMPS DATA_COM33.xlsx"

SHEET_NAME = "EDIT1 (2)"

OUT_DIR = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Figures"
os.makedirs(OUT_DIR, exist_ok=True)

FIG_441 = os.path.join(OUT_DIR, "Figure_4.4.1_Neutralised_vs_NonNeutralised.png")
TAB_441 = os.path.join(OUT_DIR, "Table_4.4.1_Effect_of_Neutralisation.xlsx")

FIG_442 = os.path.join(OUT_DIR, "Figure_4.4.2_Electrostatic_Treatment.png")
TAB_442 = os.path.join(OUT_DIR, "Table_4.4.2_Electrostatic_Treatment.xlsx")

# =========================================================
# WINDOWS
# =========================================================
# Figure 4.4.1 baseline comparison
BASELINE_WINDOWS = [
    ("15:12:00", "15:17:00"),
    ("15:30:00", "15:35:00"),
    ("15:47:00", "15:52:00"),
]

# Figure 4.4.2 electrostatic treatment (neutralised file only)
NO_CORONA_WINDOWS = [
    ("15:12:00", "15:17:00"),
    ("15:30:00", "15:35:00"),
    ("15:47:00", "15:52:00"),
]

CORONA_WINDOWS = [
    ("16:11:10", "16:16:10"),
    ("16:26:30", "16:31:30"),
    ("16:40:40", "16:45:40"),
]

CORONA_IONISER_WINDOWS = [
    ("16:59:10", "17:04:10"),
    ("17:11:30", "17:16:30"),
    ("17:25:30", "17:30:30"),
]

FINAL_RUN_WINDOWS = [
    ("17:41:35", "17:46:35"),
]

# =========================================================
# HELPERS
# =========================================================
def detect_time_col(df):
    for c in df.columns:
        if str(c).strip().lower() in ["corrected time", "time", "datetime", "timestamp", "date time"]:
            return c
    for c in df.columns:
        if "time" in str(c).lower():
            return c
    return df.columns[0]

def to_dt(series):
    return pd.to_datetime(series, errors="coerce", dayfirst=True)

def filter_time_window(df, time_col, t_start, t_end):
    out = df.copy()
    out[time_col] = to_dt(out[time_col])
    out = out.dropna(subset=[time_col]).sort_values(time_col)

    ts = pd.to_datetime(t_start).time()
    te = pd.to_datetime(t_end).time()

    return out[(out[time_col].dt.time >= ts) & (out[time_col].dt.time <= te)]

def map_bin_cols(df, time_col=None):
    cols = [c for c in df.columns if c != time_col]
    bin_cols = []
    diam = []

    for c in cols:
        # cleaned files already use numeric diameter headers
        try:
            d = float(c)
            v = pd.to_numeric(df[c], errors="coerce")
            if v.notna().sum() > 0:
                bin_cols.append(c)
                diam.append(d)
            continue
        except:
            pass

        m = re.search(r"(\d+(\.\d+)?)", str(c))
        if m:
            d = float(m.group(1))
            v = pd.to_numeric(df[c], errors="coerce")
            if v.notna().sum() > 0:
                bin_cols.append(c)
                diam.append(d)

    if len(bin_cols) < 5:
        raise ValueError("Could not detect enough diameter bin columns.")

    diam = np.array(diam, dtype=float)
    order = np.argsort(diam)
    diam = diam[order]
    bin_cols = [bin_cols[i] for i in order]

    return bin_cols, diam

def mean_distribution_from_segment(df, time_col=None):
    bin_cols, diam = map_bin_cols(df, time_col=time_col)
    y = df[bin_cols].apply(pd.to_numeric, errors="coerce").mean(axis=0).to_numpy(dtype=float)

    # convert to dN/dlogD
    logd = np.log10(diam)
    dlog = np.gradient(logd)
    dlog = np.where(dlog == 0, np.nan, dlog)
    y_dndlog = y / dlog

    return diam, y_dndlog

def build_replicate_distributions(df, time_col, windows):
    ys = []
    x_ref = None

    for t0, t1 in windows:
        seg = filter_time_window(df, time_col, t0, t1)
        if seg.empty:
            print(f"Warning: no rows found for {t0}–{t1}")
            continue

        x, y = mean_distribution_from_segment(seg, time_col=time_col)

        if x_ref is None:
            x_ref = x
        elif not np.array_equal(x, x_ref):
            y = np.interp(np.log10(x_ref), np.log10(x), y)
            x = x_ref

        ys.append(y)

    if len(ys) == 0:
        raise ValueError("No valid windows found.")

    return x_ref, np.vstack(ys)

def distribution_stats(diam_nm, dndlog):
    d = np.array(diam_nm, dtype=float)
    y = np.array(dndlog, dtype=float)

    mask = np.isfinite(d) & np.isfinite(y) & (d > 0) & (y >= 0)
    d = d[mask]
    y = y[mask]

    log10d = np.log10(d)
    dlog10 = np.gradient(log10d)
    weights = y * dlog10

    total = np.nansum(weights)
    mode = d[np.nanargmax(y)] if np.isfinite(y).any() else np.nan

    if np.nansum(weights) <= 0:
        gmd = np.nan
    else:
        mu = np.nansum(weights * np.log(d)) / np.nansum(weights)
        gmd = np.exp(mu)

    return gmd, mode, total

def summarise_replicates(x, y_stack):
    mean_y = np.nanmean(y_stack, axis=0)
    sd_y = np.nanstd(y_stack, axis=0, ddof=1) if y_stack.shape[0] > 1 else np.full_like(mean_y, np.nan)

    rows = []
    for row in y_stack:
        gmd, mode, total = distribution_stats(x, row)
        rows.append((gmd, mode, total))
    arr = np.array(rows, dtype=float)

    return {
        "mean_y": mean_y,
        "sd_y": sd_y,
        "gmd_mean": np.nanmean(arr[:, 0]),
        "gmd_sd": np.nanstd(arr[:, 0], ddof=1) if arr.shape[0] > 1 else np.nan,
        "mode_mean": np.nanmean(arr[:, 1]),
        "mode_sd": np.nanstd(arr[:, 1], ddof=1) if arr.shape[0] > 1 else np.nan,
        "total_mean": np.nanmean(arr[:, 2]),
        "total_sd": np.nanstd(arr[:, 2], ddof=1) if arr.shape[0] > 1 else np.nan,
        "n": y_stack.shape[0],
    }

def interp_stack(x_old, y_stack, x_new):
    if np.array_equal(x_old, x_new):
        return y_stack
    return np.vstack([np.interp(np.log10(x_new), np.log10(x_old), row) for row in y_stack])

def percent_reduction(cond_total, baseline_total):
    if not np.isfinite(cond_total) or not np.isfinite(baseline_total) or baseline_total == 0:
        return np.nan
    return ((baseline_total - cond_total) / baseline_total) * 100.0

# =========================================================
# LOAD CLEANED FILES
# =========================================================
neu_df = pd.read_excel(NEUTRALISED_PATH, sheet_name=SHEET_NAME)
non_df = pd.read_excel(NON_NEUTRALISED_PATH, sheet_name=SHEET_NAME)

neu_time_col = detect_time_col(neu_df)
non_time_col = detect_time_col(non_df)

print("Neutralised time column:", neu_time_col)
print("Non-neutralised time column:", non_time_col)

# =========================================================
# FIGURE 4.4.1 + TABLE 4.4.1
# =========================================================
x_neu_441, y_neu_stack_441 = build_replicate_distributions(neu_df, neu_time_col, BASELINE_WINDOWS)
x_non_441, y_non_stack_441 = build_replicate_distributions(non_df, non_time_col, BASELINE_WINDOWS)

common_x_441 = x_neu_441 if len(x_neu_441) >= len(x_non_441) else x_non_441
y_neu_stack_441 = interp_stack(x_neu_441, y_neu_stack_441, common_x_441)
y_non_stack_441 = interp_stack(x_non_441, y_non_stack_441, common_x_441)

sum_neu_441 = summarise_replicates(common_x_441, y_neu_stack_441)
sum_non_441 = summarise_replicates(common_x_441, y_non_stack_441)

fig, ax = plt.subplots(figsize=(7.2, 4.8))
ax.plot(common_x_441, sum_neu_441["mean_y"], linewidth=2.0, linestyle="-", label="Am-241 neutralised")
ax.plot(common_x_441, sum_non_441["mean_y"], linewidth=1.8, linestyle="--",
        marker="o", markersize=3, markevery=max(1, len(common_x_441)//15),
        label="Metal sheath (non-neutralised)")
ax.set_xscale("log")
ax.set_xlabel("Particle diameter (nm)")
ax.set_ylabel("Number distribution (dN/dlogD)")
ax.set_title("Figure 4.4.1. Neutralised and non-neutralised particle size distributions")
ax.grid(True, which="major", linestyle="--", linewidth=0.6)
ax.grid(True, which="minor", linestyle=":", linewidth=0.4)
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(FIG_441, dpi=600, bbox_inches="tight")
plt.show()

table_441 = pd.DataFrame({
    "Condition": ["Am-241 neutralised", "Metal sheath (non-neutralised)"],
    "GMD (nm)": [sum_neu_441["gmd_mean"], sum_non_441["gmd_mean"]],
    "Mode diameter (nm)": [sum_neu_441["mode_mean"], sum_non_441["mode_mean"]],
    "Total concentration": [sum_neu_441["total_mean"], sum_non_441["total_mean"]],
})
table_441.to_excel(TAB_441, index=False)

# =========================================================
# FIGURE 4.4.2 + TABLE 4.4.2
# =========================================================
x_no, y_no_stack = build_replicate_distributions(neu_df, neu_time_col, NO_CORONA_WINDOWS)
x_cor, y_cor_stack = build_replicate_distributions(neu_df, neu_time_col, CORONA_WINDOWS)
x_ion, y_ion_stack = build_replicate_distributions(neu_df, neu_time_col, CORONA_IONISER_WINDOWS)
x_fin, y_fin_stack = build_replicate_distributions(neu_df, neu_time_col, FINAL_RUN_WINDOWS)

common_x_442 = max([x_no, x_cor, x_ion, x_fin], key=len)
y_no_stack = interp_stack(x_no, y_no_stack, common_x_442)
y_cor_stack = interp_stack(x_cor, y_cor_stack, common_x_442)
y_ion_stack = interp_stack(x_ion, y_ion_stack, common_x_442)
y_fin_stack = interp_stack(x_fin, y_fin_stack, common_x_442)

sum_no = summarise_replicates(common_x_442, y_no_stack)
sum_cor = summarise_replicates(common_x_442, y_cor_stack)
sum_ion = summarise_replicates(common_x_442, y_ion_stack)
sum_fin = summarise_replicates(common_x_442, y_fin_stack)

fig, ax = plt.subplots(figsize=(8.0, 5.2))

ax.plot(common_x_442, sum_no["mean_y"], linewidth=2.0, linestyle="-", label="No corona")
ax.fill_between(common_x_442,
                np.maximum(sum_no["mean_y"] - sum_no["sd_y"], 0),
                sum_no["mean_y"] + sum_no["sd_y"],
                alpha=0.18)

ax.plot(common_x_442, sum_cor["mean_y"], linewidth=1.8, linestyle="--", label="Corona charger")
ax.fill_between(common_x_442,
                np.maximum(sum_cor["mean_y"] - sum_cor["sd_y"], 0),
                sum_cor["mean_y"] + sum_cor["sd_y"],
                alpha=0.18)

ax.plot(common_x_442, sum_ion["mean_y"], linewidth=1.8, linestyle="-.", label="Corona + ioniser")
ax.fill_between(common_x_442,
                np.maximum(sum_ion["mean_y"] - sum_ion["sd_y"], 0),
                sum_ion["mean_y"] + sum_ion["sd_y"],
                alpha=0.18)

ax.plot(common_x_442, sum_fin["mean_y"], linewidth=1.8, linestyle=":",
        marker="o", markersize=3, markevery=max(1, len(common_x_442)//15),
        label="Final run")

ax.set_xscale("log")
ax.set_xlabel("Particle diameter (nm)")
ax.set_ylabel("Number distribution (dN/dlogD)")
ax.set_title("Figure 4.4.2. Effect of electrostatic treatment on particle size distributions")
ax.grid(True, which="major", linestyle="--", linewidth=0.6)
ax.grid(True, which="minor", linestyle=":", linewidth=0.4)
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(FIG_442, dpi=600, bbox_inches="tight")
plt.show()

baseline_total = sum_no["total_mean"]

table_442 = pd.DataFrame({
    "Condition": ["No corona", "Corona charger", "Corona + ioniser", "Final run"],
    "n repeats": [sum_no["n"], sum_cor["n"], sum_ion["n"], sum_fin["n"]],
    "GMD mean (nm)": [sum_no["gmd_mean"], sum_cor["gmd_mean"], sum_ion["gmd_mean"], sum_fin["gmd_mean"]],
    "GMD SD (nm)": [sum_no["gmd_sd"], sum_cor["gmd_sd"], sum_ion["gmd_sd"], sum_fin["gmd_sd"]],
    "Mode mean (nm)": [sum_no["mode_mean"], sum_cor["mode_mean"], sum_ion["mode_mean"], sum_fin["mode_mean"]],
    "Mode SD (nm)": [sum_no["mode_sd"], sum_cor["mode_sd"], sum_ion["mode_sd"], sum_fin["mode_sd"]],
    "Total concentration mean": [sum_no["total_mean"], sum_cor["total_mean"], sum_ion["total_mean"], sum_fin["total_mean"]],
    "Total concentration SD": [sum_no["total_sd"], sum_cor["total_sd"], sum_ion["total_sd"], sum_fin["total_sd"]],
    "% reduction vs no corona": [
        np.nan,
        percent_reduction(sum_cor["total_mean"], baseline_total),
        percent_reduction(sum_ion["total_mean"], baseline_total),
        percent_reduction(sum_fin["total_mean"], baseline_total),
    ],
})
table_442.to_excel(TAB_442, index=False)

print("\nSaved:")
print(FIG_441)
print(TAB_441)
print(FIG_442)
print(TAB_442)

print("\nTable 4.4.1")
print(table_441)

print("\nTable 4.4.2")
print(table_442)
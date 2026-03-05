# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 17:29:07 2026

@author: papkp
"""

# Ref No: THESIS-FIG-4.1+TABLE-UPDATED-PY-NaCl-SMPS-ELPI-R1R3-2026-03-05
# Figure 4.1: Mean ± error bars across Repeat 1–3 for SMPS (Dm) vs ELPI (Da)
# + Automatically computes Table metrics: GMD, Mode diameter, GSD, Total concentration
# Uses NaCl Aerosol ON->OFF windows (SPHERE House Day 1) and fixes bin-width mismatch.

from __future__ import annotations

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================
# FILE PATHS (YOUR INPUTS)
# =========================
ELPI_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 1 ELPI VS SMPS/elpi day1.xlsx"
SMPS_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 1 ELPI VS SMPS/DAY1 SMPS DATA_COM32.xlsx"

OUTDIR = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 1 ELPI VS SMPS"
SAVE_BASENAME = "Figure_4_1_SMPS_vs_ELPI_NaCl_Repeat1to3_Mean_SD"

# Output table name (saved into OUTDIR)
TABLE_NAME = "Table_4X_SMPS_ELPI_SizeMetrics_NaCl_Repeat1to3.xlsx"

# =========================
# REPEAT WINDOWS (ON -> OFF)
# =========================
REPEATS = {
    "R1": ("15:12:00", "15:17:00"),
    "R2": ("15:30:00", "15:35:00"),
    "R3": ("15:47:00", "15:52:00"),
}

# =========================
# ERROR BAR MODE
# =========================
ERROR_MODE = "SD"          # "SD" or "SEM"
PLOT_EVERY_NTH_BIN = 2     # error bars shown every N bins to reduce clutter

# =========================
# NORMALISATION
# =========================
# Keep True for comparing modal structure (as you plotted)
# Set False if you want absolute magnitudes (only valid if both instruments are already in dN/dlogD)
NORMALISE_FOR_PLOT = True


# =========================
# HELPERS
# =========================
def read_excel_any(path: str) -> dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(path)
    return {sh: pd.read_excel(path, sheet_name=sh) for sh in xls.sheet_names}

def best_time_col(df: pd.DataFrame) -> str | None:
    candidates = [c for c in df.columns if str(c).strip().lower() in ["time", "timestamp", "date time", "datetime", "date_time"]]
    if candidates:
        return candidates[0]
    for c in df.columns:
        if "time" in str(c).lower():
            return c
    return None

def coerce_time_series(s: pd.Series) -> pd.Series:
    out = pd.to_datetime(s, errors="coerce")
    if out.isna().all():
        out = pd.to_datetime(s.astype(str), errors="coerce")
    return out

def filter_by_time_window(df: pd.DataFrame, time_col: str, t_start: str, t_end: str) -> pd.DataFrame:
    df = df.copy()
    df[time_col] = coerce_time_series(df[time_col])
    df = df.dropna(subset=[time_col]).sort_values(time_col)
    ts = pd.to_datetime(t_start)
    te = pd.to_datetime(t_end)
    return df[(df[time_col].dt.time >= ts.time()) & (df[time_col].dt.time <= te.time())]

def detect_numeric_bin_headers(cols) -> list[float]:
    bins = []
    for c in cols:
        s = str(c).strip()
        if s.lower() in ["time", "timestamp", "datetime", "date", "total", "tot", "concentration"]:
            continue
        m = re.search(r"(\d+(\.\d+)?)", s)
        if not m:
            continue
        if any(k in s.lower() for k in ["dp", "diam", "nm", "bin"]) or s.replace(".", "", 1).isdigit():
            bins.append(float(m.group(1)))
    return sorted(list(set(bins)))

def map_bin_cols(df: pd.DataFrame, diam_bins: list[float]) -> list[str]:
    cols = list(df.columns)
    out = []
    for d in diam_bins:
        if d in cols:
            out.append(d)
            continue
        matches = [c for c in cols if re.search(rf"\b{re.escape(str(d))}\b", str(c))]
        if matches:
            out.append(matches[0])
            continue
        matches = [c for c in cols if str(d) in str(c)]
        if matches:
            out.append(matches[0])
            continue
        raise ValueError(f"Could not map diameter bin {d} to a column header.")
    return out

def to_dndlog_from_wide(df: pd.DataFrame, time_col: str | None) -> tuple[np.ndarray, np.ndarray]:
    """
    Average wide-format bins over rows; convert to per-log-bin distribution.
    Fixes bin-width mismatch using np.gradient to ensure dlog has same length as x.
    """
    cols = [c for c in df.columns if (time_col is None or c != time_col)]
    diam_bins = detect_numeric_bin_headers(cols)
    if len(diam_bins) < 6:
        raise ValueError("Not enough diameter bin columns detected. Your sheet may not be wide-format bins.")

    bin_cols = map_bin_cols(df, diam_bins)

    # Reconstruct x from actual mapped column names (1:1 with y)
    x = []
    for c in bin_cols:
        m = re.search(r"(\d+(\.\d+)?)", str(c))
        if not m:
            raise ValueError(f"Could not extract numeric diameter from bin column: {c}")
        x.append(float(m.group(1)))
    x = np.array(x, dtype=float)

    y = df[bin_cols].apply(pd.to_numeric, errors="coerce").mean(axis=0).values.astype(float)

    # Sort by diameter
    order = np.argsort(x)
    x = x[order]
    y = y[order]

    # Convert to per-log-bin
    logx = np.log10(x)
    dlog = np.gradient(logx)
    dlog = np.where(dlog == 0, np.nan, dlog)

    y_dndlog = y / dlog
    return x, y_dndlog

def choose_best_sheet(sheets: dict[str, pd.DataFrame]) -> tuple[str, pd.DataFrame]:
    best_name, best_df, best_score = None, None, -1
    for name, df in sheets.items():
        if df is None or df.empty:
            continue
        score = len(detect_numeric_bin_headers(df.columns))
        if score > best_score:
            best_name, best_df, best_score = name, df, score
    if best_df is None:
        raise ValueError("No usable sheet found.")
    return best_name, best_df

def mean_and_error(stack: np.ndarray, mode: str) -> tuple[np.ndarray, np.ndarray]:
    mu = np.nanmean(stack, axis=0)
    sd = np.nanstd(stack, axis=0, ddof=1)
    if mode.upper() == "SEM":
        n = np.sum(np.isfinite(stack), axis=0)
        sem = sd / np.sqrt(np.maximum(n, 1))
        return mu, sem
    return mu, sd

def compute_metrics(diameter_nm: np.ndarray, dndlog: np.ndarray) -> dict:
    """
    Metrics computed from a dN/dlogD distribution:
      - Total concentration: integral over logD (approx) = sum(dN/dlogD * dlogD)
      - Mode diameter: argmax(dN/dlogD)
      - GMD and GSD: lognormal moments weighted by dN/dlogD * dlogD
    """
    d = np.array(diameter_nm, dtype=float)
    y = np.array(dndlog, dtype=float)

    mask = np.isfinite(d) & np.isfinite(y) & (d > 0)
    d = d[mask]
    y = y[mask]

    # log-bin widths
    logd = np.log(d)            # natural log
    log10d = np.log10(d)
    dlog10 = np.gradient(log10d)
    dlog10 = np.where(dlog10 == 0, np.nan, dlog10)

    # total number concentration (approx integral)
    # dN ≈ (dN/dlog10D) * dlog10D
    weights = y * dlog10
    total = np.nansum(weights)

    # mode (from dN/dlogD)
    mode = d[np.nanargmax(y)]

    # GMD and GSD using number weights (dN) not raw y
    w = weights
    w_sum = np.nansum(w)
    if not np.isfinite(w_sum) or w_sum <= 0:
        return {"GMD_nm": np.nan, "Mode_nm": mode, "GSD": np.nan, "Total_conc": np.nan}

    mu = np.nansum(w * logd) / w_sum
    gmd = np.exp(mu)

    var = np.nansum(w * (logd - mu) ** 2) / w_sum
    gsd = np.exp(np.sqrt(var))

    return {"GMD_nm": gmd, "Mode_nm": mode, "GSD": gsd, "Total_conc": total}


# =========================
# LOAD + SELECT SHEETS
# =========================
smps_sheets = read_excel_any(SMPS_PATH)
elpi_sheets = read_excel_any(ELPI_PATH)

smps_sheet_name, smps_df = choose_best_sheet(smps_sheets)
elpi_sheet_name, elpi_df = choose_best_sheet(elpi_sheets)

print(f"Selected SMPS sheet: {smps_sheet_name}")
print(f"Selected ELPI sheet: {elpi_sheet_name}")

smps_time_col = best_time_col(smps_df)
elpi_time_col = best_time_col(elpi_df)

if not smps_time_col:
    raise ValueError("Could not detect SMPS time column. Rename it to 'Time' or set it manually in code.")
if not elpi_time_col:
    raise ValueError("Could not detect ELPI time column. Rename it to 'Time' or set it manually in code.")

# =========================
# BUILD PER-REPEAT DISTRIBUTIONS
# =========================
smps_rep = []
elpi_rep = []
x_smps_ref = None
x_elpi_ref = None

for rep, (t_on, t_off) in REPEATS.items():
    smps_win = filter_by_time_window(smps_df, smps_time_col, t_on, t_off)
    elpi_win = filter_by_time_window(elpi_df, elpi_time_col, t_on, t_off)

    if smps_win.empty:
        raise ValueError(f"SMPS filter returned 0 rows for {rep} ({t_on}–{t_off}). Check time format.")
    if elpi_win.empty:
        raise ValueError(f"ELPI filter returned 0 rows for {rep} ({t_on}–{t_off}). Check time format.")

    x_s, y_s = to_dndlog_from_wide(smps_win, smps_time_col)
    x_e, y_e = to_dndlog_from_wide(elpi_win, elpi_time_col)

    if x_smps_ref is None:
        x_smps_ref = x_s
    if x_elpi_ref is None:
        x_elpi_ref = x_e

    # Interpolate if bin grids differ
    if not np.array_equal(x_s, x_smps_ref):
        y_s = np.interp(np.log10(x_smps_ref), np.log10(x_s), y_s)
        x_s = x_smps_ref

    if not np.array_equal(x_e, x_elpi_ref):
        y_e = np.interp(np.log10(x_elpi_ref), np.log10(x_e), y_e)
        x_e = x_elpi_ref

    smps_rep.append(y_s)
    elpi_rep.append(y_e)

smps_stack = np.vstack(smps_rep)
elpi_stack = np.vstack(elpi_rep)

# Mean ± error across repeats
smps_mean, smps_err = mean_and_error(smps_stack, ERROR_MODE)
elpi_mean, elpi_err = mean_and_error(elpi_stack, ERROR_MODE)

# =========================
# SAVE THESIS TABLE METRICS (FROM MEAN DISTRIBUTIONS)
# =========================
smps_metrics = compute_metrics(x_smps_ref, smps_mean)
elpi_metrics = compute_metrics(x_elpi_ref, elpi_mean)

table = pd.DataFrame({
    "Instrument": ["SMPS", "ELPI"],
    "GMD (nm)": [smps_metrics["GMD_nm"], elpi_metrics["GMD_nm"]],
    "Mode diameter (nm)": [smps_metrics["Mode_nm"], elpi_metrics["Mode_nm"]],
    "GSD": [smps_metrics["GSD"], elpi_metrics["GSD"]],
    "Total concentration (a.u.)": [smps_metrics["Total_conc"], elpi_metrics["Total_conc"]],
})

# Note: "a.u." because totals are based on processed dN/dlogD and depend on instrument output units.
# If your inputs are true dN/dlogDp, this will represent number concentration.

os.makedirs(OUTDIR, exist_ok=True)
table_path = os.path.join(OUTDIR, TABLE_NAME)
table.to_excel(table_path, index=False)

print("\nTable 4.X metrics:")
print(table)
print(f"\nSaved table to: {table_path}")

# =========================
# PLOT FIGURE 4.1 (WITH ERROR BARS)
# =========================
# For plotting: normalise to compare shape (optional)
if NORMALISE_FOR_PLOT:
    smps_norm = np.nanmax(smps_mean) if np.nanmax(smps_mean) > 0 else 1.0
    elpi_norm = np.nanmax(elpi_mean) if np.nanmax(elpi_mean) > 0 else 1.0
else:
    smps_norm = 1.0
    elpi_norm = 1.0

smps_mean_p = smps_mean / smps_norm
smps_err_p  = smps_err / smps_norm

elpi_mean_p = elpi_mean / elpi_norm
elpi_err_p  = elpi_err / elpi_norm

mask_smps = (np.arange(len(x_smps_ref)) % PLOT_EVERY_NTH_BIN) == 0
mask_elpi = (np.arange(len(x_elpi_ref)) % PLOT_EVERY_NTH_BIN) == 0

fig, ax = plt.subplots(figsize=(7.2, 4.8))

ax.errorbar(
    x_smps_ref[mask_smps],
    smps_mean_p[mask_smps],
    yerr=smps_err_p[mask_smps],
    fmt="o-",
    linewidth=1.6,
    capsize=2.5,
    label=f"SMPS ($D_m$) mean ± {ERROR_MODE}"
)

ax.errorbar(
    x_elpi_ref[mask_elpi],
    elpi_mean_p[mask_elpi],
    yerr=elpi_err_p[mask_elpi],
    fmt="s-",
    linewidth=1.6,
    capsize=2.5,
    label=f"ELPI ($D_a$) mean ± {ERROR_MODE}"
)

ax.set_xscale("log")
ax.set_xlabel("Particle diameter (nm, log scale)")
ax.set_ylabel("Normalised distribution ($dN/d\\log D$)" if NORMALISE_FOR_PLOT else "Distribution ($dN/d\\log D$)")
ax.set_title("Figure 4.1. SMPS vs ELPI size distributions during NaCl aerosol generation (Repeat 1–3)")

ax.grid(True, which="both", linestyle="--", linewidth=0.6)
ax.legend(frameon=False)

plt.tight_layout()

png_path = os.path.join(OUTDIR, f"{SAVE_BASENAME}.png")
pdf_path = os.path.join(OUTDIR, f"{SAVE_BASENAME}.pdf")

plt.savefig(png_path, dpi=300)
plt.savefig(pdf_path)
plt.show()

print("\nSaved figure:")
print(png_path)
print(pdf_path)
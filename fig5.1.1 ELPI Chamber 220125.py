# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 20:44:40 2026

@author: papkp
"""

# ============================================================
# UPDATED ELPI ANALYSIS CODE
# 22012025.xlsx
#
# This version:
# 1. Reads the ELPI workbook
# 2. Extracts metadata and stage bins
# 3. Extracts the chamber data table
# 4. Uses the correct total concentration column
# 5. Calculates mean size distributions for 3 repeats
# 6. Excludes the final unstable ELPI bin (6285 nm) from plots
# 7. Produces:
#    - Figure 5.1.1 mean ± SD plot
#    - individual repeat plot
#    - total concentration time series
# ============================================================

import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# USER INPUT
# ============================================================
xlsx_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/22012025.xlsx"

out_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/OUTPUT")
out_dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# AMMONIUM SULPHATE REPEAT WINDOWS
# Adjust later if needed
# ============================================================
repeat_windows = {
    "R1": ("2025-01-22 13:19:30", "2025-01-22 13:24:30"),
    "R2": ("2025-01-22 13:27:30", "2025-01-22 13:29:30"),
    "R3": ("2025-01-22 13:37:00", "2025-01-22 13:40:00"),
}

# ============================================================
# HELPERS
# ============================================================
def load_sheet(xlsx_path):
    xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
    sheet = xl.sheet_names[0]
    df = pd.read_excel(xlsx_path, sheet_name=sheet, header=None, engine="openpyxl", dtype=str)
    return df, sheet

def row_as_text(df, r):
    vals = []
    for v in df.iloc[r, :].tolist():
        if pd.notna(v):
            s = str(v).strip()
            if s != "":
                vals.append(s)
    return " ".join(vals)

def find_row_with_substring(df, substring):
    substring = substring.lower()
    for r in range(df.shape[0]):
        txt = row_as_text(df, r).lower()
        if substring in txt:
            return r
    return None

def extract_key_value_from_sheet(df, key):
    key_low = key.lower()
    for r in range(df.shape[0]):
        row_vals = [str(v).strip() for v in df.iloc[r, :].tolist() if pd.notna(v) and str(v).strip() != ""]
        if not row_vals:
            continue

        for cell in row_vals:
            low = cell.lower()
            if low.startswith(key_low + "="):
                return cell.split("=", 1)[1].strip()

        for i, cell in enumerate(row_vals):
            if cell.lower() == key_low and i + 1 < len(row_vals):
                return row_vals[i + 1]
    return None

def parse_diameters_um(df):
    row_idx = find_row_with_substring(df, "CalculatedDi(um)")
    if row_idx is None:
        raise ValueError("Could not find CalculatedDi(um) in sheet.")

    row_vals = [str(v).strip() for v in df.iloc[row_idx, :].tolist() if pd.notna(v) and str(v).strip() != ""]
    row_text = " ".join(row_vals)

    m = re.search(r"CalculatedDi\(um\)\s*=\s*(.*)", row_text, flags=re.IGNORECASE)
    if m:
        tail = m.group(1)
        nums = re.findall(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?", tail)
        vals = [float(x) for x in nums]
        if len(vals) >= 5:
            return np.array(vals, dtype=float)

    vals = []
    started = False
    for cell in row_vals:
        if "CalculatedDi(um)" in cell:
            started = True
            part = cell.split("=", 1)[1] if "=" in cell else ""
            nums = re.findall(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?", part)
            vals.extend([float(x) for x in nums])
            continue

        if started:
            nums = re.findall(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?", cell)
            if nums:
                vals.extend([float(x) for x in nums])

    if len(vals) >= 5:
        return np.array(vals, dtype=float)

    raise ValueError("Could not parse CalculatedDi(um) values.")

def find_first_data_row(df):
    for r in range(df.shape[0]):
        v = df.iat[r, 0]
        if pd.isna(v):
            continue
        s = str(v).strip()
        if re.match(r"^\d{4}[/-]\d{2}[/-]\d{2}\s+\d{2}:\d{2}:\d{2}$", s):
            return r
    raise ValueError("Could not find first ELPI data row.")

def clean_numeric(series):
    return pd.to_numeric(series, errors="coerce")

def build_tidy_elpi(df_data, diam_um):
    diam_nm = diam_um * 1000.0

    dt = pd.to_datetime(df_data.iloc[:, 0], errors="coerce")
    keep = dt.notna()
    data = df_data.loc[keep, :].copy()
    data.iloc[:, 0] = pd.to_datetime(data.iloc[:, 0], errors="coerce")

    n_bins = len(diam_nm)
    stage_start = 20
    stage_end = stage_start + n_bins

    stage_df = data.iloc[:, stage_start:stage_end].apply(clean_numeric)
    stage_df.columns = [f"{d:.1f}" for d in diam_nm]

    tidy = pd.DataFrame({"DateTime": data.iloc[:, 0]})
    for c in stage_df.columns:
        tidy[c] = stage_df[c]

    # Correct total concentration column
    if data.shape[1] > 32:
        tidy["Total"] = clean_numeric(data.iloc[:, 32])
    else:
        tidy["Total"] = np.nan

    tidy = tidy.dropna(subset=["DateTime"]).reset_index(drop=True)
    return tidy, diam_nm

def summarise_by_repeat(df_tidy, diam_nm, repeat_windows):
    bin_cols = [f"{d:.1f}" for d in diam_nm]
    rows = []

    for rep, (start, end) in repeat_windows.items():
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)
        seg = df_tidy[(df_tidy["DateTime"] >= start) & (df_tidy["DateTime"] <= end)].copy()

        if seg.empty:
            print(f"Warning: no data for {rep}")
            continue

        row = {"Repeat": rep}
        row.update(seg[bin_cols].mean(axis=0).to_dict())
        rows.append(row)

    rep_df = pd.DataFrame(rows)
    if rep_df.empty:
        raise ValueError("No repeat windows matched the data.")

    mean_vals = rep_df[bin_cols].mean(axis=0)
    std_vals = rep_df[bin_cols].std(axis=0)

    summary = pd.DataFrame({
        "Diameter_nm": diam_nm,
        "Mean_dW_dlogDp": mean_vals.values,
        "SD_dW_dlogDp": std_vals.values
    })

    return rep_df, summary

def plot_repeat_mean_sd(summary_df, out_png):
    x = summary_df["Diameter_nm"].values
    y = summary_df["Mean_dW_dlogDp"].values
    yerr = summary_df["SD_dW_dlogDp"].values

    plt.figure(figsize=(8, 5.5))
    plt.errorbar(x, y, yerr=yerr, marker="o", linewidth=2, capsize=4)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Aerodynamic diameter (nm)")
    plt.ylabel("dW/dlogDp")
    plt.title("Figure 5.1.1. Mean ELPI aerodynamic size distribution for ammonium sulphate (mean ± SD, n=3)")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(out_png, dpi=600, bbox_inches="tight")
    plt.show()

def plot_individual_repeats(rep_df, diam_nm, out_png):
    plt.figure(figsize=(8, 5.5))
    for _, row in rep_df.iterrows():
        y = [row[f"{d:.1f}"] for d in diam_nm]
        plt.plot(diam_nm, y, marker="o", linewidth=1.8, label=row["Repeat"])

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Aerodynamic diameter (nm)")
    plt.ylabel("dW/dlogDp")
    plt.title("Individual repeat ELPI size distributions for ammonium sulphate")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=600, bbox_inches="tight")
    plt.show()

def plot_total_time_series(df_tidy, repeat_windows, out_png):
    plt.figure(figsize=(10, 4.8))
    plt.plot(df_tidy["DateTime"], df_tidy["Total"], linewidth=1.5)

    for rep, (start, end) in repeat_windows.items():
        plt.axvspan(pd.Timestamp(start), pd.Timestamp(end), alpha=0.15, label=rep)

    plt.xlabel("Time")
    plt.ylabel("Total concentration")
    plt.title("ELPI total concentration time series for ammonium sulphate experiment")
    plt.grid(True, linestyle="--", linewidth=0.5)

    handles, labels = plt.gca().get_legend_handles_labels()
    seen = set()
    h2, l2 = [], []
    for h, l in zip(handles, labels):
        if l not in seen:
            h2.append(h)
            l2.append(l)
            seen.add(l)
    if h2:
        plt.legend(h2, l2)

    plt.tight_layout()
    plt.savefig(out_png, dpi=600, bbox_inches="tight")
    plt.show()

# ============================================================
# MAIN
# ============================================================
df_all, sheet = load_sheet(xlsx_file)
print(f"Sheet used: {sheet}")
print("Workbook shape:", df_all.shape)

calc_type_val = extract_key_value_from_sheet(df_all, "CalculatedType")
flow_val = extract_key_value_from_sheet(df_all, "FlowRate(lpm)")
diam_um = parse_diameters_um(df_all)

print("CalculatedType:", calc_type_val)
print("FlowRate(lpm):", flow_val)
print("CalculatedDi(um):", diam_um)

data_start = find_first_data_row(df_all)
print("First data row:", data_start)

df_data = df_all.iloc[data_start:, :].reset_index(drop=True)
df_tidy, diam_nm = build_tidy_elpi(df_data, diam_um)

print("\nTidy data preview:")
print(df_tidy.head())
print("\nDate range:", df_tidy["DateTime"].min(), "to", df_tidy["DateTime"].max())

# Save tidy data
df_tidy.to_csv(out_dir / "ELPI_tidy_data.csv", index=False)

# Repeat-based analysis
rep_df, repeat_summary = summarise_by_repeat(df_tidy, diam_nm, repeat_windows)

# ------------------------------------------------------------
# Remove final unstable bin from plots
# ------------------------------------------------------------
repeat_summary_plot = repeat_summary[repeat_summary["Diameter_nm"] < 5000].copy()
diam_nm_plot = repeat_summary_plot["Diameter_nm"].values

# Save outputs
rep_df.to_csv(out_dir / "ELPI_repeat_means.csv", index=False)
repeat_summary.to_csv(out_dir / "ELPI_repeat_summary_mean_sd.csv", index=False)
repeat_summary_plot.to_csv(out_dir / "ELPI_repeat_summary_mean_sd_plotbins.csv", index=False)

# Plots
plot_repeat_mean_sd(
    repeat_summary_plot,
    out_dir / "Figure_5_1_1_ELPI_repeat_mean_sd.png"
)

plot_individual_repeats(
    rep_df,
    diam_nm_plot,
    out_dir / "ELPI_individual_repeats.png"
)

plot_total_time_series(
    df_tidy,
    repeat_windows,
    out_dir / "ELPI_total_time_series.png"
)

print("\nDONE")
print(f"Outputs saved in: {out_dir}")
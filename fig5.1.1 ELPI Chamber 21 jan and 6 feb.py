# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 22:55:00 2026

@author: papkp
"""

import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ======================================================
# FILE PATHS
# ======================================================
file_21 = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/21_01_25_ UoB_chamber_water.txt"
file_060224 = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/ELPI 060224.xlsx"

output_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 5.1.1 ELPI CHAMBER/COMPARISON_21JAN_AND_060224")
output_dir.mkdir(parents=True, exist_ok=True)

# ======================================================
# 21 JAN WINDOWS
# ======================================================
windows_21 = {
    "Water": {
        "R1": ("2025-01-21 14:59:00", "2025-01-21 15:00:45"),
        "R2": ("2025-01-21 15:08:51", "2025-01-21 15:10:51"),
        "R3": ("2025-01-21 15:16:20", "2025-01-21 15:18:20"),
    },
    "Sodium iodide": {
        "R1": ("2025-01-21 15:37:00", "2025-01-21 15:39:00"),
        "R2": ("2025-01-21 15:44:20", "2025-01-21 15:46:20"),
        "R3": ("2025-01-21 15:51:30", "2025-01-21 15:53:30"),
    },
    "NaCl (21 Jan)": {
        # R1 intentionally excluded
        "R2": ("2025-01-21 16:17:00", "2025-01-21 16:19:00"),
        "R3": ("2025-01-21 16:24:00", "2025-01-21 16:26:00"),
        "R4": ("2025-01-21 16:31:00", "2025-01-21 16:33:00"),
    }
}

# ======================================================
# 06 FEB WINDOWS
# ======================================================
windows_060224 = {
    "NaCl (6 Feb)": {
        "R1": ("2024-02-06 15:00:00", "2024-02-06 15:33:00"),
        "R2": ("2024-02-06 15:34:00", "2024-02-06 15:51:00"),
        "R3": ("2024-02-06 15:53:00", "2024-02-06 16:05:00"),
    },
    "Sucrose": {
        "R1": ("2024-02-06 16:15:00", "2024-02-06 16:30:00"),
        "R2": ("2024-02-06 16:31:00", "2024-02-06 16:46:00"),
        "R3": ("2024-02-06 16:48:00", "2024-02-06 17:03:00"),
    },
    "KCl": {
        "R1": ("2024-02-06 17:12:00", "2024-02-06 17:27:00"),
        "R2": ("2024-02-06 17:29:00", "2024-02-06 17:44:00"),
        "R3": ("2024-02-06 17:45:00", "2024-02-06 18:00:00"),
    }
}

# ======================================================
# HELPERS
# ======================================================
def parse_elpi_txt(file_path):
    """
    Parse ELPI raw txt export into a dataframe with:
    stage bins as columns, plus 'time' and 'Total'
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    diam_um = None
    data_start = None
    calc_type = None
    calc_moment = None
    date_str = None

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith("Date="):
            date_str = line.split("=", 1)[1].strip()

        elif line.startswith("CalculatedType="):
            calc_type = line.split("=", 1)[1].strip()

        elif line.startswith("CalculatedMoment="):
            calc_moment = line.split("=", 1)[1].strip()

        elif line.startswith("CalculatedDi(um)="):
            vals = line.split("=", 1)[1].strip().split(",")
            diam_um = np.array([float(v) for v in vals], dtype=float)

        elif line == "[Data]":
            data_start = i + 1
            break

    if diam_um is None:
        raise ValueError(f"Diameter bins not found in {file_path}")
    if data_start is None:
        raise ValueError(f"[Data] section not found in {file_path}")

    data_lines = [l.strip() for l in lines[data_start:] if l.strip()]
    df = pd.read_csv(io.StringIO("\n".join(data_lines)), header=None)

    df[0] = pd.to_datetime(df[0], errors="coerce")
    df = df.dropna(subset=[0]).reset_index(drop=True)

    diam_nm = diam_um * 1000.0

    stage_start = 20
    stage_end = stage_start + len(diam_nm)

    stage_df = df.iloc[:, stage_start:stage_end].apply(pd.to_numeric, errors="coerce")
    stage_df.columns = diam_nm

    # Total concentration value column in ELPI txt exports used here
    total_col = pd.to_numeric(df.iloc[:, 32], errors="coerce")

    stage_df["time"] = df[0]
    stage_df["Total"] = total_col

    meta = {
        "date": date_str,
        "CalculatedType": calc_type,
        "CalculatedMoment": calc_moment,
        "diam_nm": diam_nm,
        "source": file_path,
    }

    return stage_df, meta


def parse_elpi_060224_xlsx(file_path):
    """
    Parse ELPI 060224 workbook using metadata rows inside the sheet,
    not the DataFrame column headers.
    """
    xl = pd.ExcelFile(file_path)
    sheet_name = "ELPI 060224" if "ELPI 060224" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, dtype=str)

    # ------------------------------------------------------
    # Find CalculatedDi row
    # ------------------------------------------------------
    diam_row = None
    for i in range(len(df)):
        row_text = " ".join(df.iloc[i].dropna().astype(str).tolist())
        if "CalculatedDi" in row_text:
            diam_row = i
            break

    if diam_row is None:
        raise ValueError("Could not find CalculatedDi row in ELPI 060224.xlsx")

    row_vals = [str(v).strip() for v in df.iloc[diam_row].tolist() if pd.notna(v) and str(v).strip() != ""]
    row_text = " ".join(row_vals)

    diam_vals = re.findall(r"\d+\.\d+", row_text)
    diam_um = np.array([float(v) for v in diam_vals], dtype=float)
    diam_nm = diam_um * 1000.0

    # ------------------------------------------------------
    # Find first actual data row with full datetime
    # ------------------------------------------------------
    data_start = None
    for i in range(len(df)):
        val = str(df.iloc[i, 0]).strip()
        if re.match(r"^\d{4}[/-]\d{2}[/-]\d{2}\s+\d{2}:\d{2}:\d{2}$", val):
            data_start = i
            break

    if data_start is None:
        raise ValueError("Could not find first ELPI datetime row in ELPI 060224.xlsx")

    df_data = df.iloc[data_start:].copy().reset_index(drop=True)

    # Parse datetime
    df_data.iloc[:, 0] = pd.to_datetime(df_data.iloc[:, 0], errors="coerce")
    df_data = df_data.dropna(subset=[df_data.columns[0]]).copy().reset_index(drop=True)

    # ------------------------------------------------------
    # Standard ELPI stage positions
    # ------------------------------------------------------
    stage_start = 20
    stage_end = stage_start + len(diam_nm)

    if df_data.shape[1] < stage_end:
        raise ValueError(
            f"ELPI 060224.xlsx has only {df_data.shape[1]} columns after data start; "
            f"expected at least {stage_end}."
        )

    stage_df = df_data.iloc[:, stage_start:stage_end].apply(pd.to_numeric, errors="coerce")
    stage_df.columns = diam_nm

    # Total concentration column if present
    if df_data.shape[1] > 32:
        total_col = pd.to_numeric(df_data.iloc[:, 32], errors="coerce")
    else:
        total_col = pd.Series(np.nan, index=df_data.index)

    stage_df["time"] = df_data.iloc[:, 0].values
    stage_df["Total"] = total_col.values

    meta = {
        "date": "2024-02-06",
        "CalculatedType": "from workbook metadata",
        "CalculatedMoment": "from workbook metadata",
        "diam_nm": diam_nm,
        "source": file_path,
        "sheet": sheet_name,
    }

    return stage_df, meta


def summarise_repeats(stage_df, diam_nm, rep_windows, min_bin_nm=38.9, max_bin_nm=5000, min_repeats_required=2):
    """
    Build repeat means and summary mean±SD.
    Drops unstable smallest and largest bins by default.
    """
    plot_bins = diam_nm[(diam_nm >= min_bin_nm) & (diam_nm < max_bin_nm)]
    repeat_means = []

    for rep, (start, end) in rep_windows.items():
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)

        seg = stage_df[
            (stage_df["time"] >= start) &
            (stage_df["time"] <= end)
        ].copy()

        if seg.empty:
            print(f"Warning: no data for {rep} between {start} and {end}")
            continue

        rep_mean = seg[plot_bins].mean(axis=0)
        rep_mean.name = rep
        repeat_means.append(rep_mean)

    if len(repeat_means) < min_repeats_required:
        print(f"Skipping because only {len(repeat_means)} repeat(s) were found.")
        return None, None, plot_bins

    rep_df = pd.DataFrame(repeat_means)

    summary_df = pd.DataFrame({
        "diameter_nm": plot_bins,
        "mean": rep_df.mean(axis=0).values,
        "sd": rep_df.std(axis=0).values
    })

    return rep_df, summary_df, plot_bins


def normalise_summary(summary_df):
    """
    Peak-normalise mean and SD.
    """
    out = summary_df.copy()
    peak = out["mean"].max()

    if pd.isna(peak) or peak <= 0:
        out["mean_norm"] = np.nan
        out["sd_norm"] = np.nan
    else:
        out["mean_norm"] = out["mean"] / peak
        out["sd_norm"] = out["sd"] / peak

    return out


def interpolate_summary(summary_df, common_grid):
    """
    Interpolate normalised summary to a common diameter grid in log space.
    """
    x = summary_df["diameter_nm"].values
    y = summary_df["mean_norm"].values
    ysd = summary_df["sd_norm"].values

    lx = np.log10(x)
    lg = np.log10(common_grid)

    y_interp = np.interp(lg, lx, y, left=np.nan, right=np.nan)
    ysd_interp = np.interp(lg, lx, ysd, left=np.nan, right=np.nan)

    return pd.DataFrame({
        "diameter_nm": common_grid,
        "mean_norm": y_interp,
        "sd_norm": ysd_interp
    })


def plot_day_absolute(results_dict, title, out_png):
    plt.figure(figsize=(9, 6))

    plotted_any = False

    for aerosol, df in results_dict.items():
        plot_df = df.copy()

        mask = (
            np.isfinite(plot_df["diameter_nm"]) &
            np.isfinite(plot_df["mean"]) &
            np.isfinite(plot_df["sd"]) &
            (plot_df["diameter_nm"] > 0) &
            (plot_df["mean"] > 0)
        )
        plot_df = plot_df.loc[mask]

        if plot_df.empty:
            print(f"Skipping plot for {aerosol}: no positive finite values.")
            continue

        plt.errorbar(
            plot_df["diameter_nm"],
            plot_df["mean"],
            yerr=plot_df["sd"],
            marker="o",
            linewidth=2,
            capsize=3,
            label=aerosol
        )
        plotted_any = True

    if not plotted_any:
        print(f"No valid positive data available for plot: {title}")
        plt.close()
        return

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Aerodynamic diameter (nm)")
    plt.ylabel("dW/dlogDp")
    plt.title(title)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=600, bbox_inches="tight")
    plt.show()


def plot_cross_normalised(results_dict, title, out_png):
    plt.figure(figsize=(9, 6))

    plotted_any = False

    for aerosol, df in results_dict.items():
        plot_df = df.copy()

        mask = (
            np.isfinite(plot_df["diameter_nm"]) &
            np.isfinite(plot_df["mean_norm"]) &
            np.isfinite(plot_df["sd_norm"]) &
            (plot_df["diameter_nm"] > 0) &
            (plot_df["mean_norm"] > 0)
        )
        plot_df = plot_df.loc[mask]

        if plot_df.empty:
            print(f"Skipping normalised plot for {aerosol}: no positive finite values.")
            continue

        plt.errorbar(
            plot_df["diameter_nm"],
            plot_df["mean_norm"],
            yerr=plot_df["sd_norm"],
            marker="o",
            linewidth=2,
            capsize=3,
            label=aerosol
        )
        plotted_any = True

    if not plotted_any:
        print(f"No valid positive data available for plot: {title}")
        plt.close()
        return

    plt.xscale("log")
    plt.xlabel("Aerodynamic diameter (nm)")
    plt.ylabel("Normalised dW/dlogDp")
    plt.title(title)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=600, bbox_inches="tight")
    plt.show()


# ======================================================
# LOAD DATASETS
# ======================================================
stage21, meta21 = parse_elpi_txt(file_21)
stage060224, meta060224 = parse_elpi_060224_xlsx(file_060224)

print("\n================ 21 JAN ================")
print(meta21)
print("Time range:", stage21["time"].min(), "to", stage21["time"].max())
print(stage21.head())

print("\n================ 06 FEB ================")
print(meta060224)
print("Time range:", stage060224["time"].min(), "to", stage060224["time"].max())
print(stage060224.head())

# ======================================================
# ANALYSE 21 JAN
# ======================================================
results_21 = {}
for aerosol, rep_windows in windows_21.items():
    print(f"\nProcessing 21 Jan: {aerosol}")
    rep_df, summary_df, _ = summarise_repeats(stage21, meta21["diam_nm"], rep_windows)

    if summary_df is None:
        print(f"Skipping {aerosol} (insufficient matching data).")
        continue

    results_21[aerosol] = summary_df
    rep_df.to_csv(output_dir / f"{aerosol.replace(' ', '_')}_21Jan_repeat_means.csv", index=True)
    summary_df.to_csv(output_dir / f"{aerosol.replace(' ', '_')}_21Jan_summary.csv", index=False)

# ======================================================
# ANALYSE 06 FEB
# ======================================================
results_060224 = {}
for aerosol, rep_windows in windows_060224.items():
    print(f"\nProcessing 06 Feb: {aerosol}")
    rep_df, summary_df, _ = summarise_repeats(stage060224, meta060224["diam_nm"], rep_windows)

    if summary_df is None:
        print(f"Skipping {aerosol} (insufficient matching data).")
        continue

    results_060224[aerosol] = summary_df
    rep_df.to_csv(output_dir / f"{aerosol.replace(' ', '_')}_060224_repeat_means.csv", index=True)
    summary_df.to_csv(output_dir / f"{aerosol.replace(' ', '_')}_060224_summary.csv", index=False)

# ======================================================
# ABSOLUTE COMPARISON BY DAY
# ======================================================
if results_21:
    plot_day_absolute(
        results_21,
        "ELPI aerodynamic size distributions for chamber aerosols (21 Jan)",
        output_dir / "ELPI_21Jan_absolute_comparison.png"
    )

if results_060224:
    plot_day_absolute(
        results_060224,
        "ELPI aerodynamic size distributions for chamber aerosols (06 Feb)",
        output_dir / "ELPI_060224_absolute_comparison.png"
    )

# ======================================================
# NORMALISED CROSS-DAY COMPARISON
# ======================================================
common_grid = np.array([38.9, 70.9, 120.1, 201.5, 315.9, 482.9, 761.3, 1230.9, 1955.5, 3088.1])

norm_results = {}

for aerosol, df in results_21.items():
    norm_df = normalise_summary(df)
    interp_df = interpolate_summary(norm_df, common_grid)
    norm_results[aerosol] = interp_df
    interp_df.to_csv(output_dir / f"{aerosol.replace(' ', '_')}_21Jan_normalised.csv", index=False)

for aerosol, df in results_060224.items():
    norm_df = normalise_summary(df)
    interp_df = interpolate_summary(norm_df, common_grid)
    norm_results[aerosol] = interp_df
    interp_df.to_csv(output_dir / f"{aerosol.replace(' ', '_')}_060224_normalised.csv", index=False)

if norm_results:
    plot_cross_normalised(
        norm_results,
        "Normalised comparison of ELPI aerodynamic size distributions",
        output_dir / "ELPI_21Jan_and_060224_normalised_comparison.png"
    )

# ======================================================
# SAVE COMBINED TABLES
# ======================================================
abs_tables = []
for aerosol, df in results_21.items():
    tmp = df.copy()
    tmp["Aerosol"] = aerosol
    tmp["Dataset"] = "21 Jan"
    abs_tables.append(tmp)

for aerosol, df in results_060224.items():
    tmp = df.copy()
    tmp["Aerosol"] = aerosol
    tmp["Dataset"] = "06 Feb"
    abs_tables.append(tmp)

if abs_tables:
    abs_tables = pd.concat(abs_tables, ignore_index=True)
    abs_tables.to_csv(output_dir / "ELPI_absolute_summary_by_dataset.csv", index=False)

norm_tables = []
for aerosol, df in norm_results.items():
    tmp = df.copy()
    tmp["Aerosol"] = aerosol
    norm_tables.append(tmp)

if norm_tables:
    norm_tables = pd.concat(norm_tables, ignore_index=True)
    norm_tables.to_csv(output_dir / "ELPI_normalised_summary_combined.csv", index=False)

print("\nDONE")
print(f"Outputs saved in: {output_dir}")
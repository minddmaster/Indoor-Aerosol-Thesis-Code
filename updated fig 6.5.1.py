# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 18:31:38 2026

@author: papkp
"""

# ============================
# SECTION 6.5 ONLY
# STIR FRY ANALYSIS
# ============================

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ============================
# FILE PATHS
# ============================

BASE_DIR = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1"

CPC_BATH_FILE = os.path.join(BASE_DIR, "CPC DAY 4 OUTSIDE BATH_EXCEL.csv")
CPC_BED_FILE  = os.path.join(BASE_DIR, "cpc012_Master Bedroom_Day4.csv")
ELPI_FILE     = os.path.join(BASE_DIR, "day4 elpi data.xlsx")
SMPS_FILE     = os.path.join(BASE_DIR, "DAY4 SMPS DATA_COM32.xlsx")

OUTPUT_DIR = os.path.join(BASE_DIR, "stir_fry_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================
# STIR FRY TIME WINDOWS
# ============================

EXP7_START = pd.to_datetime("2025-02-27 16:09:30")   # no fan
EXP7_END   = pd.to_datetime("2025-02-27 16:40:30")

EXP8_START = pd.to_datetime("2025-02-27 16:48:50")   # with fan
EXP8_END   = pd.to_datetime("2025-02-27 17:18:50")

# Approximate active cooking periods
EXP7_COOK_START = pd.to_datetime("2025-02-27 16:13:30")
EXP7_COOK_END   = pd.to_datetime("2025-02-27 16:25:00")

EXP8_COOK_START = pd.to_datetime("2025-02-27 16:52:50")
EXP8_COOK_END   = pd.to_datetime("2025-02-27 17:04:20")

# ============================
# HELPERS
# ============================

def looks_like_time_string(s):
    s = str(s).strip()
    return bool(re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", s))

def subset(df, start, end):
    return df[(df["Time"] >= start) & (df["Time"] <= end)].copy()

def get_peak(df, col):
    if df.empty:
        return np.nan
    return df[col].max()

# ============================
# CPC LOADER
# ============================

def load_cpc_csv(path, forced_date="2025-02-27", value_name="Conc"):
    """
    Reads messy CPC csv files by forcing header=None and detecting the
    first real data row. This avoids using first data row as column names.
    """
    encodings = ["utf-8", "latin1", "cp1252", "utf-16"]
    last_error = None

    for enc in encodings:
        try:
            raw = pd.read_csv(path, encoding=enc, header=None, dtype=str, on_bad_lines="skip")
            # find first row that looks like data: first cell resembles time and another cell numeric
            start_idx = None
            conc_idx = None

            for i in range(len(raw)):
                row = raw.iloc[i].tolist()
                if len(row) < 2:
                    continue
                first = str(row[0]).strip()
                if not looks_like_time_string(first):
                    continue

                # find numeric concentration column in this row
                for j in range(1, len(row)):
                    val = pd.to_numeric(str(row[j]).strip(), errors="coerce")
                    if pd.notna(val):
                        start_idx = i
                        conc_idx = j
                        break

                if start_idx is not None:
                    break

            if start_idx is None:
                continue

            df = raw.iloc[start_idx:, [0, conc_idx]].copy()
            df.columns = ["TimeRaw", value_name]

            parsed = pd.to_datetime(df["TimeRaw"].astype(str).str.strip(), format="%H:%M:%S", errors="coerce")
            if parsed.notna().sum() < 5:
                parsed = pd.to_datetime(df["TimeRaw"].astype(str).str.strip(), format="%H:%M", errors="coerce")

            if parsed.notna().sum() < 5:
                continue

            out = pd.DataFrame()
            out["Time"] = pd.to_datetime(
                forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
                errors="coerce"
            )
            out[value_name] = pd.to_numeric(df[value_name], errors="coerce")
            out = out.dropna(subset=["Time", value_name]).sort_values("Time").reset_index(drop=True)

            if len(out) < 5:
                continue

            print(f"Loaded {os.path.basename(path)} | encoding={enc}, data_row={start_idx}, conc_col={conc_idx}")
            return out

        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to load CPC file {os.path.basename(path)}. Last error: {last_error}")

# ============================
# SMPS LOADER
# ============================

def load_smps(path, forced_date="2025-02-27"):
    xls = pd.ExcelFile(path)
    sheet = xls.sheet_names[0]
    skiprows_options = [0, 10, 20, 30, 40]
    last_error = None

    for skip in skiprows_options:
        try:
            df = pd.read_excel(path, sheet_name=sheet, skiprows=skip)
            df.columns = [str(c).strip() for c in df.columns]

            time_col = None
            for c in df.columns:
                c_str = str(c).lower().strip()
                if "corrected time" in c_str or c_str == "time" or "time" in c_str:
                    time_col = c
                    break

            if time_col is None:
                continue

            parsed = pd.to_datetime(df[time_col], errors="coerce")
            if parsed.notna().sum() == 0:
                parsed = pd.to_datetime(
                    forced_date + " " + df[time_col].astype(str).str.strip(),
                    errors="coerce"
                )

            if parsed.notna().sum() < 5:
                continue

            size_cols = []
            for c in df.columns:
                if c == time_col:
                    continue
                try:
                    float(str(c).strip())
                    size_cols.append(c)
                except:
                    pass

            total_col = None
            for c in df.columns:
                c_str = str(c).lower().strip()
                if "total" in c_str and "conc" in c_str:
                    total_col = c
                    break

            out = pd.DataFrame()
            out["Time"] = pd.to_datetime(
                forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
                errors="coerce"
            )

            if total_col is not None:
                out["SMPS_Total"] = pd.to_numeric(df[total_col], errors="coerce")
            else:
                if len(size_cols) == 0:
                    continue
                out["SMPS_Total"] = df[size_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)

            out = out.dropna(subset=["Time", "SMPS_Total"]).sort_values("Time").reset_index(drop=True)

            if len(out) < 5:
                continue

            print(f"Loaded {os.path.basename(path)} using skiprows={skip}")
            return out

        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to load SMPS file {os.path.basename(path)}. Last error: {last_error}")

# ============================
# ELPI LOADER
# ============================

def load_elpi(path, forced_date="2025-02-27"):
    """
    Robust ELPI loader:
    - tries multiple skiprows
    - accepts first column as time
    - uses col 32 if available
    - else uses first numeric column after time with enough data
    """
    skiprows_options = [40, 35, 30, 45, 50, 25, 20]
    last_error = None

    for skip in skiprows_options:
        try:
            df = pd.read_excel(path, skiprows=skip, header=None)

            if df.shape[1] < 2:
                continue

            time_raw = df.iloc[:, 0].astype(str).str.strip()

            parsed = pd.to_datetime(time_raw, format="%H:%M:%S", errors="coerce")
            if parsed.notna().sum() < 5:
                parsed = pd.to_datetime(time_raw, format="%H:%M", errors="coerce")

            if parsed.notna().sum() < 5:
                extracted = time_raw.str.extract(r"(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})")[0]
                parsed = pd.to_datetime(extracted, format="%H:%M:%S", errors="coerce")
                if parsed.notna().sum() < 5:
                    parsed = pd.to_datetime(extracted, format="%H:%M", errors="coerce")

            if parsed.notna().sum() < 5:
                continue

            # choose total concentration column
            conc_idx = None

            if df.shape[1] > 32:
                test = pd.to_numeric(df.iloc[:, 32], errors="coerce")
                if test.notna().sum() > 5:
                    conc_idx = 32

            if conc_idx is None:
                for j in range(1, df.shape[1]):
                    test = pd.to_numeric(df.iloc[:, j], errors="coerce")
                    if test.notna().sum() > 20:
                        conc_idx = j
                        break

            if conc_idx is None:
                continue

            out = pd.DataFrame()
            out["Time"] = pd.to_datetime(
                forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
                errors="coerce"
            )
            out["ELPI_Total"] = pd.to_numeric(df.iloc[:, conc_idx], errors="coerce")
            out = out.dropna(subset=["Time", "ELPI_Total"]).sort_values("Time").reset_index(drop=True)

            if len(out) < 5:
                continue

            print(f"Loaded {os.path.basename(path)} | skiprows={skip}, conc_col={conc_idx}")
            return out

        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to load ELPI file {os.path.basename(path)}. Last error: {last_error}")

# ============================
# LOAD DATA
# ============================

print("Loading data...")
cpc_bath = load_cpc_csv(CPC_BATH_FILE, value_name="CPC_Bath")
cpc_bed  = load_cpc_csv(CPC_BED_FILE, value_name="CPC_Bed")
smps     = load_smps(SMPS_FILE)
elpi     = load_elpi(ELPI_FILE)

# ============================
# BUILD SUBSETS
# ============================

exp7 = {
    "bath": subset(cpc_bath, EXP7_START, EXP7_END),
    "bed":  subset(cpc_bed,  EXP7_START, EXP7_END),
    "smps": subset(smps,     EXP7_START, EXP7_END),
    "elpi": subset(elpi,     EXP7_START, EXP7_END),
}

exp8 = {
    "bath": subset(cpc_bath, EXP8_START, EXP8_END),
    "bed":  subset(cpc_bed,  EXP8_START, EXP8_END),
    "smps": subset(smps,     EXP8_START, EXP8_END),
    "elpi": subset(elpi,     EXP8_START, EXP8_END),
}

# ============================
# SUMMARY TABLE
# ============================

summary_df = pd.DataFrame([
    {
        "Condition": "No Fan",
        "Experiment": "Exp7",
        "CPC_Bath_peak": get_peak(exp7["bath"], "CPC_Bath"),
        "CPC_Bed_peak": get_peak(exp7["bed"], "CPC_Bed"),
        "SMPS_peak": get_peak(exp7["smps"], "SMPS_Total"),
        "ELPI_peak": get_peak(exp7["elpi"], "ELPI_Total"),
    },
    {
        "Condition": "Fan",
        "Experiment": "Exp8",
        "CPC_Bath_peak": get_peak(exp8["bath"], "CPC_Bath"),
        "CPC_Bed_peak": get_peak(exp8["bed"], "CPC_Bed"),
        "SMPS_peak": get_peak(exp8["smps"], "SMPS_Total"),
        "ELPI_peak": get_peak(exp8["elpi"], "ELPI_Total"),
    }
])

summary_path = os.path.join(OUTPUT_DIR, "Table_6_5_1_stir_fry_summary.csv")
summary_df.to_csv(summary_path, index=False)

print("\nSummary table:")
print(summary_df)

# ============================
# FIGURE 6.5.1
# ============================

plot_start = EXP7_START
plot_end = EXP8_END

bath_plot = subset(cpc_bath, plot_start, plot_end)
bed_plot  = subset(cpc_bed,  plot_start, plot_end)
smps_plot = subset(smps,     plot_start, plot_end)
elpi_plot = subset(elpi,     plot_start, plot_end)

for df, col, newcol in [
    (bath_plot, "CPC_Bath", "CPC_Bath_smooth"),
    (bed_plot,  "CPC_Bed",  "CPC_Bed_smooth"),
    (smps_plot, "SMPS_Total", "SMPS_smooth"),
    (elpi_plot, "ELPI_Total", "ELPI_smooth"),
]:
    df[newcol] = df[col].rolling(3, center=True, min_periods=1).mean()

plt.figure(figsize=(12, 6))

plt.plot(smps_plot["Time"], smps_plot["SMPS_smooth"], label="SMPS (Kitchen)", linewidth=2.2)
plt.plot(elpi_plot["Time"], elpi_plot["ELPI_smooth"], label="ELPI (Kitchen)", linewidth=1.8, linestyle=":")
plt.plot(bed_plot["Time"], bed_plot["CPC_Bed_smooth"], label="CPC Bedroom", linewidth=1.5, linestyle="--")
plt.plot(bath_plot["Time"], bath_plot["CPC_Bath_smooth"], label="CPC Bathroom", linewidth=1.5, linestyle="-.")

plt.axvspan(EXP7_START, EXP7_END, color="grey", alpha=0.18, label="Exp7 No Fan")
plt.axvspan(EXP8_START, EXP8_END, color="orange", alpha=0.18, label="Exp8 Fan")

plt.axvspan(EXP7_COOK_START, EXP7_COOK_END, color="grey", alpha=0.30)
plt.axvspan(EXP8_COOK_START, EXP8_COOK_END, color="orange", alpha=0.30)

plt.xlabel("Time")
plt.ylabel("Particle number concentration (particles cm$^{-3}$)")
plt.title("Figure 6.5.1. Stir-fry aerosol emissions with and without extraction fan")
plt.yscale("log")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()
plt.tight_layout()

fig_path = os.path.join(OUTPUT_DIR, "Figure_6_5_1_stir_fry.png")
plt.savefig(fig_path, dpi=300, bbox_inches="tight")
plt.show()

print(f"\nSaved figure to: {fig_path}")
print(f"Saved summary table to: {summary_path}")
print(f"Outputs folder: {OUTPUT_DIR}")
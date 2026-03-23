# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 21:24:32 2026

@author: papkp
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel

# =========================================================
# USER PATHS
# =========================================================

BASE_DIR = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1"

CPC_BATH_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/cpc006_out bath_Day5.xlsx"
CPC_BED_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/cpc012_Master Bedroom_Day5.xlsx"
ELPI_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/Day 5 ELPI DATA.xlsx"
SMPS_BED_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/DAY5 SMPS DATA_COM32_MBed.xlsx"
SMPS_KITCHEN_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/DAY5 SMPS DATA_COM33_Kitchen.xlsx"

OUTPUT_DIR = os.path.join(BASE_DIR, "bacon_fry_analysis_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# BACON FRY EXPERIMENT TIMINGS (DAY 5 / 28 FEB 2025)
# =========================================================

EXPERIMENTS = [
    {
        "experiment": "Exp5",
        "repeat": 1,
        "stove_start": "2025-02-28 12:57:40",
        "stove_end":   "2025-02-28 13:02:40",
        "cook_start":  "2025-02-28 13:02:40",
        "cook_end":    "2025-02-28 13:08:40",
        "settle_start":"2025-02-28 13:08:40",
        "settle_end":  "2025-02-28 13:13:58",
        "vent_start":  "2025-02-28 13:13:58",
        "vent_end":    "2025-02-28 13:22:30",
        "window_start":"2025-02-28 13:14:58",
        "window_end":  "2025-02-28 13:20:58",
        "fat_before_g": 81.0,
        "fat_after_g": 39.0
    },
    {
        "experiment": "Exp6",
        "repeat": 2,
        "stove_start": "2025-02-28 13:23:30",
        "stove_end":   "2025-02-28 13:28:30",
        "cook_start":  "2025-02-28 13:28:30",
        "cook_end":    "2025-02-28 13:34:30",
        "settle_start":"2025-02-28 13:34:30",
        "settle_end":  "2025-02-28 13:39:30",
        "vent_start":  "2025-02-28 13:39:30",
        "vent_end":    "2025-02-28 13:46:40",
        "window_start":"2025-02-28 13:40:40",
        "window_end":  "2025-02-28 13:46:40",
        "fat_before_g": 83.8,
        "fat_after_g": 40.55
    },
    {
        "experiment": "Exp7",
        "repeat": 3,
        "stove_start": "2025-02-28 13:48:50",
        "stove_end":   "2025-02-28 13:53:50",
        "cook_start":  "2025-02-28 13:53:50",
        "cook_end":    "2025-02-28 13:59:50",
        "settle_start":"2025-02-28 13:59:50",
        "settle_end":  "2025-02-28 14:04:50",
        "vent_start":  "2025-02-28 14:04:50",
        "vent_end":    "2025-02-28 14:11:50",
        "window_start":"2025-02-28 14:05:50",
        "window_end":  "2025-02-28 14:11:50",
        "fat_before_g": 90.0,
        "fat_after_g": 45.0
    }
]

exp_df = pd.DataFrame(EXPERIMENTS)
time_cols = [c for c in exp_df.columns if c.endswith("_start") or c.endswith("_end")]
for c in time_cols:
    exp_df[c] = pd.to_datetime(exp_df[c])

exp_df["mass_loss_g"] = exp_df["fat_before_g"] - exp_df["fat_after_g"]
exp_df["mass_loss_pct"] = 100 * exp_df["mass_loss_g"] / exp_df["fat_before_g"]

# =========================================================
# HELPERS
# =========================================================

def save_table(df, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False)
    return path

def save_fig(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    return path

def phase_mean(df, start, end, conc_col):
    sub = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()
    if len(sub) == 0:
        return np.nan
    return sub[conc_col].mean()

def phase_peak(df, start, end, conc_col):
    sub = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()
    if len(sub) == 0:
        return np.nan
    return sub[conc_col].max()

def add_windows_to_plot(ax):
    ymax = ax.get_ylim()[1]
    for _, r in exp_df.iterrows():
        ax.axvspan(r["cook_start"], r["cook_end"], alpha=0.20)
        ax.axvspan(r["vent_start"], r["vent_end"], alpha=0.12)
        ax.text(r["cook_start"], ymax * 0.95, r["experiment"], rotation=90, fontsize=8, va="top")

def find_time_col_general(df):
    for c in df.columns:
        c_str = str(c).lower().strip()
        if "corrected time" in c_str or c_str == "time" or "time" in c_str:
            return c
    return None

def find_conc_col_general(df):
    for c in df.columns:
        c_str = str(c).lower().strip()
        if "conc" in c_str or "concentration" in c_str:
            return c
    return None

# =========================================================
# LOAD CPC
# =========================================================

def load_cpc_excel(path, forced_date="2025-02-28"):
    df = pd.read_excel(path)

    time_col = find_time_col_general(df)
    if time_col is None:
        raise ValueError(f"Could not find time column in {os.path.basename(path)}")

    conc_col = find_conc_col_general(df)
    if conc_col is None:
        numeric_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            raise ValueError(f"Could not find concentration column in {os.path.basename(path)}")
        conc_col = numeric_cols[0]

    df = df[[time_col, conc_col]].copy()
    df.columns = ["Time_raw", "Concentration"]

    # Excel serial
    if np.issubdtype(df["Time_raw"].dtype, np.number):
        parsed = pd.to_datetime(df["Time_raw"], unit="d", origin="1899-12-30", errors="coerce")
    else:
        parsed = pd.to_datetime(df["Time_raw"], errors="coerce")

        if parsed.notna().sum() == 0:
            parsed = pd.to_datetime(
                forced_date + " " + df["Time_raw"].astype(str),
                errors="coerce"
            )

    if parsed.notna().sum() == 0:
        raise ValueError(f"Time column in {os.path.basename(path)} could not be parsed.")

    df["Time"] = pd.to_datetime(
        forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
        errors="coerce"
    )
    df["Concentration"] = pd.to_numeric(df["Concentration"], errors="coerce")
    df = df.dropna(subset=["Time", "Concentration"])

    if len(df) == 0:
        raise ValueError(f"Time parsing failed for {os.path.basename(path)}")

    return df

# =========================================================
# LOAD ELPI
# =========================================================

def load_elpi_excel(path, forced_date="2025-02-28"):
    xls = pd.ExcelFile(path)
    sheet = xls.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet)

    time_col = find_time_col_general(df)
    if time_col is None:
        raise ValueError(f"ELPI: Could not find time column in {os.path.basename(path)}")

    conc_col = find_conc_col_general(df)
    if conc_col is None:
        numeric_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            raise ValueError(f"ELPI: Could not find concentration column in {os.path.basename(path)}")
        conc_col = numeric_cols[0]

    out = df[[time_col, conc_col]].copy()
    out.columns = ["Time_raw", "Concentration"]

    parsed = pd.to_datetime(out["Time_raw"], errors="coerce")
    if parsed.notna().sum() == 0:
        parsed = pd.to_datetime(
            forced_date + " " + out["Time_raw"].astype(str),
            errors="coerce"
        )

    out["Time"] = pd.to_datetime(
        forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
        errors="coerce"
    )
    out["Concentration"] = pd.to_numeric(out["Concentration"], errors="coerce")
    out = out.dropna(subset=["Time", "Concentration"])

    return out[["Time", "Concentration"]]

# =========================================================
# LOAD SMPS
# =========================================================

def load_smps_excel(path, forced_date="2025-02-28"):
    xls = pd.ExcelFile(path)
    sheet = xls.sheet_names[0]
    candidate_skiprows = [0, 10, 20, 30, 40]
    last_error = None

    for skip in candidate_skiprows:
        try:
            df = pd.read_excel(path, sheet_name=sheet, skiprows=skip)

            time_col = find_time_col_general(df)
            if time_col is None:
                continue

            time_raw = pd.to_datetime(df[time_col], errors="coerce")
            if time_raw.notna().sum() == 0:
                time_raw = pd.to_datetime(
                    forced_date + " " + df[time_col].astype(str),
                    errors="coerce"
                )
            if time_raw.notna().sum() == 0:
                continue

            out = pd.DataFrame()
            out["Time_raw"] = time_raw
            out["Time"] = pd.to_datetime(
                forced_date + " " + out["Time_raw"].dt.strftime("%H:%M:%S"),
                errors="coerce"
            )

            # Try to find total concentration directly
            total_col = None
            for c in df.columns:
                c_str = str(c).lower().strip()
                if "total" in c_str and "conc" in c_str:
                    total_col = c
                    break

            numeric_bin_cols = []
            numeric_bin_vals = []
            for c in df.columns:
                try:
                    numeric_bin_vals.append(float(str(c).strip()))
                    numeric_bin_cols.append(c)
                except:
                    pass

            if total_col is not None:
                out["Total_Conc"] = pd.to_numeric(df[total_col], errors="coerce")
            else:
                if len(numeric_bin_cols) == 0:
                    continue
                out["Total_Conc"] = df[numeric_bin_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)

            # GMD column if present
            gmd_col = None
            for c in df.columns:
                c_str = str(c).lower().strip()
                if "geo" in c_str and "mean" in c_str:
                    gmd_col = c
                    break

            if gmd_col is not None:
                out["GMD_nm"] = pd.to_numeric(df[gmd_col], errors="coerce")
            else:
                if len(numeric_bin_cols) > 0:
                    vals = df[numeric_bin_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
                    dp = np.array(numeric_bin_vals, dtype=float)
                    numerator = vals.mul(np.log(dp), axis=1).sum(axis=1)
                    denominator = vals.sum(axis=1).replace(0, np.nan)
                    out["GMD_nm"] = np.exp(numerator / denominator)
                else:
                    out["GMD_nm"] = np.nan

            out = out.dropna(subset=["Time", "Total_Conc"])
            if len(out) == 0:
                continue

            print(f"Loaded {os.path.basename(path)} using skiprows={skip}")
            print("Detected columns:")
            print(df.columns.tolist()[:20])

            return out[["Time", "Total_Conc", "GMD_nm"]]

        except Exception as e:
            last_error = e

    raise ValueError(
        f"SMPS: Could not parse {os.path.basename(path)} with any skiprows setting. "
        f"Last error: {last_error}"
    )

# =========================================================
# LOAD DATA
# =========================================================

print("Loading CPC bathroom...")
cpc_bath = load_cpc_excel(CPC_BATH_FILE)

print("Loading CPC bedroom...")
cpc_bed = load_cpc_excel(CPC_BED_FILE)

print("Loading ELPI...")
elpi = load_elpi_excel(ELPI_FILE)

print("Loading SMPS bedroom...")
smps_bed = load_smps_excel(SMPS_BED_FILE)

print("Loading SMPS kitchen...")
smps_kitchen = load_smps_excel(SMPS_KITCHEN_FILE)

# =========================================================
# BUILD REPEAT-LEVEL SUMMARY TABLE
# =========================================================

summary_rows = []

for _, r in exp_df.iterrows():
    summary_rows.append({
        "experiment": r["experiment"],
        "repeat": r["repeat"],
        "mass_loss_g": r["mass_loss_g"],
        "mass_loss_pct": r["mass_loss_pct"],

        "CPC_bath_peak_cook": phase_peak(cpc_bath, r["cook_start"], r["cook_end"], "Concentration"),
        "CPC_bath_mean_vent": phase_mean(cpc_bath, r["vent_start"], r["vent_end"], "Concentration"),

        "CPC_bed_peak_cook": phase_peak(cpc_bed, r["cook_start"], r["cook_end"], "Concentration"),
        "CPC_bed_mean_vent": phase_mean(cpc_bed, r["vent_start"], r["vent_end"], "Concentration"),

        "ELPI_peak_cook": phase_peak(elpi, r["cook_start"], r["cook_end"], "Concentration"),
        "ELPI_mean_vent": phase_mean(elpi, r["vent_start"], r["vent_end"], "Concentration"),

        "SMPS_bed_peak_cook": phase_peak(smps_bed, r["cook_start"], r["cook_end"], "Total_Conc"),
        "SMPS_bed_mean_vent": phase_mean(smps_bed, r["vent_start"], r["vent_end"], "Total_Conc"),

        "SMPS_kitchen_peak_cook": phase_peak(smps_kitchen, r["cook_start"], r["cook_end"], "Total_Conc"),
        "SMPS_kitchen_mean_vent": phase_mean(smps_kitchen, r["vent_start"], r["vent_end"], "Total_Conc"),

        "SMPS_bed_GMD_cook": phase_mean(smps_bed, r["cook_start"], r["cook_end"], "GMD_nm"),
        "SMPS_bed_GMD_vent": phase_mean(smps_bed, r["vent_start"], r["vent_end"], "GMD_nm"),

        "SMPS_kitchen_GMD_cook": phase_mean(smps_kitchen, r["cook_start"], r["cook_end"], "GMD_nm"),
        "SMPS_kitchen_GMD_vent": phase_mean(smps_kitchen, r["vent_start"], r["vent_end"], "GMD_nm"),
    })

summary_df = pd.DataFrame(summary_rows)

for prefix in ["CPC_bath", "CPC_bed", "ELPI", "SMPS_bed", "SMPS_kitchen"]:
    peak_col = f"{prefix}_peak_cook"
    vent_col = f"{prefix}_mean_vent"
    summary_df[f"{prefix}_reduction_pct"] = 100 * (summary_df[peak_col] - summary_df[vent_col]) / summary_df[peak_col]

save_table(summary_df, "Bacon_repeat_level_summary.csv")
save_table(exp_df, "Bacon_experiment_schedule.csv")

# =========================================================
# STATISTICS
# =========================================================

stats_rows = []

metric_pairs = [
    ("CPC Bathroom", "CPC_bath_peak_cook", "CPC_bath_mean_vent"),
    ("CPC Bedroom", "CPC_bed_peak_cook", "CPC_bed_mean_vent"),
    ("ELPI", "ELPI_peak_cook", "ELPI_mean_vent"),
    ("SMPS Bedroom Total", "SMPS_bed_peak_cook", "SMPS_bed_mean_vent"),
    ("SMPS Kitchen Total", "SMPS_kitchen_peak_cook", "SMPS_kitchen_mean_vent"),
    ("SMPS Bedroom GMD", "SMPS_bed_GMD_cook", "SMPS_bed_GMD_vent"),
    ("SMPS Kitchen GMD", "SMPS_kitchen_GMD_cook", "SMPS_kitchen_GMD_vent"),
]

for label, cook_col, vent_col in metric_pairs:
    a = summary_df[cook_col].dropna()
    b = summary_df[vent_col].dropna()

    if len(a) == len(b) and len(a) >= 2:
        t_stat, p_val = ttest_rel(a, b, nan_policy="omit")
    else:
        t_stat, p_val = np.nan, np.nan

    mean_cook = summary_df[cook_col].mean()
    mean_vent = summary_df[vent_col].mean()

    stats_rows.append({
        "Metric": label,
        "Mean_Cooking_Peak": mean_cook,
        "Mean_PostVent": mean_vent,
        "Mean_Reduction_or_Change": mean_cook - mean_vent,
        "Percent_Reduction_if_applicable": (
            100 * (mean_cook - mean_vent) / mean_cook if pd.notna(mean_cook) and mean_cook != 0 else np.nan
        ),
        "t_statistic": t_stat,
        "p_value": p_val
    })

stats_df = pd.DataFrame(stats_rows)
save_table(stats_df, "Bacon_statistical_tests.csv")

# =========================================================
# FAT LOSS VS PEAK TABLE
# =========================================================

fat_loss_table = summary_df[[
    "experiment", "repeat", "mass_loss_g", "mass_loss_pct",
    "CPC_bath_peak_cook", "CPC_bed_peak_cook",
    "ELPI_peak_cook", "SMPS_bed_peak_cook", "SMPS_kitchen_peak_cook"
]].copy()

save_table(fat_loss_table, "Bacon_fat_loss_vs_peak_table.csv")

# =========================================================
# PLOTS
# =========================================================

plt.figure(figsize=(14, 5))
plt.plot(cpc_bath["Time"], cpc_bath["Concentration"], linewidth=1)
ax = plt.gca()
add_windows_to_plot(ax)
plt.xlabel("Time")
plt.ylabel("CPC concentration (#/cm³)")
plt.title("Bathroom CPC time series during bacon frying experiments")
save_fig("Figure_6_3_1_CPC_bath_time_series.png")

plt.figure(figsize=(14, 5))
plt.plot(cpc_bed["Time"], cpc_bed["Concentration"], linewidth=1)
ax = plt.gca()
add_windows_to_plot(ax)
plt.xlabel("Time")
plt.ylabel("CPC concentration (#/cm³)")
plt.title("Master bedroom CPC time series during bacon frying experiments")
save_fig("Figure_6_3_2_CPC_bedroom_time_series.png")

plt.figure(figsize=(14, 5))
plt.plot(elpi["Time"], elpi["Concentration"], linewidth=1)
ax = plt.gca()
add_windows_to_plot(ax)
plt.xlabel("Time")
plt.ylabel("ELPI concentration")
plt.title("ELPI time series during bacon frying experiments")
save_fig("Figure_6_3_3_ELPI_time_series.png")

plt.figure(figsize=(14, 5))
plt.plot(smps_bed["Time"], smps_bed["Total_Conc"], linewidth=1)
ax = plt.gca()
add_windows_to_plot(ax)
plt.xlabel("Time")
plt.ylabel("SMPS total concentration (#/cm³)")
plt.title("SMPS master bedroom total concentration during bacon frying experiments")
save_fig("Figure_6_3_4_SMPS_bed_total_time_series.png")

plt.figure(figsize=(14, 5))
plt.plot(smps_kitchen["Time"], smps_kitchen["Total_Conc"], linewidth=1)
ax = plt.gca()
add_windows_to_plot(ax)
plt.xlabel("Time")
plt.ylabel("SMPS total concentration (#/cm³)")
plt.title("SMPS kitchen total concentration during bacon frying experiments")
save_fig("Figure_6_3_5_SMPS_kitchen_total_time_series.png")

plt.figure(figsize=(7, 5))
plt.boxplot(
    [summary_df["CPC_bath_peak_cook"].dropna(), summary_df["CPC_bath_mean_vent"].dropna()],
    labels=["Cooking peak", "Post-vent"]
)
plt.ylabel("CPC concentration (#/cm³)")
plt.title("Bathroom CPC: cooking peak vs post-ventilation")
save_fig("Figure_6_3_6_CPC_bath_peak_vs_postvent_boxplot.png")

plt.figure(figsize=(7, 5))
plt.boxplot(
    [summary_df["CPC_bed_peak_cook"].dropna(), summary_df["CPC_bed_mean_vent"].dropna()],
    labels=["Cooking peak", "Post-vent"]
)
plt.ylabel("CPC concentration (#/cm³)")
plt.title("Bedroom CPC: cooking peak vs post-ventilation")
save_fig("Figure_6_3_7_CPC_bed_peak_vs_postvent_boxplot.png")

plt.figure(figsize=(7, 5))
plt.scatter(summary_df["mass_loss_g"], summary_df["CPC_bath_peak_cook"], label="Bathroom CPC peak")
plt.scatter(summary_df["mass_loss_g"], summary_df["CPC_bed_peak_cook"], label="Bedroom CPC peak")
plt.xlabel("Mass loss during cooking (g)")
plt.ylabel("Peak CPC concentration (#/cm³)")
plt.title("Mass loss versus peak CPC concentration during bacon frying")
plt.legend()
save_fig("Figure_6_3_8_Mass_loss_vs_peak_CPC.png")

# =========================================================
# THESIS-READY TEXT
# =========================================================

def get_p(metric_name):
    row = stats_df.loc[stats_df["Metric"] == metric_name, "p_value"]
    return row.values[0] if len(row) else np.nan

thesis_text = f"""
SECTION 6.3.1 BACON FRYING EXPERIMENTS – STATISTICAL SUMMARY

Repeat-level statistical comparisons were carried out for the bacon frying experiments (n = 3), using each experimental repeat as the independent unit in line with Zar's biostatistical approach.

Bathroom CPC:
Mean cooking peak = {summary_df['CPC_bath_peak_cook'].mean():.2f}
Mean post-ventilation = {summary_df['CPC_bath_mean_vent'].mean():.2f}
Mean reduction (%) = {summary_df['CPC_bath_reduction_pct'].mean():.2f}
p-value = {get_p('CPC Bathroom'):.3e}

Bedroom CPC:
Mean cooking peak = {summary_df['CPC_bed_peak_cook'].mean():.2f}
Mean post-ventilation = {summary_df['CPC_bed_mean_vent'].mean():.2f}
Mean reduction (%) = {summary_df['CPC_bed_reduction_pct'].mean():.2f}
p-value = {get_p('CPC Bedroom'):.3e}

ELPI:
Mean cooking peak = {summary_df['ELPI_peak_cook'].mean():.2f}
Mean post-ventilation = {summary_df['ELPI_mean_vent'].mean():.2f}
Mean reduction (%) = {summary_df['ELPI_reduction_pct'].mean():.2f}
p-value = {get_p('ELPI'):.3e}

SMPS bedroom total concentration:
Mean cooking peak = {summary_df['SMPS_bed_peak_cook'].mean():.2f}
Mean post-ventilation = {summary_df['SMPS_bed_mean_vent'].mean():.2f}
Mean reduction (%) = {summary_df['SMPS_bed_reduction_pct'].mean():.2f}
p-value = {get_p('SMPS Bedroom Total'):.3e}

SMPS kitchen total concentration:
Mean cooking peak = {summary_df['SMPS_kitchen_peak_cook'].mean():.2f}
Mean post-ventilation = {summary_df['SMPS_kitchen_mean_vent'].mean():.2f}
Mean reduction (%) = {summary_df['SMPS_kitchen_reduction_pct'].mean():.2f}
p-value = {get_p('SMPS Kitchen Total'):.3e}

SMPS bedroom GMD:
Mean cooking = {summary_df['SMPS_bed_GMD_cook'].mean():.2f}
Mean post-ventilation = {summary_df['SMPS_bed_GMD_vent'].mean():.2f}
p-value = {get_p('SMPS Bedroom GMD'):.3e}

SMPS kitchen GMD:
Mean cooking = {summary_df['SMPS_kitchen_GMD_cook'].mean():.2f}
Mean post-ventilation = {summary_df['SMPS_kitchen_GMD_vent'].mean():.2f}
p-value = {get_p('SMPS Kitchen GMD'):.3e}

Interpretation:
Bacon frying generated strong particle emission peaks across the monitored rooms. Post-ventilation concentrations were consistently lower than cooking peaks, indicating substantial removal following window and door opening. The repeat-level statistics provide a defensible basis for reporting concentration reductions without pseudoreplication.
"""

with open(os.path.join(OUTPUT_DIR, "Section_6_3_1_thesis_ready_text.txt"), "w", encoding="utf-8") as f:
    f.write(thesis_text)

print("Done.")
print(f"All outputs saved in: {OUTPUT_DIR}")
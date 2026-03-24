# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 14:31:25 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Section 6.4.1
Deep frying experiments at SPHERE House
27 February 2025

Experiments:
Exp1  WITHOUT FAN   12:41:15 - 13:03:15
Exp2  WITH FAN      13:13:33 - 13:35:40
Exp3  WITHOUT FAN   13:41:30 - 14:03:40
Exp4  WITH FAN      14:10:20 - 14:32:25
Exp5  WITHOUT FAN   14:39:13 - 15:01:20
Exp6  WITH FAN      15:06:40 - 15:28:55
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import ttest_ind, ttest_rel

# =========================================================
# USER PATHS
# =========================================================

BASE_DIR = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1"

CPC_BATH_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/CPC DAY 4 OUTSIDE BATH_EXCEL.csv"
CPC_BED_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/cpc012_Master Bedroom_Day4.csv"
ELPI_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/day4 elpi data.xlsx"
SMPS_FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/DAY4 SMPS DATA_COM32.xlsx"

OUTPUT_DIR = os.path.join(BASE_DIR, "deep_frying_analysis_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# EXPERIMENT SCHEDULE
# =========================================================

EXPERIMENTS = [
    {
        "experiment": "Exp1", "repeat": 1, "fan": "No Fan",
        "start": "2025-02-27 12:41:15", "end": "2025-02-27 13:03:15",
        "cook_start": "2025-02-27 12:46:15", "cook_end": "2025-02-27 12:48:15",
        "stove_off": "2025-02-27 13:03:15"
    },
    {
        "experiment": "Exp2", "repeat": 1, "fan": "Fan",
        "start": "2025-02-27 13:13:33", "end": "2025-02-27 13:35:40",
        "cook_start": "2025-02-27 13:18:33", "cook_end": "2025-02-27 13:20:33",
        "stove_off": "2025-02-27 13:35:40"
    },
    {
        "experiment": "Exp3", "repeat": 2, "fan": "No Fan",
        "start": "2025-02-27 13:41:30", "end": "2025-02-27 14:03:40",
        "cook_start": "2025-02-27 13:46:30", "cook_end": "2025-02-27 13:48:30",
        "stove_off": "2025-02-27 14:03:40"
    },
    {
        "experiment": "Exp4", "repeat": 2, "fan": "Fan",
        "start": "2025-02-27 14:10:20", "end": "2025-02-27 14:32:25",
        "cook_start": "2025-02-27 14:15:20", "cook_end": "2025-02-27 14:17:20",
        "stove_off": "2025-02-27 14:32:25"
    },
    {
        "experiment": "Exp5", "repeat": 3, "fan": "No Fan",
        "start": "2025-02-27 14:39:13", "end": "2025-02-27 15:01:20",
        "cook_start": "2025-02-27 14:44:13", "cook_end": "2025-02-27 14:46:13",
        "stove_off": "2025-02-27 15:01:20"
    },
    {
        "experiment": "Exp6", "repeat": 3, "fan": "Fan",
        "start": "2025-02-27 15:06:40", "end": "2025-02-27 15:28:55",
        "cook_start": "2025-02-27 15:11:40", "cook_end": "2025-02-27 15:13:40",
        "stove_off": "2025-02-27 15:28:55"
    },
]

exp_df = pd.DataFrame(EXPERIMENTS)
for c in ["start", "end", "cook_start", "cook_end", "stove_off"]:
    exp_df[c] = pd.to_datetime(exp_df[c])

# Post-cooking / post-emission window used for comparison
# Here: final 5 minutes of each experiment
exp_df["post_start"] = exp_df["end"] - pd.Timedelta(minutes=5)
exp_df["post_end"] = exp_df["end"]

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

def find_time_col(df):
    for c in df.columns:
        c_str = str(c).lower().strip()
        if "time" in c_str or "corrected time" in c_str:
            return c
    return None

def find_conc_col(df):
    for c in df.columns:
        c_str = str(c).lower().strip()
        if "conc" in c_str or "concentration" in c_str:
            return c
    return None

def assign_experiment(timestamp):
    if pd.isna(timestamp):
        return pd.Series([None, None, None])
    row = exp_df[(exp_df["start"] <= timestamp) & (exp_df["end"] >= timestamp)]
    if len(row) == 0:
        return pd.Series([None, None, None])
    row = row.iloc[0]
    return pd.Series([row["experiment"], row["repeat"], row["fan"]])

def phase_peak(df, start, end, col):
    sub = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()
    if sub.empty:
        return np.nan
    return sub[col].max()

def phase_mean(df, start, end, col):
    sub = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()
    if sub.empty:
        return np.nan
    return sub[col].mean()

def paired_stats(a, b):
    a = pd.Series(a).dropna().values
    b = pd.Series(b).dropna().values
    if len(a) == len(b) and len(a) >= 2:
        t_stat, p_val = ttest_rel(a, b)
        return t_stat, p_val
    return np.nan, np.nan

def independent_stats(a, b):
    a = pd.Series(a).dropna().values
    b = pd.Series(b).dropna().values
    if len(a) >= 2 and len(b) >= 2:
        t_stat, p_val = ttest_ind(a, b, equal_var=False)
        return t_stat, p_val
    return np.nan, np.nan

# =========================================================
# LOAD CPC CSV
# =========================================================

def load_cpc_csv(path, forced_date="2025-02-27", value_name="Concentration"):
    import os
    import numpy as np
    import pandas as pd

    encodings_to_try = ["utf-8", "latin1", "cp1252", "utf-16"]
    df = None
    last_error = None

    for enc in encodings_to_try:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"Loaded {os.path.basename(path)} with encoding={enc}")
            break
        except Exception as e:
            last_error = e

    if df is None:
        raise ValueError(
            f"Could not read {os.path.basename(path)} with common encodings. Last error: {last_error}"
        )

    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]

    # -----------------------------------------------------
    # FIND TIME COLUMN
    # -----------------------------------------------------
    time_col = None

    # First try normal named time columns
    for c in df.columns:
        c_str = str(c).lower().strip()
        if "time" in c_str or "date" in c_str:
            time_col = c
            break

    # If not found, use first column as fallback
    if time_col is None:
        time_col = df.columns[0]
        print(f"No explicit time column found in {os.path.basename(path)}; using first column: {time_col}")

    # -----------------------------------------------------
    # FIND CONCENTRATION COLUMN
    # -----------------------------------------------------
    conc_col = None
    for c in df.columns:
        if c == time_col:
            continue
        c_str = str(c).lower().strip()
        if "conc" in c_str or "concentration" in c_str:
            conc_col = c
            break

    # fallback: first numeric non-time column
    if conc_col is None:
        numeric_cols = []
        for c in df.columns:
            if c == time_col:
                continue
            try:
                pd.to_numeric(df[c], errors="raise")
                numeric_cols.append(c)
            except Exception:
                pass

        if not numeric_cols:
            # weaker fallback: coerce numeric and keep columns with some numbers
            for c in df.columns:
                if c == time_col:
                    continue
                tmp = pd.to_numeric(df[c], errors="coerce")
                if tmp.notna().sum() > 0:
                    numeric_cols.append(c)

        if not numeric_cols:
            raise ValueError(f"Could not find concentration column in {os.path.basename(path)}")

        conc_col = numeric_cols[0]
        print(f"No explicit concentration column found in {os.path.basename(path)}; using: {conc_col}")

    # -----------------------------------------------------
    # PARSE TIME
    # -----------------------------------------------------
    raw_time = df[time_col]

    parsed = None

    # Case 1: Excel serial numbers
    if np.issubdtype(raw_time.dtype, np.number):
        parsed = pd.to_datetime(raw_time, unit="d", origin="1899-12-30", errors="coerce")
    else:
        # Try generic parsing
        parsed = pd.to_datetime(raw_time, errors="coerce")

        # If that fails, try time-only strings
        if parsed.notna().sum() == 0:
            parsed = pd.to_datetime(forced_date + " " + raw_time.astype(str).str.strip(), errors="coerce")

        # Try common explicit formats
        if parsed.notna().sum() == 0:
            for fmt in ["%H:%M:%S", "%H:%M", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"]:
                try:
                    parsed = pd.to_datetime(raw_time.astype(str).str.strip(), format=fmt, errors="coerce")
                    if parsed.notna().sum() > 0:
                        break
                except Exception:
                    pass

            # If time-only format parsed, add forced date
            if parsed.notna().sum() > 0 and parsed.dt.year.nunique() == 1 and parsed.dt.year.iloc[0] == 1900:
                parsed = pd.to_datetime(forced_date + " " + parsed.dt.strftime("%H:%M:%S"), errors="coerce")

    if parsed is None or parsed.notna().sum() == 0:
        raise ValueError(f"Time parsing failed for {os.path.basename(path)}")

    # If parsed times have a real date, replace with forced_date but keep time-of-day
    out = pd.DataFrame()
    out["Time"] = pd.to_datetime(
        forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

    out[value_name] = pd.to_numeric(df[conc_col], errors="coerce")

    out = out.dropna(subset=["Time", value_name]).sort_values("Time").reset_index(drop=True)

    if out.empty:
        raise ValueError(f"No valid rows after parsing {os.path.basename(path)}")

    return out

# =========================================================
# LOAD ELPI XLSX
# =========================================================

def load_elpi_xlsx(path, forced_date="2025-02-27"):
    xls = pd.ExcelFile(path)
    sheet = xls.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    time_col = find_time_col(df)
    if time_col is None:
        raise ValueError(f"ELPI time column not found in {os.path.basename(path)}")

    conc_col = find_conc_col(df)
    if conc_col is None:
        numeric_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            raise ValueError(f"ELPI concentration column not found in {os.path.basename(path)}")
        conc_col = numeric_cols[0]

    parsed = pd.to_datetime(df[time_col], errors="coerce")
    if parsed.notna().sum() == 0:
        parsed = pd.to_datetime(forced_date + " " + df[time_col].astype(str), errors="coerce")

    out = pd.DataFrame()
    out["Time"] = pd.to_datetime(
        forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
        errors="coerce"
    )
    out["ELPI_Conc"] = pd.to_numeric(df[conc_col], errors="coerce")
    out = out.dropna(subset=["Time", "ELPI_Conc"]).sort_values("Time").reset_index(drop=True)
    return out

# =========================================================
# LOAD SMPS XLSX
# =========================================================

def load_smps_xlsx(path, forced_date="2025-02-27"):
    xls = pd.ExcelFile(path)
    sheet = xls.sheet_names[0]
    candidate_skiprows = [0, 10, 20, 30, 40]
    last_error = None

    for skip in candidate_skiprows:
        try:
            df = pd.read_excel(path, sheet_name=sheet, skiprows=skip)
            df.columns = [str(c).strip() for c in df.columns]

            time_col = find_time_col(df)
            if time_col is None:
                continue

            parsed = pd.to_datetime(df[time_col], errors="coerce")
            if parsed.notna().sum() == 0:
                parsed = pd.to_datetime(forced_date + " " + df[time_col].astype(str), errors="coerce")
            if parsed.notna().sum() == 0:
                continue

            out = pd.DataFrame()
            out["Time"] = pd.to_datetime(
                forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
                errors="coerce"
            )

            # Total concentration column if present
            total_col = None
            for c in df.columns:
                c_str = str(c).lower()
                if "total" in c_str and "conc" in c_str:
                    total_col = c
                    break

            # GMD if present
            gmd_col = None
            for c in df.columns:
                c_str = str(c).lower()
                if "geo" in c_str and "mean" in c_str:
                    gmd_col = c
                    break

            # size bin fallback
            numeric_bin_cols = []
            numeric_bin_vals = []
            for c in df.columns:
                try:
                    numeric_bin_vals.append(float(str(c).strip()))
                    numeric_bin_cols.append(c)
                except:
                    pass

            if total_col is not None:
                out["SMPS_Total"] = pd.to_numeric(df[total_col], errors="coerce")
            else:
                if len(numeric_bin_cols) == 0:
                    continue
                out["SMPS_Total"] = df[numeric_bin_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)

            if gmd_col is not None:
                out["SMPS_GMD_nm"] = pd.to_numeric(df[gmd_col], errors="coerce")
            else:
                if len(numeric_bin_cols) > 0:
                    vals = df[numeric_bin_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
                    dp = np.array(numeric_bin_vals, dtype=float)
                    numerator = vals.mul(np.log(dp), axis=1).sum(axis=1)
                    denominator = vals.sum(axis=1).replace(0, np.nan)
                    out["SMPS_GMD_nm"] = np.exp(numerator / denominator)
                else:
                    out["SMPS_GMD_nm"] = np.nan

            out = out.dropna(subset=["Time", "SMPS_Total"]).sort_values("Time").reset_index(drop=True)

            print(f"Loaded {os.path.basename(path)} using skiprows={skip}")
            return out

        except Exception as e:
            last_error = e

    raise ValueError(f"Could not parse SMPS file {os.path.basename(path)}. Last error: {last_error}")

# =========================================================
# LOAD ALL DATA
# =========================================================

print("Loading CPC bathroom...")
cpc_bath = load_cpc_csv(CPC_BATH_FILE, value_name="CPC_Bath")

print("Loading CPC bedroom...")
cpc_bed = load_cpc_csv(CPC_BED_FILE, value_name="CPC_Bed")

print("Loading ELPI...")
elpi = load_elpi_xlsx(ELPI_FILE)

print("Loading SMPS...")
smps = load_smps_xlsx(SMPS_FILE)

# =========================================================
# ADD EXPERIMENT LABELS
# =========================================================

for df in [cpc_bath, cpc_bed, elpi, smps]:
    df[["Experiment", "Repeat", "Fan"]] = df["Time"].apply(assign_experiment)

# =========================================================
# BUILD REPEAT-LEVEL SUMMARY
# =========================================================

summary_rows = []

for _, r in exp_df.iterrows():
    summary_rows.append({
        "Experiment": r["experiment"],
        "Repeat": r["repeat"],
        "Fan": r["fan"],

        "CPC_Bath_Peak": phase_peak(cpc_bath, r["cook_start"], r["end"], "CPC_Bath"),
        "CPC_Bath_Post": phase_mean(cpc_bath, r["post_start"], r["post_end"], "CPC_Bath"),

        "CPC_Bed_Peak": phase_peak(cpc_bed, r["cook_start"], r["end"], "CPC_Bed"),
        "CPC_Bed_Post": phase_mean(cpc_bed, r["post_start"], r["post_end"], "CPC_Bed"),

        "ELPI_Peak": phase_peak(elpi, r["cook_start"], r["end"], "ELPI_Conc"),
        "ELPI_Post": phase_mean(elpi, r["post_start"], r["post_end"], "ELPI_Conc"),

        "SMPS_Peak": phase_peak(smps, r["cook_start"], r["end"], "SMPS_Total"),
        "SMPS_Post": phase_mean(smps, r["post_start"], r["post_end"], "SMPS_Total"),

        "SMPS_GMD_Cook": phase_mean(smps, r["cook_start"], r["cook_end"], "SMPS_GMD_nm"),
        "SMPS_GMD_Post": phase_mean(smps, r["post_start"], r["post_end"], "SMPS_GMD_nm"),
    })

summary_df = pd.DataFrame(summary_rows)

for prefix in ["CPC_Bath", "CPC_Bed", "ELPI", "SMPS"]:
    summary_df[f"{prefix}_Reduction_pct"] = 100 * (
        (summary_df[f"{prefix}_Peak"] - summary_df[f"{prefix}_Post"]) / summary_df[f"{prefix}_Peak"]
    )

save_table(summary_df, "DeepFry_repeat_level_summary.csv")

# =========================================================
# STATISTICAL TESTS
# =========================================================

stats_rows = []

# Paired peak vs post within instrument
comparisons = [
    ("CPC Bathroom", "CPC_Bath_Peak", "CPC_Bath_Post"),
    ("CPC Bedroom", "CPC_Bed_Peak", "CPC_Bed_Post"),
    ("ELPI", "ELPI_Peak", "ELPI_Post"),
    ("SMPS Total", "SMPS_Peak", "SMPS_Post"),
    ("SMPS GMD", "SMPS_GMD_Cook", "SMPS_GMD_Post"),
]

for label, col_peak, col_post in comparisons:
    t_stat, p_val = paired_stats(summary_df[col_peak], summary_df[col_post])
    stats_rows.append({
        "Comparison": label,
        "Mean_Peak": summary_df[col_peak].mean(),
        "Mean_Post": summary_df[col_post].mean(),
        "Mean_Reduction_or_Change": summary_df[col_peak].mean() - summary_df[col_post].mean(),
        "Mean_Reduction_pct_if_applicable": (
            100 * (summary_df[col_peak].mean() - summary_df[col_post].mean()) / summary_df[col_peak].mean()
            if summary_df[col_peak].mean() not in [0, np.nan] else np.nan
        ),
        "t_statistic": t_stat,
        "p_value": p_val
    })

# Independent No Fan vs Fan
fan_stats_rows = []
metrics_for_fan = [
    ("CPC Bathroom Peak", "CPC_Bath_Peak"),
    ("CPC Bedroom Peak", "CPC_Bed_Peak"),
    ("ELPI Peak", "ELPI_Peak"),
    ("SMPS Peak", "SMPS_Peak"),
    ("SMPS GMD Cook", "SMPS_GMD_Cook"),
]

for label, col in metrics_for_fan:
    no_fan = summary_df.loc[summary_df["Fan"] == "No Fan", col]
    fan = summary_df.loc[summary_df["Fan"] == "Fan", col]
    t_stat, p_val = independent_stats(no_fan, fan)
    fan_stats_rows.append({
        "Comparison": label,
        "Mean_NoFan": no_fan.mean(),
        "Mean_Fan": fan.mean(),
        "t_statistic": t_stat,
        "p_value": p_val
    })

stats_df = pd.DataFrame(stats_rows)
fan_stats_df = pd.DataFrame(fan_stats_rows)

save_table(stats_df, "DeepFry_peak_vs_post_stats.csv")
save_table(fan_stats_df, "DeepFry_nofan_vs_fan_stats.csv")

# =========================================================
# FIGURES
# =========================================================

# Restrict plot to experiment window
plot_start = exp_df["start"].min()
plot_end = exp_df["end"].max()

cpc_bath_plot = cpc_bath[(cpc_bath["Time"] >= plot_start) & (cpc_bath["Time"] <= plot_end)].copy()
cpc_bed_plot = cpc_bed[(cpc_bed["Time"] >= plot_start) & (cpc_bed["Time"] <= plot_end)].copy()
elpi_plot = elpi[(elpi["Time"] >= plot_start) & (elpi["Time"] <= plot_end)].copy()
smps_plot = smps[(smps["Time"] >= plot_start) & (smps["Time"] <= plot_end)].copy()

# Smooth
for df, col, newcol in [
    (cpc_bath_plot, "CPC_Bath", "CPC_Bath_smooth"),
    (cpc_bed_plot, "CPC_Bed", "CPC_Bed_smooth"),
    (elpi_plot, "ELPI_Conc", "ELPI_smooth"),
    (smps_plot, "SMPS_Total", "SMPS_smooth"),
]:
    df[newcol] = df[col].rolling(3, center=True, min_periods=1).mean()

# Figure 6.4.1 time series
plt.figure(figsize=(11.5, 6.2))

plt.plot(smps_plot["Time"], smps_plot["SMPS_smooth"], linewidth=2.4, label="Kitchen (SMPS)")
plt.plot(elpi_plot["Time"], elpi_plot["ELPI_smooth"], linewidth=1.8, linestyle=":", alpha=0.9, label="Kitchen (ELPI)")
plt.plot(cpc_bath_plot["Time"], cpc_bath_plot["CPC_Bath_smooth"], linewidth=1.4, linestyle="-.", alpha=0.9, label="Bathroom (CPC)")
plt.plot(cpc_bed_plot["Time"], cpc_bed_plot["CPC_Bed_smooth"], linewidth=1.4, linestyle="--", alpha=0.9, label="Bedroom (CPC)")

for _, r in exp_df.iterrows():
    start = r["start"]
    end = r["end"]
    cook_start = r["cook_start"]
    cook_end = r["cook_end"]

    # full experiment
    plt.axvspan(start, end, alpha=0.05, color="grey")
    # active frying
    plt.axvspan(cook_start, cook_end, alpha=0.14, color="orange")

    label = f"{r['experiment']} ({'No Fan' if r['fan']=='No Fan' else 'Fan'})"
    plt.text(start, plt.ylim()[1] * 0.92, label, fontsize=8, rotation=90, va="top")

plt.xlabel("Time")
plt.ylabel("Particle number concentration (particles cm$^{-3}$)")
plt.title(
    "Figure 6.4.1. Time-resolved particle number concentration during onion ring deep frying\n"
    "showing multi-instrument response and fan effects"
)
plt.grid(True, linestyle="--", linewidth=0.5)
plt.yscale("log")
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()
plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)

save_fig("Figure_6_4_1_deep_frying_time_series.png")

# Boxplot: fan vs no fan peaks
plt.figure(figsize=(7, 5))
data_nofan = summary_df.loc[summary_df["Fan"] == "No Fan", "ELPI_Peak"].dropna()
data_fan = summary_df.loc[summary_df["Fan"] == "Fan", "ELPI_Peak"].dropna()
plt.boxplot([data_nofan, data_fan], labels=["No Fan", "Fan"])
plt.ylabel("ELPI peak concentration")
plt.title("ELPI peak concentration: No Fan vs Fan")
save_fig("Figure_ELPI_peak_nofan_vs_fan_boxplot.png")

# Boxplot: SMPS peak vs post
plt.figure(figsize=(7, 5))
plt.boxplot([summary_df["SMPS_Peak"].dropna(), summary_df["SMPS_Post"].dropna()], labels=["Peak", "Post"])
plt.ylabel("SMPS total concentration")
plt.title("SMPS total concentration: peak vs post-cooking")
save_fig("Figure_SMPS_peak_vs_post_boxplot.png")

# =========================================================
# THESIS-READY TEXT FILE
# =========================================================

def get_p(stats_df, label):
    row = stats_df.loc[stats_df["Comparison"] == label, "p_value"]
    return row.values[0] if len(row) else np.nan

thesis_text = f"""
SECTION 6.4.1 DEEP FRYING EXPERIMENTS – STATISTICAL SUMMARY

Deep frying experiments were conducted on 27 February 2025 at SPHERE House using onion rings,
with three repeats performed without the extraction fan and three repeats with the fan.

Peak vs post-cooking comparisons:
CPC Bathroom: p = {get_p(stats_df, 'CPC Bathroom'):.4g}
CPC Bedroom: p = {get_p(stats_df, 'CPC Bedroom'):.4g}
ELPI: p = {get_p(stats_df, 'ELPI'):.4g}
SMPS Total: p = {get_p(stats_df, 'SMPS Total'):.4g}
SMPS GMD: p = {get_p(stats_df, 'SMPS GMD'):.4g}

No Fan vs Fan peak comparisons:
{fan_stats_df.to_string(index=False)}

Suggested thesis wording:
Deep frying produced the highest particle concentrations among the cooking activities investigated.
Across repeat experiments, concentrations increased rapidly after the onion ring was introduced into the hot oil,
with the highest peaks measured in the kitchen by ELPI and SMPS. Experiments conducted without the extraction fan
showed higher and more sustained concentrations than those conducted with the fan. Peak-to-post comparisons
demonstrated a reduction in particle concentration after cooking, and fan-assisted experiments generally showed
faster reduction and lower persistence of particles.
"""

with open(os.path.join(OUTPUT_DIR, "Section_6_4_1_thesis_ready_text.txt"), "w", encoding="utf-8") as f:
    f.write(thesis_text)

print("Done.")
print(f"All outputs saved in: {OUTPUT_DIR}")
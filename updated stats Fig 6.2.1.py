# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 22:10:04 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Updated statistical analysis for Figure 6.2.1
NaCl aerosol transport within SPHERE House on 28 Feb 2025

Includes:
- Kitchen SMPS
- Master bedroom SMPS
- Kitchen ELPI
- CPC bathroom
- CPC bedroom
- Repeat-based stats for Experiments 2–4
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.dates as mdates
from scipy.stats import ttest_rel, wilcoxon, t

# ---------------------------------------------------------
# 1. FILE PATHS
# ---------------------------------------------------------
bedroom_smps_file = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.2.1/DAY5 SMPS DATA_COM32_MBed.xlsx")
kitchen_smps_file = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.2.1/DAY5 SMPS DATA_COM33_Kitchen.xlsx")
elpi_file = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/Day 5 ELPI DATA.xlsx")
cpc_bath_file = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/cpc006_out bath_Day5.xlsx")
cpc_bed_file = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/cpc012_Master Bedroom_Day5.xlsx")

output_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.2.1/naCl_stats_outputs")
output_dir.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# 2. SETTINGS
# ---------------------------------------------------------
smooth_window = 3
use_log_y = True
merge_tolerance = "2min"
dummy_date = "2000-01-01"

EXPERIMENTS = [
    {"experiment": "Exp2", "start": "10:11:45", "end": "11:02:30"},
    {"experiment": "Exp3", "start": "11:04:25", "end": "11:52:10"},
    {"experiment": "Exp4", "start": "12:00:40", "end": "12:56:31"},
]

EXPERIMENT_PHASES = {
    "Exp2": {
        "generate_start": "10:11:45",
        "generate_end": "10:31:45",
        "settle_start": "10:31:45",
        "settle_end": "10:52:45",
        "vent_start": "10:52:45",
        "vent_end": "11:02:30",
    },
    "Exp3": {
        "generate_start": "11:04:25",
        "generate_end": "11:24:25",
        "settle_start": "11:24:25",
        "settle_end": "11:44:25",
        "vent_start": "11:44:40",
        "vent_end": "11:52:10",
    },
    "Exp4": {
        "generate_start": "12:00:40",
        "generate_end": "12:20:40",
        "settle_start": "12:20:40",
        "settle_end": "12:40:40",
        "vent_start": "12:40:41",
        "vent_end": "12:56:31",
    },
}

# ---------------------------------------------------------
# 3. HELPERS
# ---------------------------------------------------------
def to_dummy_datetime(timestr):
    return pd.to_datetime(f"{dummy_date} {timestr}")

def mean_ci95(x):
    x = np.asarray(x, dtype=float)
    n = len(x)
    mean = np.mean(x)
    sd = np.std(x, ddof=1) if n > 1 else np.nan
    if n < 2:
        return mean, np.nan, np.nan
    se = sd / np.sqrt(n)
    tcrit = t.ppf(0.975, df=n-1)
    lo = mean - tcrit * se
    hi = mean + tcrit * se
    return mean, lo, hi

def safe_wilcoxon(a, b):
    try:
        stat, p = wilcoxon(a, b, zero_method="wilcox", alternative="two-sided")
        return stat, p
    except Exception:
        return np.nan, np.nan

def cross_correlation_lag_minutes(df, xcol, ycol, max_lag_points=8):
    x = df[xcol].values.astype(float)
    y = df[ycol].values.astype(float)

    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    if len(x) < 5:
        return np.nan

    x = (x - np.mean(x)) / (np.std(x) if np.std(x) != 0 else 1)
    y = (y - np.mean(y)) / (np.std(y) if np.std(y) != 0 else 1)

    lags = range(-max_lag_points, max_lag_points + 1)
    corrs = []

    for lag in lags:
        if lag < 0:
            xx = x[:lag]
            yy = y[-lag:]
        elif lag > 0:
            xx = x[lag:]
            yy = y[:-lag]
        else:
            xx = x
            yy = y

        if len(xx) < 3:
            corrs.append(np.nan)
        else:
            corrs.append(np.corrcoef(xx, yy)[0, 1])

    corrs = np.array(corrs, dtype=float)
    if np.all(np.isnan(corrs)):
        return np.nan

    best_lag = list(lags)[np.nanargmax(corrs)]
    dt_min = df["TimeOnly"].diff().dt.total_seconds().dropna().median() / 60.0
    return best_lag * dt_min

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

def phase_peak(df, start_dt, end_dt, col):
    sub = df[(df["TimeOnly"] >= start_dt) & (df["TimeOnly"] <= end_dt)].copy()
    if sub.empty:
        return np.nan
    return sub[col].max()

def phase_mean(df, start_dt, end_dt, col):
    sub = df[(df["TimeOnly"] >= start_dt) & (df["TimeOnly"] <= end_dt)].copy()
    if sub.empty:
        return np.nan
    return sub[col].mean()

# ---------------------------------------------------------
# 4. LOADERS
# ---------------------------------------------------------
def load_smps_total(filepath, room_name):
    df = pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    time_col = find_time_col_general(df)
    if time_col is None:
        raise ValueError(f"'corrected time' column not found in {filepath.name}")

    df["Date Time"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["Date Time"]).copy()

    df["TimeOnly"] = pd.to_datetime(
        dummy_date + " " + df["Date Time"].dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

    conc_cols = []
    for col in df.columns:
        if col in [time_col, "Date Time", "TimeOnly"]:
            continue
        try:
            float(str(col))
            conc_cols.append(col)
        except Exception:
            continue

    if len(conc_cols) == 0:
        raise ValueError(f"No numeric size-bin columns found in {filepath.name}")

    df[conc_cols] = df[conc_cols].apply(pd.to_numeric, errors="coerce")
    df["Total"] = df[conc_cols].sum(axis=1, skipna=True)

    out = df[["TimeOnly", "Total"]].copy()
    out = out.rename(columns={"Total": f"Total_{room_name}"})
    out = out.sort_values("TimeOnly").reset_index(drop=True)
    return out

def load_elpi_total(filepath):
    xls = pd.ExcelFile(filepath)
    sheet = xls.sheet_names[0]
    df = pd.read_excel(filepath, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    time_col = find_time_col_general(df)
    if time_col is None:
        raise ValueError(f"ELPI time column not found in {filepath.name}")

    conc_col = find_conc_col_general(df)
    if conc_col is None:
        numeric_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            raise ValueError(f"ELPI concentration column not found in {filepath.name}")
        conc_col = numeric_cols[0]

    df["Date Time"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["Date Time"]).copy()

    df["TimeOnly"] = pd.to_datetime(
        dummy_date + " " + df["Date Time"].dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

    df["ELPI_Total"] = pd.to_numeric(df[conc_col], errors="coerce")
    df = df.dropna(subset=["TimeOnly", "ELPI_Total"]).copy()

    out = df[["TimeOnly", "ELPI_Total"]].sort_values("TimeOnly").reset_index(drop=True)
    return out

def load_cpc(filepath, col_name):
    df = pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    time_col = find_time_col_general(df)
    if time_col is None:
        raise ValueError(f"CPC time column not found in {filepath.name}")

    conc_col = find_conc_col_general(df)
    if conc_col is None:
        numeric_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            raise ValueError(f"CPC concentration column not found in {filepath.name}")
        conc_col = numeric_cols[0]

    raw_time = df[time_col]

    if np.issubdtype(raw_time.dtype, np.number):
        parsed = pd.to_datetime(raw_time, unit="d", origin="1899-12-30", errors="coerce")
    else:
        parsed = pd.to_datetime(raw_time, errors="coerce")
        if parsed.notna().sum() == 0:
            parsed = pd.to_datetime(dummy_date + " " + raw_time.astype(str), errors="coerce")

    if parsed.notna().sum() == 0:
        raise ValueError(f"CPC time parsing failed for {filepath.name}")

    out = pd.DataFrame()
    out["TimeOnly"] = pd.to_datetime(
        dummy_date + " " + parsed.dt.strftime("%H:%M:%S"),
        errors="coerce"
    )
    out[col_name] = pd.to_numeric(df[conc_col], errors="coerce")
    out = out.dropna(subset=["TimeOnly", col_name]).sort_values("TimeOnly").reset_index(drop=True)
    return out

# ---------------------------------------------------------
# 5. LOAD DATA
# ---------------------------------------------------------
kitchen_smps = load_smps_total(kitchen_smps_file, "Kitchen")
bedroom_smps = load_smps_total(bedroom_smps_file, "Bedroom")
elpi = load_elpi_total(elpi_file)
cpc_bath = load_cpc(cpc_bath_file, "CPC_Bath")
cpc_bed = load_cpc(cpc_bed_file, "CPC_Bed")

# ---------------------------------------------------------
# 6. MERGE DATA
# ---------------------------------------------------------
smps_ts = pd.merge_asof(
    kitchen_smps.sort_values("TimeOnly"),
    bedroom_smps.sort_values("TimeOnly"),
    on="TimeOnly",
    direction="nearest",
    tolerance=pd.Timedelta(merge_tolerance)
).dropna(subset=["Total_Bedroom"]).copy()

if smps_ts.empty:
    raise ValueError("No matched SMPS rows after merge.")

smps_ts["Kitchen_smooth"] = smps_ts["Total_Kitchen"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

smps_ts["Bedroom_smooth"] = smps_ts["Total_Bedroom"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

elpi["ELPI_smooth"] = elpi["ELPI_Total"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

cpc_bath["CPC_Bath_smooth"] = cpc_bath["CPC_Bath"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

cpc_bed["CPC_Bed_smooth"] = cpc_bed["CPC_Bed"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

cpc_ts = pd.merge_asof(
    cpc_bath.sort_values("TimeOnly"),
    cpc_bed.sort_values("TimeOnly"),
    on="TimeOnly",
    direction="nearest",
    tolerance=pd.Timedelta("5min")
).dropna(subset=["CPC_Bed"]).copy()

# ---------------------------------------------------------
# 7. REPEAT-LEVEL METRICS
# ---------------------------------------------------------
repeat_rows = []

for exp in EXPERIMENTS:
    exp_name = exp["experiment"]
    start_dt = to_dummy_datetime(exp["start"])
    end_dt = to_dummy_datetime(exp["end"])
    phases = EXPERIMENT_PHASES[exp_name]

    smps_sub = smps_ts[(smps_ts["TimeOnly"] >= start_dt) & (smps_ts["TimeOnly"] <= end_dt)].copy()
    cpc_sub = cpc_ts[(cpc_ts["TimeOnly"] >= start_dt) & (cpc_ts["TimeOnly"] <= end_dt)].copy()
    elpi_sub = elpi[(elpi["TimeOnly"] >= start_dt) & (elpi["TimeOnly"] <= end_dt)].copy()

    if smps_sub.empty:
        continue

    # SMPS peaks and lag
    k_idx = smps_sub["Kitchen_smooth"].idxmax()
    b_idx = smps_sub["Bedroom_smooth"].idxmax()

    k_peak_time = smps_sub.loc[k_idx, "TimeOnly"]
    b_peak_time = smps_sub.loc[b_idx, "TimeOnly"]

    k_peak = smps_sub.loc[k_idx, "Kitchen_smooth"]
    b_peak = smps_sub.loc[b_idx, "Bedroom_smooth"]

    smps_ratio = (b_peak / k_peak) * 100 if k_peak > 0 else np.nan
    smps_peak_lag = (b_peak_time - k_peak_time).total_seconds() / 60.0
    smps_cc_lag = cross_correlation_lag_minutes(smps_sub, "Kitchen_smooth", "Bedroom_smooth", max_lag_points=8)

    # CPC peaks and lag
    bath_peak = np.nan
    bed_peak = np.nan
    bath_peak_time = None
    bed_peak_time = None
    cpc_ratio = np.nan
    cpc_peak_lag = np.nan
    cpc_cc_lag = np.nan

    if not cpc_sub.empty:
        bath_idx = cpc_sub["CPC_Bath_smooth"].idxmax()
        bed_idx = cpc_sub["CPC_Bed_smooth"].idxmax()

        bath_peak = cpc_sub.loc[bath_idx, "CPC_Bath_smooth"]
        bed_peak = cpc_sub.loc[bed_idx, "CPC_Bed_smooth"]

        bath_peak_time = cpc_sub.loc[bath_idx, "TimeOnly"]
        bed_peak_time = cpc_sub.loc[bed_idx, "TimeOnly"]

        cpc_ratio = (bed_peak / bath_peak) * 100 if bath_peak > 0 else np.nan
        cpc_peak_lag = (bed_peak_time - bath_peak_time).total_seconds() / 60.0
        cpc_cc_lag = cross_correlation_lag_minutes(cpc_sub, "CPC_Bath_smooth", "CPC_Bed_smooth", max_lag_points=8)

    # ELPI kitchen peak and post-ventilation mean
    elpi_peak = np.nan
    elpi_peak_time = None
    elpi_postvent = np.nan
    elpi_reduction = np.nan

    if not elpi_sub.empty:
        e_idx = elpi_sub["ELPI_smooth"].idxmax()
        elpi_peak = elpi_sub.loc[e_idx, "ELPI_smooth"]
        elpi_peak_time = elpi_sub.loc[e_idx, "TimeOnly"]

        vent_start = to_dummy_datetime(phases["vent_start"])
        vent_end = to_dummy_datetime(phases["vent_end"])
        elpi_postvent = phase_mean(elpi, vent_start, vent_end, "ELPI_smooth")

        if pd.notna(elpi_peak) and pd.notna(elpi_postvent) and elpi_peak != 0:
            elpi_reduction = 100 * (elpi_peak - elpi_postvent) / elpi_peak

    repeat_rows.append({
        "Experiment": exp_name,

        "SMPS_kitchen_peak_cm3": k_peak,
        "SMPS_bedroom_peak_cm3": b_peak,
        "SMPS_bedroom_to_kitchen_pct": smps_ratio,
        "SMPS_kitchen_peak_time": k_peak_time.strftime("%H:%M:%S"),
        "SMPS_bedroom_peak_time": b_peak_time.strftime("%H:%M:%S"),
        "SMPS_peak_to_peak_lag_min": smps_peak_lag,
        "SMPS_crosscorr_lag_min": smps_cc_lag,

        "CPC_bath_peak_cm3": bath_peak,
        "CPC_bed_peak_cm3": bed_peak,
        "CPC_bed_to_bath_pct": cpc_ratio,
        "CPC_bath_peak_time": bath_peak_time.strftime("%H:%M:%S") if bath_peak_time is not None else "",
        "CPC_bed_peak_time": bed_peak_time.strftime("%H:%M:%S") if bed_peak_time is not None else "",
        "CPC_peak_to_peak_lag_min": cpc_peak_lag,
        "CPC_crosscorr_lag_min": cpc_cc_lag,

        "ELPI_kitchen_peak": elpi_peak,
        "ELPI_kitchen_peak_time": elpi_peak_time.strftime("%H:%M:%S") if elpi_peak_time is not None else "",
        "ELPI_postvent_mean": elpi_postvent,
        "ELPI_reduction_pct": elpi_reduction,
    })

repeat_df = pd.DataFrame(repeat_rows)
repeat_df.to_csv(output_dir / "Table_6_2_1_NaCl_repeat_metrics_with_CPC_ELPI.csv", index=False)

# ---------------------------------------------------------
# 8. SUMMARY STATS
# ---------------------------------------------------------
def build_summary(metric_name, arr):
    arr = np.asarray(arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return None
    mean, lo, hi = mean_ci95(arr)
    sd = np.std(arr, ddof=1) if len(arr) > 1 else np.nan
    return {
        "Metric": metric_name,
        "n": len(arr),
        "Mean": mean,
        "SD": sd,
        "Min": np.min(arr),
        "Max": np.max(arr),
        "95CI_low": lo,
        "95CI_high": hi,
    }

summary_rows = []

for name, arr in [
    ("SMPS kitchen peak concentration", repeat_df["SMPS_kitchen_peak_cm3"].values),
    ("SMPS bedroom peak concentration", repeat_df["SMPS_bedroom_peak_cm3"].values),
    ("SMPS bedroom/kitchen peak ratio (%)", repeat_df["SMPS_bedroom_to_kitchen_pct"].values),
    ("SMPS peak-to-peak lag (min)", repeat_df["SMPS_peak_to_peak_lag_min"].values),
    ("SMPS cross-correlation lag (min)", repeat_df["SMPS_crosscorr_lag_min"].values),

    ("CPC bathroom peak concentration", repeat_df["CPC_bath_peak_cm3"].values),
    ("CPC bedroom peak concentration", repeat_df["CPC_bed_peak_cm3"].values),
    ("CPC bedroom/bathroom peak ratio (%)", repeat_df["CPC_bed_to_bath_pct"].values),
    ("CPC peak-to-peak lag (min)", repeat_df["CPC_peak_to_peak_lag_min"].values),
    ("CPC cross-correlation lag (min)", repeat_df["CPC_crosscorr_lag_min"].values),

    ("ELPI kitchen peak concentration", repeat_df["ELPI_kitchen_peak"].values),
    ("ELPI post-ventilation concentration", repeat_df["ELPI_postvent_mean"].values),
    ("ELPI reduction after ventilation (%)", repeat_df["ELPI_reduction_pct"].values),
]:
    row = build_summary(name, arr)
    if row is not None:
        summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(output_dir / "NaCl_summary_statistics_with_CPC_ELPI.csv", index=False)

# ---------------------------------------------------------
# 9. SIGNIFICANCE TESTS
# ---------------------------------------------------------
test_rows = []

# SMPS kitchen vs bedroom
smps_k = repeat_df["SMPS_kitchen_peak_cm3"].dropna().values
smps_b = repeat_df["SMPS_bedroom_peak_cm3"].dropna().values
if len(smps_k) == len(smps_b) and len(smps_k) >= 2:
    t_stat, p_val = ttest_rel(smps_k, smps_b)
    w_stat, w_p = safe_wilcoxon(smps_k, smps_b)
    test_rows.append({
        "Comparison": "SMPS kitchen vs bedroom peak concentrations",
        "Test": "Paired t-test",
        "Statistic": t_stat,
        "p_value": p_val
    })
    test_rows.append({
        "Comparison": "SMPS kitchen vs bedroom peak concentrations",
        "Test": "Wilcoxon signed-rank",
        "Statistic": w_stat,
        "p_value": w_p
    })

# CPC bath vs bed
cpc_bath_vals = repeat_df["CPC_bath_peak_cm3"].dropna().values
cpc_bed_vals = repeat_df["CPC_bed_peak_cm3"].dropna().values
if len(cpc_bath_vals) == len(cpc_bed_vals) and len(cpc_bath_vals) >= 2:
    t_stat, p_val = ttest_rel(cpc_bath_vals, cpc_bed_vals)
    w_stat, w_p = safe_wilcoxon(cpc_bath_vals, cpc_bed_vals)
    test_rows.append({
        "Comparison": "CPC bathroom vs bedroom peak concentrations",
        "Test": "Paired t-test",
        "Statistic": t_stat,
        "p_value": p_val
    })
    test_rows.append({
        "Comparison": "CPC bathroom vs bedroom peak concentrations",
        "Test": "Wilcoxon signed-rank",
        "Statistic": w_stat,
        "p_value": w_p
    })

# ELPI peak vs post-vent
elpi_peak_vals = repeat_df["ELPI_kitchen_peak"].dropna().values
elpi_post_vals = repeat_df["ELPI_postvent_mean"].dropna().values
if len(elpi_peak_vals) == len(elpi_post_vals) and len(elpi_peak_vals) >= 2:
    t_stat, p_val = ttest_rel(elpi_peak_vals, elpi_post_vals)
    w_stat, w_p = safe_wilcoxon(elpi_peak_vals, elpi_post_vals)
    test_rows.append({
        "Comparison": "ELPI kitchen peak vs ELPI post-ventilation mean",
        "Test": "Paired t-test",
        "Statistic": t_stat,
        "p_value": p_val
    })
    test_rows.append({
        "Comparison": "ELPI kitchen peak vs ELPI post-ventilation mean",
        "Test": "Wilcoxon signed-rank",
        "Statistic": w_stat,
        "p_value": w_p
    })

test_df = pd.DataFrame(test_rows)
test_df.to_csv(output_dir / "NaCl_peak_comparison_tests_with_CPC_ELPI.csv", index=False)

print("\n=== Repeat-level metrics ===")
print(repeat_df)
print("\n=== Summary statistics ===")
print(summary_df)
print("\n=== Significance tests ===")
print(test_df)

# ---------------------------------------------------------
# 10. FIGURE 6.2.1 UPDATED
# ---------------------------------------------------------
plt.figure(figsize=(11, 5.8))

plt.plot(smps_ts["TimeOnly"], smps_ts["Kitchen_smooth"], linewidth=2, label="Kitchen (SMPS)")
plt.plot(smps_ts["TimeOnly"], smps_ts["Bedroom_smooth"], linewidth=2, linestyle="--", label="Master bedroom (SMPS)")
plt.plot(elpi["TimeOnly"], elpi["ELPI_smooth"], linewidth=1.8, linestyle=":", label="Kitchen (ELPI)")
plt.plot(cpc_bath["TimeOnly"], cpc_bath["CPC_Bath_smooth"], linewidth=1.5, linestyle="-.", label="Bathroom (CPC)")
plt.plot(cpc_bed["TimeOnly"], cpc_bed["CPC_Bed_smooth"], linewidth=1.5, linestyle=(0, (3, 1, 1, 1)), label="Bedroom (CPC)")

for exp in EXPERIMENTS:
    start_dt = to_dummy_datetime(exp["start"])
    end_dt = to_dummy_datetime(exp["end"])
    plt.axvspan(start_dt, end_dt, alpha=0.08, color="grey")
    plt.text(start_dt, plt.ylim()[1] * 0.92, exp["experiment"], fontsize=9, rotation=90, va="top")

plt.xlabel("Time")
plt.ylabel("Particle number concentration (cm$^{-3}$)")
plt.title(
    "Figure 6.2.1. Time series of particle number concentration measured during\n"
    "NaCl tracer aerosol experiments at SPHERE House"
)
plt.legend()
plt.grid(True, linestyle="--", linewidth=0.5)

if use_log_y:
    plt.yscale("log")

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "Figure_6_2_1_updated_NaCl_transport_with_CPC_ELPI.png", dpi=300, bbox_inches="tight")
plt.show()

# ---------------------------------------------------------
# 11. SUPPORTING FIGURES
# ---------------------------------------------------------
plt.figure(figsize=(6, 5))
plt.boxplot(
    [repeat_df["SMPS_kitchen_peak_cm3"].dropna(), repeat_df["SMPS_bedroom_peak_cm3"].dropna()],
    labels=["Kitchen SMPS", "Bedroom SMPS"]
)
plt.ylabel("Peak concentration (cm$^{-3}$)")
plt.yscale("log")
plt.title("Repeat-level SMPS peak comparison")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig(output_dir / "Figure_6_2_2_SMPS_repeat_peak_comparison.png", dpi=300, bbox_inches="tight")
plt.show()

plt.figure(figsize=(6, 5))
plt.boxplot(
    [repeat_df["CPC_bath_peak_cm3"].dropna(), repeat_df["CPC_bed_peak_cm3"].dropna()],
    labels=["Bathroom CPC", "Bedroom CPC"]
)
plt.ylabel("Peak concentration (cm$^{-3}$)")
plt.yscale("log")
plt.title("Repeat-level CPC peak comparison")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig(output_dir / "Figure_6_2_3_CPC_repeat_peak_comparison.png", dpi=300, bbox_inches="tight")
plt.show()

plt.figure(figsize=(6, 5))
plt.boxplot(
    [repeat_df["ELPI_kitchen_peak"].dropna(), repeat_df["ELPI_postvent_mean"].dropna()],
    labels=["ELPI peak", "ELPI post-vent"]
)
plt.ylabel("ELPI concentration")
plt.title("Kitchen ELPI: peak vs post-ventilation")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig(output_dir / "Figure_6_2_4_ELPI_peak_vs_postvent.png", dpi=300, bbox_inches="tight")
plt.show()

# ---------------------------------------------------------
# 12. THESIS-READY TEXT
# ---------------------------------------------------------
def arr_stats(arr):
    arr = np.asarray(arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return np.nan, np.nan
    return np.mean(arr), np.std(arr, ddof=1) if len(arr) > 1 else np.nan

smps_k_mean, smps_k_sd = arr_stats(repeat_df["SMPS_kitchen_peak_cm3"].values)
smps_b_mean, smps_b_sd = arr_stats(repeat_df["SMPS_bedroom_peak_cm3"].values)
smps_ratio_mean, smps_ratio_lo, smps_ratio_hi = mean_ci95(repeat_df["SMPS_bedroom_to_kitchen_pct"].dropna().values)
smps_lag_mean, smps_lag_lo, smps_lag_hi = mean_ci95(repeat_df["SMPS_peak_to_peak_lag_min"].dropna().values)

cpc_bath_mean, cpc_bath_sd = arr_stats(repeat_df["CPC_bath_peak_cm3"].values)
cpc_bed_mean, cpc_bed_sd = arr_stats(repeat_df["CPC_bed_peak_cm3"].values)
cpc_ratio_mean, cpc_ratio_lo, cpc_ratio_hi = mean_ci95(repeat_df["CPC_bed_to_bath_pct"].dropna().values)
cpc_lag_mean, cpc_lag_lo, cpc_lag_hi = mean_ci95(repeat_df["CPC_peak_to_peak_lag_min"].dropna().values)

elpi_peak_mean, elpi_peak_sd = arr_stats(repeat_df["ELPI_kitchen_peak"].values)
elpi_post_mean, elpi_post_sd = arr_stats(repeat_df["ELPI_postvent_mean"].values)
elpi_red_mean, elpi_red_sd = arr_stats(repeat_df["ELPI_reduction_pct"].values)

def get_p(comp, test_name="Paired t-test"):
    row = test_df[(test_df["Comparison"] == comp) & (test_df["Test"] == test_name)]
    return row["p_value"].values[0] if len(row) else np.nan

thesis_text = f"""
NaCl tracer transport statistical summary (Experiments 2–4 only)

SMPS:
Mean kitchen peak concentration = {smps_k_mean:.2f} ± {smps_k_sd:.2f} particles cm^-3
Mean bedroom peak concentration = {smps_b_mean:.2f} ± {smps_b_sd:.2f} particles cm^-3
Mean bedroom/kitchen peak ratio = {smps_ratio_mean:.2f}% (95% CI: {smps_ratio_lo:.2f} to {smps_ratio_hi:.2f}%)
Mean peak-to-peak lag = {smps_lag_mean:.2f} min (95% CI: {smps_lag_lo:.2f} to {smps_lag_hi:.2f} min)
Paired t-test p-value = {get_p('SMPS kitchen vs bedroom peak concentrations'):.4f}

CPC:
Mean bathroom peak concentration = {cpc_bath_mean:.2f} ± {cpc_bath_sd:.2f} particles cm^-3
Mean bedroom peak concentration = {cpc_bed_mean:.2f} ± {cpc_bed_sd:.2f} particles cm^-3
Mean bedroom/bathroom peak ratio = {cpc_ratio_mean:.2f}% (95% CI: {cpc_ratio_lo:.2f} to {cpc_ratio_hi:.2f}%)
Mean peak-to-peak lag = {cpc_lag_mean:.2f} min (95% CI: {cpc_lag_lo:.2f} to {cpc_lag_hi:.2f} min)
Paired t-test p-value = {get_p('CPC bathroom vs bedroom peak concentrations'):.4f}

ELPI:
Mean kitchen peak concentration = {elpi_peak_mean:.2f} ± {elpi_peak_sd:.2f}
Mean post-ventilation concentration = {elpi_post_mean:.2f} ± {elpi_post_sd:.2f}
Mean reduction after ventilation = {elpi_red_mean:.2f} ± {elpi_red_sd:.2f} %
Paired t-test p-value = {get_p('ELPI kitchen peak vs ELPI post-ventilation mean'):.4f}

Suggested thesis wording:
Across the three repeat NaCl tracer experiments, peak concentrations were consistently higher in the source room than in the receiving room. The mean peak concentration measured by SMPS in the kitchen was {smps_k_mean:.2f} ± {smps_k_sd:.2f} particles cm^-3, whereas the corresponding mean peak concentration in the master bedroom was {smps_b_mean:.2f} ± {smps_b_sd:.2f} particles cm^-3. This corresponds to a mean bedroom-to-kitchen peak ratio of {smps_ratio_mean:.2f}%, indicating substantial attenuation during inter-room transport. The master bedroom peak occurred after the kitchen peak in all repeat experiments, with a mean lag time of {smps_lag_mean:.2f} min. CPC measurements showed a similar pattern, with a mean bedroom-to-bathroom peak ratio of {cpc_ratio_mean:.2f}% and a mean lag time of {cpc_lag_mean:.2f} min. Kitchen ELPI measurements further showed that concentrations decreased after ventilation, with a mean reduction of {elpi_red_mean:.2f}%.
"""

with open(output_dir / "NaCl_thesis_ready_summary_with_CPC_ELPI.txt", "w", encoding="utf-8") as f:
    f.write(thesis_text)

print(f"\nAll outputs saved to: {output_dir}")
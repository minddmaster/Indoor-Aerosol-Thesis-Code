# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 14:54:57 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
MASTER SCRIPT
Charge-state analysis — Day 1 (24-02-2025)
SPHERE House

Produces:
    Figure 6.2.1a  SMPS COM32 vs COM33
    Figure 6.2.1b  ELPI
    Figure 6.2.1c  DRX PM2.5
    Table 6.2.2    Peak summary
    Table 6.2.3    Paired nearest-time statistics
    Table 6.2.4    Run-level summary metrics
    Table 6.2.5    Two-way ANOVA
    Table 6.2.6    Mixed model summary

Notes:
- COM32 = with Am-241 neutraliser
- COM33 = without Am-241 neutraliser
- ELPI = floor level
- DRX = kitchen floor, ~0.5 m lower than ELPI sampling point
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from scipy.stats import ttest_rel
import statsmodels.api as sm
from statsmodels.formula.api import ols
import statsmodels.formula.api as smf


# =========================================================
# FILE PATHS
# =========================================================
SMPS_COM32 = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Charge state analysis/DAY1 SMPS DATA_COM32.xlsx"
SMPS_COM33 = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Charge state analysis/DAY1 SMPS DATA_COM33.xlsx"
DRX_FILE   = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Charge state analysis/drx_TEST 1_027_day1_exel.xlsx"
ELPI_FILE  = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Charge state analysis/elpi day1.xlsx"

OUTPUT_DIR = os.path.join(os.path.dirname(SMPS_COM32), "charge_state_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FORCED_DATE = "2025-02-24"

# Main display/filter window
START_TIME = pd.to_datetime("2025-02-24 14:45:00")
END_TIME   = pd.to_datetime("2025-02-24 18:00:00")

# DRX time offset correction
DRX_HOUR_SHIFT = 12


# =========================================================
# EXPERIMENT WINDOWS
# =========================================================
CONDITIONS = [
    {
        "label": "No corona charger",
        "color": "lightgrey",
        "runs": [
            ("Test",    "14:50:01", "15:03:00"),
            ("Repeat1", "15:12:00", "15:22:00"),
            ("Repeat2", "15:30:00", "15:40:00"),
            ("Repeat3", "15:47:00", "15:57:00"),
            ("Final",   "17:41:35", "17:51:35"),
        ],
    },
    {
        "label": "Corona charger",
        "color": "lightblue",
        "runs": [
            ("Repeat1", "16:11:10", "16:21:10"),
            ("Repeat2", "16:26:30", "16:36:30"),
            ("Repeat3", "16:40:40", "16:50:40"),
        ],
    },
    {
        "label": "Corona charger + ionizer",
        "color": "navajowhite",
        "runs": [
            ("Repeat1", "16:59:10", "17:09:10"),
            ("Repeat2", "17:11:30", "17:21:30"),
            ("Repeat3", "17:25:30", "17:35:30"),
        ],
    },
]

GEN_WINDOWS = [
    ("14:50:01", "14:56:00", "grey"),
    ("15:12:00", "15:17:00", "grey"),
    ("15:30:00", "15:35:00", "grey"),
    ("15:47:00", "15:52:00", "grey"),
    ("16:11:10", "16:16:10", "lightblue"),
    ("16:26:30", "16:31:30", "lightblue"),
    ("16:40:40", "16:45:40", "lightblue"),
    ("16:59:10", "17:04:10", "orange"),
    ("17:11:30", "17:16:30", "orange"),
    ("17:25:30", "17:30:30", "orange"),
    ("17:41:35", "17:46:35", "grey"),
]


# =========================================================
# HELPERS
# =========================================================
def dt(hms: str) -> pd.Timestamp:
    return pd.to_datetime(f"{FORCED_DATE} {hms}")

def safe_peak(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return np.nan if s.empty else s.max()

def safe_mean(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return np.nan if s.empty else s.mean()

def safe_std(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return np.nan if s.empty else s.std()

def smooth_series(df: pd.DataFrame, col: str, window: int = 3) -> pd.Series:
    return df[col].rolling(window, center=True, min_periods=1).mean()

def filter_window(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df["Time"] >= start) & (df["Time"] <= end)].copy()

def extract_time_from_string(s: pd.Series) -> pd.Series:
    extracted = s.astype(str).str.strip().str.extract(r"(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})")[0]
    return extracted

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


# =========================================================
# LOADERS
# =========================================================
def load_smps(file, forced_date=FORCED_DATE):
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

            out = pd.DataFrame()
            out["Time"] = parse_time_series(df[time_col], forced_date)

            total_col = None
            for c in df.columns:
                c_str = str(c).lower().strip()
                if "total" in c_str and "conc" in c_str:
                    total_col = c
                    break

            if total_col is not None:
                out["Total"] = pd.to_numeric(df[total_col], errors="coerce")
            else:
                size_cols = []
                for c in df.columns:
                    if c == time_col:
                        continue
                    try:
                        float(str(c).strip())
                        size_cols.append(c)
                    except Exception:
                        pass

                if len(size_cols) == 0:
                    continue

                out["Total"] = df[size_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)

            out = out.dropna(subset=["Time", "Total"]).sort_values("Time").reset_index(drop=True)
            if len(out) < 5:
                continue

            print(f"Loaded {os.path.basename(file)} using skiprows={skip}")
            print(out.head())
            return out

        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to load SMPS file {os.path.basename(file)}. Last error: {last_error}")


def load_drx(file, forced_date=FORCED_DATE, hour_shift=12):
    df = pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]
    print("\nDRX columns:", df.columns.tolist())

    time_col = None
    for col in df.columns:
        if "time" in str(col).lower():
            time_col = col
            break
    if time_col is None:
        raise ValueError("No DRX time column found")

    value_col = None
    for col in df.columns:
        c = str(col).lower().replace(" ", "")
        if "pm2.5" in c or "pm25" in c or "pm2_5" in c:
            value_col = col
            break
    if value_col is None:
        raise ValueError("No DRX PM2.5 column found")

    raw_time = df[time_col]

    if np.issubdtype(raw_time.dtype, np.number):
        parsed = pd.to_datetime(raw_time, unit="d", origin="1899-12-30", errors="coerce")
    else:
        raw_str = raw_time.astype(str).str.strip()

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

    out = pd.DataFrame()
    out["Time"] = pd.to_datetime(
        forced_date + " " + parsed.dt.strftime("%H:%M:%S"),
        errors="coerce"
    )
    out["Time"] = out["Time"] + pd.Timedelta(hours=hour_shift)
    out["DRX_PM25"] = pd.to_numeric(df[value_col], errors="coerce")
    out = out.dropna(subset=["Time", "DRX_PM25"]).sort_values("Time").reset_index(drop=True)

    print("\nDRX after hour shift:")
    print(out.head())
    return out


def load_elpi(file, forced_date=FORCED_DATE):
    last_error = None

    for skip in [40, 35, 30, 45, 50, 25, 20]:
        try:
            df = pd.read_excel(file, skiprows=skip, header=None)
            if df.shape[1] < 2:
                continue

            out = pd.DataFrame()
            out["Time"] = parse_time_series(df.iloc[:, 0], forced_date)

            conc_idx = None
            if df.shape[1] > 32:
                test = pd.to_numeric(df.iloc[:, 32], errors="coerce")
                if test.notna().sum() > 10:
                    conc_idx = 32

            if conc_idx is None:
                for j in range(1, df.shape[1]):
                    test = pd.to_numeric(df.iloc[:, j], errors="coerce")
                    if test.notna().sum() > 20:
                        conc_idx = j
                        break

            if conc_idx is None:
                continue

            out["ELPI_Total"] = pd.to_numeric(df.iloc[:, conc_idx], errors="coerce")
            out = out.dropna(subset=["Time", "ELPI_Total"]).sort_values("Time").reset_index(drop=True)

            if len(out) < 5:
                continue

            print(f"Loaded {os.path.basename(file)} | skiprows={skip}, conc_col={conc_idx}")
            print(out.head())
            return out

        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to load ELPI file {os.path.basename(file)}. Last error: {last_error}")


# =========================================================
# RUN-LEVEL METRICS
# =========================================================
def get_run_metrics(df, value_col, instrument_name, instrument_state, charge_condition, run_name, start_hms, end_hms):
    start = dt(start_hms)
    end = dt(end_hms)
    sub = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()

    if sub.empty:
        return {
            "instrument": instrument_name,
            "instrument_state": instrument_state,
            "charge_condition": charge_condition,
            "run": run_name,
            "n_points": 0,
            "mean_conc": np.nan,
            "peak_conc": np.nan,
            "std_conc": np.nan,
            "auc": np.nan
        }

    y = pd.to_numeric(sub[value_col], errors="coerce").dropna()

    if y.empty:
        return {
            "instrument": instrument_name,
            "instrument_state": instrument_state,
            "charge_condition": charge_condition,
            "run": run_name,
            "n_points": 0,
            "mean_conc": np.nan,
            "peak_conc": np.nan,
            "std_conc": np.nan,
            "auc": np.nan
        }

    auc = np.trapz(y.values, dx=1)

    return {
        "instrument": instrument_name,
        "instrument_state": instrument_state,
        "charge_condition": charge_condition,
        "run": run_name,
        "n_points": len(y),
        "mean_conc": y.mean(),
        "peak_conc": y.max(),
        "std_conc": y.std(),
        "auc": auc
    }


# =========================================================
# LOAD DATA
# =========================================================
print("Loading data...")

com32 = load_smps(SMPS_COM32)
com33 = load_smps(SMPS_COM33)
drx   = load_drx(DRX_FILE, hour_shift=DRX_HOUR_SHIFT)
elpi  = load_elpi(ELPI_FILE)

# Full-window filtered data for figures and top-level summaries
com32 = filter_window(com32, START_TIME, END_TIME)
com33 = filter_window(com33, START_TIME, END_TIME)
drx   = filter_window(drx, START_TIME, END_TIME)
elpi  = filter_window(elpi, START_TIME, END_TIME)

print("\nRows after filtering:")
print("COM32:", len(com32))
print("COM33:", len(com33))
print("DRX  :", len(drx))
print("ELPI :", len(elpi))


# =========================================================
# TOP-LEVEL SUMMARY TABLE
# =========================================================
summary_df = pd.DataFrame({
    "Metric": ["Mean", "Std", "Peak"],
    "COM32": [safe_mean(com32["Total"]), safe_std(com32["Total"]), safe_peak(com32["Total"])],
    "COM33": [safe_mean(com33["Total"]), safe_std(com33["Total"]), safe_peak(com33["Total"])],
    "ELPI": [safe_mean(elpi["ELPI_Total"]), safe_std(elpi["ELPI_Total"]), safe_peak(elpi["ELPI_Total"])],
    "DRX_PM25": [safe_mean(drx["DRX_PM25"]), safe_std(drx["DRX_PM25"]), safe_peak(drx["DRX_PM25"])],
})

summary_path = os.path.join(OUTPUT_DIR, "Table_6_2_2_charge_summary.csv")
summary_df.to_csv(summary_path, index=False)

print("\nSummary table:")
print(summary_df)


# =========================================================
# FIGURE 6.2.1a — SMPS
# =========================================================
plt.figure(figsize=(11, 5.5))

com32_plot = com32.copy()
com33_plot = com33.copy()
com32_plot["Total_smooth"] = smooth_series(com32_plot, "Total", window=3)
com33_plot["Total_smooth"] = smooth_series(com33_plot, "Total", window=3)

plt.plot(com32_plot["Time"], com32_plot["Total_smooth"], label="SMPS COM32 (Am-241 neutralised)", linewidth=2)
plt.plot(com33_plot["Time"], com33_plot["Total_smooth"], label="SMPS COM33 (non-neutralised)", linewidth=2)

condition_labels_done = set()
for cond in CONDITIONS:
    for _, start_hms, end_hms in cond["runs"]:
        label = cond["label"] if cond["label"] not in condition_labels_done else None
        plt.axvspan(dt(start_hms), dt(end_hms), color=cond["color"], alpha=0.18, label=label)
        condition_labels_done.add(cond["label"])

for start_hms, end_hms, color in GEN_WINDOWS:
    plt.axvspan(dt(start_hms), dt(end_hms), color=color, alpha=0.30)

plt.xlim(START_TIME, END_TIME)
plt.xlabel("Time")
plt.ylabel("Particle number concentration (particles cm$^{-3}$)")
plt.title("Figure 6.2.1a. SMPS response under different charge-state conditions")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()
plt.tight_layout()
fig_a = os.path.join(OUTPUT_DIR, "Figure_6_2_1a_SMPS_charge_state.png")
plt.savefig(fig_a, dpi=300, bbox_inches="tight")
plt.show()


# =========================================================
# FIGURE 6.2.1b — ELPI
# =========================================================
plt.figure(figsize=(11, 5.5))

elpi_plot = elpi.copy()
elpi_plot["ELPI_smooth"] = smooth_series(elpi_plot, "ELPI_Total", window=5)
plt.plot(elpi_plot["Time"], elpi_plot["ELPI_smooth"], label="ELPI (kitchen floor)", linewidth=1.6)

condition_labels_done = set()
for cond in CONDITIONS:
    for _, start_hms, end_hms in cond["runs"]:
        label = cond["label"] if cond["label"] not in condition_labels_done else None
        plt.axvspan(dt(start_hms), dt(end_hms), color=cond["color"], alpha=0.18, label=label)
        condition_labels_done.add(cond["label"])

for start_hms, end_hms, color in GEN_WINDOWS:
    plt.axvspan(dt(start_hms), dt(end_hms), color=color, alpha=0.30)

plt.xlim(START_TIME, END_TIME)
plt.xlabel("Time")
plt.ylabel("Particle number concentration")
plt.title("Figure 6.2.1b. ELPI response under different charge-state conditions")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()
plt.tight_layout()
fig_b = os.path.join(OUTPUT_DIR, "Figure_6_2_1b_ELPI_charge_state.png")
plt.savefig(fig_b, dpi=300, bbox_inches="tight")
plt.show()


# =========================================================
# FIGURE 6.2.1c — DRX
# =========================================================
plt.figure(figsize=(11, 5.5))

drx_plot = drx.copy()
drx_plot = drx_plot.set_index("Time").resample("1min").mean().reset_index()
drx_plot["DRX_smooth"] = smooth_series(drx_plot, "DRX_PM25", window=3)
plt.plot(drx_plot["Time"], drx_plot["DRX_smooth"], label="DRX PM$_{2.5}$", linewidth=1.6, linestyle="--")

condition_labels_done = set()
for cond in CONDITIONS:
    for _, start_hms, end_hms in cond["runs"]:
        label = cond["label"] if cond["label"] not in condition_labels_done else None
        plt.axvspan(dt(start_hms), dt(end_hms), color=cond["color"], alpha=0.18, label=label)
        condition_labels_done.add(cond["label"])

for start_hms, end_hms, color in GEN_WINDOWS:
    plt.axvspan(dt(start_hms), dt(end_hms), color=color, alpha=0.30)

plt.xlim(START_TIME, END_TIME)
plt.xlabel("Time")
plt.ylabel("PM$_{2.5}$ mass concentration (µg m$^{-3}$)")
plt.title("Figure 6.2.1c. DRX PM$_{2.5}$ response under different charge-state conditions")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()
plt.tight_layout()
fig_c = os.path.join(OUTPUT_DIR, "Figure_6_2_1c_DRX_charge_state.png")
plt.savefig(fig_c, dpi=300, bbox_inches="tight")
plt.show()


# =========================================================
# PAIRED STATISTICS — NEAREST-TIME MATCHING
# =========================================================
print("\nRunning paired statistical analysis with nearest-time matching...")

com32_sorted = com32[["Time", "Total"]].sort_values("Time").reset_index(drop=True)
com33_sorted = com33[["Time", "Total"]].sort_values("Time").reset_index(drop=True)

merged = pd.merge_asof(
    com32_sorted,
    com33_sorted,
    on="Time",
    direction="nearest",
    tolerance=pd.Timedelta("10s"),
    suffixes=("_COM32", "_COM33")
)

merged = merged.dropna()

print("Aligned data points:", len(merged))

if len(merged) > 2:
    t_stat, p_value = ttest_rel(merged["Total_COM32"], merged["Total_COM33"])
    diff = merged["Total_COM33"] - merged["Total_COM32"]
    diff_std = diff.std(ddof=1)
    cohen_d = diff.mean() / diff_std if diff_std != 0 else np.nan

    mean_32 = merged["Total_COM32"].mean()
    mean_33 = merged["Total_COM33"].mean()

    paired_stats_df = pd.DataFrame({
        "Metric": ["n_pairs", "Mean_COM32", "Mean_COM33", "t_statistic", "p_value", "Cohens_d"],
        "Value": [len(merged), mean_32, mean_33, t_stat, p_value, cohen_d]
    })

    print("\n=== PAIRED STATISTICAL RESULTS ===")
    print(paired_stats_df)

    if pd.notna(p_value):
        if p_value < 0.001:
            print("\nThesis sentence:")
            print("A paired comparison of time-matched SMPS measurements showed that the non-neutralised configuration (COM33) recorded significantly higher concentrations than the neutralised configuration (COM32) (paired t-test, p < 0.001), confirming a systematic charge-state effect on the measured aerosol response.")
        elif p_value < 0.05:
            print("\nThesis sentence:")
            print("A paired comparison of time-matched SMPS measurements showed that the non-neutralised configuration (COM33) recorded significantly higher concentrations than the neutralised configuration (COM32) (paired t-test, p < 0.05), confirming a systematic charge-state effect on the measured aerosol response.")
        else:
            print("\nThesis sentence:")
            print("A paired comparison of time-matched SMPS measurements indicated that COM33 tended to record higher concentrations than COM32, although this difference was not statistically significant at the 5% level.")
else:
    paired_stats_df = pd.DataFrame({
        "Metric": ["n_pairs", "Mean_COM32", "Mean_COM33", "t_statistic", "p_value", "Cohens_d"],
        "Value": [len(merged), np.nan, np.nan, np.nan, np.nan, np.nan]
    })
    print("Not enough aligned points for paired t-test.")

paired_stats_path = os.path.join(OUTPUT_DIR, "Table_6_2_3_paired_stats_nearest_time.csv")
paired_stats_df.to_csv(paired_stats_path, index=False)


# =========================================================
# RUN-LEVEL SUMMARY
# =========================================================
condition_map = {
    "No corona charger": "baseline",
    "Corona charger": "corona",
    "Corona charger + ionizer": "corona_ionizer"
}

rows = []

for cond in CONDITIONS:
    cond_name = condition_map[cond["label"]]

    for run_name, start_hms, end_hms in cond["runs"]:
        run_id = f"{cond_name}_{run_name}"

        rows.append(get_run_metrics(
            com32, "Total",
            instrument_name="COM32",
            instrument_state="neutralised",
            charge_condition=cond_name,
            run_name=run_id,
            start_hms=start_hms,
            end_hms=end_hms
        ))

        rows.append(get_run_metrics(
            com33, "Total",
            instrument_name="COM33",
            instrument_state="non_neutralised",
            charge_condition=cond_name,
            run_name=run_id,
            start_hms=start_hms,
            end_hms=end_hms
        ))

run_summary_df = pd.DataFrame(rows)
run_summary_path = os.path.join(OUTPUT_DIR, "Table_6_2_4_run_level_summary.csv")
run_summary_df.to_csv(run_summary_path, index=False)

print("\nRun-level summary:")
print(run_summary_df)


# =========================================================
# TWO-WAY ANOVA
# =========================================================
anova_df = run_summary_df.dropna(subset=["peak_conc"]).copy()

if len(anova_df) > 0:
    try:
        anova_model = ols("peak_conc ~ C(charge_condition) * C(instrument_state)", data=anova_df).fit()
        anova_table = sm.stats.anova_lm(anova_model, typ=2)

        print("\n=== TWO-WAY ANOVA: PEAK CONCENTRATION ===")
        print(anova_table)

        anova_path = os.path.join(OUTPUT_DIR, "Table_6_2_5_two_way_anova_peak.csv")
        anova_table.to_csv(anova_path)
    except Exception as e:
        print("\nANOVA failed:", e)
        anova_table = pd.DataFrame({"Error": [str(e)]})
        anova_path = os.path.join(OUTPUT_DIR, "Table_6_2_5_two_way_anova_peak.csv")
        anova_table.to_csv(anova_path, index=False)
else:
    anova_table = pd.DataFrame({"Error": ["No valid data for ANOVA"]})
    anova_path = os.path.join(OUTPUT_DIR, "Table_6_2_5_two_way_anova_peak.csv")
    anova_table.to_csv(anova_path, index=False)


# =========================================================
# MIXED MODEL
# =========================================================
mixed_df = run_summary_df.dropna(subset=["peak_conc"]).copy()

try:
    if len(mixed_df) > 0:
        mixed_model = smf.mixedlm(
            "peak_conc ~ C(charge_condition) * C(instrument_state)",
            data=mixed_df,
            groups=mixed_df["run"]
        )
        mixed_result = mixed_model.fit()

        print("\n=== MIXED MODEL: PEAK CONCENTRATION ===")
        print(mixed_result.summary())

        mixed_summary_path = os.path.join(OUTPUT_DIR, "Table_6_2_6_mixed_model_peak.txt")
        with open(mixed_summary_path, "w", encoding="utf-8") as f:
            f.write(str(mixed_result.summary()))
    else:
        mixed_summary_path = os.path.join(OUTPUT_DIR, "Table_6_2_6_mixed_model_peak.txt")
        with open(mixed_summary_path, "w", encoding="utf-8") as f:
            f.write("No valid data for mixed model.")
except Exception as e:
    print("\nMixed model failed:", e)
    mixed_summary_path = os.path.join(OUTPUT_DIR, "Table_6_2_6_mixed_model_peak.txt")
    with open(mixed_summary_path, "w", encoding="utf-8") as f:
        f.write(f"Mixed model failed: {e}")


# =========================================================
# FINAL OUTPUTS
# =========================================================
print("\nSaved files:")
print(fig_a)
print(fig_b)
print(fig_c)
print(summary_path)
print(paired_stats_path)
print(run_summary_path)
print(anova_path)
print(mixed_summary_path)
print("\nOutputs saved to:", OUTPUT_DIR)
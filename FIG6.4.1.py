# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 22:01:04 2026

@author: papkp
"""

# =========================================================
# SECTION 6.4 / FIGURE 6.4.1 – DEEP FRY ANALYSIS
# Onion ring deep frying: SMPS, CPC, ELPI, DustTrak DRX
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# =========================================================
# 1. FILE PATHS
# =========================================================
cpc_bath_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/CPC DAY 4 OUTSIDE BATH_EXCEL.csv"
)

cpc_bed_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/cpc012_Master Bedroom_Day4.csv"
)

elpi_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/day4 elpi data.xlsx"
)

smps_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/DAY4 SMPS DATA_COM32.xlsx"
)

drx_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1/sphereday4_drX.csv"
)

# =========================================================
# 2. DEEP FRY TIMELINE
# =========================================================
DEEPFRY_TIMELINE = [
    ("Exp1 no fan", "12:41:15", "13:03:15"),
    ("Exp2 with fan", "13:13:33", "13:35:40"),
    ("Exp3 no fan", "13:41:30", "14:03:40"),
    ("Exp4 with fan", "14:10:20", "14:32:25"),
    ("Exp5 no fan", "14:39:13", "15:01:20"),
    ("Exp6 with fan", "15:06:40", "15:28:55"),
]

plot_start = "12:35:00"
plot_end   = "15:35:00"

# =========================================================
# 3. SETTINGS
# =========================================================
smooth_smps = 3
smooth_cpc_bed = 3
smooth_cpc_bath = 1
smooth_elpi = 5
smooth_drx = 5
use_log_y = True

phase_colors = {
    "Exp1 no fan": "#f4cccc",
    "Exp2 with fan": "#d9ead3",
    "Exp3 no fan": "#f4cccc",
    "Exp4 with fan": "#d9ead3",
    "Exp5 no fan": "#f4cccc",
    "Exp6 with fan": "#d9ead3",
}
phase_alpha = 0.18

# =========================================================
# 4. HELPERS
# =========================================================
def parse_time_series(series):
    dt = pd.to_datetime(series, errors="coerce")
    if dt.notna().sum() > 0:
        return dt

    s = series.astype(str).str.strip()
    dt = pd.to_datetime(s, errors="coerce")
    if dt.notna().sum() > 0:
        return dt

    dt = pd.to_datetime("2000-01-01 " + s, errors="coerce")
    if dt.notna().sum() > 0:
        return dt

    num = pd.to_numeric(series, errors="coerce")
    if num.notna().sum() > 0:
        dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(num, unit="D")
        if dt.notna().sum() > 0:
            return dt

    return pd.Series(pd.NaT, index=series.index)

def to_timeonly(dt_series):
    return pd.to_datetime(
        "2000-01-01 " + pd.to_datetime(dt_series).dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

def load_cpc_csv(filepath, label):
    # -----------------------------------------------------
    # Read a larger preview to detect the real header row
    # -----------------------------------------------------
    try:
        preview = pd.read_csv(filepath, header=None, encoding="utf-8", nrows=120)
        file_encoding = "utf-8"
    except UnicodeDecodeError:
        preview = pd.read_csv(filepath, header=None, encoding="latin1", nrows=120)
        file_encoding = "latin1"

    header_row = None

    for i in range(len(preview)):
        row_vals = [str(x).strip() for x in preview.iloc[i].tolist() if pd.notna(x)]
        row_text = " | ".join(row_vals).lower()

        if "time" in row_text and ("concentration" in row_text or "#/cm" in row_text):
            header_row = i
            break

    if header_row is None:
        print("\nPreview rows for debugging:")
        print(preview.head(40))
        raise ValueError(f"Could not detect the real CPC header row in {filepath.name}")

    # -----------------------------------------------------
    # Load again using detected header row
    # -----------------------------------------------------
    df = pd.read_csv(filepath, header=header_row, encoding=file_encoding)
    df.columns = [str(c).strip() for c in df.columns]

    print(f"\nLoaded CPC: {filepath.name}")
    print(f"Detected header row: {header_row}")
    print("Columns:", list(df.columns))

    # Find time column
    time_col = None
    for c in ["Time", "Date Time", "Datetime", "DateTime", "Timestamp"]:
        if c in df.columns:
            time_col = c
            break

    if time_col is None:
        for c in df.columns:
            if "time" in str(c).lower():
                time_col = c
                break

    if time_col is None:
        raise ValueError(f"No CPC time column found in {filepath.name}")

    # Find concentration column
    conc_col = None
    for c in [
        "Concentration (#/cm³)",
        "Concentration (#/cm3)",
        "Concentration",
        "Conc",
        "Counts",
        "Total"
    ]:
        if c in df.columns:
            conc_col = c
            break

    if conc_col is None:
        for c in df.columns:
            if c == time_col:
                continue
            vals = pd.to_numeric(df[c], errors="coerce")
            if vals.notna().sum() > 0:
                conc_col = c
                break

    if conc_col is None:
        raise ValueError(f"No CPC concentration column found in {filepath.name}")

    df["DateTime"] = parse_time_series(df[time_col])
    df["Value"] = pd.to_numeric(df[conc_col], errors="coerce")
    df = df.dropna(subset=["DateTime", "Value"]).copy()
    df["TimeOnly"] = to_timeonly(df["DateTime"])

    out = df[["TimeOnly", "Value"]].copy()
    out = out.rename(columns={"Value": label})
    out = out.sort_values("TimeOnly").reset_index(drop=True)

    print(f"Using time column: {time_col}")
    print(f"Using concentration column: {conc_col}")
    print(f"Rows kept: {len(out)}")
    print(f"Time range: {out['TimeOnly'].min()} to {out['TimeOnly'].max()}")

    return out

def load_smps_total(filepath, label):
    df = pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    print(f"\nLoaded SMPS: {filepath.name}")
    print("Columns:", list(df.columns))

    time_col = None
    for c in ["corrected time", "Time", "Date Time", "DateTime"]:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        raise ValueError("SMPS time column not found.")

    df["DateTime"] = parse_time_series(df[time_col])
    df = df.dropna(subset=["DateTime"]).copy()
    df["TimeOnly"] = to_timeonly(df["DateTime"])

    conc_cols = [c for c in df.columns if c not in [time_col, "DateTime", "TimeOnly"]]
    df[conc_cols] = df[conc_cols].apply(pd.to_numeric, errors="coerce")
    df["Total"] = df[conc_cols].sum(axis=1, skipna=True)

    out = df[["TimeOnly", "Total"]].copy()
    out = out.rename(columns={"Total": label})
    out = out.sort_values("TimeOnly").reset_index(drop=True)

    print(f"Rows kept: {len(out)}")
    print(f"Time range: {out['TimeOnly'].min()} to {out['TimeOnly'].max()}")

    return out

def load_elpi_total(filepath, label):
    df = pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    print(f"\nLoaded ELPI: {filepath.name}")
    print("Columns:", list(df.columns))

    time_col = None
    for c in ["corrected time", "Time", "Date Time", "DateTime"]:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        for c in df.columns:
            if "time" in c.lower():
                time_col = c
                break
    if time_col is None:
        raise ValueError("ELPI time column not found.")

    df["DateTime"] = parse_time_series(df[time_col])
    df = df.dropna(subset=["DateTime"]).copy()
    df["TimeOnly"] = to_timeonly(df["DateTime"])

    if "Concentration value" in df.columns:
        df["Total"] = pd.to_numeric(df["Concentration value"], errors="coerce")
        used = "Concentration value"
    else:
        numeric_cols = []
        for c in df.columns:
            if c in [time_col, "DateTime", "TimeOnly"]:
                continue
            vals = pd.to_numeric(df[c], errors="coerce")
            if vals.notna().sum() > 0:
                numeric_cols.append(c)
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        df["Total"] = df[numeric_cols].sum(axis=1, skipna=True)
        used = f"summed numeric columns: {numeric_cols}"

    df = df.dropna(subset=["Total"]).copy()

    out = df[["TimeOnly", "Total"]].copy()
    out = out.rename(columns={"Total": label})
    out = out.sort_values("TimeOnly").reset_index(drop=True)

    print("Using ELPI total:", used)
    print(f"Rows kept: {len(out)}")
    print(f"Time range: {out['TimeOnly'].min()} to {out['TimeOnly'].max()}")

    return out

def load_drx_csv(filepath, label):
    try:
        df = pd.read_csv(filepath)
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="latin1")

    df.columns = [str(c).strip() for c in df.columns]

    print(f"\nLoaded DRX: {filepath.name}")
    print("Columns:", list(df.columns))

    time_col = None
    for c in ["Time", "Date Time", "Datetime", "DateTime", "timestamp", "Timestamp"]:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        time_col = df.columns[0]

    df["DateTime"] = parse_time_series(df[time_col])

    preferred_order = ["PM2.5 [ug/m3]", "PM1 [ug/m3]", "PM10 [ug/m3]"]
    value_col = None
    for c in preferred_order:
        if c in df.columns:
            value_col = c
            break
    if value_col is None:
        for c in df.columns:
            if c == time_col:
                continue
            vals = pd.to_numeric(df[c], errors="coerce")
            if vals.notna().sum() > 0:
                value_col = c
                break

    df["Value"] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=["DateTime", "Value"]).copy()
    df["TimeOnly"] = to_timeonly(df["DateTime"])

    out = df[["TimeOnly", "Value"]].copy()
    out = out.rename(columns={"Value": label})
    out = out.sort_values("TimeOnly").reset_index(drop=True)

    print(f"Using time column: {time_col}")
    print(f"Using DRX value column: {value_col}")
    print(f"Rows kept: {len(out)}")
    print(f"Time range: {out['TimeOnly'].min()} to {out['TimeOnly'].max()}")

    return out

def apply_window(df, start_str, end_str):
    start_dt = pd.to_datetime("2000-01-01 " + start_str)
    end_dt = pd.to_datetime("2000-01-01 " + end_str)
    return df[(df["TimeOnly"] >= start_dt) & (df["TimeOnly"] <= end_dt)].copy()

def get_peak_info(df, time_col, value_col):
    idx = df[value_col].idxmax()
    return df.loc[idx, time_col], df.loc[idx, value_col]

# =========================================================
# 5. LOAD DATA
# =========================================================
cpc_bed = load_cpc_csv(cpc_bed_file, "Master bedroom CPC")
cpc_bath = load_cpc_csv(cpc_bath_file, "Outside bathroom CPC")
elpi = load_elpi_total(elpi_file, "ELPI kitchen")
smps = load_smps_total(smps_file, "SMPS kitchen")
drx = load_drx_csv(drx_file, "DRX")

# =========================================================
# 6. FILTER WINDOW
# =========================================================
cpc_bed = apply_window(cpc_bed, plot_start, plot_end)
cpc_bath = apply_window(cpc_bath, plot_start, plot_end)
elpi = apply_window(elpi, plot_start, plot_end)
smps = apply_window(smps, plot_start, plot_end)
drx = apply_window(drx, plot_start, plot_end)

# =========================================================
# 7. SMOOTHING
# =========================================================
if not cpc_bed.empty:
    cpc_bed["Master bedroom CPC smooth"] = cpc_bed["Master bedroom CPC"].rolling(
        smooth_cpc_bed, center=True, min_periods=1
    ).mean()

if not cpc_bath.empty:
    cpc_bath["Outside bathroom CPC smooth"] = cpc_bath["Outside bathroom CPC"].rolling(
        smooth_cpc_bath, center=True, min_periods=1
    ).mean()

if not elpi.empty:
    elpi["ELPI kitchen smooth"] = elpi["ELPI kitchen"].rolling(
        smooth_elpi, center=True, min_periods=1
    ).mean()

if not smps.empty:
    smps["SMPS kitchen smooth"] = smps["SMPS kitchen"].rolling(
        smooth_smps, center=True, min_periods=1
    ).mean()

if not drx.empty:
    drx["DRX smooth"] = drx["DRX"].rolling(
        smooth_drx, center=True, min_periods=1
    ).mean()

# =========================================================
# 8. SUMMARY TABLE
# =========================================================
summary_rows = []

for exp_name, start_str, end_str in DEEPFRY_TIMELINE:
    row = {"Experiment": exp_name, "Start": start_str, "End": end_str}

    for df_src, smooth_col, short_name in [
        (smps, "SMPS kitchen smooth", "SMPS"),
        (elpi, "ELPI kitchen smooth", "ELPI"),
        (cpc_bed, "Master bedroom CPC smooth", "CPC_Bed"),
        (cpc_bath, "Outside bathroom CPC smooth", "CPC_Bath"),
        (drx, "DRX smooth", "DRX"),
    ]:
        if df_src.empty:
            row[f"{short_name}_PeakTime"] = None
            row[f"{short_name}_Peak"] = None
            continue

        block = apply_window(df_src, start_str, end_str)
        if block.empty or block[smooth_col].dropna().empty:
            row[f"{short_name}_PeakTime"] = None
            row[f"{short_name}_Peak"] = None
        else:
            pt, pv = get_peak_info(block, "TimeOnly", smooth_col)
            row[f"{short_name}_PeakTime"] = pt.strftime("%H:%M:%S")
            row[f"{short_name}_Peak"] = pv

    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)
print("\n================ DEEP FRY SUMMARY TABLE ================\n")
print(summary_df)
print("\n========================================================\n")

# =========================================================
# 9. PLOT
# =========================================================
fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True)

ax = axes[0]
if not smps.empty:
    ax.plot(smps["TimeOnly"], smps["SMPS kitchen smooth"], linewidth=2, label="SMPS kitchen")
if not elpi.empty:
    ax.plot(elpi["TimeOnly"], elpi["ELPI kitchen smooth"], linewidth=2, linestyle="--", label="ELPI kitchen")
ax.set_ylabel("Kitchen\n(number conc.)")
if use_log_y:
    ax.set_yscale("log")
ax.legend()
ax.grid(True, linestyle="--", linewidth=0.5)
ax.set_title("Figure 6.4.1. Time series of particle concentration during onion ring deep frying")

ax = axes[1]
if not cpc_bed.empty:
    ax.plot(cpc_bed["TimeOnly"], cpc_bed["Master bedroom CPC smooth"], linewidth=2, label="Master bedroom CPC")
if not cpc_bath.empty:
    ax.plot(cpc_bath["TimeOnly"], cpc_bath["Outside bathroom CPC smooth"], linewidth=2, linestyle="--", marker="o", markersize=3, label="Outside bathroom CPC")
ax.set_ylabel("Upper floor\n(CPC)")
if use_log_y:
    ax.set_yscale("log")
ax.legend()
ax.grid(True, linestyle="--", linewidth=0.5)

ax = axes[2]
if not drx.empty:
    ax.plot(drx["TimeOnly"], drx["DRX smooth"], linewidth=2, label="DRX")
ax.set_ylabel("DRX")
ax.legend()
ax.grid(True, linestyle="--", linewidth=0.5)

ax = axes[3]
for exp_name, start_str, end_str in DEEPFRY_TIMELINE:
    start_dt = pd.to_datetime("2000-01-01 " + start_str)
    end_dt = pd.to_datetime("2000-01-01 " + end_str)
    ax.axvspan(start_dt, end_dt, alpha=phase_alpha, color=phase_colors[exp_name], label=exp_name)

handles, labels = ax.get_legend_handles_labels()
seen = set()
new_h, new_l = [], []
for h, l in zip(handles, labels):
    if l not in seen:
        new_h.append(h)
        new_l.append(l)
        seen.add(l)
ax.legend(new_h, new_l, ncol=3, fontsize=8, loc="upper center")
ax.set_ylim(0, 1)
ax.set_yticks([])
ax.set_ylabel("Exp.")
ax.grid(False)

axes[-1].set_xlabel("Time")
for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.autofmt_xdate()
plt.tight_layout()
plt.show()

# =========================================================
# 10. SAVE SUMMARY
# =========================================================
output_dir = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.4.1"
)
output_dir.mkdir(parents=True, exist_ok=True)

summary_file = output_dir / "DeepFry_Summary_Table.xlsx"
summary_df.to_excel(summary_file, index=False)

print("Saved summary table:", summary_file)
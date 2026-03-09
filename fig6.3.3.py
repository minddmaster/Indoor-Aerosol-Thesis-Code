# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 18:38:01 2026

@author: papkp
"""

# =========================================================
# FIGURE 6.3.3 – CPC time series during cooking aerosol transport
# Master bedroom vs outside bathroom
# Robust time parsing version
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# ---------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------
bathroom_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/cpc006_out bath_Day5.xlsx"
)

bedroom_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/cpc012_Master Bedroom_Day5.xlsx"
)

# ---------------------------------------------------------
# BACON TIMELINE
# ---------------------------------------------------------
BACON_TIMELINE = [
    ("Heat",        "12:57:40", "13:02:40"),
    ("Fry",         "13:02:40", "13:08:40"),
    ("Decay",       "13:08:40", "13:13:58"),
    ("Ventilation", "13:13:58", "13:22:30"),

    ("Heat",        "13:23:30", "13:28:30"),
    ("Fry",         "13:28:30", "13:34:30"),
    ("Decay",       "13:34:30", "13:39:30"),
    ("Ventilation", "13:39:30", "13:46:40"),

    ("Heat",        "13:48:50", "13:53:50"),
    ("Fry",         "13:53:50", "13:59:50"),
    ("Decay",       "13:59:50", "14:04:50"),
    ("Ventilation", "14:04:50", "14:11:50"),
]

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------
resample_interval = "1min"
merge_tolerance = "5min"
smooth_window_bedroom = 3
smooth_window_bathroom = 1
use_log_y = True

plot_start = "12:55:00"
plot_end   = "14:12:00"

phase_colors = {
    "Heat": "orange",
    "Fry": "red",
    "Decay": "blue",
    "Ventilation": "green"
}
phase_alpha = 0.07

# ---------------------------------------------------------
# ROBUST TIME PARSER
# ---------------------------------------------------------
def parse_cpc_time(series):
    # 1. direct datetime parse
    dt = pd.to_datetime(series, errors="coerce")
    if dt.notna().sum() > 0:
        return dt

    # 2. string parse
    s = series.astype(str).str.strip()
    dt = pd.to_datetime(s, errors="coerce")
    if dt.notna().sum() > 0:
        return dt

    # 3. time-only parse
    dt = pd.to_datetime("2000-01-01 " + s, errors="coerce")
    if dt.notna().sum() > 0:
        return dt

    # 4. Excel serial date/time parse
    num = pd.to_numeric(series, errors="coerce")
    if num.notna().sum() > 0:
        # Excel origin
        dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(num, unit="D")
        if dt.notna().sum() > 0:
            return dt

    return pd.Series(pd.NaT, index=series.index)

# ---------------------------------------------------------
# CPC LOADER
# ---------------------------------------------------------
def load_cpc_file(filepath, location_name):
    df = pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    print(f"\nLoaded: {filepath.name}")
    print("Columns:", list(df.columns))
    print("First 10 raw time values:")
    print(df.iloc[:10, 0])

    # Find time column
    time_col = None
    for col in ["Date Time", "Datetime", "DateTime", "corrected time", "Time", "Timestamp", "date time"]:
        if col in df.columns:
            time_col = col
            break
    if time_col is None:
        time_col = df.columns[0]

    # Find concentration column
    conc_col = None
    for col in [
        "Concentration (#/cm³)",
        "Concentration (#/cm3)",
        "Concentration",
        "Conc",
        "Particle Concentration",
        "Number Concentration",
        "CPC",
        "Total",
        "Counts"
    ]:
        if col in df.columns:
            conc_col = col
            break

    if conc_col is None:
        for col in df.columns:
            if col == time_col:
                continue
            test = pd.to_numeric(df[col], errors="coerce")
            if test.notna().sum() > 0:
                conc_col = col
                break

    if conc_col is None:
        raise ValueError(f"No concentration column found in {filepath.name}")

    df["DateTime"] = parse_cpc_time(df[time_col])
    df["Concentration"] = pd.to_numeric(df[conc_col], errors="coerce")

    print("Parsed DateTime non-null:", df["DateTime"].notna().sum())
    print("Parsed Concentration non-null:", df["Concentration"].notna().sum())

    df = df.dropna(subset=["DateTime", "Concentration"]).copy()

    if df.empty:
        raise ValueError(
            f"No valid rows after parsing in {filepath.name}. "
            f"Check the raw time values printed above."
        )

    # Use time of day only
    df["TimeOnly"] = pd.to_datetime(
        "2000-01-01 " + df["DateTime"].dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

    out = df[["TimeOnly", "Concentration"]].copy()
    out = out.rename(columns={"Concentration": location_name})
    out = out.sort_values("TimeOnly").reset_index(drop=True)

    print(f"Using time column: {time_col}")
    print(f"Using concentration column: {conc_col}")
    print(f"Rows kept: {len(out)}")
    print(f"Time range: {out['TimeOnly'].min()} to {out['TimeOnly'].max()}")

    return out

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
bedroom = load_cpc_file(bedroom_file, "Master bedroom")
bathroom = load_cpc_file(bathroom_file, "Outside bathroom")

# ---------------------------------------------------------
# RESAMPLE
# ---------------------------------------------------------
bedroom = (
    bedroom.set_index("TimeOnly")
    .resample(resample_interval)
    .mean()
    .reset_index()
)

bathroom = (
    bathroom.set_index("TimeOnly")
    .resample(resample_interval)
    .mean()
    .reset_index()
)

# ---------------------------------------------------------
# MERGE
# ---------------------------------------------------------
ts = pd.merge_asof(
    bedroom.sort_values("TimeOnly"),
    bathroom.sort_values("TimeOnly"),
    on="TimeOnly",
    direction="nearest",
    tolerance=pd.Timedelta(merge_tolerance)
)

ts = ts.dropna(subset=["Outside bathroom"]).copy()

if ts.empty:
    raise ValueError("Merged CPC dataset is empty even after robust parsing.")

# ---------------------------------------------------------
# FILTER WINDOW
# ---------------------------------------------------------
plot_start_dt = pd.to_datetime("2000-01-01 " + plot_start)
plot_end_dt   = pd.to_datetime("2000-01-01 " + plot_end)

ts = ts[(ts["TimeOnly"] >= plot_start_dt) & (ts["TimeOnly"] <= plot_end_dt)].copy()

if ts.empty:
    print("No data in chosen bacon window.")
    print("Available merged range:", bedroom["TimeOnly"].min(), "to", bedroom["TimeOnly"].max())
    raise ValueError("Adjust plot_start and plot_end.")

# ---------------------------------------------------------
# SMOOTHING
# ---------------------------------------------------------
ts["Bedroom_smooth"] = ts["Master bedroom"].rolling(
    smooth_window_bedroom, center=True, min_periods=1
).mean()

ts["Bathroom_smooth"] = ts["Outside bathroom"].rolling(
    smooth_window_bathroom, center=True, min_periods=1
).mean()

# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------
bed_idx = ts["Bedroom_smooth"].idxmax()
bath_idx = ts["Bathroom_smooth"].idxmax()

bed_peak_time = ts.loc[bed_idx, "TimeOnly"]
bath_peak_time = ts.loc[bath_idx, "TimeOnly"]

bed_peak_value = ts.loc[bed_idx, "Bedroom_smooth"]
bath_peak_value = ts.loc[bath_idx, "Bathroom_smooth"]

delay_min = (bath_peak_time - bed_peak_time).total_seconds() / 60
bath_fraction_pct = (bath_peak_value / bed_peak_value) * 100 if bed_peak_value > 0 else float("nan")

print("\n================ FIGURE 6.3.3 SUMMARY ================")
print("Master bedroom peak time:", bed_peak_time.strftime("%H:%M:%S"))
print("Master bedroom peak concentration (cm^-3):", round(bed_peak_value, 0))
print("Outside bathroom peak time:", bath_peak_time.strftime("%H:%M:%S"))
print("Outside bathroom peak concentration (cm^-3):", round(bath_peak_value, 0))
print("Outside bathroom peak as % of bedroom peak:", round(bath_fraction_pct, 1))
print("Approx. delay (min):", round(delay_min, 2))
print("======================================================\n")

# ---------------------------------------------------------
# PLOT
# ---------------------------------------------------------
plt.figure(figsize=(11, 5))

plt.plot(
    ts["TimeOnly"],
    ts["Bedroom_smooth"],
    linewidth=2,
    label="Master bedroom CPC"
)

plt.plot(
    ts["TimeOnly"],
    ts["Bathroom_smooth"],
    linewidth=2,
    linestyle="--",
    marker="o",
    markersize=6,
    label="Outside bathroom CPC"
)

for phase, start, end in BACON_TIMELINE:
    start_dt = pd.to_datetime("2000-01-01 " + start)
    end_dt   = pd.to_datetime("2000-01-01 " + end)
    plt.axvspan(start_dt, end_dt, alpha=phase_alpha, color=phase_colors[phase])

plt.xlabel("Time")
plt.ylabel("Particle number concentration (cm$^{-3}$)")
plt.title(
    "Figure 6.3.3 Time series of CPC particle number concentration measured in the "
    "master bedroom and outside the bathroom during cooking aerosol transport"
)

plt.legend()
plt.grid(True, linestyle="--", linewidth=0.5)

if use_log_y:
    plt.yscale("log")

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.show()
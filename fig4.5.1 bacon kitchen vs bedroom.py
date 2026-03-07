# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 20:04:36 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Ref No: THESIS-FIG-4.5.1-AND-4.5.2-FULLDAY-BACON-FIXED-2026-03-05

Generates:
1. Figure 4.5.1 – Bacon experiment only (log scale)
2. Figure 4.5.2 – Full-day time series including 5% NaCl + bacon (log scale)

Fixes:
- keeps separate variables for full-day and bacon-only data
- avoids NameError for ts_full
- uses nearest-time matching for asynchronous SMPS scans
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================
# FILE PATHS
# =========================================================
BEDROOM_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/fig 4.5.1 bacon kitchen vs bedroom/DAY5 SMPS DATA_COM32_MBed.xlsx"
KITCHEN_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/fig 4.5.1 bacon kitchen vs bedroom/DAY5 SMPS DATA_COM33_Kitchen.xlsx"

OUT_DIR = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Figures"
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FIG_BACON = os.path.join(OUT_DIR, "Figure_4.5.1_Kitchen_vs_Bedroom_SMPS_Bacon_LOG.png")
OUT_FIG_FULLDAY = os.path.join(OUT_DIR, "Figure_4.5.2_FullDay_SMPS_Kitchen_vs_Bedroom_NaCl_LOG.png")

# =========================================================
# SETTINGS
# =========================================================
MATCH_TOLERANCE = "2min"
COMMON_DATE = "2025-01-01"
LOG_FLOOR = 1.0

BACON_START = "12:00:00"
BACON_END   = "14:00:00"

FULLDAY_START = "10:00:00"
FULLDAY_END   = "14:15:00"

# =========================================================
# TIMELINES
# =========================================================
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

FULLDAY_TIMELINE = [
    ("NaCl generation", "10:11:45", "10:31:45"),
    ("NaCl settling",   "10:31:45", "10:52:45"),
    ("Ventilation",     "10:52:45", "11:02:30"),

    ("NaCl generation", "11:04:25", "11:24:25"),
    ("NaCl settling",   "11:24:25", "11:44:25"),
    ("Ventilation",     "11:44:40", "11:52:10"),

    ("NaCl generation", "12:00:40", "12:20:40"),
    ("NaCl settling",   "12:20:40", "12:40:40"),
    ("Ventilation",     "12:40:41", "12:56:31"),

    ("Heat",            "12:57:40", "13:02:40"),
    ("Fry",             "13:02:40", "13:08:40"),
    ("Decay",           "13:08:40", "13:13:58"),
    ("Ventilation",     "13:13:58", "13:22:30"),

    ("Heat",            "13:23:30", "13:28:30"),
    ("Fry",             "13:28:30", "13:34:30"),
    ("Decay",           "13:34:30", "13:39:30"),
    ("Ventilation",     "13:39:30", "13:46:40"),

    ("Heat",            "13:48:50", "13:53:50"),
    ("Fry",             "13:53:50", "13:59:50"),
    ("Decay",           "13:59:50", "14:04:50"),
    ("Ventilation",     "14:04:50", "14:11:50"),
]

# =========================================================
# HELPERS
# =========================================================
def detect_time_col(df):
    candidates = ["corrected time", "CORRECTED TIME", "Time", "time", "Datetime", "Timestamp", "date time"]
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        if "time" in str(c).lower():
            return c
    return None

def to_dt(series):
    return pd.to_datetime(series, errors="coerce", dayfirst=True)

def force_common_date(dt_series, common_date=COMMON_DATE):
    dt_series = pd.to_datetime(dt_series, errors="coerce")
    base = pd.Timestamp(common_date)
    out = []
    for t in dt_series:
        if pd.isna(t):
            out.append(pd.NaT)
        else:
            out.append(pd.Timestamp(
                year=base.year,
                month=base.month,
                day=base.day,
                hour=t.hour,
                minute=t.minute,
                second=t.second
            ))
    return pd.to_datetime(out)

def map_bin_cols(df, time_col=None):
    cols = [c for c in df.columns if c != time_col]
    bin_cols = []
    diam = []

    for c in cols:
        try:
            d = float(c)
            v = pd.to_numeric(df[c], errors="coerce")
            if v.notna().sum() > 0:
                bin_cols.append(c)
                diam.append(d)
            continue
        except:
            pass

        m = re.search(r"(\d+(\.\d+)?)", str(c))
        if m:
            d = float(m.group(1))
            v = pd.to_numeric(df[c], errors="coerce")
            if v.notna().sum() > 0:
                bin_cols.append(c)
                diam.append(d)

    if len(bin_cols) < 5:
        raise ValueError("Could not detect enough SMPS diameter bin columns.")

    diam = np.array(diam, dtype=float)
    order = np.argsort(diam)
    diam = diam[order]
    bin_cols = [bin_cols[i] for i in order]
    return bin_cols, diam

def choose_best_sheet(path):
    xls = pd.ExcelFile(path)
    best_sheet = None
    best_df = None
    best_score = -1

    print(f"\nSheets in {os.path.basename(path)}:")
    for sh in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sh)
        time_col = detect_time_col(df)
        try:
            bin_cols, _ = map_bin_cols(df, time_col)
            score = len(bin_cols)
        except:
            score = 0
        print(f" - {sh} | score={score} | time_col={time_col}")

        if score > best_score:
            best_score = score
            best_sheet = sh
            best_df = df

    return best_sheet, best_df

def total_concentration(df, time_col):
    bin_cols, diam = map_bin_cols(df, time_col)
    y = df[bin_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    logd = np.log10(diam)
    dlog = np.gradient(logd)
    return np.nansum(y * dlog, axis=1)

def build_matched_timeseries(kitchen_path, bedroom_path, tolerance=MATCH_TOLERANCE):
    bed_sheet, bed_df = choose_best_sheet(bedroom_path)
    kit_sheet, kit_df = choose_best_sheet(kitchen_path)

    print("\nSelected bedroom sheet:", bed_sheet)
    print("Selected kitchen sheet:", kit_sheet)

    bed_time = detect_time_col(bed_df)
    kit_time = detect_time_col(kit_df)

    print("Bedroom time column:", bed_time)
    print("Kitchen time column:", kit_time)

    if bed_time is None or kit_time is None:
        raise ValueError("Could not detect time column in one or both files.")

    bed_df[bed_time] = force_common_date(to_dt(bed_df[bed_time]))
    kit_df[kit_time] = force_common_date(to_dt(kit_df[kit_time]))

    bed_df = bed_df.dropna(subset=[bed_time]).sort_values(bed_time).copy()
    kit_df = kit_df.dropna(subset=[kit_time]).sort_values(kit_time).copy()

    bed_df["Total"] = total_concentration(bed_df, bed_time)
    kit_df["Total"] = total_concentration(kit_df, kit_time)

    bed_ts = bed_df[[bed_time, "Total"]].rename(columns={bed_time: "Time", "Total": "Total_Bedroom"}).copy()
    kit_ts = kit_df[[kit_time, "Total"]].rename(columns={kit_time: "Time", "Total": "Total_Kitchen"}).copy()

    bed_ts["Time"] = pd.to_datetime(bed_ts["Time"], errors="coerce")
    kit_ts["Time"] = pd.to_datetime(kit_ts["Time"], errors="coerce")

    bed_ts = bed_ts.dropna(subset=["Time"]).sort_values("Time").reset_index(drop=True)
    kit_ts = kit_ts.dropna(subset=["Time"]).sort_values("Time").reset_index(drop=True)

    print("\nKitchen time range:", kit_ts["Time"].min(), "to", kit_ts["Time"].max())
    print("Bedroom time range:", bed_ts["Time"].min(), "to", bed_ts["Time"].max())

    ts = pd.merge_asof(
        kit_ts,
        bed_ts,
        on="Time",
        direction="nearest",
        tolerance=pd.Timedelta(tolerance)
    ).dropna()

    if ts.empty:
        raise ValueError("No matched data after nearest-time merge.")

    return ts.set_index("Time").sort_index()

def shade_timeline(ax, base_date, timeline, alpha=0.06):
    for phase, start, end in timeline:
        start_t = pd.Timestamp(f"{base_date} {start}")
        end_t = pd.Timestamp(f"{base_date} {end}")
        ax.axvspan(start_t, end_t, alpha=alpha)

# =========================================================
# BUILD MATCHED SERIES
# =========================================================
ts_all = build_matched_timeseries(KITCHEN_PATH, BEDROOM_PATH, MATCH_TOLERANCE)

# full-day dataframe
full_start_ts = pd.Timestamp(f"{COMMON_DATE} {FULLDAY_START}")
full_end_ts   = pd.Timestamp(f"{COMMON_DATE} {FULLDAY_END}")

ts_full = ts_all[(ts_all.index >= full_start_ts) & (ts_all.index <= full_end_ts)].copy()

if ts_full.empty:
    raise ValueError("No matched data in full-day window.")

ts_full["Total_Kitchen_log"] = ts_full["Total_Kitchen"].clip(lower=LOG_FLOOR)
ts_full["Total_Bedroom_log"] = ts_full["Total_Bedroom"].clip(lower=LOG_FLOOR)

# bacon-only dataframe
bacon_start_ts = pd.Timestamp(f"{COMMON_DATE} {BACON_START}")
bacon_end_ts   = pd.Timestamp(f"{COMMON_DATE} {BACON_END}")

ts_bacon = ts_all[(ts_all.index >= bacon_start_ts) & (ts_all.index <= bacon_end_ts)].copy()

if ts_bacon.empty:
    raise ValueError("No matched data in bacon window.")

ts_bacon["Total_Kitchen_log"] = ts_bacon["Total_Kitchen"].clip(lower=LOG_FLOOR)
ts_bacon["Total_Bedroom_log"] = ts_bacon["Total_Bedroom"].clip(lower=LOG_FLOOR)

# =========================================================
# FIGURE 4.5.1 – BACON
# =========================================================
base_date_bacon = ts_bacon.index[0].date()

fig, ax = plt.subplots(figsize=(10, 5.5))

ax.plot(
    ts_bacon.index,
    ts_bacon["Total_Kitchen_log"],
    linewidth=2.2,
    linestyle="-",
    label="Kitchen SMPS"
)

ax.plot(
    ts_bacon.index,
    ts_bacon["Total_Bedroom_log"],
    linewidth=1.8,
    linestyle="--",
    marker="o",
    markersize=3,
    markevery=1,
    label="Master bedroom SMPS"
)

shade_timeline(ax, base_date_bacon, BACON_TIMELINE, alpha=0.06)

ax.set_yscale("log")
ax.set_ylim(LOG_FLOOR, None)
ax.set_xlabel("Time")
ax.set_ylabel("Total particle number concentration (cm$^{-3}$)")
ax.set_title("Figure 4.5.1. Time series of aerosol concentration in the kitchen and master bedroom during the bacon frying experiment")
ax.grid(True, which="major", linestyle="--", linewidth=0.6)
ax.grid(True, which="minor", linestyle=":", linewidth=0.4)
ax.legend(frameon=False, loc="upper right")

plt.tight_layout()
plt.savefig(OUT_FIG_BACON, dpi=600, bbox_inches="tight")
plt.show()

# =========================================================
# FIGURE 4.5.2 – FULL DAY
# =========================================================
base_date_full = ts_full.index[0].date()

fig, ax = plt.subplots(figsize=(12, 5.8))

ax.plot(
    ts_full.index,
    ts_full["Total_Kitchen_log"],
    linewidth=2.2,
    linestyle="-",
    label="Kitchen SMPS"
)

ax.plot(
    ts_full.index,
    ts_full["Total_Bedroom_log"],
    linewidth=1.8,
    linestyle="--",
    marker="o",
    markersize=2.5,
    markevery=1,
    label="Master bedroom SMPS"
)

shade_timeline(ax, base_date_full, FULLDAY_TIMELINE, alpha=0.05)

ax.set_yscale("log")
ax.set_ylim(LOG_FLOOR, None)
ax.set_xlabel("Time")
ax.set_ylabel("Total particle number concentration (cm$^{-3}$)")
ax.set_title("Full-day time series of aerosol concentration in the kitchen and master bedroom\nincluding 5% NaCl aerosol and bacon frying experiments")
ax.grid(True, which="major", linestyle="--", linewidth=0.6)
ax.grid(True, which="minor", linestyle=":", linewidth=0.4)
ax.legend(frameon=False, loc="upper right")

plt.tight_layout()
plt.savefig(OUT_FIG_FULLDAY, dpi=600, bbox_inches="tight")
plt.show()
# =========================================================
# FIGURE 4.5.1 – TWO PANEL PLOT (BACON WINDOW)
# =========================================================

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(10, 6),
    sharex=True
)

base_date_bacon = ts_bacon.index[0].date()

# -------------------------
# Bedroom (TOP)
# -------------------------
ax1.plot(
    ts_bacon.index,
    ts_bacon["Total_Bedroom_log"],
    linewidth=2.0,
    linestyle="--",
    marker="o",
    markersize=4,
    markevery=1
)

shade_timeline(ax1, base_date_bacon, BACON_TIMELINE, alpha=0.06)

ax1.set_ylabel("Bedroom\n(cm$^{-3}$)")
ax1.set_yscale("log")
ax1.set_ylim(LOG_FLOOR, None)
ax1.grid(True, which="major", linestyle="--", linewidth=0.5)
ax1.grid(True, which="minor", linestyle=":", linewidth=0.4)

ax1.set_title(
    "Figure 4.5.1. Time series of aerosol concentration measured in the kitchen and master bedroom during bacon frying"
)

# -------------------------
# Kitchen (BOTTOM)
# -------------------------
ax2.plot(
    ts_bacon.index,
    ts_bacon["Total_Kitchen_log"],
    linewidth=2.2,
    linestyle="-"
)

shade_timeline(ax2, base_date_bacon, BACON_TIMELINE, alpha=0.06)

ax2.set_ylabel("Kitchen\n(cm$^{-3}$)")
ax2.set_xlabel("Time")
ax2.set_yscale("log")
ax2.set_ylim(LOG_FLOOR, None)
ax2.grid(True, which="major", linestyle="--", linewidth=0.5)
ax2.grid(True, which="minor", linestyle=":", linewidth=0.4)

plt.tight_layout()

OUT_FIG = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Figures/Figure_4.5.1_Kitchen_Bedroom_TwoPanel.png"

plt.savefig(OUT_FIG, dpi=600, bbox_inches="tight")
plt.show()

print("Saved figure:", OUT_FIG)
print("Plotted bacon range:", ts_bacon.index.min(), "to", ts_bacon.index.max())

# =========================================================
# SUMMARIES
# =========================================================
print("\nSaved figures:")
print(OUT_FIG_BACON)
print(OUT_FIG_FULLDAY)

k_peak_bacon = ts_bacon["Total_Kitchen"].idxmax()
b_peak_bacon = ts_bacon["Total_Bedroom"].idxmax()

print("\nBacon summary")
print("Matched points:", len(ts_bacon))
print("Plotted bacon range:", ts_bacon.index.min(), "to", ts_bacon.index.max())
print("Kitchen peak concentration:", ts_bacon["Total_Kitchen"].max())
print("Bedroom peak concentration:", ts_bacon["Total_Bedroom"].max())
print("Kitchen peak time:", k_peak_bacon)
print("Bedroom peak time:", b_peak_bacon)
print("Peak timing difference (bedroom - kitchen, min):", round((b_peak_bacon - k_peak_bacon).total_seconds() / 60, 2))

print("\nFull-day summary")
print("Matched points:", len(ts_full))
print("Plotted full-day range:", ts_full.index.min(), "to", ts_full.index.max())
print("Kitchen max concentration:", ts_full["Total_Kitchen"].max())
print("Bedroom max concentration:", ts_full["Total_Bedroom"].max())
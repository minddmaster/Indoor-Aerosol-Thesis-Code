# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 10:33:06 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Updated Figure 6.3.1
Time-resolved particle number concentration during bacon frying
showing multi-instrument response and ventilation effects

Includes:
- Kitchen SMPS
- Master bedroom SMPS
- Kitchen ELPI
- Bathroom CPC
- Bedroom CPC

Plots bacon experiments only:
- Exp5
- Exp6
- Exp7
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# =========================================================
# FILE PATHS
# =========================================================
BASE_DIR = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1")

SMPS_BED_FILE = BASE_DIR / "DAY5 SMPS DATA_COM32_MBed.xlsx"
SMPS_KITCHEN_FILE = BASE_DIR / "DAY5 SMPS DATA_COM33_Kitchen.xlsx"
ELPI_FILE = BASE_DIR / "Day 5 ELPI DATA.xlsx"
CPC_BATH_FILE = BASE_DIR / "cpc006_out bath_Day5.xlsx"
CPC_BED_FILE = BASE_DIR / "cpc012_Master Bedroom_Day5.xlsx"

OUTPUT_DIR = BASE_DIR / "figure_6_3_1_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# SETTINGS
# =========================================================
dummy_date = "2000-01-01"
smooth_window = 3
use_log_y = True
smps_merge_tolerance = "2min"
cpc_merge_tolerance = "5min"

# Bacon experiments only
EXPERIMENTS = [
    {
        "experiment": "Exp5",
        "start": "12:57:40",
        "end": "13:22:30",
        "cook_start": "13:02:40",
        "cook_end": "13:08:40",
        "vent_start": "13:13:58",
        "vent_end": "13:22:30",
    },
    {
        "experiment": "Exp6",
        "start": "13:23:30",
        "end": "13:46:40",
        "cook_start": "13:28:30",
        "cook_end": "13:34:30",
        "vent_start": "13:39:30",
        "vent_end": "13:46:40",
    },
    {
        "experiment": "Exp7",
        "start": "13:48:50",
        "end": "14:11:50",
        "cook_start": "13:53:50",
        "cook_end": "13:59:50",
        "vent_start": "14:04:50",
        "vent_end": "14:11:50",
    },
]

# =========================================================
# HELPERS
# =========================================================
def to_dummy_datetime(timestr: str) -> pd.Timestamp:
    return pd.to_datetime(f"{dummy_date} {timestr}")

def find_time_col_general(df: pd.DataFrame):
    for c in df.columns:
        c_str = str(c).lower().strip()
        if "corrected time" in c_str or c_str == "time" or "time" in c_str:
            return c
    return None

def find_conc_col_general(df: pd.DataFrame):
    for c in df.columns:
        c_str = str(c).lower().strip()
        if "conc" in c_str or "concentration" in c_str:
            return c
    return None

def load_smps_total(filepath: Path, room_name: str) -> pd.DataFrame:
    xls = pd.ExcelFile(filepath)
    sheet = xls.sheet_names[0]
    candidate_skiprows = [0, 10, 20, 30, 40]
    last_error = None

    for skip in candidate_skiprows:
        try:
            df = pd.read_excel(filepath, sheet_name=sheet, skiprows=skip)
            df.columns = [str(c).strip() for c in df.columns]

            time_col = find_time_col_general(df)
            if time_col is None:
                continue

            df["Date Time"] = pd.to_datetime(df[time_col], errors="coerce")
            if df["Date Time"].notna().sum() == 0:
                df["Date Time"] = pd.to_datetime(
                    "2025-02-28 " + df[time_col].astype(str),
                    errors="coerce"
                )
            if df["Date Time"].notna().sum() == 0:
                continue

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
                continue

            df[conc_cols] = df[conc_cols].apply(pd.to_numeric, errors="coerce")
            df["Total"] = df[conc_cols].sum(axis=1, skipna=True)

            out = df[["TimeOnly", "Total"]].copy()
            out = out.rename(columns={"Total": f"Total_{room_name}"})
            out = out.dropna(subset=["TimeOnly", f"Total_{room_name}"])
            out = out.sort_values("TimeOnly").reset_index(drop=True)

            print(f"Loaded {filepath.name} using skiprows={skip}")
            return out

        except Exception as e:
            last_error = e

    raise ValueError(f"Could not parse SMPS file {filepath.name}. Last error: {last_error}")

def load_elpi_total(filepath: Path) -> pd.DataFrame:
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

    parsed = pd.to_datetime(df[time_col], errors="coerce")
    if parsed.notna().sum() == 0:
        parsed = pd.to_datetime("2025-02-28 " + df[time_col].astype(str), errors="coerce")

    df["TimeOnly"] = pd.to_datetime(
        dummy_date + " " + parsed.dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

    df["ELPI_Total"] = pd.to_numeric(df[conc_col], errors="coerce")
    df = df.dropna(subset=["TimeOnly", "ELPI_Total"]).copy()

    out = df[["TimeOnly", "ELPI_Total"]].sort_values("TimeOnly").reset_index(drop=True)
    return out

def load_cpc(filepath: Path, col_name: str) -> pd.DataFrame:
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
            parsed = pd.to_datetime("2025-02-28 " + raw_time.astype(str), errors="coerce")

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

# =========================================================
# LOAD DATA
# =========================================================
kitchen_smps = load_smps_total(SMPS_KITCHEN_FILE, "Kitchen")
bedroom_smps = load_smps_total(SMPS_BED_FILE, "Bedroom")
elpi = load_elpi_total(ELPI_FILE)
cpc_bath = load_cpc(CPC_BATH_FILE, "CPC_Bath")
cpc_bed = load_cpc(CPC_BED_FILE, "CPC_Bed")

# =========================================================
# MERGE / SMOOTH
# =========================================================
smps_ts = pd.merge_asof(
    kitchen_smps.sort_values("TimeOnly"),
    bedroom_smps.sort_values("TimeOnly"),
    on="TimeOnly",
    direction="nearest",
    tolerance=pd.Timedelta(smps_merge_tolerance)
).dropna(subset=["Total_Bedroom"]).copy()

if smps_ts.empty:
    raise ValueError("No matched SMPS rows after merge. Increase smps_merge_tolerance.")

smps_ts["Kitchen_smooth"] = smps_ts["Total_Kitchen"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

smps_ts["Bedroom_smooth"] = smps_ts["Total_Bedroom"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

# Fix unrealistic sharp SMPS kitchen drops
smps_ts["Kitchen_smooth"] = smps_ts["Kitchen_smooth"].replace(0, np.nan)
smps_ts["Kitchen_smooth"] = smps_ts["Kitchen_smooth"].clip(lower=500)

elpi["ELPI_smooth"] = elpi["ELPI_Total"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

cpc_bath["CPC_Bath_smooth"] = cpc_bath["CPC_Bath"].rolling(
    smooth_window, center=True, min_periods=1
).mean()
cpc_bed["CPC_Bed_smooth"] = cpc_bed["CPC_Bed"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

# =========================================================
# RESTRICT TO BACON WINDOW ONLY
# =========================================================
plot_start = to_dummy_datetime("12:57:40")
plot_end = to_dummy_datetime("14:11:50")

smps_plot = smps_ts[(smps_ts["TimeOnly"] >= plot_start) & (smps_ts["TimeOnly"] <= plot_end)].copy()
elpi_plot = elpi[(elpi["TimeOnly"] >= plot_start) & (elpi["TimeOnly"] <= plot_end)].copy()
cpc_bath_plot = cpc_bath[(cpc_bath["TimeOnly"] >= plot_start) & (cpc_bath["TimeOnly"] <= plot_end)].copy()
cpc_bed_plot = cpc_bed[(cpc_bed["TimeOnly"] >= plot_start) & (cpc_bed["TimeOnly"] <= plot_end)].copy()

# =========================================================
# PLOT FIGURE 6.3.1
# =========================================================
plt.figure(figsize=(11.5, 6.2))

# Main lines: SMPS strongest emphasis
plt.plot(smps_plot["TimeOnly"], smps_plot["Kitchen_smooth"], linewidth=2.6, label="Kitchen (SMPS)")
plt.plot(smps_plot["TimeOnly"], smps_plot["Bedroom_smooth"], linewidth=2.6, linestyle="--", label="Master bedroom (SMPS)")

# Secondary lines: ELPI and CPC lighter
plt.plot(elpi_plot["TimeOnly"], elpi_plot["ELPI_smooth"], linewidth=1.7, linestyle=":", alpha=0.85, label="Kitchen (ELPI)")
plt.plot(cpc_bath_plot["TimeOnly"], cpc_bath_plot["CPC_Bath_smooth"], linewidth=1.4, linestyle="-.", alpha=0.85, label="Bathroom (CPC)")
plt.plot(cpc_bed_plot["TimeOnly"], cpc_bed_plot["CPC_Bed_smooth"], linewidth=1.4, linestyle=(0, (3, 1, 1, 1)), alpha=0.85, label="Bedroom (CPC)")

# Shade experiments and frying phases
for exp in EXPERIMENTS:
    start_dt = to_dummy_datetime(exp["start"])
    end_dt = to_dummy_datetime(exp["end"])
    cook_start = to_dummy_datetime(exp["cook_start"])
    cook_end = to_dummy_datetime(exp["cook_end"])
    vent_start = to_dummy_datetime(exp["vent_start"])

    # Light full experiment shading
    plt.axvspan(start_dt, end_dt, alpha=0.05, color="grey")
    # Stronger frying phase highlight
    plt.axvspan(cook_start, cook_end, alpha=0.14, color="orange")
    # Ventilation start marker
    plt.axvline(vent_start, linestyle=":", linewidth=1.0, alpha=0.65)

    plt.text(start_dt, plt.ylim()[1] * 0.92, exp["experiment"], fontsize=9, rotation=90, va="top")

plt.xlabel("Time")
plt.ylabel("Particle number concentration (particles cm$^{-3}$)")
plt.title(
    "Figure 6.3.1. Time-resolved particle number concentration during bacon frying\n"
    "showing multi-instrument response and ventilation effects"
)

plt.grid(True, linestyle="--", linewidth=0.5)

if use_log_y:
    plt.yscale("log")

plt.xlim(plot_start, plot_end)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()

# Move legend outside so it doesn't cover data
plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)

plt.tight_layout()

fig_path = OUTPUT_DIR / "Figure_6_3_1_bacon_time_series_updated.png"
plt.savefig(fig_path, dpi=300, bbox_inches="tight")
plt.show()

print(f"Saved figure to: {fig_path}")
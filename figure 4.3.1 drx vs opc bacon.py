# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 19:59:18 2026

@author: papkp
"""

# Ref No: THESIS-FIG-4.3.1-DRX-OPC-MASS-LOGSCALE-PHASELABELS-DAY5-BACON-2026-03-05
# Updated:
# - Removes fat-loss annotations
# - Adds vertical phase labels with scientific naming: Heat / Fry / Decay / Ventilation
# - Moves phase labels higher on log axis for readability
# - Lightens shading so signals stand out
# - Log-scale y-axis + log-safe clipping
# - Auto-detects time columns, auto-creates output folder

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

DRX_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 5 Bacon expt/TEST 1_001_sphereday 5_DRX.csv"
OPC_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 5 Bacon expt/OPC2_007_sphereday5_opc5_kitchen.CSV"

OUT_FIG = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Figures/Figure_4.3.1_DRX_OPC_PM25_Bacon_Day5_LOG_PhaseLabels.png"

timeline = [
    ("Repeat 1 — Stove",     "12:57:40", "13:02:40"),
    ("Repeat 1 — Fry",       "13:02:40", "13:08:40"),
    ("Repeat 1 — Settle",    "13:08:40", "13:13:58"),
    ("Repeat 1 — Ventilate", "13:13:58", "13:22:30"),
    ("Repeat 2 — Stove",     "13:23:30", "13:28:30"),
    ("Repeat 2 — Fry",       "13:28:30", "13:34:30"),
    ("Repeat 2 — Settle",    "13:34:30", "13:39:30"),
    ("Repeat 2 — Ventilate", "13:39:30", "13:46:40"),
    ("Repeat 3 — Stove",     "13:48:50", "13:53:50"),
    ("Repeat 3 — Fry",       "13:53:50", "13:59:50"),
    ("Repeat 3 — Settle",    "13:59:50", "14:04:50"),
    ("Repeat 3 — Ventilate", "14:04:50", "14:11:50"),
]

CROP_START = "12:57:40"
CROP_END   = "14:11:50"
RESAMPLE = "10S"
LOG_FLOOR = 1.0  # µg m^-3 (prevents log(0); can change to 0.1 if needed)

PHASE_LABEL_Y = LOG_FLOOR * 12   # move labels higher than baseline for readability
SHADE_ALPHA = 0.05              # lighter shading

def read_csv_robust(path):
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        for sep in (",", ";", "\t"):
            try:
                df = pd.read_csv(path, encoding=enc, sep=sep, low_memory=False)
                if df.shape[1] >= 2:
                    return df
            except Exception:
                pass
    return pd.read_csv(path, encoding="latin1", low_memory=False)

def to_dt(s):
    return pd.to_datetime(s, errors="coerce", dayfirst=True)

def detect_time_col(df):
    candidates = ["Time", "time", "DateTime", "Datetime", "Timestamp", "corrected time", "Unnamed: 0"]
    for c in candidates:
        if c in df.columns:
            return c
    return df.columns[0]

def find_drx_pm25_col(df):
    if "PM2.5 [ug/m3]" in df.columns:
        return "PM2.5 [ug/m3]"
    for c in df.columns:
        n = str(c).lower().replace(" ", "")
        if "pm2.5" in n or "pm25" in n:
            return c
    return None

phase_map = {
    "Stove": "Heat",
    "Fry": "Fry",
    "Settle": "Decay",
    "Ventilate": "Ventilation"
}

# ---- Load DRX ----
drx = read_csv_robust(DRX_PATH)
drx_time_col = detect_time_col(drx)
drx_pm25_col = find_drx_pm25_col(drx)

if drx_pm25_col is None:
    print("DRX columns:", list(drx.columns))
    raise ValueError("Could not find DRX PM2.5 column. Set drx_pm25_col manually.")

drx["Time"] = to_dt(drx[drx_time_col])
drx["DRX_PM25"] = pd.to_numeric(drx[drx_pm25_col], errors="coerce")
drx = drx.dropna(subset=["Time", "DRX_PM25"]).set_index("Time").sort_index()

# ---- Load OPC ----
opc = read_csv_robust(OPC_PATH)
opc_time_col = detect_time_col(opc)

opc_pm25_col = "PM_2.500(ug/m^3)"
if opc_pm25_col not in opc.columns:
    print("OPC columns:", list(opc.columns))
    raise ValueError("Could not find OPC PM_2.500(ug/m^3). Check exact header in OPC CSV.")

opc["Time"] = to_dt(opc[opc_time_col])
opc["OPC_PM25"] = pd.to_numeric(opc[opc_pm25_col], errors="coerce")
opc = opc.dropna(subset=["Time", "OPC_PM25"]).set_index("Time").sort_index()

# ---- Align + crop ----
ts = drx[["DRX_PM25"]].resample(RESAMPLE).mean().join(
    opc[["OPC_PM25"]].resample(RESAMPLE).mean(),
    how="inner"
).dropna()

ts = ts.between_time(CROP_START, CROP_END).copy()

if ts.empty:
    raise ValueError("No data after time-of-day cropping. Check CROP_START/CROP_END.")

base_date = ts.index[0].date()

# ---- Log-safe clipping ----
ts["DRX_PM25_clip"] = ts["DRX_PM25"].clip(lower=LOG_FLOOR)
ts["OPC_PM25_clip"] = ts["OPC_PM25"].clip(lower=LOG_FLOOR)

# ---- Plot ----
fig, ax = plt.subplots(figsize=(11, 5.5))

ax.plot(
    ts.index, ts["DRX_PM25_clip"],
    linewidth=2.2,
    linestyle="-",
    label="DustTrak DRX PM$_{2.5}$"
)

ax.plot(
    ts.index, ts["OPC_PM25_clip"],
    linewidth=1.8,
    linestyle="--",
    marker="o",
    markersize=2.5,
    markevery=12,
    label="OPC-N2 PM$_{2.5}$"
)

# Shade phases + vertical labels
for label, start, end in timeline:
    start_t = pd.Timestamp(f"{base_date} {start}")
    end_t   = pd.Timestamp(f"{base_date} {end}")
    ax.axvspan(start_t, end_t, alpha=SHADE_ALPHA)

    phase_raw = label.split("—")[-1].strip()
    phase = phase_map.get(phase_raw, phase_raw)

    mid = start_t + (end_t - start_t) / 2
    ax.text(
        mid, PHASE_LABEL_Y,
        phase,
        rotation=90,
        ha="center",
        va="bottom",
        fontsize=9,
        alpha=0.80
    )

# Repeat boundaries
for tmark in ["13:22:30", "13:46:40", "14:11:50"]:
    ax.axvline(pd.Timestamp(f"{base_date} {tmark}"), linestyle="--", linewidth=1.0)

# Axes + title
ax.set_yscale("log")
ax.set_ylim(LOG_FLOOR, None)
ax.set_xlabel("Time")
ax.set_ylabel("PM$_{2.5}$ mass concentration (µg m$^{-3}$)")
ax.set_title("Figure 4.3.1. DustTrak DRX and OPC-N2 PM$_{2.5}$ mass concentration during bacon frying (Day 5)")

# Grid + legend
ax.grid(True, which="major", linestyle="--", linewidth=0.6)
ax.grid(True, which="minor", linestyle=":", linewidth=0.4)
ax.legend(frameon=False, loc="upper left")

plt.tight_layout()

# Save
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
plt.savefig(OUT_FIG, dpi=600, bbox_inches="tight")
plt.show()

print("\nColumns used:")
print("DRX time column:", drx_time_col)
print("DRX PM2.5 column:", drx_pm25_col)
print("OPC time column:", opc_time_col)
print("OPC PM2.5 column:", opc_pm25_col)
print("Saved figure to:", OUT_FIG)
print("Plotted range:", ts.index.min(), "to", ts.index.max())
print("Log floor used:", LOG_FLOOR, "µg m^-3")
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 18:50:25 2026

@author: papkp
"""

# =========================================================
# FIGURE 6.3.4 – ELPI kitchen time series during bacon frying
# Updated version using "Concentration value" as ELPI total
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# ---------------------------------------------------------
# FILE PATH
# ---------------------------------------------------------
elpi_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/Day 5 ELPI DATA.xlsx"
)

# ---------------------------------------------------------
# BACON COOKING TIMELINE
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
use_log_y = True
plot_start = "12:55:00"
plot_end   = "14:12:00"
smooth_window = 5

phase_colors = {
    "Heat": "orange",
    "Fry": "red",
    "Decay": "blue",
    "Ventilation": "green"
}
phase_alpha = 0.07

# ---------------------------------------------------------
# LOAD ELPI DATA
# ---------------------------------------------------------
df = pd.read_excel(elpi_file)
df.columns = [str(c).strip() for c in df.columns]

print("\nInitial columns:")
print(list(df.columns))

# If needed, detect header row
if not any("time" in str(c).lower() for c in df.columns):
    preview = pd.read_excel(elpi_file, header=None, nrows=20)
    header_row = 0

    for i in range(len(preview)):
        row_vals = [str(x).strip() for x in preview.iloc[i].tolist() if pd.notna(x)]
        row_text = " | ".join(row_vals).lower()
        if any(k in row_text for k in ["time", "stage", "total", "conc", "mass"]):
            header_row = i
            break

    df = pd.read_excel(elpi_file, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]

    print(f"\nDetected header row: {header_row}")
    print("Columns after reloading:")
    print(list(df.columns))

# ---------------------------------------------------------
# FIND TIME COLUMN
# ---------------------------------------------------------
time_col = None
time_candidates = [
    "Time", "time", "Date Time", "DateTime", "Datetime",
    "corrected time", "Timestamp", "timestamp"
]

for col in time_candidates:
    if col in df.columns:
        time_col = col
        break

if time_col is None:
    for col in df.columns:
        if "time" in str(col).lower():
            time_col = col
            break

if time_col is None:
    raise ValueError("No time column found. Check printed columns above.")

print("\nUsing time column:", time_col)

# ---------------------------------------------------------
# PARSE TIME
# ---------------------------------------------------------
df["DateTime"] = pd.to_datetime(df[time_col], errors="coerce")

if df["DateTime"].notna().sum() == 0:
    df["DateTime"] = pd.to_datetime(
        df[time_col].astype(str).str.strip(),
        errors="coerce"
    )

df = df.dropna(subset=["DateTime"]).copy()

if df.empty:
    raise ValueError("No valid time values found after parsing.")

# Use time-of-day only
df["TimeOnly"] = pd.to_datetime(
    "2000-01-01 " + df["DateTime"].dt.strftime("%H:%M:%S"),
    errors="coerce"
)

# ---------------------------------------------------------
# USE TRUE ELPI TOTAL COLUMN
# ---------------------------------------------------------
if "Concentration value" in df.columns:
    df["ELPI_Total"] = pd.to_numeric(df["Concentration value"], errors="coerce")
    print("Using total concentration column: Concentration value")
else:
    raise ValueError(
        "'Concentration value' column not found. Check printed columns above."
    )

df = df.dropna(subset=["ELPI_Total"]).copy()

print("\nRows kept:", len(df))
print("Time range:", df["TimeOnly"].min(), "to", df["TimeOnly"].max())

# ---------------------------------------------------------
# FILTER BACON WINDOW
# ---------------------------------------------------------
plot_start_dt = pd.to_datetime("2000-01-01 " + plot_start)
plot_end_dt   = pd.to_datetime("2000-01-01 " + plot_end)

ts = df[(df["TimeOnly"] >= plot_start_dt) & (df["TimeOnly"] <= plot_end_dt)].copy()

if ts.empty:
    print("\nNo data found in selected bacon window.")
    print("Available range:", df["TimeOnly"].min(), "to", df["TimeOnly"].max())
    raise ValueError("Adjust plot_start and plot_end.")

# ---------------------------------------------------------
# SMOOTHING
# ---------------------------------------------------------
ts = ts.sort_values("TimeOnly").reset_index(drop=True)
ts["ELPI_smooth"] = ts["ELPI_Total"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

# ---------------------------------------------------------
# PEAK SUMMARY
# ---------------------------------------------------------
peak_idx = ts["ELPI_smooth"].idxmax()
peak_time = ts.loc[peak_idx, "TimeOnly"]
peak_value = ts.loc[peak_idx, "ELPI_smooth"]

print("\n================ FIGURE 6.3.4 SUMMARY ================")
print("Peak time:", peak_time.strftime("%H:%M:%S"))
print("Peak concentration:", round(peak_value, 2))
print("======================================================\n")

# ---------------------------------------------------------
# PLOT
# ---------------------------------------------------------
plt.figure(figsize=(11, 5))

plt.plot(
    ts["TimeOnly"],
    ts["ELPI_smooth"],
    linewidth=2,
    label="ELPI kitchen"
)

# Shade bacon phases
for phase, start, end in BACON_TIMELINE:
    start_dt = pd.to_datetime("2000-01-01 " + start)
    end_dt   = pd.to_datetime("2000-01-01 " + end)

    plt.axvspan(
        start_dt,
        end_dt,
        alpha=phase_alpha,
        color=phase_colors[phase]
    )

# First-cycle labels only
top_label_y = ts["ELPI_smooth"].max() * 1.10
plt.text(pd.to_datetime("2000-01-01 12:59:30"), top_label_y, "Heat", fontsize=9)
plt.text(pd.to_datetime("2000-01-01 13:04:30"), top_label_y, "Fry", fontsize=9)
plt.text(pd.to_datetime("2000-01-01 13:10:00"), top_label_y, "Decay", fontsize=9)
plt.text(pd.to_datetime("2000-01-01 13:16:00"), top_label_y, "Ventilation", fontsize=9)

# Mark and annotate peak
plt.scatter(peak_time, peak_value, zorder=5)

plt.annotate(
    f"Peak\n{peak_value:.2e}",
    xy=(peak_time, peak_value),
    xytext=(22, 12),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="->", lw=0.8),
    fontsize=9
)

plt.xlabel("Time")
plt.ylabel("Particle concentration")
plt.title(
    "Figure 6.3.4 Time series of ELPI particle concentration measured in the kitchen "
    "during bacon frying"
)

plt.legend()
plt.grid(True, linestyle="--", linewidth=0.5)

if use_log_y:
    plt.yscale("log")
    plt.ylim(3e3, 3e6)

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()

plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------
output_dir = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.4"
)
output_dir.mkdir(parents=True, exist_ok=True)

png_file = output_dir / "Figure_6_3_4_ELPI_Kitchen_Bacon.png"
tiff_file = output_dir / "Figure_6_3_4_ELPI_Kitchen_Bacon.tiff"

plt.figure(1)
plt.savefig(png_file, dpi=600, bbox_inches="tight")
plt.savefig(tiff_file, dpi=600, bbox_inches="tight")

print("Saved PNG:", png_file)
print("Saved TIFF:", tiff_file)
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 17:43:56 2026

@author: papkp
"""

# =========================================================
# FIGURE 6.1 – NaCl aerosol transport within the building
# Merge SMPS files using time of day only
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.dates as mdates

# ---------------------------------------------------------
# 1. FILE PATHS
# ---------------------------------------------------------
bedroom_file = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.2.1/DAY5 SMPS DATA_COM32_MBed.xlsx")
kitchen_file = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.2.1/DAY5 SMPS DATA_COM33_Kitchen.xlsx")

# ---------------------------------------------------------
# 2. SETTINGS
# ---------------------------------------------------------
smooth_window = 3
use_log_y = True

# leave as None first, then tighten later if needed
start_time = None
end_time = None

# example for later:
# start_time = "10:30:00"
# end_time   = "12:30:00"

merge_tolerance = "2min"

# ---------------------------------------------------------
# 3. LOAD FUNCTION
# ---------------------------------------------------------
def load_smps_total(filepath, room_name):
    df = pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    if "corrected time" not in df.columns:
        raise ValueError(f"'corrected time' column not found in {filepath.name}")

    df["Date Time"] = pd.to_datetime(df["corrected time"], errors="coerce")
    df = df.dropna(subset=["Date Time"]).copy()

    # create a common dummy date so only time-of-day matters
    df["TimeOnly"] = pd.to_datetime(
        "2000-01-01 " + df["Date Time"].dt.strftime("%H:%M:%S"),
        errors="coerce"
    )

    # concentration columns = all bin columns
    conc_cols = [col for col in df.columns if col not in ["corrected time", "Date Time", "TimeOnly"]]
    df[conc_cols] = df[conc_cols].apply(pd.to_numeric, errors="coerce")

    # sum bins to get total number concentration
    df["Total"] = df[conc_cols].sum(axis=1, skipna=True)

    out = df[["TimeOnly", "Total"]].copy()
    out = out.rename(columns={"Total": f"Total_{room_name}"})
    out = out.sort_values("TimeOnly").reset_index(drop=True)

    return out

# ---------------------------------------------------------
# 4. LOAD DATA
# ---------------------------------------------------------
bedroom = load_smps_total(bedroom_file, "Bedroom")
kitchen = load_smps_total(kitchen_file, "Kitchen")

print("Kitchen time range:")
print(kitchen["TimeOnly"].min(), "to", kitchen["TimeOnly"].max())
print("Kitchen rows:", len(kitchen))

print("\nBedroom time range:")
print(bedroom["TimeOnly"].min(), "to", bedroom["TimeOnly"].max())
print("Bedroom rows:", len(bedroom))

# ---------------------------------------------------------
# 5. MERGE BY NEAREST TIME-OF-DAY
# ---------------------------------------------------------
ts = pd.merge_asof(
    kitchen.sort_values("TimeOnly"),
    bedroom.sort_values("TimeOnly"),
    on="TimeOnly",
    direction="nearest",
    tolerance=pd.Timedelta(merge_tolerance)
)

ts = ts.dropna(subset=["Total_Bedroom"]).copy()

print("\nMerged rows:", len(ts))
if ts.empty:
    raise ValueError(
        "No matched rows after merge. Increase merge_tolerance to 3min or 4min."
    )

print("Merged time range:")
print("Start:", ts["TimeOnly"].min())
print("End:  ", ts["TimeOnly"].max())

# ---------------------------------------------------------
# 6. OPTIONAL FILTER
# ---------------------------------------------------------
if start_time is not None and end_time is not None:
    start_dt = pd.to_datetime("2000-01-01 " + start_time)
    end_dt   = pd.to_datetime("2000-01-01 " + end_time)

    ts = ts[(ts["TimeOnly"] >= start_dt) & (ts["TimeOnly"] <= end_dt)].copy()

    if ts.empty:
        raise ValueError("No data found in selected time window.")

# ---------------------------------------------------------
# 7. SMOOTHING
# ---------------------------------------------------------
ts["Kitchen_smooth"] = ts["Total_Kitchen"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

ts["Bedroom_smooth"] = ts["Total_Bedroom"].rolling(
    smooth_window, center=True, min_periods=1
).mean()

# ---------------------------------------------------------
# 8. PEAKS
# ---------------------------------------------------------
k_peak_idx = ts["Kitchen_smooth"].idxmax()
b_peak_idx = ts["Bedroom_smooth"].idxmax()

k_peak_time = ts.loc[k_peak_idx, "TimeOnly"]
b_peak_time = ts.loc[b_peak_idx, "TimeOnly"]

k_peak_value = ts.loc[k_peak_idx, "Kitchen_smooth"]
b_peak_value = ts.loc[b_peak_idx, "Bedroom_smooth"]

transport_delay_min = (b_peak_time - k_peak_time).total_seconds() / 60
bedroom_fraction = (b_peak_value / k_peak_value) * 100

print("\n================ TRANSPORT SUMMARY ================")
print("Kitchen peak time:", k_peak_time.strftime("%H:%M:%S"))
print("Bedroom peak time:", b_peak_time.strftime("%H:%M:%S"))
print("Kitchen peak concentration (cm^-3):", round(k_peak_value, 0))
print("Bedroom peak concentration (cm^-3):", round(b_peak_value, 0))
print("Transport delay (min):", round(transport_delay_min, 2))
print("Bedroom peak as % of kitchen peak:", round(bedroom_fraction, 1))
print("===================================================\n")

# ---------------------------------------------------------
# 9. PLOT
# ---------------------------------------------------------
plt.figure(figsize=(10, 5))

plt.plot(
    ts["TimeOnly"],
    ts["Kitchen_smooth"],
    linewidth=2,
    label="Kitchen"
)

plt.plot(
    ts["TimeOnly"],
    ts["Bedroom_smooth"],
    linewidth=2,
    linestyle="--",
    label="Master bedroom"
)

plt.scatter(k_peak_time, k_peak_value, zorder=5)
plt.scatter(b_peak_time, b_peak_value, zorder=5)

plt.annotate(
    f"Kitchen peak\n{k_peak_value:.2e}",
    xy=(k_peak_time, k_peak_value),
    xytext=(10, 10),
    textcoords="offset points",
    fontsize=9
)

plt.annotate(
    f"Bedroom peak\n{b_peak_value:.2e}",
    xy=(b_peak_time, b_peak_value),
    xytext=(10, -20),
    textcoords="offset points",
    fontsize=9
)

plt.xlabel("Time")
plt.ylabel("Particle number concentration (cm$^{-3}$)")
plt.title(
    "Figure 6.1. Time series of particle number concentration measured simultaneously\n"
    "in the kitchen and master bedroom during a NaCl tracer aerosol experiment"
)
plt.legend()
plt.grid(True, linestyle="--", linewidth=0.5)

if use_log_y:
    plt.yscale("log")

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.show()
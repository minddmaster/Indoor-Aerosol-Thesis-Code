# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 18:19:08 2026

@author: papkp
"""

# =========================================================
# FIGURE 6.3.1 – SMPS particle size distribution during bacon frying
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ---------------------------------------------------------
# FILE PATH
# ---------------------------------------------------------
smps_kitchen_file = Path(
r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 6.3.1/DAY5 SMPS DATA_COM33_Kitchen.xlsx"
)

# ---------------------------------------------------------
# BACON FRY PERIODS
# ---------------------------------------------------------
FRY_PERIODS = [
("13:02:40","13:08:40"),
("13:28:30","13:34:30"),
("13:53:50","13:59:50")
]

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
df = pd.read_excel(smps_kitchen_file)
df.columns = [str(c).strip() for c in df.columns]

df["DateTime"] = pd.to_datetime(df["corrected time"], errors="coerce")
df = df.dropna(subset=["DateTime"])

# convert time of day
df["TimeOnly"] = pd.to_datetime("2000-01-01 " + df["DateTime"].dt.strftime("%H:%M:%S"))

# size bin columns
diam_cols = [c for c in df.columns if c not in ["corrected time","DateTime","TimeOnly"]]

# convert numeric
df[diam_cols] = df[diam_cols].apply(pd.to_numeric,errors="coerce")

# convert diameter labels
diameters = [float(c) for c in diam_cols]

# ---------------------------------------------------------
# EXTRACT FRY DATA
# ---------------------------------------------------------
fry_frames = []

for start,end in FRY_PERIODS:

    start_dt = pd.to_datetime("2000-01-01 "+start)
    end_dt   = pd.to_datetime("2000-01-01 "+end)

    sel = df[(df["TimeOnly"]>=start_dt) & (df["TimeOnly"]<=end_dt)]

    fry_frames.append(sel)

fry_data = pd.concat(fry_frames)

# mean distribution
mean_dist = fry_data[diam_cols].mean()

# ---------------------------------------------------------
# PLOT
# ---------------------------------------------------------
plt.figure(figsize=(7,5))

plt.plot(
diameters,
mean_dist,
linewidth=2
)

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Particle diameter (nm)")
plt.ylabel("Particle number concentration (cm$^{-3}$)")

plt.title(
"Figure 6.3.1 Particle size distribution measured during bacon frying"
)

plt.grid(True,linestyle="--",linewidth=0.5)

plt.tight_layout()
plt.show()
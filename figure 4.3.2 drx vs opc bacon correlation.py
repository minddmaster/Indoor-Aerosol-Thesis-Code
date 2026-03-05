# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 20:28:39 2026

@author: papkp
"""

# Ref No: THESIS-FIG-4.3.2-INSTRUMENT-COMPARISON-PM1-PM25-PM10-2026-03-05

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress

DRX_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 5 Bacon expt/TEST 1_001_sphereday 5_DRX.csv"
OPC_PATH = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/day 5 Bacon expt/OPC2_007_sphereday5_opc5_kitchen.CSV"

OUT_DIR = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Figures/"
os.makedirs(OUT_DIR, exist_ok=True)

RESAMPLE = "10S"

# -------------------------
# Load DRX
# -------------------------

drx = pd.read_csv(DRX_PATH, low_memory=False)

drx["Time"] = pd.to_datetime(drx["Time"], errors="coerce")

drx["PM1"] = pd.to_numeric(drx["PM1 [ug/m3]"], errors="coerce")
drx["PM25"] = pd.to_numeric(drx["PM2.5 [ug/m3]"], errors="coerce")
drx["PM10"] = pd.to_numeric(drx["PM10 [ug/m3]"], errors="coerce")

drx = drx.dropna(subset=["Time"])
drx = drx.set_index("Time")

# -------------------------
# Load OPC
# -------------------------

opc = pd.read_csv(OPC_PATH, low_memory=False)

opc["Time"] = pd.to_datetime(opc["Unnamed: 0"], errors="coerce")

opc["PM1"] = pd.to_numeric(opc["PM_1.000(ug/m^3)"], errors="coerce")
opc["PM25"] = pd.to_numeric(opc["PM_2.500(ug/m^3)"], errors="coerce")
opc["PM10"] = pd.to_numeric(opc["PM_10.000(ug/m^3)"], errors="coerce")

opc = opc.dropna(subset=["Time"])
opc = opc.set_index("Time")

# -------------------------
# Synchronise data
# -------------------------

ts = drx.resample(RESAMPLE).mean().join(
     opc.resample(RESAMPLE).mean(),
     how="inner",
     lsuffix="_DRX",
     rsuffix="_OPC"
)

ts = ts.dropna()

print("Total paired measurements:", len(ts))

# -------------------------
# Function to plot comparison
# -------------------------

def plot_correlation(metric):

    x = ts[f"{metric}_DRX"].values
    y = ts[f"{metric}_OPC"].values

    slope, intercept, r_value, p_value, std_err = linregress(x,y)

    x_line = np.linspace(min(x), max(x), 100)
    y_line = slope*x_line + intercept

    plt.figure(figsize=(6,5))

    plt.scatter(x,y,s=15,alpha=0.6,label="Measurements")

    plt.plot(x_line,y_line,
             linestyle="--",
             linewidth=2,
             label=f"Linear fit (R² = {r_value**2:.3f})")

    plt.xlabel(f"DustTrak DRX {metric} (µg m⁻³)")
    plt.ylabel(f"OPC-N2 {metric} (µg m⁻³)")

    plt.title(f"Correlation between DRX and OPC {metric}")

    plt.grid(True)
    plt.legend()

    out_file = OUT_DIR + f"Figure_4.3.2_{metric}_Comparison.png"

    plt.tight_layout()
    plt.savefig(out_file, dpi=600)

    plt.show()

    print(metric, "R² =", r_value**2)

# -------------------------
# Generate all three plots
# -------------------------

plot_correlation("PM1")
plot_correlation("PM25")
plot_correlation("PM10")
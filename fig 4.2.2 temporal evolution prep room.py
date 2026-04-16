# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 21:01:06 2026

@author: papkp
"""

import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# FILE PATHS
# ==========================================
cpc_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 2.2 PREPROOM/Analysis/CPC006.csv"
opc_drx_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 2.2 PREPROOM/Analysis/scaled_PM2.5_OPC + DRX.xlsx"
elpi_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 2.2 PREPROOM/Analysis/12_04_24_2 UoB_PrepRoom.dat"

output_png = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 2.2 PREPROOM/Analysis/Figure_4_2_2_multi_instrument.png"

# ==========================================
# SETTINGS
# ==========================================
base_date = "2024-04-12 "
plot_start = "2024-04-12 13:45:00"
plot_end   = "2024-04-12 14:20:00"

# ==========================================
# HELPER
# ==========================================
def norm(series):
    series = pd.to_numeric(series, errors="coerce")
    smin = series.min()
    smax = series.max()
    if pd.isna(smin) or pd.isna(smax) or smax == smin:
        return pd.Series(np.nan, index=series.index)
    return (series - smin) / (smax - smin)

# ==========================================
# LOAD OPC + DRX
# ==========================================
opc = pd.read_excel(opc_drx_file)

print("OPC/DRX columns:")
print(opc.columns.tolist())

opc["time_opc"] = pd.to_datetime(base_date + opc["OPC Time"].astype(str), errors="coerce")
opc["time_drx"] = pd.to_datetime(base_date + opc["DRX Time"].astype(str), errors="coerce")

opc_signal = opc[["time_opc", "opc4_RollMean_PM2.5 (scaled)"]].copy()
opc_signal.rename(columns={
    "time_opc": "time",
    "opc4_RollMean_PM2.5 (scaled)": "OPC_PM25"
}, inplace=True)

drx_signal = opc[["time_drx", "DRX PM2.5 [ug/m3]"]].copy()
drx_signal.rename(columns={
    "time_drx": "time",
    "DRX PM2.5 [ug/m3]": "DRX_PM25"
}, inplace=True)

# ==========================================
# LOAD CPC
# ==========================================
cpc = pd.read_csv(cpc_file, encoding="latin1", sep=None, engine="python")

print("\nCPC columns:")
print(cpc.columns.tolist())

cpc["time"] = pd.to_datetime(base_date + cpc["Time"].astype(str), errors="coerce")
cpc["CPC06"] = pd.to_numeric(cpc["CPC06 Concentration (#/cm³)"], errors="coerce")
cpc["CPC12"] = pd.to_numeric(cpc["CPC12 Concentration (#/cm³)"], errors="coerce")
cpc["CPC"] = cpc[["CPC06", "CPC12"]].mean(axis=1)

cpc_signal = cpc[["time", "CPC"]].dropna()

# ==========================================
# LOAD ELPI FROM .dat FILE
# ==========================================
with open(elpi_file, "r", encoding="latin1", errors="ignore") as f:
    lines = f.readlines()

# Find [Data] section
data_start = None
for i, line in enumerate(lines):
    if line.strip() == "[Data]":
        data_start = i + 1
        break

if data_start is None:
    raise ValueError("Could not find [Data] section in ELPI .dat file.")

data_lines = [line.strip() for line in lines[data_start:] if line.strip()]

elpi = pd.read_csv(
    io.StringIO("\n".join(data_lines)),
    header=None,
    sep=",",
    engine="python"
)

print("\nELPI shape:", elpi.shape)
print("First ELPI row:")
print(elpi.iloc[0])

elpi["time"] = pd.to_datetime(elpi.iloc[:, 0], errors="coerce")
elpi["ELPI_total"] = pd.to_numeric(elpi.iloc[:, 32], errors="coerce")

elpi_signal = elpi[["time", "ELPI_total"]].dropna()

print("\nELPI signal preview:")
print(elpi_signal.head())

# ==========================================
# MERGE ALL DATA
# ==========================================
df = opc_signal.copy()

for dataset in [drx_signal, cpc_signal, elpi_signal]:
    df = pd.merge(df, dataset, on="time", how="outer")

df = df.sort_values("time").drop_duplicates(subset="time").reset_index(drop=True)

# Drop rows where all signals are missing
df = df.dropna(subset=["OPC_PM25", "DRX_PM25", "CPC", "ELPI_total"], how="all")

# Resample to 30 seconds
df = (
    df.set_index("time")
      .resample("30S")
      .mean()
      .interpolate(limit_direction="both")
      .reset_index()
)

print("\nMerged dataframe preview:")
print(df.head())

# ==========================================
# TRIM TO EVENT WINDOW
# ==========================================
df_plot = df[
    (df["time"] >= pd.Timestamp(plot_start)) &
    (df["time"] <= pd.Timestamp(plot_end))
].copy()

# ==========================================
# NORMALISE USING EVENT WINDOW ONLY
# ==========================================
df_plot["OPC_norm"] = norm(df_plot["OPC_PM25"])
df_plot["DRX_norm"] = norm(df_plot["DRX_PM25"])
df_plot["CPC_norm"] = norm(df_plot["CPC"])
df_plot["ELPI_norm"] = norm(df_plot["ELPI_total"])

print("\nCPC summary in plot window:")
print(df_plot["CPC"].describe())

# ==========================================
# PLOT
# ==========================================
plt.figure(figsize=(10, 5))

plt.plot(df_plot["time"], df_plot["OPC_norm"], label="OPC (PM2.5)", linewidth=2)
plt.plot(df_plot["time"], df_plot["DRX_norm"], label="DRX (PM2.5)", linewidth=2)
plt.plot(df_plot["time"], df_plot["CPC_norm"], label="CPC (number)", linewidth=2)
plt.plot(df_plot["time"], df_plot["ELPI_norm"], label="ELPI (total)", linewidth=2)

plt.xlabel("Time")
plt.ylabel("Normalised concentration")
plt.legend(frameon=True, loc="upper right")
plt.grid(True, linestyle="--", alpha=0.3)

plt.tight_layout()
plt.savefig(output_png, dpi=300, bbox_inches="tight")
plt.show()

print("\nSaved figure to:")
print(output_png)
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 22:28:28 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import glob
import os
from statsmodels.nonparametric.smoothers_lowess import lowess

# --------------------------------
# Folder paths
# --------------------------------
outdoor_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.x/BDFI OUTDOOR 30 MINS"
gf_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.x/BDFI GROUND FLOOR 30 MINS"
ff_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.x/BDFI FIRST FLOOR 30 MINS"

save_path = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/merged_BDFI_PM25.csv"

# --------------------------------
# Extract PM2.5 from one file
# --------------------------------
def extract_pm25_from_file(filepath, label_keywords=("AQ PM2.5", "BDFI AQ PM2.5")):
    raw = pd.read_csv(filepath, header=None)

    pm25_blocks = []
    ncols = raw.shape[1]

    for c in range(ncols - 3):
        first_row_label = str(raw.iloc[0, c + 3]).strip()

        if first_row_label in label_keywords:
            temp = raw.iloc[:, [c, c + 1]].copy()
            temp.columns = ["Time", "PM25"]

            temp = temp.dropna(subset=["Time", "PM25"])
            temp["Time"] = pd.to_datetime(temp["Time"], dayfirst=True, errors="coerce")
            temp["PM25"] = pd.to_numeric(temp["PM25"], errors="coerce")
            temp = temp.dropna(subset=["Time", "PM25"])

            pm25_blocks.append(temp)

    if not pm25_blocks:
        raise ValueError(f"No PM2.5 block found in file: {os.path.basename(filepath)}")

    out = pd.concat(pm25_blocks, ignore_index=True)
    out = out.drop_duplicates(subset="Time").sort_values("Time")
    return out

# --------------------------------
# Load all files in a folder
# --------------------------------
def load_pm25_folder(folder, output_name):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))

    if not files:
        raise ValueError(f"No CSV files found in folder: {folder}")

    all_dfs = []

    for f in files:
        print(f"Reading {os.path.basename(f)}")
        temp = extract_pm25_from_file(f)
        all_dfs.append(temp)

    df = pd.concat(all_dfs, ignore_index=True)
    df = df.drop_duplicates(subset="Time").sort_values("Time")
    df = df.rename(columns={"PM25": output_name})
    return df

# --------------------------------
# Load datasets
# --------------------------------
outdoor = load_pm25_folder(outdoor_folder, "Outdoor")
gf = load_pm25_folder(gf_folder, "Indoor_GF")
ff = load_pm25_folder(ff_folder, "Indoor_FF")

print("Outdoor rows:", len(outdoor))
print("Ground floor rows:", len(gf))
print("First floor rows:", len(ff))

# --------------------------------
# Merge and save
# --------------------------------
df = outdoor.merge(gf, on="Time", how="inner")
df = df.merge(ff, on="Time", how="inner")
df = df.sort_values("Time").dropna()

print("Merged rows:", len(df))
print(df.head())

df.to_csv(save_path, index=False)
print(f"\nSaved merged dataset to:\n{save_path}")

# --------------------------------
# Optional quick infiltration check
# --------------------------------
df = df[df["Outdoor"] > 0].copy()
df["IO_GF"] = df["Indoor_GF"] / df["Outdoor"]
df["IO_FF"] = df["Indoor_FF"] / df["Outdoor"]

df_qc = df[(df["IO_GF"] <= 1.2) & (df["IO_FF"] <= 1.2)].copy()

P = np.nanpercentile(df_qc["Outdoor"], 95)
df_hi = df_qc[df_qc["Outdoor"] >= P].copy()

fitted_GF = lowess(df_hi["IO_GF"], df_hi["Outdoor"], frac=1.0, return_sorted=True)
fitted_FF = lowess(df_hi["IO_FF"], df_hi["Outdoor"], frac=1.0, return_sorted=True)

Finf_GF = np.mean(fitted_GF[:, 1])
Finf_FF = np.mean(fitted_FF[:, 1])

print("\nQuick check:")
print("Ground Floor Finf =", round(Finf_GF, 3))
print("First Floor Finf  =", round(Finf_FF, 3))
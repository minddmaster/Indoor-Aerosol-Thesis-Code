# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 13:19:20 2026

@author: papkp
"""

import pandas as pd
import glob
import os

# =====================================================
# FOLDER PATHS
# =====================================================

gf_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/BDFI GROUND FLOOR 30 MINS"
ff_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/BDFI FIRST FLOOR 30 MINS"

output_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final"
os.makedirs(output_folder, exist_ok=True)

co2_output_path = os.path.join(output_folder, "Merged_BDFI_CO2_Data.xlsx")

# =====================================================
# EXTRACT CO2 FROM ONE FILE
# =====================================================

def extract_co2_from_file(filepath, label_keywords=("AQ CO2 Concentration", "BDFI AQ CO2 Concentration")):
    raw = pd.read_csv(filepath, header=None)

    co2_blocks = []
    ncols = raw.shape[1]

    for c in range(ncols - 3):
        label = str(raw.iloc[0, c + 3]).strip()

        if label in label_keywords:
            temp = raw.iloc[:, [c, c + 1]].copy()
            temp.columns = ["Time", "CO2"]

            temp = temp.dropna(subset=["Time", "CO2"])
            temp["Time"] = pd.to_datetime(temp["Time"], dayfirst=True, errors="coerce")
            temp["CO2"] = pd.to_numeric(temp["CO2"], errors="coerce")
            temp = temp.dropna(subset=["Time", "CO2"])

            co2_blocks.append(temp)

    if not co2_blocks:
        raise ValueError(f"No CO2 block found in file: {os.path.basename(filepath)}")

    out = pd.concat(co2_blocks, ignore_index=True)
    out = out.drop_duplicates(subset="Time").sort_values("Time")
    return out

# =====================================================
# LOAD ALL FILES FROM A FOLDER
# =====================================================

def load_co2_folder(folder, output_name):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))

    if not files:
        raise ValueError(f"No CSV files found in folder: {folder}")

    all_dfs = []

    for f in files:
        print(f"Reading {os.path.basename(f)}")
        temp = extract_co2_from_file(f)
        all_dfs.append(temp)

    df = pd.concat(all_dfs, ignore_index=True)
    df = df.drop_duplicates(subset="Time").sort_values("Time")
    df = df.rename(columns={"CO2": output_name})

    return df

# =====================================================
# LOAD GROUND AND FIRST FLOOR CO2
# =====================================================

gf_co2 = load_co2_folder(gf_folder, "Ground Floor CO2")
ff_co2 = load_co2_folder(ff_folder, "First Floor CO2")

print("Ground Floor CO2 rows:", len(gf_co2))
print("First Floor CO2 rows:", len(ff_co2))

# =====================================================
# MERGE
# =====================================================

co2_df = gf_co2.merge(ff_co2, on="Time", how="inner")
co2_df = co2_df.sort_values("Time").dropna()

print("Merged CO2 rows:", len(co2_df))
print("Date range:", co2_df["Time"].min(), "to", co2_df["Time"].max())
print(co2_df.head())

# =====================================================
# SAVE
# =====================================================

co2_df.to_excel(co2_output_path, index=False)

print("\nCO2 file saved to:")
print(co2_output_path)
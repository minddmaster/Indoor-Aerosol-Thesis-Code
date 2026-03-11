# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 11:46:29 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# =========================================================
# 1. PATHS
# =========================================================
base_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1"

first_floor_folder = os.path.join(base_folder, "BDFI FIRST FLOOR 30 MINS")
ground_floor_folder = os.path.join(base_folder, "BDFI GROUND FLOOR 30 MINS")
outdoor_folder = os.path.join(base_folder, "BDFI OUTDOOR 30 MINS")

output_folder = os.path.join(base_folder, "outputs_co2")
os.makedirs(output_folder, exist_ok=True)

START_DATE = pd.Timestamp("2023-06-09 00:00:00")
END_DATE   = pd.Timestamp("2024-01-14 23:59:59")

# =========================================================
# 2. HELPERS
# =========================================================
def list_data_files(folder):
    patterns = ["*.csv", "*.xlsx", "*.xls"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(folder, pattern)))
    return sorted(files)

def read_raw_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file_path, header=None)
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path, header=None)
    return None

def extract_metric_from_wide_file(file_path, metric_name, output_name):
    """
    Raw files are arranged in repeated blocks:
    [time, value, unit, metric_name, blank, blank, blank]
    """
    df = read_raw_file(file_path)

    if df is None or df.empty:
        print(f"Could not read: {file_path}")
        return pd.DataFrame(columns=["Time", output_name])

    matches = []

    for col in df.columns:
        metric_rows = df.index[df[col].astype(str).str.strip() == metric_name].tolist()

        for r in metric_rows:
            time_col = col - 3
            value_col = col - 2

            if time_col >= 0 and value_col >= 0:
                temp = pd.DataFrame({
                    "Time": pd.to_datetime(df.iloc[:, time_col], errors="coerce", dayfirst=True),
                    output_name: pd.to_numeric(df.iloc[:, value_col], errors="coerce")
                })

                temp = temp.dropna(subset=["Time", output_name])
                temp = temp[temp[output_name] >= 0]

                if not temp.empty:
                    matches.append(temp)

    if not matches:
        print(f"Metric '{metric_name}' not found in {os.path.basename(file_path)}")
        return pd.DataFrame(columns=["Time", output_name])

    combined = pd.concat(matches, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Time"])
    combined = combined.sort_values("Time")
    return combined

def load_folder_metric(folder, metric_name, output_name):
    files = list_data_files(folder)

    if not os.path.exists(folder):
        print(f"Folder does not exist: {folder}")
        return pd.DataFrame(columns=["Time", output_name])

    if not files:
        print(f"No files found in: {folder}")
        return pd.DataFrame(columns=["Time", output_name])

    all_data = []

    print(f"\nLoading {output_name}")
    print(f"Metric name: {metric_name}")

    for file_path in files:
        print(f"  -> {os.path.basename(file_path)}")
        temp = extract_metric_from_wide_file(file_path, metric_name, output_name)
        if not temp.empty:
            all_data.append(temp)

    if not all_data:
        print(f"No usable data found for {output_name}")
        return pd.DataFrame(columns=["Time", output_name])

    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Time"])
    combined = combined.sort_values("Time")

    print(f"Loaded {len(combined)} rows for {output_name}")
    print(f"Time range: {combined['Time'].min()} to {combined['Time'].max()}")

    return combined

# =========================================================
# 3. EXTRACT CO2
# =========================================================
# First floor and outdoor use "AQ CO2 Concentration"
# Ground floor uses "BDFI AQ CO2 Concentration"

ff_co2 = load_folder_metric(first_floor_folder, "AQ CO2 Concentration", "First Floor CO2")
gf_co2 = load_folder_metric(ground_floor_folder, "BDFI AQ CO2 Concentration", "Ground Floor CO2")
out_co2 = load_folder_metric(outdoor_folder, "AQ CO2 Concentration", "Outdoor CO2")

# =========================================================
# 4. OPTIONAL: EXTRACT PM2.5 AS WELL
# =========================================================
ff_pm25 = load_folder_metric(first_floor_folder, "AQ PM2.5", "First Floor PM2.5")
gf_pm25 = load_folder_metric(ground_floor_folder, "BDFI AQ PM2.5", "Ground Floor PM2.5")
out_pm25 = load_folder_metric(outdoor_folder, "AQ PM2.5", "Outdoor PM2.5")

# =========================================================
# 5. MERGE ALL
# =========================================================
merged = pd.merge(ff_co2, gf_co2, on="Time", how="outer")
merged = pd.merge(merged, out_co2, on="Time", how="outer")

merged = pd.merge(merged, ff_pm25, on="Time", how="outer")
merged = pd.merge(merged, gf_pm25, on="Time", how="outer")
merged = pd.merge(merged, out_pm25, on="Time", how="outer")

merged["Time"] = pd.to_datetime(merged["Time"], errors="coerce")
merged = merged.dropna(subset=["Time"])
merged = merged[(merged["Time"] >= START_DATE) & (merged["Time"] <= END_DATE)]
merged = merged.sort_values("Time")

# average duplicates if any
merged = merged.groupby("Time", as_index=False).mean(numeric_only=True)

print("\nMerged preview:")
print(merged.head())
print("Merged time range:", merged["Time"].min(), "to", merged["Time"].max())

# =========================================================
# 6. SAVE MERGED FILE
# =========================================================
merged_path = os.path.join(output_folder, "Merged_BDFI_CO2_PM25.xlsx")
merged.to_excel(merged_path, index=False)

print("\nSaved merged file:")
print(merged_path)

# =========================================================
# 7. FIGURE 7.4.1 EXAMPLE: GROUND FLOOR CO2 vs GROUND FLOOR PM2.5
# =========================================================
plot_df = merged.dropna(subset=["Ground Floor CO2", "Ground Floor PM2.5"]).copy()

plt.figure(figsize=(8, 6))
plt.scatter(plot_df["Ground Floor CO2"], plot_df["Ground Floor PM2.5"], alpha=0.4)

plt.xlabel("Ground floor CO₂ concentration (ppm)")
plt.ylabel("Ground floor PM2.5 concentration (μg m$^{-3}$)")
plt.title("Figure 7.4.1 – Relationship between ground floor CO₂ and PM2.5")
plt.grid(alpha=0.3)
plt.tight_layout()

fig_path = os.path.join(output_folder, "Figure_7_4_1_GroundFloor_CO2_vs_PM25.png")
plt.savefig(fig_path, dpi=600, bbox_inches="tight")
plt.show()

print("\nSaved figure:")
print(fig_path)
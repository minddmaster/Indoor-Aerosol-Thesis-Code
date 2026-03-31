# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 00:14:11 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

# =====================================================
# 1. SETTINGS
# =====================================================

ALIGNMENT_FACTOR = 0.477  # DustTrak / MM11048 scaling

outdoor_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/BDFI OUTDOOR 30 MINS"
gf_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/BDFI GROUND FLOOR 30 MINS"
ff_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/BDFI FIRST FLOOR 30 MINS"

output_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final"
os.makedirs(output_folder, exist_ok=True)

merged_excel_path = os.path.join(output_folder, "Merged_BDFI_PM25_Data_BiasCorrected.xlsx")
daily_excel_path = os.path.join(output_folder, "Daily_Averaged_BDFI_PM25_BiasCorrected.xlsx")
monthly_excel_path = os.path.join(output_folder, "Table_7_1_1_Monthly_PM25_BiasCorrected.xlsx")
daily_plot_path = os.path.join(output_folder, "Figure_7_1_1_Daily_Averaged_PM25_BiasCorrected.png")
boxplot_path = os.path.join(output_folder, "Figure_7_2_1_IO_Boxplot_BiasCorrected.png")

# =====================================================
# 2. EXTRACT PM2.5 FROM ONE FILE
# =====================================================

def extract_pm25_from_file(filepath, label_keywords=("AQ PM2.5", "BDFI AQ PM2.5")):
    raw = pd.read_csv(filepath, header=None)

    pm25_blocks = []
    ncols = raw.shape[1]

    for c in range(ncols - 3):
        label = str(raw.iloc[0, c + 3]).strip()

        if label in label_keywords:
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

# =====================================================
# 3. LOAD ALL FILES FROM A FOLDER
# =====================================================

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

# =====================================================
# 4. LOAD DATA
# =====================================================

outdoor = load_pm25_folder(outdoor_folder, "Outdoor")
gf = load_pm25_folder(gf_folder, "Ground Floor")
ff = load_pm25_folder(ff_folder, "First Floor")

print("Outdoor rows:", len(outdoor))
print("Ground Floor rows:", len(gf))
print("First Floor rows:", len(ff))

# =====================================================
# 5. MERGE
# =====================================================

df = outdoor.merge(gf, on="Time", how="inner")
df = df.merge(ff, on="Time", how="inner")
df = df.sort_values("Time").dropna()

print("Merged rows before filtering:", len(df))
print("Date range before filtering:", df["Time"].min(), "to", df["Time"].max())

# =====================================================
# 6. REMOVE KNOWN BAD / UNAVAILABLE PERIODS
# =====================================================

df["Time"] = pd.to_datetime(df["Time"])

bad_periods = [
    ("2024-08-21", "2024-09-10"),
    ("2024-09-10", "2024-09-30"),
    ("2024-09-30", "2024-10-20"),
    ("2024-10-20", "2024-11-08"),
    ("2024-11-08", "2024-11-28"),
    ("2024-12-16", "2025-01-05"),
    ("2025-01-05", "2025-01-25"),
    ("2025-01-25", "2025-02-14"),
    ("2025-02-14", "2025-03-06"),
    ("2025-03-06", "2025-03-26"),
    ("2025-03-26", "2025-04-15"),
    ("2025-04-15", "2025-05-05"),
    ("2025-05-05", "2025-05-25"),
]

for start, end in bad_periods:
    df = df[~((df["Time"] >= pd.Timestamp(start)) & (df["Time"] <= pd.Timestamp(end)))]

print("Merged rows after filtering:", len(df))
print("Date range after filtering:", df["Time"].min(), "to", df["Time"].max())

# =====================================================
# 7. APPLY BIAS CORRECTION
# =====================================================

for col in ["Outdoor", "Ground Floor", "First Floor"]:
    df[col] = df[col] * ALIGNMENT_FACTOR

print(f"Applied alignment factor: {ALIGNMENT_FACTOR}")

# save corrected merged data
df.to_excel(merged_excel_path, index=False)
print("Bias-corrected merged dataset saved to:")
print(merged_excel_path)

# =====================================================
# 8. DAILY AVERAGES
# =====================================================

daily_df = df.set_index("Time")
daily_avg = daily_df.resample("D").mean(numeric_only=True)

# preserve gaps as missing days
daily_avg = daily_avg.asfreq("D")

daily_avg.to_excel(daily_excel_path)
print("Daily averaged data saved to:")
print(daily_excel_path)

# =====================================================
# 9. DAILY TIME SERIES PLOT
# =====================================================

plt.figure(figsize=(12, 6))
plt.plot(daily_avg.index, daily_avg["First Floor"], label="First floor indoor")
plt.plot(daily_avg.index, daily_avg["Ground Floor"], label="Ground floor indoor")
plt.plot(daily_avg.index, daily_avg["Outdoor"], label="Outdoor")

plt.xlabel("Time")
plt.ylabel("PM2.5 concentration (µg m$^{-3}$)")
plt.title("Daily averaged indoor and outdoor PM2.5 concentrations in the BDFI Office")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(daily_plot_path, dpi=600)
plt.show()

print("Daily plot saved to:")
print(daily_plot_path)

# =====================================================
# 10. MONTHLY TABLE
# =====================================================

monthly_avg = daily_df.resample("M").mean(numeric_only=True)
monthly_avg["FF/O Ratio"] = monthly_avg["First Floor"] / monthly_avg["Outdoor"]
monthly_avg["GF/O Ratio"] = monthly_avg["Ground Floor"] / monthly_avg["Outdoor"]

monthly_avg = monthly_avg.rename(columns={
    "First Floor": "First Floor Mean",
    "Ground Floor": "Ground Floor Mean",
    "Outdoor": "Outdoor Mean"
})

monthly_avg = monthly_avg[
    ["First Floor Mean", "Ground Floor Mean", "Outdoor Mean", "FF/O Ratio", "GF/O Ratio"]
].round(2)

monthly_avg.to_excel(monthly_excel_path)
print("Monthly table saved to:")
print(monthly_excel_path)

print("\nMonthly table preview:")
print(monthly_avg.head(12))

# =====================================================
# 11. I/O BOXPLOT
# =====================================================

df_io = df.copy()
df_io = df_io[df_io["Outdoor"] > 0].copy()

df_io["FF_IO"] = df_io["First Floor"] / df_io["Outdoor"]
df_io["GF_IO"] = df_io["Ground Floor"] / df_io["Outdoor"]

# remove invalid / extreme ratios
df_io = df_io[(df_io["FF_IO"] > 0) & (df_io["GF_IO"] > 0)]
df_io = df_io[(df_io["FF_IO"] < 5) & (df_io["GF_IO"] < 5)]

fig, ax = plt.subplots(figsize=(8, 6))
bp = ax.boxplot(
    [df_io["FF_IO"], df_io["GF_IO"]],
    patch_artist=True,
    widths=0.5,
    showfliers=False
)

colors = ["steelblue", "darkorange"]
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)

ax.set_xticklabels(["First Floor", "Ground Floor"], fontsize=12)
ax.set_ylabel("Indoor / Outdoor PM₂.₅ Ratio", fontsize=12)
ax.set_title("Distribution of Indoor–Outdoor PM₂.₅ Ratios in the BDFI Building")
ax.axhline(1, linestyle="--", linewidth=1.5)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(boxplot_path, dpi=600)
plt.show()

print("Boxplot saved to:")
print(boxplot_path)
monthly_filtered = monthly_avg.loc["2024-05":"2026-03"]
print(monthly_filtered)
monthly_filtered.to_excel("Appendix_B_Table.xlsx")
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 23:27:06 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import matplotlib.dates as mdates

# =========================================================
# 1. PATHS
# =========================================================
base_folder = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1"

first_floor_folder = os.path.join(base_folder, "BDFI FIRST FLOOR 30 MINS")
ground_floor_folder = os.path.join(base_folder, "BDFI GROUND FLOOR 30 MINS")
outdoor_folder = os.path.join(base_folder, "BDFI OUTDOOR 30 MINS")

output_folder = os.path.join(base_folder, "outputs_final")
os.makedirs(output_folder, exist_ok=True)

# =========================================================
# 2. SETTINGS
# =========================================================
TARGET_METRIC_FIRST = "AQ PM2.5"
TARGET_METRIC_GROUND = "BDFI AQ PM2.5"
TARGET_METRIC_OUTDOOR = "AQ PM2.5"

START_DATE = pd.Timestamp("2023-06-09 00:00:00")
END_DATE   = pd.Timestamp("2024-01-14 23:59:59")

# =========================================================
# 3. HELPER FUNCTIONS
# =========================================================
def list_data_files(folder):
    patterns = ["*.csv", "*.xlsx", "*.xls"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(folder, pattern)))
    return sorted(files)

def assign_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Autumn"

def read_raw_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file_path, header=None)
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path, header=None)
    else:
        return None

def extract_metric_from_wide_file(file_path, metric_name, output_name):
    """
    Extract one metric from wide repeated-block files:
    [time, value, unit, metric name, blank, blank, blank]
    """
    df = read_raw_file(file_path)

    if df is None or df.empty:
        print(f"Could not read or empty: {file_path}")
        return pd.DataFrame(columns=["Time", output_name])

    print(f"\nReading: {os.path.basename(file_path)}")
    print(f"Shape: {df.shape}")

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
                    print(f"  Found '{metric_name}' at column {col} -> extracted {len(temp)} rows")

    if not matches:
        print(f"  Metric '{metric_name}' not found in {os.path.basename(file_path)}")
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

    print(f"\n==============================")
    print(f"Loading {output_name}")
    print(f"Folder: {folder}")
    print(f"Metric: {metric_name}")
    print(f"==============================")

    for file_path in files:
        temp = extract_metric_from_wide_file(file_path, metric_name, output_name)
        if not temp.empty:
            all_data.append(temp)

    if not all_data:
        print(f"No usable {metric_name} data found in {folder}")
        return pd.DataFrame(columns=["Time", output_name])

    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Time"])
    combined = combined.sort_values("Time")

    print(f"\nLoaded {len(combined)} rows for {output_name}")
    print(f"Time range: {combined['Time'].min()} to {combined['Time'].max()}")

    return combined

def season_spans(start, end):
    """
    Return seasonal spans between start and end.
    Meteorological seasons:
    Spring: Mar-May, Summer: Jun-Aug, Autumn: Sep-Nov, Winter: Dec-Feb
    """
    spans = []
    current = pd.Timestamp(start.year, start.month, 1)

    while current <= end:
        year = current.year
        month = current.month

        if month in [12, 1, 2]:
            season = "Winter"
            if month == 12:
                season_start = pd.Timestamp(year, 12, 1)
                season_end = pd.Timestamp(year + 1, 3, 1)
            else:
                season_start = pd.Timestamp(year, 1, 1)
                season_end = pd.Timestamp(year, 3, 1)
        elif month in [3, 4, 5]:
            season = "Spring"
            season_start = pd.Timestamp(year, 3, 1)
            season_end = pd.Timestamp(year, 6, 1)
        elif month in [6, 7, 8]:
            season = "Summer"
            season_start = pd.Timestamp(year, 6, 1)
            season_end = pd.Timestamp(year, 9, 1)
        else:
            season = "Autumn"
            season_start = pd.Timestamp(year, 9, 1)
            season_end = pd.Timestamp(year, 12, 1)

        span_start = max(season_start, start)
        span_end = min(season_end, end)

        if span_start < span_end:
            spans.append((span_start, span_end, season))

        current = season_end

    # remove duplicates
    unique_spans = []
    seen = set()
    for s in spans:
        key = (s[0], s[1], s[2])
        if key not in seen:
            unique_spans.append(s)
            seen.add(key)

    return unique_spans

# =========================================================
# 4. LOAD DATA
# =========================================================
first_floor = load_folder_metric(first_floor_folder, TARGET_METRIC_FIRST, "First Floor")
ground_floor = load_folder_metric(ground_floor_folder, TARGET_METRIC_GROUND, "Ground Floor")
outdoor = load_folder_metric(outdoor_folder, TARGET_METRIC_OUTDOOR, "Outdoor")

print("\nLoaded data sizes:")
print("First Floor:", first_floor.shape)
print("Ground Floor:", ground_floor.shape)
print("Outdoor:", outdoor.shape)

if first_floor.empty and ground_floor.empty and outdoor.empty:
    raise ValueError("No PM2.5 data could be extracted from any folder.")

# =========================================================
# 5. MERGE DATA
# =========================================================
merged = pd.merge(first_floor, ground_floor, on="Time", how="outer")
merged = pd.merge(merged, outdoor, on="Time", how="outer")

merged["Time"] = pd.to_datetime(merged["Time"], errors="coerce")
merged = merged.dropna(subset=["Time"])
merged = merged[(merged["Time"] >= START_DATE) & (merged["Time"] <= END_DATE)]
merged = merged.sort_values("Time")

# Average duplicate timestamps
merged = merged.groupby("Time", as_index=False).mean(numeric_only=True)

if merged.empty:
    raise ValueError("Merged dataset is empty after date filtering.")

merged = merged.set_index("Time")

print("\nMerged dataset preview:")
print(merged.head())
print("Merged time range:", merged.index.min(), "to", merged.index.max())

# =========================================================
# 6. DAILY / MONTHLY / SEASONAL
# =========================================================
daily = merged.resample("D").mean(numeric_only=True)
monthly = merged.resample("MS").mean(numeric_only=True)

daily["Month"] = daily.index.month
daily["Season"] = daily["Month"].apply(assign_season)

monthly["Month_Name"] = monthly.index.strftime("%B")
monthly["Year_Month"] = monthly.index.strftime("%b-%Y")

if "Outdoor" in monthly.columns:
    if "First Floor" in monthly.columns:
        monthly["FF/O Ratio"] = monthly["First Floor"] / monthly["Outdoor"]
    if "Ground Floor" in monthly.columns:
        monthly["GF/O Ratio"] = monthly["Ground Floor"] / monthly["Outdoor"]

# =========================================================
# 7. TABLE 7.1
# =========================================================
table_7_1 = monthly.copy()

keep_cols = []
for col in ["Month_Name", "First Floor", "Ground Floor", "Outdoor", "FF/O Ratio", "GF/O Ratio"]:
    if col in table_7_1.columns:
        keep_cols.append(col)

table_7_1 = table_7_1[keep_cols].copy()
table_7_1 = table_7_1.rename(columns={
    "Month_Name": "Month",
    "First Floor": "First Floor Mean PM2.5 (μg m^-3)",
    "Ground Floor": "Ground Floor Mean PM2.5 (μg m^-3)",
    "Outdoor": "Outdoor Mean PM2.5 (μg m^-3)",
    "FF/O Ratio": "First Floor/Outdoor Ratio",
    "GF/O Ratio": "Ground Floor/Outdoor Ratio"
}).round(2)

print("\nTable 7.1 preview:")
print(table_7_1)

table_7_1.to_excel(os.path.join(output_folder, "Table_7_1_Monthly_PM25_Averages.xlsx"))

# =========================================================
# 8. SEASONAL SUMMARY
# =========================================================
seasonal_cols = [c for c in ["First Floor", "Ground Floor", "Outdoor"] if c in daily.columns]
seasonal_summary = daily.groupby("Season")[seasonal_cols].mean(numeric_only=True)

if "Outdoor" in seasonal_summary.columns:
    if "First Floor" in seasonal_summary.columns:
        seasonal_summary["FF/O Ratio"] = seasonal_summary["First Floor"] / seasonal_summary["Outdoor"]
    if "Ground Floor" in seasonal_summary.columns:
        seasonal_summary["GF/O Ratio"] = seasonal_summary["Ground Floor"] / seasonal_summary["Outdoor"]

season_order = ["Winter", "Spring", "Summer", "Autumn"]
seasonal_summary = seasonal_summary.reindex(season_order).round(2)

print("\nSeasonal summary:")
print(seasonal_summary)

seasonal_summary.to_excel(os.path.join(output_folder, "Seasonal_Summary_PM25_BDFI.xlsx"))

# =========================================================
# 9. FIGURE 7.1 – DAILY TIME SERIES (THESIS-STYLE)
# =========================================================
fig, ax = plt.subplots(figsize=(14, 6))

# Light seasonal shading
season_colour = {
    "Winter": "#d9eaf7",
    "Spring": "#e6f4e6",
    "Summer": "#fff4cc",
    "Autumn": "#f7e1d7"
}

for span_start, span_end, season in season_spans(START_DATE, END_DATE):
    ax.axvspan(span_start, span_end, alpha=0.20, color=season_colour[season], lw=0)

if "First Floor" in daily.columns:
    ax.plot(daily.index, daily["First Floor"], linewidth=2.0, label="First floor indoor")
if "Ground Floor" in daily.columns:
    ax.plot(daily.index, daily["Ground Floor"], linewidth=2.0, label="Ground floor indoor")
if "Outdoor" in daily.columns:
    ax.plot(daily.index, daily["Outdoor"], linewidth=2.0, label="Outdoor")

ax.set_xlabel("Time", fontsize=12)
ax.set_ylabel("PM2.5 concentration (μg m$^{-3}$)", fontsize=12)
ax.set_title("Daily averaged indoor and outdoor PM2.5 concentrations in the BDFI office", fontsize=13)
ax.legend(fontsize=10, frameon=True)
ax.grid(True, alpha=0.3)

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%Y"))
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "Figure_7_1_BDFI_Daily_PM25_Time_Series.png"), dpi=600, bbox_inches="tight")
plt.show()

# =========================================================
# 10. MONTHLY BAR CHART
# =========================================================
monthly_plot_cols = [c for c in ["First Floor", "Ground Floor", "Outdoor"] if c in monthly.columns]

if monthly_plot_cols:
    monthly_plot = monthly[monthly_plot_cols].copy()
    monthly_plot.index = monthly.index.strftime("%b-%Y")

    ax = monthly_plot.plot(kind="bar", figsize=(12, 6), width=0.8)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Mean PM2.5 concentration (μg m$^{-3}$)", fontsize=12)
    ax.set_title("Monthly mean indoor and outdoor PM2.5 concentrations", fontsize=13)
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.legend(fontsize=10, frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "Monthly_Mean_PM25_BDFI.png"), dpi=600, bbox_inches="tight")
    plt.show()

# =========================================================
# 11. MONTHLY RATIO PLOT
# =========================================================
fig, ax = plt.subplots(figsize=(12, 5))
ratio_plotted = False

if "FF/O Ratio" in monthly.columns:
    ax.plot(monthly.index, monthly["FF/O Ratio"], marker="o", linewidth=2.0, markersize=5,
            label="First floor / outdoor")
    ratio_plotted = True

if "GF/O Ratio" in monthly.columns:
    ax.plot(monthly.index, monthly["GF/O Ratio"], marker="s", linewidth=2.0, markersize=5,
            label="Ground floor / outdoor")
    ratio_plotted = True

if ratio_plotted:
    ax.axhline(1.0, linestyle="--", linewidth=1.2)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Indoor/outdoor ratio", fontsize=12)
    ax.set_title("Monthly indoor/outdoor PM2.5 ratios", fontsize=13)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, frameon=True)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%Y"))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "Monthly_IO_PM25_Ratios_BDFI.png"), dpi=600, bbox_inches="tight")
    plt.show()
else:
    plt.close()

# =========================================================
# 12. EXPORT CLEAN DATA
# =========================================================
merged.reset_index().to_excel(os.path.join(output_folder, "Merged_BDFI_PM25_Data.xlsx"), index=False)
daily.reset_index().to_excel(os.path.join(output_folder, "Daily_PM25_BDFI.xlsx"), index=False)
monthly.reset_index().to_excel(os.path.join(output_folder, "Monthly_PM25_BDFI.xlsx"), index=False)

print("\nAnalysis complete.")
print("Saved files in:")
print(output_folder)
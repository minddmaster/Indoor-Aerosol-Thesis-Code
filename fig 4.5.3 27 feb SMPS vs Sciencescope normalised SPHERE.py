# =========================================================
# SMPS KITCHEN vs SCIENCESCOPE KITCHEN
# 27 February 2025
#
# UPDATED VERSION:
# 1. Loads SMPS time-only data and reconstructs full datetime
# 2. Loads ScienceScope kitchen data
# 3. Aggregates SMPS to 30-minute bins
# 4. Merges both datasets
# 5. Produces:
#    - raw comparison plots
#    - normalised comparison plots
#    - scatter plots
#    - event-change analysis table
# =========================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from scipy.stats import pearsonr, spearmanr

# =========================================================
# USER PATHS
# =========================================================
smps_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 4.5.2 SPHERE 28 FEB/DAY4 SMPS DATA_COM32.xlsx"
sciencescope_kitchen_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 4.5.2 SPHERE 28 FEB/26 feb 16.30 - 28 Feb 10.30 2025 SPHERE X223 Kitchen.csv"

output_dir = Path(r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 4.5.2 SPHERE 28 FEB/SMPS_vs_ScienceScope_27Feb")
output_dir.mkdir(parents=True, exist_ok=True)

# =========================================================
# SETTINGS
# =========================================================
analysis_date = "27/02/2025"
analysis_start = pd.to_datetime("27/02/2025 00:00:00", dayfirst=True)
analysis_end   = pd.to_datetime("27/02/2025 23:59:59", dayfirst=True)

# 27 Feb 2025 cooking experiment block
event_start = pd.to_datetime("27/02/2025 12:41:15", dayfirst=True)
event_end   = pd.to_datetime("27/02/2025 17:18:50", dayfirst=True)

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 11
})

# =========================================================
# FUNCTIONS
# =========================================================
def load_sciencescope_csv(filepath, location_name="Kitchen"):
    raw = pd.read_csv(filepath, header=None)
    records = []
    ncols = raw.shape[1]

    for start in range(0, ncols, 7):
        if start + 3 >= ncols:
            continue

        dt_col = raw.iloc[:, start]
        value_col = raw.iloc[:, start + 1]
        param_col = raw.iloc[:, start + 3]

        param_name = param_col.dropna().astype(str).str.strip().replace("", np.nan).dropna()
        if param_name.empty:
            continue
        param_name = param_name.iloc[0]

        temp = pd.DataFrame({
            "datetime": pd.to_datetime(dt_col, dayfirst=True, errors="coerce"),
            "value": pd.to_numeric(value_col, errors="coerce")
        }).dropna(subset=["datetime"])

        temp = temp[temp["datetime"].dt.year >= 2020]
        temp["parameter"] = param_name
        records.append(temp)

    tidy = pd.concat(records, ignore_index=True)

    wide = tidy.pivot_table(
        index="datetime",
        columns="parameter",
        values="value",
        aggfunc="mean"
    ).reset_index()

    rename_map = {
        "AQ PM1.0": "PM1",
        "AQ PM2.5": "PM2_5",
        "AQ PM10.0": "PM10",
        "AQ CO": "CO",
        "AQ CO2 Concentration": "CO2",
        "AQ VOC": "VOC",
        "AQ VOC ": "VOC",
        "AQ Temperature": "Temperature",
        "AQ Sound Level": "Sound",
        "AQ RSSI": "RSSI"
    }

    wide = wide.rename(columns=rename_map)
    wide.columns.name = None
    wide = wide.sort_values("datetime").drop_duplicates(subset="datetime").reset_index(drop=True)

    keep_cols = ["datetime"]
    for c in ["PM1", "PM2_5", "PM10", "CO", "CO2", "VOC", "Temperature"]:
        if c in wide.columns:
            keep_cols.append(c)

    wide = wide[keep_cols].copy()

    rename_out = {"datetime": "datetime"}
    for c in keep_cols:
        if c != "datetime":
            rename_out[c] = f"{c}_{location_name}"
    wide = wide.rename(columns=rename_out)

    return wide


def load_smps_timeonly(filepath, sheet_name="edit1 (2)"):
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=0)
    df = df.dropna(axis=1, how="all").copy()
    df.columns = [str(c).strip() for c in df.columns]

    print("\nSMPS columns:")
    print(df.columns.tolist())

    if "corrected time" not in df.columns:
        raise ValueError("Column 'corrected time' was not found in the SMPS sheet.")

    raw_time = df["corrected time"]
    parsed_time = pd.to_datetime(raw_time, errors="coerce")

    time_strings = pd.Series(index=df.index, dtype="object")
    good = parsed_time.notna()
    time_strings.loc[good] = parsed_time.loc[good].dt.strftime("%H:%M:%S")
    time_strings.loc[~good] = raw_time.loc[~good].astype(str).str.strip()

    full_datetime = pd.to_datetime(
        analysis_date + " " + time_strings.astype(str),
        dayfirst=True,
        errors="coerce"
    )

    df["datetime"] = full_datetime

    exclude_cols = {"corrected time", "datetime"}
    numeric_cols = []

    for c in df.columns:
        if c in exclude_cols:
            continue
        temp = pd.to_numeric(df[c], errors="coerce")
        if temp.notna().sum() > 10:
            df[c] = temp
            numeric_cols.append(c)

    if not numeric_cols:
        raise ValueError("No usable numeric SMPS columns found.")

    total_col = None
    for c in numeric_cols:
        cl = c.lower()
        if "total" in cl:
            total_col = c
            break
    if total_col is None:
        for c in numeric_cols:
            cl = c.lower()
            if "conc" in cl or "number" in cl:
                total_col = c
                break

    if total_col is None:
        size_bin_cols = []
        for c in numeric_cols:
            try:
                float(str(c))
                size_bin_cols.append(c)
            except Exception:
                pass

        if len(size_bin_cols) >= 10:
            df["Total_SMPS"] = df[size_bin_cols].sum(axis=1, skipna=True)
            print(f"\nNo explicit total column found.")
            print(f"Using summed size-distribution columns: {len(size_bin_cols)} bins")
        else:
            df["Total_SMPS"] = df[numeric_cols].sum(axis=1, skipna=True)
            print(f"\nNo explicit total column found.")
            print(f"Using sum of all numeric columns: {len(numeric_cols)} columns")
    else:
        df["Total_SMPS"] = df[total_col]
        print(f"\nUsing explicit SMPS total column: {total_col}")

    out = df[["datetime", "Total_SMPS"]].dropna().copy()
    out = out.sort_values("datetime").drop_duplicates(subset="datetime").reset_index(drop=True)

    return out, df


def minmax(series):
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().sum() < 2:
        return pd.Series(np.nan, index=s.index)
    smin, smax = s.min(), s.max()
    if smax == smin:
        return pd.Series(np.nan, index=s.index)
    return (s - smin) / (smax - smin)


def add_event_shading(ax):
    ax.axvspan(event_start, event_end, alpha=0.08)


# =========================================================
# LOAD DATA
# =========================================================
science = load_sciencescope_csv(sciencescope_kitchen_file, location_name="Kitchen")
smps, smps_full = load_smps_timeonly(smps_file, sheet_name="edit1 (2)")

smps_full.to_csv(output_dir / "SMPS_full_parsed_debug.csv", index=False)

# =========================================================
# FILTER TO 27 FEB
# =========================================================
smps = smps[(smps["datetime"] >= analysis_start) & (smps["datetime"] <= analysis_end)].copy()
science = science[(science["datetime"] >= analysis_start) & (science["datetime"] <= analysis_end)].copy()

print("\nSMPS 27 Feb rows:", len(smps))
print("ScienceScope 27 Feb rows:", len(science))

print("\nSMPS datetime range:")
if not smps.empty:
    print(smps["datetime"].min(), "to", smps["datetime"].max())

print("\nScienceScope datetime range:")
if not science.empty:
    print(science["datetime"].min(), "to", science["datetime"].max())

smps.to_csv(output_dir / "SMPS_27Feb_raw_filtered.csv", index=False)
science.to_csv(output_dir / "ScienceScope_27Feb_raw_filtered.csv", index=False)

# =========================================================
# CREATE 30-MINUTE BINS
# =========================================================
smps["time_bin"] = smps["datetime"].dt.floor("30min")
science["time_bin"] = science["datetime"].dt.floor("30min")

smps_30 = (
    smps.groupby("time_bin", as_index=False)["Total_SMPS"]
    .mean()
    .rename(columns={"time_bin": "datetime"})
)

science_cols = [c for c in science.columns if c not in ["datetime", "time_bin"]]
science_30 = (
    science.groupby("time_bin", as_index=False)[science_cols]
    .mean()
    .rename(columns={"time_bin": "datetime"})
)

print("\nSMPS 30-min rows:", len(smps_30))
print("ScienceScope 30-min rows:", len(science_30))

merged = pd.merge(smps_30, science_30, on="datetime", how="inner").sort_values("datetime").reset_index(drop=True)
merged.to_csv(output_dir / "SMPS_ScienceScope_27Feb_merged.csv", index=False)

print("\nMerged rows:", len(merged))
if not merged.empty:
    print(merged.head())

if merged.empty:
    raise ValueError(
        "Merged dataset is empty. Check SMPS_full_parsed_debug.csv and the filtered CSV files."
    )

# =========================================================
# NORMALISATION
# =========================================================
for c in ["Total_SMPS", "PM1_Kitchen", "PM2_5_Kitchen", "PM10_Kitchen"]:
    if c in merged.columns:
        merged[f"{c}_norm"] = minmax(merged[c])

# =========================================================
# CORRELATION ANALYSIS
# =========================================================
results = []
targets = ["PM1_Kitchen", "PM2_5_Kitchen", "PM10_Kitchen"]

for target in targets:
    if target in merged.columns:
        temp = merged[["Total_SMPS", target]].dropna()
        if len(temp) >= 3:
            pearson_r, pearson_p = pearsonr(temp["Total_SMPS"], temp[target])
            spearman_rho, spearman_p = spearmanr(temp["Total_SMPS"], temp[target])

            results.append({
                "comparison": f"Total_SMPS vs {target}",
                "n_points": len(temp),
                "pearson_r": pearson_r,
                "pearson_p": pearson_p,
                "spearman_rho": spearman_rho,
                "spearman_p": spearman_p
            })

corr_df = pd.DataFrame(results)
corr_df.to_csv(output_dir / "correlation_results.csv", index=False)

print("\nCorrelation results:")
print(corr_df if not corr_df.empty else "No valid correlations calculated.")

# =========================================================
# FIGURE 1: RAW TIME SERIES
# =========================================================
fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

pairs = [
    ("PM1_Kitchen", "PM$_1$"),
    ("PM2_5_Kitchen", "PM$_{2.5}$"),
    ("PM10_Kitchen", "PM$_{10}$")
]

for i, (ax, (sensor_col, label)) in enumerate(zip(axes, pairs)):
    ax.plot(
        merged["datetime"], merged["Total_SMPS"],
        marker="o", linewidth=2.2, markersize=4, label="SMPS total number"
    )
    if sensor_col in merged.columns:
        ax.plot(
            merged["datetime"], merged[sensor_col],
            marker="s", linestyle="--", linewidth=2.2, markersize=4,
            label=f"ScienceScope {label}"
        )
    add_event_shading(ax)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.set_ylabel("Concentration")
    if i == 0:
        ax.legend(frameon=False, loc="upper right")

axes[0].set_title("SMPS kitchen total number concentration versus ScienceScope kitchen PM on 27 February 2025")
axes[-1].set_xlabel("Time")
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "timeseries_raw.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================================================
# FIGURE 2: NORMALISED TIME SERIES
# =========================================================
fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

for i, (ax, (sensor_col, label)) in enumerate(zip(axes, pairs)):
    ax.plot(
        merged["datetime"], merged["Total_SMPS_norm"],
        marker="o", linewidth=2.2, markersize=4, label="SMPS total number (normalised)"
    )
    norm_col = f"{sensor_col}_norm"
    if norm_col in merged.columns:
        ax.plot(
            merged["datetime"], merged[norm_col],
            marker="s", linestyle="--", linewidth=2.2, markersize=4,
            label=f"ScienceScope {label} (normalised)"
        )
    add_event_shading(ax)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.set_ylabel("Normalised")
    if i == 0:
        ax.legend(frameon=False, loc="upper right")

axes[0].set_title("Normalised comparison of SMPS and ScienceScope kitchen measurements on 27 February 2025")
axes[-1].set_xlabel("Time")
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "timeseries_normalised.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================================================
# FIGURE 3: SCATTER PLOTS
# =========================================================
available_targets = [t for t in targets if t in merged.columns]

if available_targets:
    fig, axes = plt.subplots(1, len(available_targets), figsize=(5 * len(available_targets), 4.8))
    if len(available_targets) == 1:
        axes = [axes]

    for ax, sensor_col in zip(axes, available_targets):
        temp = merged[["Total_SMPS", sensor_col]].dropna()
        ax.scatter(temp["Total_SMPS"], temp[sensor_col], s=40)

        if len(temp) >= 2:
            z = np.polyfit(temp["Total_SMPS"], temp[sensor_col], 1)
            p = np.poly1d(z)
            x_line = np.linspace(temp["Total_SMPS"].min(), temp["Total_SMPS"].max(), 100)
            ax.plot(x_line, p(x_line), linewidth=2)

        ax.set_title(sensor_col.replace("_Kitchen", "").replace("_", "."))
        ax.set_xlabel("SMPS total number")
        ax.set_ylabel(sensor_col)
        ax.grid(True, linestyle="--", linewidth=0.5)

        if not corr_df.empty:
            row = corr_df[corr_df["comparison"] == f"Total_SMPS vs {sensor_col}"]
            if not row.empty:
                txt = (
                    f"Pearson r = {row['pearson_r'].iloc[0]:.2f}\n"
                    f"Spearman ρ = {row['spearman_rho'].iloc[0]:.2f}"
                )
                ax.text(
                    0.05, 0.95, txt,
                    transform=ax.transAxes,
                    va="top", ha="left",
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
                )

    plt.tight_layout()
    plt.savefig(output_dir / "scatter_correlations.png", dpi=600, bbox_inches="tight")
    plt.close()

# =========================================================
# EVENT CHANGE ANALYSIS
# =========================================================
print("\nRunning event change analysis...")

event_data = merged[
    (merged["datetime"] >= event_start.floor("30min")) &
    (merged["datetime"] <= event_end.ceil("30min"))
].copy()

background_data = merged[merged["datetime"] < event_start.floor("30min")].copy()

# If no background rows exist, use first 2 merged rows
if len(background_data) == 0:
    background_data = merged.iloc[:2].copy()

print("Background rows:", len(background_data))
print("Event rows:", len(event_data))

metrics = ["Total_SMPS", "PM1_Kitchen", "PM2_5_Kitchen", "PM10_Kitchen"]
event_results = []

for m in metrics:
    if m not in merged.columns:
        continue

    background_mean = background_data[m].mean()
    event_mean = event_data[m].mean()
    event_peak = event_data[m].max()

    if pd.isna(background_mean) or background_mean == 0:
        mean_ratio = np.nan
        mean_percent_change = np.nan
        peak_ratio = np.nan
        peak_percent_change = np.nan
    else:
        mean_ratio = event_mean / background_mean
        mean_percent_change = ((event_mean - background_mean) / background_mean) * 100
        peak_ratio = event_peak / background_mean
        peak_percent_change = ((event_peak - background_mean) / background_mean) * 100

    event_results.append({
        "Metric": m,
        "Background_Mean": background_mean,
        "Event_Mean": event_mean,
        "Event_Peak": event_peak,
        "Mean_Ratio": mean_ratio,
        "Mean_Percent_Change": mean_percent_change,
        "Peak_Ratio": peak_ratio,
        "Peak_Percent_Change": peak_percent_change
    })

event_change_df = pd.DataFrame(event_results)
event_change_df.to_csv(output_dir / "event_change_analysis.csv", index=False)

print("\nEvent Change Results:")
print(event_change_df)

# =========================================================
# FIGURE 4: EVENT-ONLY COMPARISON
# =========================================================
fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

plot_metrics = [
    ("Total_SMPS", "SMPS total number concentration"),
    ("PM1_Kitchen", "ScienceScope PM$_1$"),
    ("PM2_5_Kitchen", "ScienceScope PM$_{2.5}$"),
    ("PM10_Kitchen", "ScienceScope PM$_{10}$")
]

for ax, (col, ylabel) in zip(axes, plot_metrics):
    if col in merged.columns:
        ax.plot(
            merged["datetime"], merged[col],
            marker="o", linewidth=2.2, markersize=4
        )
    add_event_shading(ax)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.set_ylabel(ylabel)

axes[0].set_title("Separate response of SMPS number concentration and ScienceScope mass concentration on 27 February 2025")
axes[-1].set_xlabel("Time")
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "event_response_separate_metrics.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================================================
# FIGURE 5: NORMALISED SEPARATE EVENT RESPONSE
# =========================================================
fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

for ax, (col, ylabel) in zip(axes, plot_metrics):
    norm_col = f"{col}_norm"
    if norm_col in merged.columns:
        ax.plot(
            merged["datetime"], merged[norm_col],
            marker="o", linewidth=2.2, markersize=4
        )
    add_event_shading(ax)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.set_ylabel(f"{ylabel}\n(normalised)")

axes[0].set_title("Normalised response of SMPS and ScienceScope metrics during the 27 February 2025 cooking period")
axes[-1].set_xlabel("Time")
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(output_dir / "event_response_separate_metrics_normalised.png", dpi=600, bbox_inches="tight")
plt.close()

# =========================================================
# SUMMARY
# =========================================================
summary_cols = [c for c in merged.columns if c != "datetime"]
merged[summary_cols].describe().T.to_csv(output_dir / "summary_statistics.csv")

print("\nDone. Files saved to:")
print(output_dir)

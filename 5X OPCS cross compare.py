import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

opc_files = {
    "OPC1": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Chamber Validation/10 May/OPC1.xlsx",
    "OPC2": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Chamber Validation/10 May/OPC2.xlsx",
    "OPC4": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Chamber Validation/10 May/OPC4.xlsx",
    "OPC5": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Chamber Validation/10 May/OPC5.xlsx",
    "OPC6": r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Chamber Validation/10 May/OPC6.xlsx",
}

PM_CHOICE = "PM2.5"
PM_PATTERNS = {
    "PM1": ["pm_1.000", "pm1", "pm_1"],
    "PM2.5": ["pm_2.500", "pm2.5", "pm_2.5", "pm25"],
    "PM10": ["pm_10.000", "pm10", "pm_10"],
}

def detect_pm_column(df, pm_choice):
    patterns = PM_PATTERNS[pm_choice]
    for c in df.columns:
        cl = str(c).lower().replace(" ", "")
        if any(p in cl for p in patterns):
            return c
    raise ValueError(f"No {pm_choice} column found. Columns: {list(df.columns)}")

def load_opc(file_path, label, pm_choice):
    df = pd.read_excel(file_path)

    pm_col = detect_pm_column(df, pm_choice)

    # force numeric (very important)
    s = pd.to_numeric(df[pm_col], errors="coerce")

    # reset index to simple 0..n-1
    s = s.reset_index(drop=True)
    return s.rename(label)

# ---- Load all
series = {}
for lab, path in opc_files.items():
    series[lab] = load_opc(path, lab, PM_CHOICE)
    print(f"{lab}: n={len(series[lab])}, NaNs={series[lab].isna().sum()}")

# ---- Align by common overlap length
min_len = min(len(s) for s in series.values())
print("\nMinimum common length across OPC files:", min_len)

combined = pd.DataFrame({lab: s.iloc[:min_len].values for lab, s in series.items()})

# Drop rows where ALL are missing, but keep partial rows
combined = combined.dropna(how="all")

print("Combined shape after overlap alignment:", combined.shape)
print("Rows with any NaN:", combined.isna().any(axis=1).sum())

# If you need strict all-5 comparison, drop rows missing any OPC:
combined_all = combined.dropna(how="any")
print("Combined shape (all 5 present):", combined_all.shape)

# Choose which to use:
use = combined_all  # strict
# use = combined      # lenient (keeps rows where some OPCs missing)

if len(use) == 0:
    raise ValueError(
        "Still no overlapping rows with all OPCs present. "
        "At least one OPC column is mostly empty or lengths are very different. "
        "Check the NaNs printed above."
    )

# ---- Inter-OPC CV (%)
mean_opc = use.mean(axis=1)
std_opc = use.std(axis=1)
cv_opc = (std_opc / mean_opc) * 100

print(f"\nMean inter-OPC CV (%): {cv_opc.mean():.2f}")
print(f"Median inter-OPC CV (%): {cv_opc.median():.2f}")

# ---- Bias vs ensemble mean
bias_df = pd.DataFrame(index=use.columns)
for opc in use.columns:
    bias_df.loc[opc, "Bias vs mean (µg/m³)"] = (use[opc] - mean_opc).mean()
    bias_df.loc[opc, "Bias vs mean (%)"] = ((use[opc] - mean_opc) / mean_opc).mean() * 100

print("\nBias relative to ensemble mean:")
print(bias_df)

# ---- Plots
plt.figure(figsize=(12,5))
for opc in use.columns:
    plt.plot(use.index, use[opc], alpha=0.75, label=opc)
plt.ylabel(f"{PM_CHOICE} (µg/m³)")
plt.xlabel("Sample index (common overlap)")
plt.title(f"Co-located OPC Comparison ({PM_CHOICE})")
plt.legend(ncol=3)
plt.tight_layout()
plt.show()

plt.figure(figsize=(10,4))
plt.plot(cv_opc.index, cv_opc)
plt.ylabel("Inter-OPC CV (%)")
plt.xlabel("Sample index (common overlap)")
plt.title(f"Inter-OPC Variability (CV) — {PM_CHOICE}")
plt.tight_layout()
plt.show()

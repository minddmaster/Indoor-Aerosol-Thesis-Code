# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 07:04:40 2026

@author: papkp
"""

# -*- coding: utf-8 -*-
"""
Extract and merge CO data from raw BDFI 30-minute files
Based on observed raw format:
col 0 = Time
col 1 = CO value
col 3 = label (AQ CO / BDFI AQ CO)
"""

from pathlib import Path
import pandas as pd

# =====================================================
# USER INPUTS
# =====================================================

folders = {
    "First Floor CO": [
        r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/BDFI DATA 30 MIN INTERVAL 2023-2026/BDFI FIRST FLOOR 30 MINS",
        r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/BDFI DATA 30 MIN INTERVAL 2023-2026/part 2 - bdfi first floor 229 sensor",
    ],
    "Ground Floor CO": [
        r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/BDFI DATA 30 MIN INTERVAL 2023-2026/BDFI GROUND FLOOR 30 MINS",
        r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/BDFI DATA 30 MIN INTERVAL 2023-2026/PART 2- BDFI GROUND FLOOR",
    ],
    "Outdoor CO": [
        r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/BDFI DATA 30 MIN INTERVAL 2023-2026/BDFI OUTDOOR 30 MINS",
        r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/BDFI DATA 30 MIN INTERVAL 2023-2026/part 2 - bdfi outer 225 sensor",
    ],
}

output_file = Path(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Fig 7.5.1/outputs_final/Merged_BDFI_CO_Data.xlsx"
)

# =====================================================
# HELPERS
# =====================================================

def list_files(folder_path: str):
    p = Path(folder_path)
    if not p.exists():
        print(f"[WARNING] Folder does not exist: {folder_path}")
        return []
    files = []
    for pattern in ["*.csv", "*.xlsx", "*.xls"]:
        files.extend(p.glob(pattern))
    return sorted(files)

def read_raw_file(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".csv":
            try:
                df = pd.read_csv(file_path, header=None, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, header=None, encoding="latin1")
        else:
            df = pd.read_excel(file_path, header=None)
        return df
    except Exception as e:
        print(f"[WARNING] Could not read {file_path.name}: {e}")
        return pd.DataFrame()

def extract_co_from_raw(df: pd.DataFrame, location_name: str, file_name: str) -> pd.DataFrame:
    """
    Expected raw structure:
    col 0 = Time
    col 1 = CO value
    col 3 = metric label ('AQ CO' or 'BDFI AQ CO')
    """
    if df.empty or df.shape[1] < 4:
        print(f"[WARNING] Skipped {file_name}: insufficient columns")
        return pd.DataFrame()

    # Validate that column 3 looks like CO label in at least first few rows
    label_values = df.iloc[:10, 3].astype(str).str.strip().str.lower()
    if not any(("aq co" in x and "co2" not in x) for x in label_values):
        print(f"[WARNING] Skipped {file_name}: column 3 does not look like CO label")
        return pd.DataFrame()

    out = pd.DataFrame({
        "Time": pd.to_datetime(df.iloc[:, 0], errors="coerce", dayfirst=True),
        location_name: pd.to_numeric(df.iloc[:, 1], errors="coerce")
    })

    out = out.dropna(subset=["Time"])
    out = out.sort_values("Time")

    return out

def load_location_data(location_name: str, folder_list: list[str]) -> pd.DataFrame:
    parts = []

    print(f"\n--- Processing: {location_name} ---")
    for folder in folder_list:
        files = list_files(folder)
        print(f"Folder: {folder}")
        print(f"Files found: {len(files)}")

        for f in files:
            raw = read_raw_file(f)
            part = extract_co_from_raw(raw, location_name, f.name)
            if not part.empty:
                parts.append(part)
                print(f"  Loaded: {f.name} ({len(part)} rows)")
            else:
                print(f"  Skipped: {f.name}")

    if not parts:
        print(f"[WARNING] No usable data found for {location_name}")
        return pd.DataFrame(columns=["Time", location_name])

    combined = pd.concat(parts, ignore_index=True)
    combined = combined.sort_values("Time")

    # Remove duplicate timestamps by keeping first non-null value
    combined = combined.groupby("Time", as_index=False)[location_name].first()

    print(f"Combined rows for {location_name}: {len(combined)}")
    return combined

# =====================================================
# MAIN
# =====================================================

location_dfs = []
for location_name, folder_list in folders.items():
    location_dfs.append(load_location_data(location_name, folder_list))

merged = None
for d in location_dfs:
    if merged is None:
        merged = d.copy()
    else:
        merged = merged.merge(d, on="Time", how="outer")

if merged is None:
    raise ValueError("No data could be merged.")

merged = merged.sort_values("Time").reset_index(drop=True)

output_file.parent.mkdir(parents=True, exist_ok=True)
merged.to_excel(output_file, index=False)

print("\n=== MERGE COMPLETE ===")
print(f"Rows: {len(merged)}")
print("Columns:", merged.columns.tolist())
print(f"Saved to:\n{output_file}")
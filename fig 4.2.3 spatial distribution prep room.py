# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 21:05:37 2026

@author: papkp
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import pandas as pd

# ==========================================
# LOAD OPC DATA
# ==========================================
opc_file = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 2.2 PREPROOM/Analysis/scaled_PM2.5_OPC + DRX.xlsx"
opc = pd.read_excel(opc_file)

print("OPC columns:")
print(opc.columns.tolist())

# ==========================================
# SENSOR LOCATIONS (metres, approximate)
# Based on Figure 4.2.1 / room layout
# ==========================================
sensor_coords = {
    "OPC1": (5.2, 4.5),
    "OPC2": (0.8, 3.2),
    "OPC4": (4.5, 0.5),
    "OPC5": (5.8, 0.5),
    "OPC6": (0.5, 0.3)
}

source = (3.8, 2.5)

# ==========================================
# EXTRACT REPRESENTATIVE PEAK VALUES
# Use mean of top 10 values for robustness
# ==========================================
peak_values = {}

for name in sensor_coords.keys():
    col = f"{name.lower()}_RollMean_PM2.5 (scaled)"

    # Special case because OPC6 column has two spaces before "(scaled)"
    if name == "OPC6":
        col = "opc6_RollMean_PM2.5  (scaled)"

    if col in opc.columns:
        vals = pd.to_numeric(opc[col], errors="coerce").dropna()
        if len(vals) > 0:
            peak_values[name] = vals.nlargest(10).mean()
        else:
            print(f"No usable data in column: {col}")
    else:
        print(f"Column not found: {col}")

print("\nRepresentative peak values:")
print(peak_values)

# ==========================================
# PREPARE DATA FOR INTERPOLATION
# ==========================================
points = np.array([sensor_coords[k] for k in peak_values.keys()])
values = np.array([peak_values[k] for k in peak_values.keys()])

# Create interpolation grid
grid_x, grid_y = np.mgrid[0:6.2:200j, 0:5.0:200j]

# Interpolate
grid_z = griddata(points, values, (grid_x, grid_y), method="cubic")

# ==========================================
# PLOT HEATMAP
# ==========================================
plt.figure(figsize=(8, 6))

contour = plt.contourf(grid_x, grid_y, grid_z, levels=20)
plt.colorbar(contour, label="PM2.5 concentration")

# Plot sensor locations
for name, (x, y) in sensor_coords.items():
    plt.scatter(x, y, color="black", s=40)
    plt.text(x + 0.08, y, name, fontsize=9)

# Plot aerosol source
plt.scatter(*source, color="red", marker="*", s=180)
plt.text(source[0] + 0.08, source[1], "Source", color="red", fontsize=9)

plt.xlabel("Room width (m)")
plt.ylabel("Room length (m)")
plt.xlim(0, 6.2)
plt.ylim(0, 5.0)

plt.tight_layout()
plt.savefig(
    r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/FIG 2.2 PREPROOM/Analysis/Figure_4_2_3_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()
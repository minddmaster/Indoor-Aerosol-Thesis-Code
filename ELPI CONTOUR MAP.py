# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 21:39:41 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

FILE = r"C:/Users/papkp/OneDrive - University of Bristol/Desktop/THESIS/Final thesis/Data Analysis for thesis/Charge state analysis/elpi day1.xlsx"
OUTPUT_DIR = os.path.dirname(FILE)

# Load data
df = pd.read_excel(FILE, skiprows=40, header=None)

# Time
time = pd.to_datetime(df.iloc[:, 0], errors='coerce')

# Extract numeric columns only
data = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')

# Drop empty columns
data = data.dropna(axis=1, how='all')

# Clean rows
mask = time.notna()
time = time[mask]
data = data[mask]

# Convert to numpy
Z = data.values.T  # shape: (stages, time)

n_stages = Z.shape[0]
n_time = Z.shape[1]

print(f"Stages: {n_stages}, Time points: {n_time}")

# Generate ELPI diameters dynamically (log-spaced)
diameters = np.logspace(np.log10(0.03), np.log10(10), n_stages)

# Time index
t = np.arange(n_time)

# Plot
plt.figure(figsize=(10,6))

# FIX: use shading='nearest'
plt.pcolormesh(t, diameters, Z, shading='nearest')

plt.yscale('log')
plt.colorbar(label='Particle concentration')

plt.xlabel('Time index')
plt.ylabel('Particle diameter (µm)')
plt.title('ELPI size distribution evolution')

plt.tight_layout()

out_path = os.path.join(OUTPUT_DIR, "Figure_ELPI_contour_fixed.png")
plt.savefig(out_path, dpi=300)
plt.show()

print("Saved:", out_path)
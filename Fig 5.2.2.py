# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 13:43:20 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Clean decay dataset
data = {
    "Time": ["14:10", "14:15", "14:20", "14:25"],
    "Conc": [11739, 7129, 5430, 4793]
}

df = pd.DataFrame(data)

# Time in minutes from start of decay
df["t_min"] = np.arange(len(df)) * 5

# Log transform
df["lnC"] = np.log(df["Conc"])

# Linear regression
coeff = np.polyfit(df["t_min"], df["lnC"], 1)
slope = coeff[0]
intercept = coeff[1]

# Decay constant and ACH
k = -slope
ACH = k * 60

# Predicted values
df["lnC_fit"] = intercept + slope * df["t_min"]

# R²
ss_res = np.sum((df["lnC"] - df["lnC_fit"]) ** 2)
ss_tot = np.sum((df["lnC"] - df["lnC"].mean()) ** 2)
r2 = 1 - (ss_res / ss_tot)

print(f"Decay constant k = {k:.4f} min⁻¹")
print(f"Estimated ACH = {ACH:.2f} h⁻¹")
print(f"R² = {r2:.3f}")

# Plot
plt.figure(figsize=(7, 5))
plt.scatter(df["t_min"], df["lnC"], s=60, label="Observed")
plt.plot(df["t_min"], df["lnC_fit"], linewidth=2, label="Linear fit")

plt.xlabel("Time since start of decay (min)", fontsize=12)
plt.ylabel("ln(Particle number concentration, # cm$^{-3}$)", fontsize=12)
plt.title("Figure 5.4. Log-transformed aerosol decay in the preparation room", fontsize=13)
plt.xticks(fontsize=11)
plt.yticks(fontsize=11)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(fontsize=10)

# Annotation box
textstr = (
    f"$k$ = {k:.3f} min$^{{-1}}$\n"
    f"ACH = {ACH:.2f} h$^{{-1}}$\n"
    f"$R^2$ = {r2:.3f}"
)
plt.text(
    0.98, 0.95, textstr,
    transform=plt.gca().transAxes,
    fontsize=10,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
)

plt.tight_layout()
plt.savefig("Figure_5_4_log_decay_curve_improved.png", dpi=300, bbox_inches="tight")
plt.show()
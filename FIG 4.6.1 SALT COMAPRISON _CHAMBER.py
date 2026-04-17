# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 01:30:15 2026

@author: papkp
"""

import numpy as np
import matplotlib.pyplot as plt

# Diameter bins
diam = np.array([21, 39, 71, 120, 202, 316, 483, 761, 1231, 1956, 3088, 6285])

# Replace with your actual mean ± SD values
data = {
    "H2O": {
        "mean": np.array([1000, 1500, 12000, 13000, 11000, 12000, 3000, 500, 0, 0, 0, 0]),
        "sd":   np.array([300, 400, 1200, 1300, 1100, 1200, 500, 100, 0, 0, 0, 0]),
    },
    "NaCl": {
        "mean": np.array([0, 0, 30000, 70000, 70000, 75000, 28000, 9000, 1000, 0, 0, 0]),
        "sd":   np.array([0, 0, 4000, 5000, 4500, 5000, 3000, 1200, 200, 0, 0, 0]),
    },
    "Ammonium Sulphate": {
        "mean": np.array([2000, 10000, 50000, 80000, 75000, 100000, 48000, 13000, 1500, 0, 0, 0]),
        "sd":   np.array([500, 1500, 6000, 7000, 6500, 8000, 4500, 1500, 300, 0, 0, 0]),
    },
    "Choline Chloride": {
        "mean": np.array([18000, 17000, 70000, 76000, 72000, 92000, 44000, 14000, 1200, 0, 0, 0]),
        "sd":   np.array([2000, 1800, 6500, 7000, 6500, 7500, 4000, 1400, 250, 0, 0, 0]),
    },
}

# Consistent colour scheme
colours = {
    "H2O": "#1f77b4",
    "NaCl": "#ff7f0e",
    "Ammonium Sulphate": "#2ca02c",
    "Choline Chloride": "#d62728",
}

plt.figure(figsize=(9,5))

# Plot in logical order
order = ["H2O", "NaCl", "Ammonium Sulphate", "Choline Chloride"]

for aerosol in order:
    vals = data[aerosol]
    plt.errorbar(
        diam,
        vals["mean"],
        yerr=vals["sd"],
        fmt='o-',
        linewidth=2,
        markersize=4,
        capsize=3,
        capthick=1,
        elinewidth=1,
        color=colours[aerosol],
        label=aerosol
    )

# Axis formatting
plt.xscale("log")
plt.xticks([21, 71, 202, 761, 3088])

plt.xlabel("Particle aerodynamic diameter (nm)", fontsize=12)
plt.ylabel(r"$dN/d\log D_p$ (# cm$^{-3}$)", fontsize=12)

plt.grid(True, which="both", linestyle="--", alpha=0.3)

plt.legend(frameon=False, loc="upper right")

plt.tight_layout()
plt.savefig("Figure_4_1_proxy_aerosols_FINAL.png", dpi=600)
plt.show()
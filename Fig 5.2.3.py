# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 13:44:52 2026

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
df["t_min"] = np.arange(len(df)) * 5

# Normalise by initial decay concentration
C0 = df["Conc"].iloc[0]
df["C_norm"] = df["Conc"] / C0

plt.figure(figsize=(7, 5))
plt.plot(df["t_min"], df["C_norm"], marker="o", linewidth=2)

plt.xlabel("Time since start of decay (min)", fontsize=12)
plt.ylabel("Normalised concentration, $C/C_0$", fontsize=12)
plt.title("Figure 5.5. Normalised aerosol decay in the preparation room", fontsize=13)
plt.xticks(fontsize=11)
plt.yticks(fontsize=11)
plt.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.savefig("Figure_5_5_normalised_decay_curve.png", dpi=300, bbox_inches="tight")
plt.show()
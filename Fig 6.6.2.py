# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 19:10:26 2026

@author: papkp
"""

# =========================================================
# FIGURE 6.6 – COMPARISON OF COOKING EMISSIONS
# Peak particle concentrations for different cooking methods
# =========================================================

import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------
# ENTER YOUR PEAK VALUES
# (from your analysis tables)
# ---------------------------------------------------------

data = {
    "Cooking Method": ["Bacon Frying", "Deep Frying", "Stir Frying"],
    
    "Kitchen Peak (cm^-3)": [
        1.3e5,   # bacon frying
        1.7e5,   # deep frying
        9.4e4    # stir fry
    ],
    
    "Bedroom Peak (cm^-3)": [
        4.1e4,
        5.2e4,
        2.8e4
    ]
}

df = pd.DataFrame(data)

# ---------------------------------------------------------
# PLOT
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(7,5))

x = range(len(df))

ax.bar(
    [i - 0.2 for i in x],
    df["Kitchen Peak (cm^-3)"],
    width=0.4,
    label="Kitchen",
)

ax.bar(
    [i + 0.2 for i in x],
    df["Bedroom Peak (cm^-3)"],
    width=0.4,
    label="Bedroom",
)

ax.set_yscale("log")

ax.set_xticks(x)
ax.set_xticklabels(df["Cooking Method"])

ax.set_ylabel("Peak particle concentration (cm$^{-3}$)")
ax.set_title("Figure 6.6 – Comparison of particle emissions from cooking methods")

ax.legend()
ax.grid(True, linestyle="--", alpha=0.4)
for i,v in enumerate(df["Kitchen Peak (cm^-3)"]):
    ax.text(i-0.2, v*1.05, f"{v:.1e}", ha='center')

for i,v in enumerate(df["Bedroom Peak (cm^-3)"]):
    ax.text(i+0.2, v*1.05, f"{v:.1e}", ha='center')

plt.tight_layout()
plt.show()
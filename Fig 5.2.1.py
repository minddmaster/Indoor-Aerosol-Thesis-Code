# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 13:41:45 2026

@author: papkp
"""

import pandas as pd
import matplotlib.pyplot as plt

# Example time series data
time = ["14:00","14:05","14:10","14:15","14:20","14:25"]
conc = [7837,11739,7129,5430,4793,5103]

df = pd.DataFrame({
    "time": time,
    "conc": conc
})

plt.figure(figsize=(8,5))

plt.plot(df["time"], df["conc"], marker="o", linewidth=2)

plt.xlabel("Time", fontsize=12)
plt.ylabel("Particle number concentration (# cm$^{-3}$)", fontsize=12)

plt.title(
"Figure 5.3. Time series of aerosol dispersion in the preparation room",
fontsize=13
)

plt.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.savefig("Figure_5_3_preparation_room_timeseries.png", dpi=300)
plt.show()
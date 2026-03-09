# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 14:46:05 2026

@author: papkp
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Example dataset (replace with your extracted CPC data)
data = {
    "Time": ["14:10","14:15","14:20","14:25","14:30","14:35","14:40"],
    "Conc": [11739,7129,5430,4793,2200,850,300]
}

df = pd.DataFrame(data)

# Convert time to minutes
df["t_min"] = np.arange(len(df)) * 5

# Split datasets
vent_off = df[df["t_min"] <= 15]   # 14:10–14:25
vent_on  = df[df["t_min"] >= 15]   # 14:25 onwards

def decay_fit(df_decay):
    df_decay = df_decay.copy()
    df_decay["lnC"] = np.log(df_decay["Conc"])
    
    coeff = np.polyfit(df_decay["t_min"], df_decay["lnC"],1)
    
    slope = coeff[0]
    intercept = coeff[1]
    
    k = -slope
    ACH = k * 60
    
    df_decay["ln_fit"] = intercept + slope * df_decay["t_min"]
    
    ss_res = np.sum((df_decay["lnC"]-df_decay["ln_fit"])**2)
    ss_tot = np.sum((df_decay["lnC"]-df_decay["lnC"].mean())**2)
    r2 = 1 - (ss_res/ss_tot)
    
    return df_decay,k,ACH,r2

# Fit decay curves
off_fit,k_off,ACH_off,r2_off = decay_fit(vent_off)
on_fit,k_on,ACH_on,r2_on = decay_fit(vent_on)

print("Ventilation OFF")
print("k =",round(k_off,4),"min^-1")
print("ACH =",round(ACH_off,2),"h^-1")
print("R2 =",round(r2_off,3))

print("\nVentilation ON")
print("k =",round(k_on,4),"min^-1")
print("ACH =",round(ACH_on,2),"h^-1")
print("R2 =",round(r2_on,3))

# Plot
plt.figure(figsize=(8,5))

plt.plot(vent_off["t_min"],vent_off["Conc"],
         marker="o",linewidth=2,label="Ventilation OFF")

plt.plot(vent_on["t_min"],vent_on["Conc"],
         marker="s",linewidth=2,label="Ventilation ON")

plt.xlabel("Time since decay start (min)",fontsize=12)
plt.ylabel("Particle number concentration (# cm$^{-3}$)",fontsize=12)
plt.title("Figure 5.5 Aerosol decay under different ventilation conditions",fontsize=13)

plt.grid(True,linestyle="--",alpha=0.5)
plt.legend()

plt.tight_layout()
plt.savefig("Figure_5_5_ventilation_comparison.png",dpi=300)

plt.show()
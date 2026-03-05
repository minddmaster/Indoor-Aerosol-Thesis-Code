Dispersion of Indoor Aerosols and Their Exposure Implications in Residential Environments
Overview

This repository contains the data processing and analysis scripts used in the PhD research project:

“Dispersion of Indoor Aerosols and Their Exposure Implications in Residential Environments.”

The research investigates the generation, dispersion, transport, and decay of indoor aerosol particles within residential environments. The study focuses on understanding how indoor emission sources, such as cooking activities and controlled aerosol generation, influence particle concentration levels and potential exposure in different indoor spaces.

Experimental measurements were conducted in a residential setting using multiple aerosol measurement instruments. The data analysis scripts provided in this repository were used to process raw instrument data and generate the figures and tables presented in the thesis.

Research Objectives

The analysis contained in this repository supports the following key objectives:

Characterising indoor aerosol particle size distributions generated from different emission sources.

Investigating the dispersion and transport of aerosols between rooms within residential buildings.

Evaluating the temporal evolution and decay of aerosol concentrations following emission events.

Comparing measurements obtained from different aerosol instruments.

Assessing exposure implications for occupants under varying indoor ventilation conditions.

Experimental Environment

Experiments were conducted in a residential property where aerosol sources were generated primarily in the kitchen, with measurements taken simultaneously in both the source room and a receptor room (master bedroom).

This experimental configuration allowed the investigation of:

Aerosol generation in indoor environments

Inter-room particle transport

Concentration attenuation between rooms

The influence of ventilation on particle decay

Instruments Used

The following aerosol measurement instruments were used during the experiments:

Scanning Mobility Particle Sizer (SMPS+C)
Measures particle number size distributions typically within the ultrafine particle range.

Condensation Particle Counter (CPC)
Measures total particle number concentration.

Electrical Low Pressure Impactor (ELPI)
Provides size-segregated particle number and mass concentrations based on aerodynamic diameter.

DustTrak DRX Aerosol Monitor
Measures particulate matter mass concentrations including PM₁, PM₂.₅ and PM₁₀.

Cambustion DMS500
Used for high-time-resolution particle size distribution measurements.

Repository Structure
Indoor-Aerosol-Dispersion-Thesis
│
├── data_processing
│   ├── smps_analysis.py
│   ├── elpi_analysis.py
│   └── cpc_time_series.py
│
├── figures
│   ├── figure_4_1_smps_elpi_comparison.py
│   └── figure_generation_scripts.py
│
├── sample_data
│   └── example_processed_data.csv
│
└── README.md
Example Figures Generated

Scripts in this repository were used to generate figures included in the thesis, such as:

Figure 4.1 – Comparison of SMPS mobility diameter distribution and ELPI aerodynamic diameter distribution during NaCl atomisation experiments.

These figures demonstrate differences between particle measurement principles and size definitions across aerosol instruments.

Software Requirements

The analysis scripts require Python 3.9 or later.

Required Python libraries include:

pandas

numpy

matplotlib

scipy

These packages can be installed using:

pip install pandas numpy matplotlib scipy
Data Analysis Workflow

The typical workflow used for aerosol data analysis in this study is as follows:

Import raw data files from aerosol instruments (Excel or CSV formats).

Perform data cleaning and organisation using Pandas.

Calculate particle concentration and size distribution metrics.

Generate time-series and size distribution plots using Matplotlib.

Export figures for inclusion in the thesis.

Reproducibility

This repository provides the scripts used to generate the results presented in the thesis. The repository supports transparent and reproducible research practices in indoor aerosol science.

Citation

If using code or analysis methods from this repository, please cite:

Perumal, P. K. (2026).
Dispersion of Indoor Aerosols and Their Exposure Implications in Residential Environments – Data Analysis Scripts.
GitHub Repository.

Contact

Prem Kumar Perumal
Centre for Doctoral Training in Aerosol Science
University of Bristol

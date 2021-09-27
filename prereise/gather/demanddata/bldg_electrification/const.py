import os

import numpy as np
import pandas as pd

state_list = [
    "AL",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]

classes = ["res", "com"]

# Years with temperature data
yr_temps_all = list(range(2008, 2018))
yr_temps_first, yr_temps_last = yr_temps_all[0], yr_temps_all[-1]

# COP and capacity ratio models based on:
# (a) 50th percentile NEEP CCHP database [midperfhp],
# (b) 90th percentile NEEP CCHP database [advperfhp],
# (c) future HP targets, average of residential and commercial targets [futurehp]
dir_path = os.path.dirname(os.path.abspath(__file__))
hp_param = pd.read_csv(os.path.join(dir_path, "data", "hp_parameters.csv"))
hp_param_dhw = pd.read_csv(os.path.join(dir_path, "data", "hp_parameters_dhw.csv"))
puma_data = pd.read_csv(
    os.path.join(dir_path, "data", "puma_data.csv"), index_col="puma"
)

# Reference temperatures for computations
temp_ref = {"res": 18.3, "com": 16.7}

# Unit conversions
conv_kw_to_mw = 1 / 1000  # Convert kW to MW
conv_mmbtu_to_kwh = 293.0711  # Convert MMBtu (million Btu) to kWh
conv_m2_to_ft2 = 1 / (0.3048 ** 2)  # Convert square meters to square feet
conv_ft2_to_bsf = 1 / (10 ** 9)  # Convert square feet to billion square feet

eff_htg_ff_base = 0.80  # Assumed efficiency of existing fossil fuel HTG
eff_dhw_ff_base = 0.58  # Assumed efficiency of existing fossil fuel DHW

dhw_res_mult = [
    0.049666,
    0.020822,
    0.043178,
    0.040899,
    0.042389,
    0.653633,
    1.779551,
    2.715222,
    2.237019,
    1.265490,
    0.902268,
    0.995814,
    1.076690,
    0.878641,
    0.895299,
    0.973195,
    1.002082,
    0.957677,
    1.230816,
    1.858849,
    1.783014,
    1.219244,
    0.897841,
    0.480701,
]

dhw_com_mult = [1] * 24  # placeholder in case we need a multiplier for commercial

# Cooking efficiency multipliers
cooking_multiplier = {
    ("com", "low"): 0.46,
    ("com", "high"): 0.4,
    ("res", "low"): 0.44,
    ("res", "high"): 0.26,
}

# Setting res hot water slope as 0.01x res hot water const
dhw_lin_scalar = 0.01

bounds_lower_res = [0, 0.00000959, 0.00000269]
bounds_upper_res = [np.inf, 0.00001827, 0.00000864]

# Setting com cooking const as 1.5x com hot water const
cook_c_scalar = 1.5

dhw_low_bound_com = 0.00000796
dhw_high_bound_com = 0.00001858

other_high_bound_com = 0.00000228

recs_date_1 = 2009
recs_date_2 = 2015

cbecs_date_1 = 2003
cbecs_date_2 = 2012

target_year = 2010

# Regions to differentiate fuel usage: NorthEast, MidWest, South, West. Defined by RECS/CBECS surveys
regions = {
    "northeast": ["CT", "MA", "ME", "NH", "NJ", "NY", "PA", "RI", "VT"],
    "midwest": ["IA", "IL", "IN", "KS", "MI", "MN", "MO", "ND", "NE", "OH", "SD", "WI"],
    "south": [
        "AL",
        "AR",
        "DC",
        "DE",
        "FL",
        "GA",
        "KY",
        "LA",
        "MD",
        "MS",
        "NC",
        "OK",
        "SC",
        "TN",
        "TX",
        "VA",
        "WV",
    ],
    "west": [
        "AK",
        "AZ",
        "CA",
        "CO",
        "HI",
        "ID",
        "MT",
        "NM",
        "NV",
        "OR",
        "UT",
        "WA",
        "WY",
    ],
}

fuel = ["natgas", "fok", "othergas", "elec"]

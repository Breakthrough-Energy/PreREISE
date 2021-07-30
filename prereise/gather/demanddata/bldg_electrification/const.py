import os

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

# Years with temperature data
yr_temps_all = list(range(2008, 2018))
yr_temps_first, yr_temps_last = yr_temps_all[0], yr_temps_all[-1]

# COP and capacity ratio models based on:
# (a) 50th percentile NEEP CCHP database [midperfhp],
# (b) 90th percentile NEEP CCHP database [advperfhp],
# (c) future HP targets, average of residential and commercial targets [futurehp]
dir_path = os.path.dirname(os.path.abspath(__file__))
hp_param = pd.read_csv(os.path.join(dir_path, "data", "hp_parameters.csv"))
puma_data = pd.read_csv(
    os.path.join(dir_path, "data", "puma_data.csv"),
    index_col="puma",
)

# Reference temperatures for computations
temp_ref_res = 18.3
temp_ref_com = 16.7

# Unit conversions
conv_kw_to_mw = 1 / 1000
conv_mmbtu_to_kwh = 293.0711

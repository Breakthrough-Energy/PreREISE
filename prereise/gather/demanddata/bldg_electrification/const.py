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

# COP and capacity ratio models based on:
# (a) 50th percentile NEEP CCHP database [midperfhp],
# (b) 90th percentile NEEP CCHP database [advperfhp],
# (c) future HP targets, average of residential and commercial targets [futurehp]
dir_path = os.path.dirname(os.path.abspath(__file__))
hp_param = pd.read_csv(os.path.join(dir_path, "data", "hp_parameters.csv"))
puma_data = pd.read_csv(os.path.join(dir_path, "data", "puma_data.csv"))

# Reference temperatures for computations
temp_ref_res = 18.3
temp_ref_com = 16.7

# Unit conversions
conv_mmbtu_to_kwh = 293.0711

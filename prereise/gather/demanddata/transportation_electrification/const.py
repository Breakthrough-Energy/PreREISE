model_year = 2040

ldv_location_allowed = {
    1: {1},  # home only
    2: set(range(1, 13)),  # home and go to work related
    4: {1, 21},  # home and school only
    5: {1, 11, 12, 21},  # home and work and school
    6: {10, 11, 12},  # only work
}

hdv_location_allowed = {
    1: {1},  # base only
}

why_to_list = [
    1,
    53,  # home related
    10,
    11,
    12,  # work related
    13,
    14,
    17,
    20,
    21,
    22,
    23,  # other
    24,
    30,
    40,
    41,
    42,
    50,
    51,
    52,
    54,
    55,
    60,
    61,
    62,
    63,
    64,
    65,
    80,
    81,
    82,
    83,
]

nhts_census_column_names = [
    "Household",
    "Vehicle ID",
    "Person ID",
    "Scaling Factor Applied",
    "Trip Number",
    "Date",
    "Day of Week",
    "If Weekend",
    "Trip start time (HHMM)",
    "Trip end time (HHMM)",
    "Travel Minutes",
    "Dwell time",
    "Miles traveled",
    "Vehicle miles traveled",
    "why from",
    "why to",
    "Vehicle type",
    "Household vehicle count",
    "Household size",
    "Trip type",
    "Start time (hour decimal)",
    "End time (hour decimal)",
    "Dwell time (hour decimal)",
    "Travel time (hour decimal)",
    "Vehicle speed (mi/hour)",
    "sample vehicle number",
    "total vehicle trips",
    "total vehicle miles traveled",
]

ldv_columns_transform = {
    "sample vehicle number": "vehicle_number",
    "why to": "why_to",
    "why from": "why_from",
    "trip number": "trip_number",
    "Miles traveled": "trip_miles",
    "total vehicle trips": "total_trips",
    "Dwell time (hour decimal)": "dwell_time",
    "End time (hour decimal)": "trip_end",
}

hdv_data_column_names = [
    "Vehicle Number",
    "Trip Number",
    "Home base end (1/0)",
    "Destination from",
    "Destination to",
    "Trip Distance",
    "Trip Start",
    "Trip End",
    "Dwell Time",
    "Trip Time",
    "Speed",
    "Total Vehicle Trips",
    "Total Vehicle Miles",
]

hdv_columns_transform = {
    "Vehicle Number": "vehicle_number",
    "Home base end (1/0)": "why_to",
    "Trip Number": "trip_number",
    "Trip Distance": "trip_miles",
    "Total Vehicle Trips": "total_trips",
    "Dwell Time": "dwell_time",
    "Trip End": "trip_end",
}

# from grid to battery efficiency
charging_efficiency = 0.9

safety_coefficient = 1

ER = 1

emfacvmt = 758118400

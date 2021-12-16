import pandas as pd

# Download CSV of NHTS 2017 from https://nhts.ornl.gov/


def load_data(census_division: int, filepath: str = "trippub.csv"):
    """Load the data at trippub.csv.

    :param int census_division: any of the 9 census regions defined by the US census bureau
    :param str filepath: filepath for the "trippub.csv" file in downloaded NHTS data
    :raises ValueError: if the census division is not between 1 and 9, inclusive.
    :return: (*pd.DataFrame*) -- the data loaded from trippub.csv.
    """
    if not (1 <= census_division <= 9):
        raise ValueError("census_region must be between 1 and 9 (inclusive).")

    nhts_census = pd.read_csv(filepath)

    df = pd.DataFrame(nhts_census)

    return df


def data_filtering(census_division):
    """Filter raw NHTS data to be used in mileage.py

    :param int census_division: any of the 9 census regions defined by the US census bureau
    :param str filepath: filepath for the "trippub.csv" file in downloaded NHTS data
    :return: (*pd.DataFrame*) -- filtered and sorted trip data
    """

    nhts_raw = load_data(census_division)

    # filter to be only vehicle trips (TRPTRANS values 1-6)
    nhts = nhts_raw[nhts_raw.TRPTRANS.isin(range(1, 7))]

    # filter out repeated trips (VMT = -1)
    nhts = nhts[nhts.VMT_MILE != -1]

    # get correct census division
    nhts = nhts[nhts.CENSUS_D == census_division]

    column_translations = {
        "HOUSEID": "Household",
        "VEHID": "Vehicle ID",
        "PERSONID": "Person ID",
        "WTTRDFIN": "Scaling Factor Applied",
        "TDTRPNUM": "Trip Number",
        "TDAYDATE": "Date",
        "TRAVDAY": "Day of Week",
        "TDWKND": "If Weekend",
        "STRTTIME": "Trip start time (HHMM)",
        "ENDTIME": "Trip end time (HHMM)",
        "TRVLCMIN": "Travel Minutes",
        "DWELTIME": "Dwell time",
        "TRPMILES": "Miles traveled",
        "VMT_MILE": "Vehicle miles traveled",
        "WHYFROM": "why from",
        "WHYTO": "why to",
        "TRPTRANS": "Vehicle type",
        "HHVEHCNT": "Household vehicle count",
        "HHSIZE": "Household size",
    }

    sorted_data = nhts[column_translations.keys()].rename(
        column_translations, axis="columns"
    )

    sorted_data = sorted_data.reindex(
        list(sorted_data.columns)
        + [
            "Start time (hour decimal)",
            "End time (hour decimal)",
            "Dwell time (hour decimal)",
            "Travel time (hour decimal)",
            "Vehicle speed (mi/hour)",
            "sample vehicle number",
            "total vehicle trips",
            "total vehicle miles traveled",
        ],
        axis="columns",
    )

    # columns that require calculations: 21-28
    sorted_data["Start time (hour decimal)"] = [
        row // 100 + row % 100 / 60 for row in sorted_data["Trip start time (HHMM)"]
    ]
    sorted_data["End time (hour decimal)"] = [
        row // 100 + row % 100 / 60 for row in sorted_data["Trip end time (HHMM)"]
    ]
    sorted_data["Travel time (hour decimal)"] = (
        sorted_data["End time (hour decimal)"]
        - sorted_data["Start time (hour decimal)"]
    )
    sorted_data["Vehicle speed (mi/hour)"] = (
        sorted_data["Vehicle miles traveled"]
        / sorted_data["Travel time (hour decimal)"]
    )

    i = 0
    l = len(sorted_data)
    curr_household = sorted_data.iloc[0, sorted_data.columns.get_loc("Household")]
    curr_vehicle_id = sorted_data.iloc[0, sorted_data.columns.get_loc("Vehicle ID")]
    sample_veh_num = 1
    total_trips = 0
    total_miles = 0

    while i < l:
        if (
            curr_vehicle_id
            == sorted_data.iloc[i, sorted_data.columns.get_loc("Vehicle ID")]
            and curr_household
            == sorted_data.iloc[i, sorted_data.columns.get_loc("Household")]
        ):

            total_trips += 1
            total_miles += sorted_data.iloc[
                i, sorted_data.columns.get_loc("Vehicle miles traveled")
            ]

            if total_trips > 1:
                sorted_data.iloc[
                    i - 1, sorted_data.columns.get_loc("Dwell time (hour decimal)")
                ] = (
                    sorted_data.iloc[
                        i, sorted_data.columns.get_loc("Start time (hour decimal)")
                    ]
                    - sorted_data.iloc[
                        i - 1, sorted_data.columns.get_loc("End time (hour decimal)")
                    ]
                )

            # if the last entry is == the prev few entries, this makes sure they get added in;
            # otherwise, it would break out of loop w/o adding
            if i == (l - 1):
                sorted_data.iloc[
                    i - total_trips + 1 :,
                    sorted_data.columns.get_loc("sample vehicle number"),
                ] = sample_veh_num
                sorted_data.iloc[
                    i - total_trips + 1 :,
                    sorted_data.columns.get_loc("total vehicle trips"),
                ] = total_trips
                sorted_data.iloc[
                    i - total_trips + 1 :,
                    sorted_data.columns.get_loc("total vehicle miles traveled"),
                ] = total_miles

                if total_trips == 1:
                    sorted_data.iloc[
                        i, sorted_data.columns.get_loc("Dwell time (hour decimal)")
                    ] = 24 - (
                        sorted_data.iloc[
                            i - 1,
                            sorted_data.columns.get_loc("Start time (hour decimal)"),
                        ]
                        - sorted_data.iloc[
                            i - 1,
                            sorted_data.columns.get_loc("End time (hour decimal)"),
                        ]
                    )
                else:
                    sorted_data.iloc[
                        i, sorted_data.columns.get_loc("Dwell time (hour decimal)")
                    ] = (
                        24
                        - sorted_data.iloc[
                            i - 1,
                            sorted_data.columns.get_loc("End time (hour decimal)"),
                        ]
                        + sorted_data.iloc[
                            i - total_trips - 1,
                            sorted_data.columns.get_loc("Start time (hour decimal)"),
                        ]
                    )

        else:
            sorted_data.iloc[
                i - total_trips : i,
                sorted_data.columns.get_loc("sample vehicle number"),
            ] = sample_veh_num
            sorted_data.iloc[
                i - total_trips : i, sorted_data.columns.get_loc("total vehicle trips")
            ] = total_trips
            sorted_data.iloc[
                i - total_trips : i,
                sorted_data.columns.get_loc("total vehicle miles traveled"),
            ] = total_miles

            sample_veh_num += 1

            if total_trips == 1:
                sorted_data.iloc[
                    i - 1, sorted_data.columns.get_loc("Dwell time (hour decimal)")
                ] = 24 - (
                    sorted_data.iloc[
                        i - 1, sorted_data.columns.get_loc("Start time (hour decimal)")
                    ]
                    - sorted_data.iloc[
                        i - 1, sorted_data.columns.get_loc("End time (hour decimal)")
                    ]
                )
            else:
                sorted_data.iloc[
                    i - 1, sorted_data.columns.get_loc("Dwell time (hour decimal)")
                ] = (
                    24
                    - sorted_data.iloc[
                        i - 1, sorted_data.columns.get_loc("End time (hour decimal)")
                    ]
                    + sorted_data.iloc[
                        i - total_trips - 1,
                        sorted_data.columns.get_loc("Start time (hour decimal)"),
                    ]
                )

            total_trips = 1
            total_miles = sorted_data.iloc[
                i, sorted_data.columns.get_loc("Vehicle miles traveled")
            ]

            curr_vehicle_id = sorted_data.iloc[
                i, sorted_data.columns.get_loc("Vehicle ID")
            ]
            curr_household = sorted_data.iloc[
                i, sorted_data.columns.get_loc("Household")
            ]

            # this makes sure the last entry gets included;
            # otherwise, it would break out of loop w/o adding
            if i == (l - 1):
                sorted_data.iloc[
                    i, sorted_data.columns.get_loc("total vehicle trips")
                ] = total_trips
                sorted_data.iloc[
                    i, sorted_data.columns.get_loc("total vehicle miles traveled")
                ] = total_miles
                sorted_data.iloc[
                    i, sorted_data.columns.get_loc("sample vehicle number")
                ] = sample_veh_num

                if total_trips == 1:
                    sorted_data.iloc[
                        i, sorted_data.columns.get_loc("Dwell time (hour decimal)")
                    ] = 24 - (
                        sorted_data.iloc[
                            i - 1,
                            sorted_data.columns.get_loc("Start time (hour decimal)"),
                        ]
                        - sorted_data.iloc[
                            i - 1,
                            sorted_data.columns.get_loc("End time (hour decimal)"),
                        ]
                    )
                else:
                    sorted_data.iloc[
                        i, sorted_data.columns.get_loc("Dwell time (hour decimal)")
                    ] = (
                        24
                        - sorted_data.iloc[
                            i - 1,
                            sorted_data.columns.get_loc("End time (hour decimal)"),
                        ]
                        + sorted_data.iloc[
                            i - total_trips - 1,
                            sorted_data.columns.get_loc("Start time (hour decimal)"),
                        ]
                    )

        i += 1

    return sorted_data

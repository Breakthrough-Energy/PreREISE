import pandas as pd

# Download CSV of NHTS 2017 from https://nhts.ornl.gov/


def calculate_dwell_time(data: pd.DataFrame):
    """Calculates the dwell time, how long a vehicle has been charging

    :param pandas.DataFrame data: the data to calculate the dwell time from
    :return: (*pandas.Series*) -- list of dwell times
    """
    dwells = (
        data["Start time (hour decimal)"].iloc[1:].values
        - data["End time (hour decimal)"].iloc[:-1]
    )
    dwells.loc[data.index[-1]] = (
        24
        - data["End time (hour decimal)"].iloc[-1]
        + data["Start time (hour decimal)"].iloc[0]
    )

    return dwells


def data_filtering(raw_nhts, census_division):
    """Filter raw NHTS data to be used in mileage.py

    :param pandas.DataFrame raw_nhts: raw NHTS dataframe
    :param int census_division: any of the 9 census regions defined by the US census bureau
    :return: (*pandas.DataFrame*) -- filtered and sorted trip data
    """

    # filter to be only vehicle trips (TRPTRANS values 1-6)
    # filter out repeated trips (VMT = -1)
    # get correct census division
    nhts = raw_nhts.loc[
        raw_nhts.TRPTRANS.isin(range(1, 7))
        & (raw_nhts.VMT_MILE != -1)
        & (raw_nhts.CENSUS_D == census_division)
    ]

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

    filtered_data = nhts[column_translations.keys()].rename(
        column_translations, axis="columns"
    )

    filtered_data = filtered_data.reindex(
        list(filtered_data.columns)
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
    filtered_data["Start time (hour decimal)"] = [
        row // 100 + row % 100 / 60 for row in filtered_data["Trip start time (HHMM)"]
    ]
    filtered_data["End time (hour decimal)"] = [
        row // 100 + row % 100 / 60 for row in filtered_data["Trip end time (HHMM)"]
    ]
    filtered_data["Travel time (hour decimal)"] = (
        filtered_data["End time (hour decimal)"]
        - filtered_data["Start time (hour decimal)"]
    )
    filtered_data["Vehicle speed (mi/hour)"] = (
        filtered_data["Vehicle miles traveled"]
        / filtered_data["Travel time (hour decimal)"]
    )

    grouping = filtered_data.groupby(["Household", "Vehicle ID"])
    filtered_data["sample vehicle number"] = grouping.ngroup() + 1
    filtered_data["total vehicle trips"] = grouping["Vehicle miles traveled"].transform(
        len
    )
    filtered_data["total vehicle miles traveled"] = grouping[
        "Vehicle miles traveled"
    ].transform(sum)

    # drop the 'household' and 'vehicle id' index
    filtered_data["Dwell time (hour decimal)"] = grouping.apply(
        calculate_dwell_time
    ).droplevel([0, 1])

    return filtered_data

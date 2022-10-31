import calendar
import os

import numpy as np
import pandas as pd
from scipy.io import loadmat

from prereise.gather.demanddata.transportation_electrification import const


def get_model_year_dti(model_year: int):
    """Creates a DatetimeIndex based on the input year of the model.

    :param int model_year: the input year of the model
    :return: (*pandas.DatetimeIndex model_year_dti*) -- a DatetimeIndex encompassing
        the model year.
    """
    return pd.date_range(
        start=f"{model_year}-01-01", end=f"{model_year}-12-31", freq="D"
    )


def get_input_day(model_year_dti: pd.DatetimeIndex):
    """Determine whether each day of the model year is a weekend (1) or weekday (2)

    :param pandas.DatetimeIndex model_year_dti: a DatetimeIndex encompassing the
        model year.
    :return: (*numpy.ndarray*) -- array of 1s and 2s indicating weekend/weekday
        designations for the model year.
    """
    return model_year_dti.dayofweek.isin(range(5)).astype(int) + 1


def get_data_day(data: pd.DataFrame):
    """Get weekday/weekend designation value from data.

    :param pandas.DataFrame data: the data to get day of week from.
    :return: (*numpy.array*) -- indicates weekend or weekday for every day.
    """
    return np.array(data["If Weekend"])


def get_kwhmi(model_year, veh_type, veh_range):
    """Get the fuel efficiency value based on the model year and vehicle type.

    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040, 2050.
    :param str veh_type: determine which category (MDV, HDV, or Transit) to produce
        a fuel efficiency value for.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :return: (*float*) -- fuel efficiency value from the Fuel_efficiencies.csv
    :raises ValueError: if ``veh_range`` is not 100, 200, or 300 and if ``veh_type``
        is not 'LDT', 'LDV', 'MDV', 'HDV', or 'Transit
    """
    allowable_vehicle_types = {"LDT", "LDV", "MDV", "HDV", "Transit"}
    allowable_ranges = {100, 200, 300}

    if veh_range not in allowable_ranges:
        raise ValueError(f"veh_range must be one of {allowable_ranges}")

    filepath = os.path.join(
        const.data_folder_path,
        "Fuel_Efficiencies.csv",
    )
    data = pd.read_csv(filepath, index_col="veh_type")

    if (veh_type.upper() == "LDV") or (veh_type.upper() == "LDT"):
        kwhmi = data.loc[f"{veh_type.upper()}_{veh_range}", str(model_year)]

    elif (veh_type.upper() == "MDV") or (veh_type.upper() == "HDV"):
        kwhmi = data.loc[f"{veh_type.upper()}", str(model_year)]

    elif veh_type == "Transit":
        kwhmi = data.loc[f"{veh_type}", str(model_year)]

    else:
        raise ValueError(f"veh_type must be one of {allowable_vehicle_types}")

    return kwhmi


def load_data(census_region: int, filepath: str = "nhts_census_updated.mat"):
    """Load the data at nhts_census.mat.

    :param int census_region: the census region to load data from.
    :param str filepath: the path to the matfile.
    :raises ValueError: if the census division is not between 1 and 9, inclusive.
    :return: (*pandas.DataFrame*) -- the data loaded from nths_census.mat, with column
        names added.
    """
    if not (1 <= census_region <= 9):
        raise ValueError("census_region must be between 1 and 9 (inclusive).")
    if filepath.endswith(".csv"):
        census_data = pd.read_csv(filepath)
    else:
        nhts_census = loadmat(filepath)
        raw_data = nhts_census[f"census_{census_region}_updated_dwell"]
        census_data = pd.DataFrame(raw_data, columns=const.nhts_census_column_names)

    census_data = census_data.rename(columns=const.ldv_columns_transform)

    return census_data


def load_hdv_data(
    veh_type,
    filepath,
):
    """Load the data at fdata_v10st.mat.

    :param str veh_type: vehicle type ("hhdv: and "mhdv") category for trips
    :param str filepath: the path to the matfile.
    :return: (*pandas.DataFrame*) -- the data loaded from fdata_v10st.mat, with column
        names added.
    """
    if filepath.endswith(".csv"):
        hdv_data = pd.read_csv(filepath)
    else:
        mat_data = loadmat(filepath)
        raw_data = mat_data[f"{veh_type}_data"]

        hdv_data = pd.DataFrame(raw_data, columns=const.hdv_data_column_names)

    hdv_data = hdv_data.rename(columns=const.hdv_columns_transform)

    return hdv_data


def load_urbanized_scaling_factor(
    model_year,
    veh_type,
    veh_range,
    urbanized_area,
    state,
    filepath="Regional_scaling_factors_UA_",
):
    """Load the scaling factor for urbanized areas based on model year and vehicle
    type for the inputted urbanized area and state.

    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040, 2050.
    :param str veh_type: determine which category (MDV, HDV, or Transit) to produce
        a fuel efficiency value for.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :param str urbanized_area: name of urbanized area or city.
    :param str state: the US state the inputted urbanized area is in.
    :param str filepath: the path to the csv.
    :return: (*int/float*) -- scaling factor value from the Regional_scaling_factors_UA_{model_year}.csv
    :raises ValueError: if ``veh_range`` is not 100, 200, or 300 and if ``veh_type``
        is not 'LDT', 'LDV', 'MDV', 'HDV', or 'Transit
    """
    allowable_vehicle_types = {"LDT", "LDV", "MDV", "HDV", "Transit"}
    allowable_ranges = {100, 200, 300}

    if veh_range not in allowable_ranges:
        raise ValueError(f"veh_range must be one of {allowable_ranges}")

    data = pd.read_csv(filepath + str(model_year) + ".csv", index_col=["UA", "State"])

    if veh_type.upper() == "LDV":
        bev_vmt = data.loc[
            (urbanized_area, state), f"{veh_type.upper()} Car - {veh_range} mi"
        ]

    elif veh_type.upper() == "LDT":
        bev_vmt = data.loc[(urbanized_area, state), f"LDV Truck - {veh_range} mi"]

    elif (veh_type.upper() == "MDV") or (veh_type.upper() == "HDV"):
        bev_vmt = data.loc[(urbanized_area, state), f"{veh_type.upper()} Truck"]

    elif veh_type == "Transit":
        bev_vmt = data.loc[(urbanized_area, state), f"{veh_type} Bus"]

    else:
        raise ValueError(f"veh_type must be one of {allowable_vehicle_types}")

    return bev_vmt


def load_rural_scaling_factor(
    model_year, veh_type, veh_range, state, filepath="Regional_scaling_factors_RA_"
):
    """Load the scaling factor for rural areas based on model year and vehicle
    type for the inputted state.

    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040, 2050.
    :param str veh_type: determine which category (MDV, HDV, or Transit) to produce
        a fuel efficiency value for.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :param str state: the US state the inputted urbanized area is in.
    :param str filepath: the path to the csv.
    :return: (*int/float*) -- scaling factor value from the Regional_scaling_factors_RA_{model_year}.csv
    :raises ValueError: if ``veh_range`` is not 100, 200, or 300 and if ``veh_type``
        is not 'LDT', 'LDV', 'MDV', 'HDV', or 'Transit
    """
    allowable_vehicle_types = {"LDT", "LDV", "MDV", "HDV", "Transit"}
    allowable_ranges = {100, 200, 300}

    if veh_range not in allowable_ranges:
        raise ValueError(f"veh_range must be one of {allowable_ranges}")

    data = pd.read_csv(filepath + str(model_year) + ".csv", index_col=["State"])

    if veh_type.upper() == "LDV":
        bev_vmt = data.loc[state.upper(), f"{veh_type.upper()} Car - {veh_range} mi"]

    elif veh_type.upper() == "LDT":
        bev_vmt = data.loc[state.upper(), f"LDV Truck - {veh_range} mi"]

    elif (veh_type.upper() == "MDV") or (veh_type.upper() == "HDV"):
        bev_vmt = data.loc[state.upper(), f"{veh_type.upper()} Truck"]

    elif veh_type == "Transit":
        bev_vmt = data.loc[state.upper(), f"{veh_type} Bus"]

    else:
        raise ValueError(f"veh_type must be one of {allowable_vehicle_types}")

    return bev_vmt


def remove_ldt(data: pd.DataFrame):
    """Remove light duty trucks (vehicle types 4-6) from data loaded from nths_census.mat.
    Keep light duty vehicles (vehicle types 1-3).

    :param pandas.DataFrame data: the data returned from :func:`load_data`.
    :return: (*pandas.DataFrame*) -- the data loaded from :func:`load_data` with all
        rows involving LDT removed.
    """
    return data.loc[data["Vehicle type"].isin(range(1, 4))].copy()


def remove_ldv(data: pd.DataFrame):
    """Remove light duty vehicles (vehicle types 1-3) from data loaded from nths_census.mat.
    Keep light duty trucks (vehicle types 4-6).

    :param pandas.DataFrame data: the data returned from :func:`load_data`.
    :return: (*pandas.DataFrame*) -- the data loaded from :func:`load_data` with all
        rows involving LDT removed.
    """
    return data.loc[data["Vehicle type"].isin(range(4, 7))].copy()


def update_if_weekend(data: pd.DataFrame):
    """Updates the "If Weekend" values depending on the "Day of Week" value.
    Fridays and Sundays overlap into the weekend or weekday due to the
    vehicle time window, 6AM - 5:59AM.

    :param pandas.DataFrame data: the data returned from :func:`remove_ldt` or
        :func:`remove_ldv`.
    :return: (*pandas.DataFrame*) -- the data loaded from :func:`remove_ldt` or
        :func:`remove_ldv`
        with updated "If Weekend" values.
    """
    # weekend in the case of 1 or 7
    data.loc[data["Day of Week"].isin({1, 7}), "If Weekend"] = 1

    # weekday in the case of 2-6 (inclusive)
    data.loc[data["Day of Week"].isin(range(2, 7)), "If Weekend"] = 2

    return data


def generate_daily_weighting(year, area_type="urban"):
    """Generate daily weighting factors based on vehicle-miles-travelled distributions.

    :param int/str year: year to generate weighting factors for.
    :param str area_type: Either 'urban' or 'rural'.
    :return: (*pandas.Series*) -- index is the day of the year, values are the fraction
        of the year's vehicle miles travelled are estimated to occur in that day.
    :raises ValueError: if ``area_type`` is neither 'urban' nor 'rural'.
    """
    allowable_area_types = {"urban", "rural"}
    if area_type not in allowable_area_types:
        raise ValueError(f"area_type must be one of {allowable_area_types}")
    data_dir = const.data_folder_path
    monthly_distribution = pd.read_csv(
        os.path.join(data_dir, "moves_monthly.csv"), index_col=0
    )
    weekday_distribution = pd.read_csv(
        os.path.join(data_dir, "moves_daily.csv"), index_col=0
    )
    weekday_distribution.loc["weekday"] /= 5  # normalize to each day within weekdays
    weekday_distribution.loc["weekend"] /= 2  # normalize to each day within weekends
    year_type = "leap_year" if calendar.isleap(int(year)) else "regular_year"
    index = get_model_year_dti(year)
    # Retrieve the appropriate day weighting value
    daily_values = index.to_series().map(
        lambda x: weekday_distribution.loc[
            "weekday" if x.dayofweek < 5 else "weekend", area_type
        ]
    )
    # Normalize each month so that it sums to 1, and multiply by each month's share
    daily_values *= daily_values.index.month.map(
        monthly_distribution[year_type]
        / monthly_distribution[year_type].sum()  # correct for independent rounding
        / daily_values.groupby(daily_values.index.month).sum()
    )
    return daily_values


def get_total_daily_vmt(data: pd.DataFrame, input_day, daily_values):
    """Calculates the total VMT and total vehicles for for each day of the model year,
    based on if the day is a weekend (1) or weekday (2).

    :param pandas.DataFrame data: the data returned from :func:`load_data`.
    :param numpy.ndarray input_day: day of the week for each day in the year derived
        from :func:`get_input_day`.
    :param pandas.Series daily_values: daily weight factors returned from
        :func:`generate_daily_weighting`.
    :return: (*np.array*) -- an array where each element is the daily VMT and total
        vehicles for that day.
    """
    weekend_vmt = data.loc[data["If Weekend"] == 1, "trip_miles"].sum()
    weekday_vmt = data.loc[data["If Weekend"] == 2, "trip_miles"].sum()

    annual_vmt = 0
    for i in range(len(input_day)):
        if input_day[i] == 1:
            annual_vmt += weekend_vmt
        elif input_day[i] == 2:
            annual_vmt += weekday_vmt

    daily_vmt_total = daily_values * annual_vmt

    return daily_vmt_total


def get_total_hdv_daily_vmt(data: pd.DataFrame, veh_range):
    """Calculates the total VMT and total vehicles for for each day of the model year,
    based on vehicle range.

    :param pandas.DataFrame data: the data returned from :func:`load_data`.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :return: (*np.array*) -- an array where each element is the daily VMT and total
        vehicles for that day.
    :raises ValueError: if ``veh_range`` is not 100, 200, or 300
    """
    allowable_ranges = {100, 200, 300}
    if veh_range not in allowable_ranges:
        raise ValueError(f"veh_range must be one of {allowable_ranges}")

    range_vmt = data["trip_miles"].copy()
    range_vmt[data["Total Vehicle Miles"] > veh_range] = 0
    daily_vmt_total = sum(range_vmt) * np.ones(365)

    return daily_vmt_total

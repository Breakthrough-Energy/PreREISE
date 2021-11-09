import numpy as np
import pandas as pd
from prereise.gather.demanddata.transportation_electrification import const
from scipy.io import loadmat
from typing import List

def get_model_year_dti(model_year: int):
    return pd.date_range(
        start=f"{model_year}-01-01", end=f"{model_year}-12-31", freq="D"
    )


def get_input_day(model_year_dti: pd.DatetimeIndex):
    """Determine whether each day of the model year is a weekend (1) or weekday (2)

    :param pd.DatetimeIndex model_year_dti: a DatetimeIndex encompassing the model year.
    :return: (*np.ndarray*) -- array of 1s and 2s indicating weekend/weekday designations for the model year.

    """
    return model_year_dti.dayofweek.isin(range(5)).astype(int) + 1


def get_input_month(model_year_dti: pd.DatetimeIndex):
    """Determine month of each day

    :param pd.DatetimeIndex model_year_dti: a DatetimeIndex encompassing the model year.
    :return: (*np.ndarray*) -- stores the month the day is in for each day of the year.
    """
    return model_year_dti.month


def get_data_month(data: pd.DataFrame):
    """Get month value from data.

    :param pd.DataFrame data: the data to get months from.
    :return: (*pd.Series*) -- list of months.
    """
    return data["Date"].dt.month


def get_data_day(data: pd.DataFrame):
    """Get weekday/weekend designation value from data.

    :param pd.DataFrame data: the data to get day of week from.
    :return: (*np.array*) -- indicates weekend or weekday for every day.
    """
    return np.array(data["If Weekend"])


def load_data(census_region: int, filepath: str = "nhts_census.mat"):
    """Load the data at nhts_census.mat.

    :param int census_region: the census region to load data from.
    :param str filepath: the path to the matfile.
    :raises ValueError: if the census division is not between 1 and 9, inclusive.
    :return: (*pd.DataFrame*) -- the data loaded from nths_census.mat, with column
        names added.
    """
    if not (1 <= census_region <= 9):
        raise ValueError("census_region must be between 1 and 9 (inclusive).")

    # Somehow load in the matfile
    nhts_census = loadmat(filepath)
    # Load the data for the desired region
    raw_data = nhts_census[f"census_{census_region}_sorted"]
    # Convert to data frame, adding column names
    df = pd.DataFrame(raw_data, columns=const.nhts_census_column_names)

    return df


def remove_ldt(data: pd.DataFrame):
    """Remove light duty trucks from data loaded from nths_census.mat.

    :param pd.DataFrame data: the data returned from :func:`load_data`.
    :return: (*pd.DataFrame*) -- the data loaded from :func:`load_data` with all rows
        involving LDT removed.
    """

    return data.loc[data["Vehicle type"] < 5].copy()


# ldt = light duty truck
# ldv = light duty vehicle
def total_daily_vmt(
    census_region: int,
    comm_type: int,
    locationstrategy: List[int],
    input_day: List[int],
):
    """load data and use the parameters to calculate total_daily_vmt.

    :param int census_region: the type of census
    :param int comm_type: the type of Commute
    :param list locationstrategy: strategy for each location
    :param list input_day: day of the week for each day in the year derived from
        first_func
    :return: (*np.array*) -- an array where each element is a year of entries for each vehicle
        type
    """
    # get the data
    data = remove_ldt(load_data(census_region))
    n = len(data)

    if comm_type == 1:
        # removes VMT for trips from work->home and home-> work
        # (not exactly correct due to chained trips involving work and home but no
        # way to remove the data)
        if all([i != 2 for i in locationstrategy]):
            locationstrategy = 2
            # putting this part in function means rest of code won't be able to see
            # change in locationstrategy value.
            # will have to use global or return locationstrategy and reassign
            print('"locationstrategy" changed to "Home and Work" for comm_type == 1')
        # isolates home->work trips
        trip_home_work = data.loc[data["why from"] == 1 and data["why to"] == 11]
        # isolates work->home trips
        trip_work_home = data.loc[data["why from"] == 11 and data["why to"] == 1]

        # set trips from work to home to 0 distance
        data.loc[trip_work_home.index, "Miles traveled"] = 0
        data.loc[trip_home_work.index, "Miles traveled"] = 0

    # pre-processing of vehicle trip data to determine weekday or weekend
    # weekend in the case of 1 or 7
    data.loc[data["Day of Week"].isin({1, 7}), "If Weekend"] = 1
    # weekday in the case of 2-6 (inclusive)
    data.loc[data["Day of Week"].isin(list(range(2, 7))), "If Weekend"] = 2

    data_day = get_data_day(data)
    daily_vmt_total = np.zeros(len(input_day))

    for day_iter in range(len(input_day)):
        for i in range(n):
            if data_day[i] == input_day[day_iter]:
                daily_vmt_total[day_iter][0] += data[i][12]
                daily_vmt_total[day_iter][1] += 1

    return daily_vmt_total

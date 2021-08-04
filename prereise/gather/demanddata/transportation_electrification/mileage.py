import numpy as np
import pandas as pd
from scipy.io import loadmat

from prereise.gather.demanddata.transportation_electrification import const


# can use PHEV and EV


def get_input_day(month_days: list[int], month_first_day: list[int]) -> np.ndarray:
    """Determine month of each day and day of week for any given day in the year.

    :param list month_days: a list of integers where each value in the list represents
        the number of days in that month (0 indexed).
    :param list month_first_day: a list of integers where each value in the list
        represents the day of the week of the first day of that month (0 indexed).
    :return: (*np.ndarray*) -- first list stores the day of the week for each day of
        the year, second list stores the month the day is in for each day of the year.

    """
    # initalize day counter
    day_count = 0

    # initialize
    input_day = np.zeros(365, int)

    # iterate over 12 months
    for i in range(len(month_days)):
        # initialize first day of each month for use in the next for loop
        k = month_first_day[i]

        # Iterate over the day of each month
        for j in range(month_days[i]):

            # if k < 6: weekday, if k >= 6: weekend
            if k < 6:
                input_day[day_count] = 2
            elif k >= 6:
                input_day[day_count] = 1

            # restarts the week counter independent of the intial day
            if k == 7:
                k = 1
            else:
                k += 1

            # increment day counter
            day_count += 1

    return input_day


def get_input_month(month_days: list[int], month_first_day: list[int]) -> np.ndarray:
    """Determine month of each day

    :param list month_days: a list of integers where each value in the list represents
        the number of days in that month (0 indexed).
    :param list month_first_day: a list of integers where each value in the list
        represents the day of the week of the first day of that month (0 indexed).
    :return: (*np.ndarray*) -- stores the month the day is in for each day of the year.
    """
    # initalize day counter
    day_count = 0

    # initialize integers because all zeros
    input_month = np.zeros(365, int)

    # iterate over 12 months
    for i in range(len(month_days)):
        # Iterate over the day of each month
        for j in range(month_days[i]):
            # Populate input_month with month of each day ex: input_month[100] gives us month number of day 101
            input_month[day_count] = i

            # increment day counter
            day_count += 1

    return input_month


def get_month2(data: np.array(list[float or int])) -> np.array(int):
    """Get month2 value from data.

    :param np.array data: the data to get months from.
    :return: (*np.array*) -- list of months.
    """
    return np.array([x[5] % 100 for x in data], int)


def get_dayofweek2(data: np.array(list[float or int])) -> np.array(int):
    """Get dayofweek2 value from data.

    :param np.array data: the data to get day of week from.
    :return: (*np.array*) -- the day of the week for each entry in data.
    """
    return np.array([x[6] for x in data], int)


def get_day2(data: np.array(list[float or int])) -> np.array(int):
    """Get day2 value from data.

    :param np.array data: the data to get day of week from.
    :return: (*np.array*) -- indicates weekend or weekday for every day.
    """
    return np.array([x[7] for x in data])


def load_data(census_region: int, filepath: str = "nhts_census.mat") -> pd.DataFrame:
    """Load the data at nhts_census.mat.

    :param int census_region: the census region to load data from.
    :param str filepath: the path to the matfile.
    :raises ValueError: if the census division is not between 1 and 9, inclusive.
    :return: (*pandas.DataFrame*) -- the data loaded from nths_census.mat, with column
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


def remove_ldt(data: pd.DataFrame) -> pd.DataFrame:
    """Remove light duty trucks from data loaded from nths_census.mat.

    :param pandas.DataFrame data: the data returned from load_data.
    :return: (*pandas.DataFrame*) -- the data loaded from load_data with all rows
        involving LDT removed.
    """

    return data.loc[data["Vehicle type"] < 5].copy()


# ldt = light duty truck
# ldv = light duty vehicle
def total_daily_vmt(
    census_region: int,
    comm_type: int,
    locationstrategy: list[int],
    input_day: list[int],
) -> np.array[list[float]]:
    """load data and use the parameters to calculate total_daily_vmt.

    :param int census_region: the type of census
    :param int comm_type: the type of Commute
    :param list locationstrategy: strategy for each location
    :param list input_day: day of the week for each day in the year derived from
        first_func
    :return: (*list*) -- daily_vmt_total each row is a year of entries for each vehicle
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

    day2 = get_day2(data)
    daily_vmt_total = np.zeros(365)

    for day_iter in range(365):
        for i in range(n):
            if day2[i] == input_day[day_iter]:
                daily_vmt_total[day_iter][0] += data[i][12]
                daily_vmt_total[day_iter][1] += 1

    return daily_vmt_total

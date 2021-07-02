# up to line 117 done
import numpy as np
from scipy.io import loadmat

kate = 1
battery_size_list = []

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


def load_data(census_1: int) -> list[list[float or int]]:
    """Load the data at nhts_census.mat

    :param int census_1: the type of census.
    :return: (*list*) -- the data loaded from nths_census.mat.
    """
    # somehow load in 'nhts_census.mat'
    nhts_census = loadmat("nhts_census.mat")

    # census_1 will be 1-9 incluse, so i in range(1,10)
    for i in range(1, 10):
        # return the proper one
        if census_1 == i:
            return nhts_census[f"census_{i}_sorted"]


def remove_ldt(newdata: list[list[float or int]]) -> list[list[float or int]]:
    """Remove light duty trucks from data loaded from nths_census.mat.

    :param list newdata: the data returned from load_data.
    :return: (*list*) -- the data loaded from load_data with lal rows involving LDT
        removed.
    """
    # keep track of which rows to delete
    rows_to_delete = set()
    for vtype in range(len(newdata)):
        # >4 for LDV, <5 for LDT
        if newdata[vtype][16] < 5:
            rows_to_delete.add(vtype)

    # create a new list for all the data values that don't include the rows we want to remove
    data = []
    for i in range(len(newdata)):
        if i not in rows_to_delete:
            data.append(newdata[i])

    return data


# ldt = light duty truck
# ldv = light duty vehicle
def total_daily_vmt(
    census_1: int, comm_type: int, locationstrategy: list[int], input_day: list[int]
) -> np.array[list[float]]:
    """load data and use the parameters to calculate total_daily_vmt.

    :param int census_1: the type of census
    :param int comm_type: the type of Commute
    :param list locationstrategy: strategy for each location
    :param list input_day: day of the week for each day in the year derived from
        first_func
    :return: (*list*) -- daily_vmt_total each row is a year of entries for each vehicle
        type
    """
    # get the data
    data = np.array(remove_ldt(load_data(census_1)))
    n = len(data)
    # removes VMT for trips from work->home and home-> work
    # (not exactly correct due to chained trips involving work and home but no
    # way to remove the data)
    if comm_type == 1:
        if all([i != 2 for i in locationstrategy]):
            locationstrategy = 2  # putting this part in function means rest of code won't be able to see change in locationstrategy value
            # will have to use global or return locationstrategy and reassign
            print('"locationstrategy" changed to "Home and Work" for comm_type == 1')
        # isolates home->work trips
        trip_home_work = [
            i for i in range(len(data)) if (data[i][14] == 1 + data[i][15] == 11) == 2
        ]
        # isolates work->home trips
        trip_work_home = [
            i for i in range(len(data)) if (data[i][14] == 11 + data[i][15] == 1) == 2
        ]

        # set trips from work to home and vice versa to 0 in column 12 (0 indexed, 13 1 indexed)
        for trip in trip_home_work:
            data[trip][12] = 0

        for trip in trip_work_home:
            data[trip][12] = 0

    # pre-processing of vehicle trip data to determine VMT and trips per day to speed up later operation
    for its in range(len(data)):  # kef
        # weekend in the case of 1 or 7
        if data[its][6] == 1 or data[its][6] == 7:
            data[its][7] = 1
        # weekday in the case of 2-6 (inclusive)
        elif 2 <= data[its][6] and data[its][6] <= 6:
            data[its][7] = 2

    day2 = get_day2(data)
    daily_vmt_total = np.array([[0, 0] for i in range(365)])

    for day_iter in range(365):
        for i in range(n):
            if day2[i] == input_day[day_iter]:
                daily_vmt_total[day_iter][0] += data[i][12]
                daily_vmt_total[day_iter][1] += 1

    return daily_vmt_total

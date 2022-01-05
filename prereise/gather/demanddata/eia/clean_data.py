import numpy as np
import pandas as pd


def fix_dataframe_outliers(demand):
    """Make a data frame of demand with outliers replaced with values interpolated
    from the non-outlier edge points using :py:func:`slope_interpolate`.

    :param pandas.Dataframe demand: demand data frame with UTC timestamp as indicss
        and BA name as column name.
    :return: (*pandas.DataFrame*) -- data frame with anomalous demand values replaced
        by interpolated values.
    """
    demand_fix_outliers = pd.DataFrame(index=demand.index)
    for ba in demand.columns.to_list():
        demand_ba = demand[ba]
        outlier_output = slope_interpolate(pd.DataFrame(demand_ba))
        demand_fix_outliers[ba] = outlier_output[ba]
    return demand_fix_outliers


def slope_interpolate(ba_df):
    """Look for demand outliers by applying a z-score threshold to the demand slope.
    Loop through all the outliers detected, determine the non-outlier edge points and
    then interpolate a line joining these 2 edge points. The line value at the
    timestamp of the the outlier event is used to replace the anomalous value.

    :param pandas.DataFrame ba_df: demand data frame with UTC timestamp as indices and
        BA name as column name.
    :return: (*pandas.DataFrame*) -- data frame indexed with anomalous demand values
        replaced by interpolated values.

    .. note::
        It is implicitly assumed that:

        1. demand is correlated with temperature, and temperature rise is limited by
        heat capacity which is finite and generally uniform across region; hence,
        temperature dependent derivative spikes are unphysical.

        2. there is indeed nothing anomalous that happened to electrical usage in the
        relevant time range, so using a line to estimate the correct value is
        reasonable.


    .. todo::
        If there are more than a few hours (say > 4) of anomalous behavior, linear
        interpolation may give a bad estimate. Non-linear interpolation methods
        should be considered, and other information may be needed to interpolate
        properly, for example, the temperature data or other relevant profiles.
    """
    df = ba_df.copy()
    ba_name = df.columns[0]

    df["delta"] = df[ba_name].diff()
    delta_mu = df["delta"].describe().loc["mean"]
    delta_sigma = df["delta"].describe().loc["std"]
    df["delta_zscore"] = np.abs((df["delta"] - delta_mu) / delta_sigma)

    # Find the outliers
    outlier_index_list = df.loc[df["delta_zscore"] > 5].index

    hour_save = -1
    for i in outlier_index_list:
        hour_index = df.index.get_loc(i)
        if hour_save == -1:
            hour_save = hour_index
            next_save = hour_index + 1
            continue
        if hour_index == next_save:
            next_save = hour_index + 1
            continue

        # Check for zeros: consecutive zeros, which don't have delta_zscore
        # exceed threshold, will get extrapolated to the next non-zero value.
        # This is fine for, say up to 5 hours; will not be appropriate
        # otherwise since it may not capture the periodic patterns.
        # Print a warning

        if df.iloc[hour_index - 1][ba_name] == 0:
            next_save = hour_index + 1
            continue

        num = next_save - hour_save

        if num > 4:
            print("Too many zeros near ", i, "! Review data!")

        start = df.iloc[hour_save - 1][ba_name]
        dee = (df.iloc[next_save - 1][ba_name] - start) / num
        for j in range(hour_save - 1, next_save):
            save_me = df.iloc[j][ba_name]
            df.iloc[j][ba_name] = start + (j - hour_save + 1) * dee
            print(j, save_me, df.iloc[j][ba_name])
        hour_save = hour_index
        next_save = hour_index + 1

    if hour_save != -1:
        num = next_save - hour_save
        start = df.iloc[hour_save - 1][ba_name]
        dee = (df.iloc[next_save - 1][ba_name] - start) / num
        for j in range(hour_save - 1, next_save):
            save_me = df.iloc[j][ba_name]
            df.iloc[j][ba_name] = start + (j - hour_save + 1) * dee
            print(j, save_me, df.iloc[j][ba_name])

    return df


def replace_with_shifted_demand(demand, start, end):
    """Replace missing data within overall demand data frame with averages of nearby
    shifted demand.

    :param pandas.DataFrame demand: data frame with hourly demand where the columns are
        BA regions.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime start: start of period
        of interest.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime end: end of period
        of interest.
    :return: (*pandas.DataFrame*) -- data frame with missing demand data filled in.
    """

    # Create a data frame where each column is the same demand data,
    # but shifted by a specific time interval
    look_back1day = demand.shift(1, freq="D")
    look_back2day = demand.shift(2, freq="D")
    look_back1week = demand.shift(7, freq="D")
    look_forward1day = demand.shift(-1, freq="D")
    look_forward2day = demand.shift(-2, freq="D")
    look_forward1week = demand.shift(-7, freq="D")

    shifted_demand = pd.concat(
        [
            demand,
            look_back1day,
            look_forward1day,
            look_back2day,
            look_forward2day,
            look_back1week,
            look_forward1week,
        ],
        axis=1,
    )

    # Include only the dates we care about
    shifted_demand = shifted_demand.loc[start:end]
    shifted_demand["dayofweek"] = shifted_demand.index.dayofweek
    column_names = [
        "look_back1day",
        "look_forward1day",
        "look_back2day",
        "look_forward2day",
        "look_back1week",
        "look_forward1week",
        "dayofweek",
    ]

    # Dicts of weekdays. 0 = Monday, 1 = Tuesday, etc.
    # day_map: attempt to shift the data by only one day if possible
    # Do not fill in Mon-Fri with the weekend days and vice versa
    day_map = {
        0: ["look_forward1day"],
        1: ["look_forward1day", "look_back1day"],
        2: ["look_forward1day", "look_back1day"],
        3: ["look_forward1day", "look_back1day"],
        4: ["look_back1day"],
        5: ["look_forward1day"],
        6: ["look_back1day"],
    }

    # If we are still missing data, look two days
    more_days_map = {
        0: ["look_forward2day"],
        1: ["look_forward2day"],
        2: ["look_back2day", "look_forward2day"],
        3: ["look_back2day"],
        4: ["look_back2day"],
        5: ["look_back1week", "look_forward1week"],
        6: ["look_back1week", "look_forward1week"],
    }

    # Finally, check for data exactly one week ago / one week from date
    more_more_days_map = {
        0: ["look_back1week", "look_forward1week"],
        1: ["look_back1week", "look_forward1week"],
        2: ["look_back1week", "look_forward1week"],
        3: ["look_back1week", "look_forward1week"],
        4: ["look_back1week", "look_forward1week"],
        5: ["look_back1week", "look_forward1week"],
        6: ["look_back1week", "look_forward1week"],
    }

    # Attempt to shift demand data,
    # getting progressively more aggressive if necessary
    filled_demand = pd.DataFrame(index=demand.index)
    for ba_name in demand.columns:
        shifted_demand_ba = shifted_demand.loc[:, [ba_name, "dayofweek"]]
        shifted_demand_ba.columns = [ba_name] + column_names
        shifted_demand_ba[ba_name] = fill_ba_demand(shifted_demand_ba, ba_name, day_map)
        shifted_demand_ba[ba_name] = fill_ba_demand(
            shifted_demand_ba, ba_name, more_days_map
        )
        filled_demand[ba_name] = fill_ba_demand(
            shifted_demand_ba, ba_name, more_more_days_map
        )
    return filled_demand


def fill_ba_demand(df_ba, ba_name, day_map):
    """Replace missing data in BA demand and returns result.

    :param pandas.DataFrame df_ba: data frame for BA demand, shifted demand, and day
        of the week
    :param str ba_name: name of the BA in data frame.
    :param dict day_map: mapping for replacing missing demand data with shifted demand.
    :return: (*pandas.Series*) --  series of BA demand filled in
    """
    for day in range(0, 7):
        df_ba.loc[(df_ba.dayofweek == day) & (df_ba[ba_name].isna()), ba_name] = df_ba[
            day_map[day]
        ].mean(axis=1)
    return df_ba[ba_name]

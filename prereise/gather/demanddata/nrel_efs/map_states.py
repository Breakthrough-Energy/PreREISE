from collections import defaultdict

import pandas as pd
from powersimdata.input.grid import Grid
from powersimdata.network.usa_tamu.constants.zones import (
    abv2state,
    id2abv,
    id2timezone,
)


def decompose_demand_profile_by_state_to_loadzone(df, save=None):
    """Transforms the sectoral demand data so that it is separated by load zone rather
    than by state.

    :param pandas.DataFrame df: DataFrame of the sectoral demand data, where the rows
        are time steps (in local time) and the columns are the states. This input is
        intended to be the output of :py:func:`combine_efs_demand` or the components
        that are output from :py:func:`partition_flexibility_by_sector`.
    :param str save: Saves a .csv if a str representing a valid file path and file
        name is provided. Defaults to None, indicating that a .csv file should not be
        saved.
    :return: (*pandas.DataFrame*) -- Sectoral demand, split by load zone ID.
    :raises TypeError: if df is not a pandas.DataFrame or if save is not input as a str.
    :raises ValueError: if df does not have the proper time stamps or the correct number
        of states.
    """

    # Check that a DataFrame is input
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be input as a pandas.DataFrame.")

    # Check the demand DataFrame time stamps and column headers
    if not df.index.equals(
        pd.date_range("2016-01-01", "2017-01-01", freq="H", closed="left")
    ):
        raise ValueError("This data does not have the proper time stamps.")
    if set(df.columns) != set(abv2state) - {"AK", "HI"}:
        raise ValueError("This data does not include all 48 states.")

    # Grab the grid information
    grid = Grid(["USA"])

    # Find Pd for each load zone and determine the fraction of Pd per load zone by state
    pd_by_lz = grid.bus.groupby("zone_id")["Pd"].sum()
    pd_state_total = defaultdict(float)
    for i, s in id2abv.items():
        pd_state_total[s] += pd_by_lz[i]
    pd_frac = {i: pd_by_lz[i] / pd_state_total[id2abv[i]] for i in id2abv}

    # Split states into load zones
    df_lz = pd.DataFrame(index=df.index, columns=list(id2abv))
    for i in df_lz.columns:
        df_lz[i] = df[id2abv[i]] * pd_frac[i]

    # Convert from local hours to UTC time
    df_lz = shift_local_time_by_loadzone_to_utc(df_lz)

    # Save the demand data, if desired
    if save is not None:
        if not isinstance(save, str):
            raise TypeError("The file path and file name must be input as a str.")
        else:
            df_lz.to_csv(save)

    # Return the demand that is separated by load zone ID
    return df_lz


def shift_local_time_by_loadzone_to_utc(df):
    """Maps the local time for each load zone to the corresponding UTC time.

    :param pandas.DataFrame df: DataFrame of the demand data, where the rows are time
        steps (in local time) and the columns are load zone IDs.
    :return: (*pandas.DataFrame*) -- Demand, shifted to account for UTC time.
    :raises TypeError: if df is not a pandas.DataFrame.
    :raises ValueError: if df does not have the proper time stamps or the correct number
        of states.
    """

    # Check that a DataFrame is input
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be input as a pandas.DataFrame.")

    # Check the demand DataFrame dimensions and headers
    if not df.index.equals(
        pd.date_range("2016-01-01", "2017-01-01", freq="H", closed="left")
    ):
        raise ValueError("This data does not have the proper time stamps.")
    if set(df.columns) != set(id2abv):
        raise ValueError("This data does not include all load zones.")

    # Shift values according to UTC time correction
    df_tz = df.copy()
    for i in df_tz.columns:
        tz_val = int(id2timezone[i][-1])
        df_tz[i] = df_tz[i].shift(tz_val)

        # Populate with data from December 30 (same day of week) that is the same time
        df_tz[i][0:tz_val] = df.iloc[(8736 - tz_val) : 8736][i].values

    # Rename index
    df_tz.index.name = "UTC Time"

    # Return the demand that has been shifted to meet UTC time
    return df_tz

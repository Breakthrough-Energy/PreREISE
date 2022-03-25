from collections import defaultdict

import pandas as pd
from powersimdata.input.grid import Grid
from powersimdata.network.usa_tamu.constants.zones import (
    abv2id,
    abv2state,
    id2abv,
    id2timezone,
    interconnect2id,
)


def decompose_demand_profile_by_state_to_loadzone(
    df, profile_type, regions=None, save=None
):
    """Transforms the sectoral demand data so that it is separated by load zone rather
    than by state.

    :param pandas.DataFrame df: DataFrame of the sectoral demand data, where the rows
        are time steps (in local time) and the columns are the states. This input is
        intended to be the output of :py:func:`combine_efs_demand` or the components
        that are output from :py:func:`partition_flexibility_by_sector`.
    :param str profile_type: A string that identifies the type of profile that is
        provided. Can be one of *'demand'* or *'demand_flexibility'*.
    :param iterable regions: The combination of interconnection names and state
        abbreviations that dictate the zone IDs to be included. Can choose any of:
        *'Eastern'*, *'Western'*, *'Texas'*, any state abbreviation in the contiguous
        United States, or *'All'*. Defaults to None.
    :param str save: Saves a .csv if a string representing a valid file path and file
        name is provided. Defaults to None, indicating that a .csv file should not be
        saved.
    :return: (*pandas.DataFrame*) -- Sectoral demand, split by load zone ID.
    :raises TypeError: if df is not a pandas.DataFrame, if profile_type is not a string,
        if regions is not an iterable, if the components of regions are not strings, or
        if save is not input as a string.
    :raises ValueError: if df does not have the proper timestamps or the correct number
        of states, if profile_type is not valid, or if the components of regions are
        not valid.
    """

    # Account for the immutable default parameter
    if regions is None:
        regions = {"All"}

    # Check the data types of the inputs
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be input as a pandas.DataFrame.")
    if not isinstance(profile_type, str):
        raise TypeError("profile_type must be input as a str.")
    if not isinstance(regions, (set, list)):
        raise TypeError(
            "Combination of interconnections and state abbreviations must be input as "
            + "a set or list."
        )

    # Check the demand DataFrame timestamps and column headers
    if not df.index.equals(
        pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left")
    ):
        raise ValueError("This data does not have the proper timestamps.")
    if set(df.columns) != set(abv2state) - {"AK", "HI"}:
        raise ValueError("This data does not include all 48 states.")

    # Check the value of profile_type
    if profile_type not in {"demand", "demand_flexibility"}:
        raise ValueError(f"{profile_type} is not a valid selection for profile_type.")

    # Check that the components of regions are str
    if not all(isinstance(x, str) for x in regions):
        raise TypeError(
            "Individual interconnections and state abbreviations must be input as a "
            + "str."
        )

    # Reformat components of regions
    regions = {x.upper() if len(x) == 2 else x.capitalize() for x in regions}
    if "All" in regions:
        regions = {"Eastern", "Western", "Texas"}

    # Check that the components of regions are valid
    possible_regions = ({"Eastern", "Western", "Texas"} | set(abv2state)) - {"AK", "HI"}
    if not regions.issubset(possible_regions):
        invalid_regions = regions - possible_regions
        raise ValueError(f'Invalid regions: {", ".join(invalid_regions)}')

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

    # Determine the loadzones to be inlcuded in the profile, as specified by regions
    loadzones = sorted(
        set().union(
            *[abv2id[r] if len(r) == 2 else interconnect2id[r] for r in regions]
        )
    )

    # Keep the appropriate loadzones
    df_lz = df_lz[loadzones]

    # Change the column headers if the profile_type is "demand_flexibility"
    if profile_type == "demand_flexibility":
        df_lz.columns = [f"zone.{x}" for x in loadzones]

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
    :raises ValueError: if df does not have the proper timestamps or the correct number
        of states.
    """

    # Check that a DataFrame is input
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be input as a pandas.DataFrame.")

    # Check the demand DataFrame dimensions and headers
    if not df.index.equals(
        pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left")
    ):
        raise ValueError("This data does not have the proper timestamps.")
    if set(df.columns) != set(id2abv):
        raise ValueError("This data does not include all load zones.")

    # Shift values according to UTC time correction
    df_tz = df.copy()
    for i in df_tz.columns:
        tz_val = int(id2timezone[i][-1])
        df_tz[i] = df_tz[i].shift(tz_val)

        # Populate with data from December 30 (same day of week) that is the same time
        df_tz.iloc[0:tz_val, df_tz.columns.get_loc(i)] = df.iloc[
            (8736 - tz_val) : 8736
        ][i].values

    # Rename index
    df_tz.index.name = "UTC Time"

    # Return the demand that has been shifted to meet UTC time
    return df_tz

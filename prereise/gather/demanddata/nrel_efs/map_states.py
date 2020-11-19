import re

import pandas as pd
from powersimdata.input.grid import Grid
from powersimdata.network.usa_tamu.constants.zones import (
    abv2state,
    id2abv,
    id2timezone,
)


def map_to_loadzone(agg_dem, save=None):
    """
    Transforms the aggregated sectoral demand data so that it is separated by load zone
    rather than by state.

    :param pandas.DataFrame agg_dem: DataFrame of the aggregated sectoral demand data,
        where the rows are time steps (in local time) and the columns are the states.
    :param str save: Saves a .csv if a str representing a valid file path and file
        name is provided. Defaults to None, indicating that a .csv file should not be
        saved.
    :return: (*pandas.DataFrame*) -- Aggregate sectoral demand, split by load zone ID.
    :raises TypeError: if agg_dem is not a pandas.DataFrame or if save is not input as
        a str.
    :raises ValueError: if agg_dem does not have the proper index, the correct number of
        time steps, or the correct number of states.
    """

    # Check that a DataFrame is input
    if not isinstance(agg_dem, pd.DataFrame):
        raise TypeError("agg_dem must be input as a pandas.DataFrame.")

    # Check the aggregate demand DataFrame dimensions and headers
    if agg_dem.index.name != "Local Time":
        raise ValueError("This data does not have the proper index.")
    if len(agg_dem) != 8784:
        raise ValueError("This data does not have the proper number of time steps.")
    if set(agg_dem.columns.values) != set(abv2state) - {"AK", "HI"}:
        raise ValueError("This data does not include all 48 states.")

    # Grab the grid information
    grid = Grid(["USA"])

    # Map the states to the load zone IDs
    abv2id = {
        k: {v for v in id2abv.keys() if id2abv[v] == k} for k in set(id2abv.values())
    }

    # Find Pd for each load zone and determine the fraction of Pd per load zone by state
    pd_by_lz_df = grid.bus[["Pd", "zone_id"]]
    pd_by_lz_df = pd_by_lz_df.groupby("zone_id").sum()
    pd_by_lz = {}
    pd_frac = {}
    for x in abv2id:
        pd_by_lz[x] = {y: pd_by_lz_df.loc[y]["Pd"] for y in abv2id[x]}
        pd_tot = sum({pd_by_lz[x][y] for y in pd_by_lz[x]})
        pd_frac[x] = {y: pd_by_lz[x][y] / pd_tot for y in pd_by_lz[x]}

    # Split states into load zones
    agg_dem_lz = pd.DataFrame(index=agg_dem.index, columns=list(str(x) for x in id2abv))
    for x in id2abv:
        agg_dem_lz[str(x)] = agg_dem[id2abv[x]] * pd_frac[id2abv[x]][x]

    # Convert from local hours to UTC time
    agg_dem_lz = map_to_utc(agg_dem_lz)

    # Save the aggregated demand data, if desired
    if save is not None:
        if not isinstance(save, str):
            raise TypeError("The file path and file name must be input as a str.")
        else:
            agg_dem_lz.to_csv(save)

    # Return the aggregate sectoral demand that is separated by load zone ID
    return agg_dem_lz


def map_to_utc(agg_dem):
    """
    Maps the local times to the corresponding UTC times.

    :param pandas.DataFrame agg_dem: DataFrame of the aggregated demand data, where the
        rows are time steps (in local time) and the columns are load zone IDs.
    :return: (*pandas.DataFrame*) -- Aggregate demand, shifted to account for UTC time.
    :raises TypeError: if agg_dem is not a pandas.DataFrame.
    :raises ValueError: if agg_dem does not have the proper index, the correct number of
        time steps, or the correct number of states.
    """

    # Check that a DataFrame is input
    if not isinstance(agg_dem, pd.DataFrame):
        raise TypeError("agg_dem must be input as a pandas.DataFrame.")

    # Check the aggregate demand DataFrame dimensions and headers
    if agg_dem.index.name != "Local Time":
        raise ValueError("This data does not have the proper index.")
    if len(agg_dem) != 8784:
        raise ValueError("This data does not have the proper number of time steps.")
    if set(agg_dem.columns.values) != set(str(x) for x in id2abv):
        raise ValueError("This data does not include all load zones.")

    # Shift values according to UTC time correction
    agg_dem_tz = agg_dem.copy()
    for i in set(agg_dem_tz.columns):
        tz_val = int(re.search(r"\d+", id2timezone[int(i)]).group())
        agg_dem_tz[i] = agg_dem_tz[i].shift(tz_val)

        # Populate with data from December 30 (same day of week) that is the same time
        agg_dem_tz[i][0:tz_val] = agg_dem.iloc[(8736 - tz_val) : 8736][i].values

    # Rename index
    agg_dem_tz.index.name = "UTC Time"

    # Return the aggregate demand that has been shifted to meet UTC time
    return agg_dem_tz

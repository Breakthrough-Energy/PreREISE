import pandas as pd
from powersimdata.network.usa_tamu.constants.zones import abv2state

from prereise.gather.demanddata.nrel_efs.get_efs_data import (
    partition_by_sector,
)


def combine_efs_demand(es, ta, year, local_sects=None, local_paths=None, save=None):
    """Aggregate the sectoral demand data so that a single demand point is observed for
    each state and time stamp. This function can either access local copies of the
    sectoral demand data or can access the demand data from online.

    :param str es: An electrification scenario. Can choose one of: *'Reference'*,
        *'Medium'*, or *'High'*.
    :param str ta: A technology advancement. Can choose one of: *'Slow'*, *'Moderate'*,
        or *'Rapid'*.
    :param int year: The selected year's worth of demand data. Can choose one of: 2018,
        2020, 2024, 2030, 2040, or 2050.
    :param set/list local_sects: The sectors for which .csv files of demand data are
        already stored locally. Can choose any of: *'Transportation'*, *'Residential'*,
        *'Commercial'*, *'Industrial'*, or *'All'*. Defaults to None, indicating that
        all sectoral demand needs to be accessed from online.
    :param set/list local_paths: The paths that point to the .csv files of sectoral
        demand data. Ordering within the set/list does not need to match that in
        local_sects. Defaults to None.
    :param str save: Saves a .csv if a str representing a valid file path and file
        name is provided. Defaults to None, indicating that a .csv file should not be
        saved.
    :return: (*pandas.DataFrame*) -- Aggregate demand data for all sectors.
    :raises TypeError: if local_sects and local_paths are not input as a set or list, if
        save is not input as a str, if the components of local_sects and local_paths are
        not input as str, or if local_sects and local_paths are not of the same type.
    :raises ValueError: if the components of local_sects are not valid, if local_sects
        and local_paths do not have the same number of components, or if the
        locally-stored data does not have the proper time stamp labels, the correct
        number of time steps, or the correct number of states.
    """

    # Check that the inputs are of an appropriate type
    if not isinstance(local_sects, (set, list, type(None))):
        raise TypeError("Sectors with downloaded data must be input as a set or list.")
    if not isinstance(local_paths, (set, list, type(None))):
        raise TypeError("File paths of sectoral data must be input as a set or list.")

    # Check that the components of local_sects and local_paths are str
    if isinstance(local_sects, (set, list)):
        if not all(isinstance(x, str) for x in local_sects):
            raise TypeError("Individual sectors must be input as a str.")
    if isinstance(local_paths, (set, list)):
        if not all(isinstance(x, str) for x in local_paths):
            raise TypeError("Individual file paths must be input as a str.")

    # Reformat components of local_sects
    if local_sects is not None:
        local_sects = {x.capitalize() for x in local_sects}
        if "All" in local_sects:
            local_sects = {"Transportation", "Residential", "Commercial", "Industrial"}

        # Check that the components of local_sects are valid
        if not local_sects.issubset(
            {"Transportation", "Residential", "Commercial", "Industrial"}
        ):
            invalid_sect = local_sects - {
                "Transportation",
                "Residential",
                "Commercial",
                "Industrial",
            }
            raise ValueError(f'Invalid sectors: {", ".join(invalid_sect)}')

    # Check that local_sects and local_files are of the same type and length
    if None in [local_sects, local_paths]:
        if type(local_sects) != type(local_paths):
            raise TypeError("local_sects and local_paths must be of the same type.")
        else:
            local_sects = set()
            local_paths = set()
    else:
        if len(local_sects) != len(local_paths):
            raise ValueError("local_sects and local_paths must have the same length.")

    # Obtain the sectoral demand data
    agg_dem = 0
    for i in local_paths:
        # Try loading the sectoral demand that is stored locally
        temp_dem = pd.read_csv(i)

        # Access the column headers and set the index
        temp_cols = list(temp_dem.columns.values)
        if "Local Time" in temp_cols:
            temp_dem.set_index("Local Time", inplace=True)
            temp_cols.remove("Local Time")
        else:
            raise ValueError("This data does not include the necessary time stamps.")

        # Check the DataFrame dimensions and headers
        if len(temp_dem) != 8784:
            raise ValueError("This data does not have the proper number of time steps.")
        if set(temp_cols) != set(abv2state) - {"AK", "HI"}:
            raise ValueError("This data does not include all 48 states.")

        # Add the sectoral demand to the aggregate demand
        agg_dem += temp_dem

    # Acquire the sectoral demand that is not stored locally
    missing_sects = {
        "Transportation",
        "Residential",
        "Commercial",
        "Industrial",
    } - local_sects
    if len(missing_sects) > 0:
        temp_dem = partition_by_sector(es, ta, year, missing_sects, save=False)
        for i in missing_sects:
            agg_dem += temp_dem[i]

    # Save the aggregated demand data, if desired
    if save is not None:
        if not isinstance(save, str):
            raise TypeError("The file path and file name must be input as a str.")
        else:
            agg_dem.to_csv(save)

    # Return the aggregate demand for all sectors
    return agg_dem

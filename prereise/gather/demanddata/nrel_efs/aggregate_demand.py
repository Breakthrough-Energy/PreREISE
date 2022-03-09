import pandas as pd

from prereise.gather.const import abv2state


def combine_efs_demand(efs_dem=None, non_efs_dem=None, save=None):
    """Aggregate the sectoral demand data so that a single demand point is observed for
    each state and timestamp. This function can either access local copies of the
    sectoral demand data or can access the demand data from online.

    :param dict efs_dem: A dict of pandas.DataFrame objects that contain sectoral demand
        data for each state and time step. This input is intended to be the output of
        :py:func:`partition_demand_by_sector`, which is associated with NREL's EFS.
        Defaults to None.
    :param list non_efs_dem: A list of pandas.DataFrame objects that contain sectoral
        demand data for each state and time step. This input is intended to be the
        output of :py:func:`access_non_efs_demand`, which is not associated with NREL's
        EFS. Defaults to None.
    :param str save: Saves a .csv if a string representing a valid file path and file
        name is provided. Defaults to None, indicating that a .csv file should not be
        saved.
    :return: (*pandas.DataFrame*) -- Aggregate demand data for all sectors (both EFS and
        non-EFS).
    :raises TypeError: if efs_dem is not input as a dict, if non_efs_dem is not input as
        a list, if the components of efs_dem and non_efs_dem are not pandas.DataFrames,
        or if save is not input as a string.
    :raises ValueError: if both efs_dem and non_efs_dem are entered as None or if the
        components of efs_dem and non_efs_dem do not have the proper timestamps or the
        correct number of states.
    """

    # Check that both of the inputs are not input as None
    if all(x is None for x in [efs_dem, non_efs_dem]):
        raise ValueError(
            "No sectoral demand was provided, so there is nothing to aggregate."
        )

    # Check that the inputs are of an appropriate type
    if not isinstance(efs_dem, (dict, type(None))):
        raise TypeError("All EFS sectoral demand data must be input as a dict.")
    if not isinstance(non_efs_dem, (list, type(None))):
        raise TypeError("All non-EFS sectoral demand data must be input as a list.")

    # Check that the components of efs_dem and non_efs_dem are DataFrames
    if isinstance(efs_dem, dict):
        if not all(isinstance(efs_dem[i], pd.DataFrame) for i in efs_dem):
            raise TypeError(
                "EFS sectoral demand data must be input as a pandas.DataFrame."
            )
    if isinstance(non_efs_dem, list):
        if not all(isinstance(x, pd.DataFrame) for x in non_efs_dem):
            raise TypeError(
                "Non-EFS sectoral demand data must be input as a pandas.DataFrame."
            )

    # Initialize agg_dem
    agg_dem = pd.DataFrame(
        0,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
        columns=sorted(set(abv2state) - {"AK", "HI"}),
    )
    agg_dem.index.name = "Local Time"

    # Aggregate the EFS sectoral demand
    if efs_dem is not None:
        for i in efs_dem:
            # Check the DataFrame dimensions and headers
            if not efs_dem[i].index.equals(
                pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left")
            ):
                raise ValueError("This data does not have the proper timestamps.")
            if set(efs_dem[i].columns) != set(abv2state) - {"AK", "HI"}:
                raise ValueError("This data does not include all 48 states.")

            # Add the sectoral demand to the aggregate demand
            agg_dem += efs_dem[i]

    # Aggregate the non-EFS sectoral demand
    if non_efs_dem is not None:
        for x in non_efs_dem:
            # Check the DataFrame dimensions and headers
            if not x.index.equals(
                pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left")
            ):
                raise ValueError("This data does not have the proper timestamps.")
            if set(x.columns) != set(abv2state) - {"AK", "HI"}:
                raise ValueError("This data does not include all 48 states.")

            # Add the sectoral demand to the aggregate demand
            agg_dem += x

    # Save the aggregated demand data, if desired
    if save is not None:
        if not isinstance(save, str):
            raise TypeError("The file path and file name must be input as a str.")
        else:
            agg_dem.to_csv(save)

    # Return the aggregate demand for all sectors
    return agg_dem


def access_non_efs_demand(dem_paths):
    """Access any of the sectoral demand that the user intends to use that is external
    to NREL's EFS studies. This function also ensures that each data set is formatted
    appropriately, so as to allow easy aggregation with the NREL EFS sectoral demand.

    :param iterable dem_paths: The paths that point to the .csv files of sectoral demand
        data that is not associated with NREL's EFS. Ordering within the iterable does
        not need to match that in local_sects.
    :return: (*list*) -- A list of pandas.DataFrame objects that contain sectoral demand
        data for each state and time step. This sectoral demand is not a part of NREL's
        EFS.
    :raises TypeError: if dem_paths are not input as an iterable or if the components of
        dem_paths are not input as strings.
    :raises ValueError: if the data located in each path in dem_path does not have the
        proper timestamps or the correct number of states.
    """

    # Check that dem_paths is of an appropriate type
    if not isinstance(dem_paths, (set, list)):
        raise TypeError("File paths of sectoral data must be input as a set or list.")

    # Check that the components of dem_paths are str
    if not all(isinstance(x, str) for x in dem_paths):
        raise TypeError("Individual file paths must be input as a str.")

    # Obtain the sectoral demand data
    sect_dem = []
    for i in dem_paths:
        # Try loading the locally-stored sectoral demand
        try:
            temp_dem = pd.read_csv(i, parse_dates=True, index_col="Local Time")
        except ValueError:
            raise ValueError("This data does not provide the timestamps correctly.")

        # Check the DataFrame dimensions and headers
        if not temp_dem.index.equals(
            pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left")
        ):
            raise ValueError("This data does not have the proper timestamps.")
        if set(temp_dem.columns) != set(abv2state) - {"AK", "HI"}:
            raise ValueError("This data does not include all 48 states.")

        # Store the setoral demand data
        sect_dem.append(temp_dem)

    # Return the list of non-EFS sectoral demand
    return sect_dem

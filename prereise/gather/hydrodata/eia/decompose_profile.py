import pandas as pd
from powersimdata.input.grid import Grid
from powersimdata.network.usa_tamu.constants.zones import abv2interconnect, abv2loadzone


def get_profile_by_state(profile, state, grid=None):
    """Decompose total hydro profile into plant level profile based on hydro
    generator capacities in the query state.

    :param pandas.Series/list profile: profile in query state.
    :param str state: the query state.
    :param powersimdata.input.grid.Grid grid: Grid instance. Use the generator
        capacities in the given grid if provided, otherwise use the base grid.
    :return: (*pandas.DataFrame*) -- hydro profile for each plant
        in the query state.
    :raises TypeError: if profile is not a time-series and/or
        state is not a str.
    :raises ValueError: if state is invalid.
    """
    if not isinstance(profile, (pd.Series, list)):
        raise TypeError("profile must be a pandas.Series object or list")
    if not isinstance(state, str):
        raise TypeError("state must be a str")

    if state not in abv2loadzone.keys():
        raise ValueError(
            "Invalid state. Possible states are %s"
            % " | ".join(set(abv2loadzone.keys()))
        )
    if not grid:
        grid = Grid([abv2interconnect[state]])

    plant = grid.plant
    hydro_plant_in_state = plant[
        (plant.type == "hydro") & (plant["zone_name"].isin(abv2loadzone[state]))
    ]

    hydro_capacity_in_state = hydro_plant_in_state["Pmax"].sum()
    hydro_profile = pd.DataFrame(
        columns=hydro_plant_in_state.index, index=profile.index
    )

    for i in hydro_profile.columns:
        factor = hydro_plant_in_state.loc[i]["Pmax"] / hydro_capacity_in_state
        plant_profile = [v * factor for v in profile]
        hydro_profile[i] = plant_profile.copy()

    return hydro_profile


def get_profile_by_plant(plant_df, total_profile):
    """Decompose total hydro profile into plant level profile based on hydro
    generator capacities in the dataframe.

    :param pandas.DataFrame plant_df: plant dataframe contains generator
        capacity as 'Pmax' for each entry.
    :param pandas.Series/list total_profile: aggregated profile to decompose
    :return: (*pandas.DataFrame*) -- hydro profile for each plant decomposed
        from the total_profile.
    :raises TypeError: if plant_df is not a pandas.Dataframe and/or
        total_profile is not a time-series and/or all elements in
        total_profile are numbers.
    :raises ValueError: if plant_df does not contain 'Pmax' as a column.
    """
    if not isinstance(plant_df, pd.DataFrame):
        raise TypeError("plant_df must be a pandas.DataFrame object")
    if not isinstance(total_profile, (pd.Series, list)):
        raise TypeError("total_profile must be a pandas.Series object or list")
    if not all([isinstance(val, (float, int)) for val in total_profile]):
        raise TypeError("total_profile must be all numbers")
    if "Pmax" not in plant_df.columns:
        raise ValueError("Pmax must be one of the columns of plant_df")

    total_hydro_capacity = plant_df["Pmax"].sum()
    res_profile = pd.DataFrame(index=total_profile.index, columns=plant_df.index)

    for plantid in res_profile.columns:
        if total_hydro_capacity == 0:
            factor = 0
        else:
            factor = plant_df.loc[plantid]["Pmax"] / total_hydro_capacity
        plant_profile = [val * factor for val in total_profile]
        res_profile[plantid] = plant_profile.copy()
    return res_profile


def get_normalized_profile(plant_df, plant_profile):
    """Normalize plant level profile by Pmax of the corresponding plant

    :param pandas.DataFrame plant_df: plant dataframe contains generator capacity as
        'Pmax' for each entry.
    :param pandas.DataFrame plant_profile: plant level profile with values of generation
    :return: (*pandas.DataFrame*) -- normalized plant level profile
    :raises TypeError: if plant_df and/or plant_profile is not a pandas.Dataframe
    :raises ValueError: if plant_df does not contain 'Pmax' as a column and/or
        plants in plant_df don't match the ones in plant_profile
    """
    if not isinstance(plant_df, pd.DataFrame):
        raise TypeError("plant_df must be a pandas.DataFrame object")
    if not isinstance(plant_profile, pd.DataFrame):
        raise TypeError("plant_profile must be a pandas.DataFrame object")
    if "Pmax" not in plant_df.columns:
        raise ValueError("Pmax must be one of the columns of plant_df")
    if sorted(plant_df.index) != sorted(plant_profile.columns):
        raise ValueError("plant_df and plant_profile must contain same plants")
    return plant_profile.divide(plant_df["Pmax"]).clip(0, 1).fillna(0)

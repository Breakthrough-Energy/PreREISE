import pandas as pd
from powersimdata.input.grid import Grid
from powersimdata.network.usa_tamu.constants.zones import (
    abv2interconnect,
    abv2loadzone,
)


def get_profile(profile, state):
    """Decompose total hydro profile into plant level profile based on hydro generator
    capacities in the query state.

    :param pandas.DataFrame profile: profile in query state.
    :param str state: the query state.
    :return: (*pandas.DataFrame*) -- hydro profile for each plant in the query state.
    :raises TypeError: if profile is not a time-series and/or state is not a str.
    :raises ValueError: if state is invalid.
    """
    if not isinstance(profile, pd.Series):
        raise TypeError("profile must be a pandas.Series object")
    if not isinstance(state, str):
        raise TypeError("state must be a str")

    if state not in abv2loadzone.keys():
        raise ValueError(
            "Invalid state. Possible states are %s"
            % " | ".join(set(abv2loadzone.keys()))
        )

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

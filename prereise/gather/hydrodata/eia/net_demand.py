from powersimdata.input.grid import Grid
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.network.usa_tamu.constants.zones import abv2loadzone
from powersimdata.scenario.analyze import Analyze
from powersimdata.scenario.scenario import Scenario


def get_net_demand_profile(
    state, scenario=None, interconnect=None, profile_version="vJan2021"
):
    """Get the net demand profile of a specific state based on base profiles or a given
    scenario.

    :param str state: state abbreviation.
    :param powersimdata.scenario.scenario.Scenario scenario: Scenario instance. Get
        the net demand profile of the given scenario if provided, otherwise use base
        profiles.
    :param str interconnect: Interconnection name when scenario is not provided.
    :param str profile_version: Version of the base profiles used in calculations.
    :return: (*pandas.Series*) -- net demand profile in the state.
    :raises TypeError: scenario is not a Scenario object and/or state is not a string.
    :raises ValueError: if state is invalid and/or the scenario is not in analyze
        state and/or both scenario and interconnect are not provided.
    """
    if not isinstance(state, str):
        raise TypeError("state must be a str")
    if scenario and not isinstance(scenario, Scenario):
        raise TypeError(f"scenario must be a {Scenario} object")
    if interconnect and not isinstance(interconnect, str):
        raise TypeError("interconnect must be a string")

    if state not in abv2loadzone.keys():
        raise ValueError(
            "Invalid state. Possible states are %s"
            % " | ".join(set(abv2loadzone.keys()))
        )
    if scenario and not isinstance(scenario.state, Analyze):
        raise ValueError("scenario must in analyze state")
    if not scenario and not interconnect:
        raise ValueError("Either a scenario or an interconnect needs to be specified")

    if scenario:
        wind = scenario.state.get_wind()
        solar = scenario.state.get_solar()
        demand = scenario.state.get_demand()
        grid = scenario.state.get_grid()
    else:
        scenario_info = {
            "interconnect": interconnect,
            "grid_model": "usa_tamu",
            "base_wind": profile_version,
            "base_solar": profile_version,
            "base_demand": profile_version,
        }
        grid = Grid(interconnect)
        tf = TransformProfile(scenario_info, grid, {})
        wind = tf.get_profile("wind")
        solar = tf.get_profile("solar")
        demand = tf.get_profile("demand")

    plant = grid.plant

    wind_plant_in_state = plant[
        (plant.type == "wind") & (plant.zone_name.isin(abv2loadzone[state]))
    ].index

    solar_plant_in_state = plant[
        (plant.type == "solar") & (plant.zone_name.isin(abv2loadzone[state]))
    ].index

    wind_in_state = wind[wind_plant_in_state].sum(axis=1)
    solar_in_state = solar[solar_plant_in_state].sum(axis=1)

    loadzone_in_state = [
        grid.zone2id[z] for z in abv2loadzone[state] if z in grid.zone2id
    ]
    demand_in_state = demand[loadzone_in_state].sum(axis=1)
    net_demand_in_state = demand_in_state - wind_in_state - solar_in_state

    return net_demand_in_state.clip(0, None)

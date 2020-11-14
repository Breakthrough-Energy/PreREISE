from powersimdata.network.usa_tamu.constants.zones import abv2loadzone
from powersimdata.scenario.analyze import Analyze
from powersimdata.scenario.scenario import Scenario


def get_net_demand_profile(state, scenario):
    """Get the net demand profile of a specific state based on a scenario.

    :param str state: state abbreviation.
    :param powersimdata.scenario.scenario.Scenario scenario: Scenario instance.
    :return: (*pandas.DataFrame*) -- net demand profile in the state.
    :raises ValueError: if state is invalid.
    :raises TypeError: is scenario is not a Scenario object.
    """
    if not isinstance(state, str):
        raise TypeError("state must be a str")
    if not isinstance(scenario, Scenario):
        raise TypeError(f"scenario must be a {Scenario} object")

    if state not in abv2loadzone.keys():
        raise ValueError(
            "Invalid state. Possible states are %s"
            % " | ".join(set(abv2loadzone.keys()))
        )
    if not isinstance(scenario.state, Analyze):
        raise ValueError("scenario must in analyze state")

    wind = scenario.state.get_wind()
    solar = scenario.state.get_solar()
    demand = scenario.state.get_demand()
    grid = scenario.state.get_grid()
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

    return net_demand_in_state

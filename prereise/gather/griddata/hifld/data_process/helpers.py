import pandas as pd

from prereise.gather.griddata.hifld import const


def map_state_and_county_to_interconnect(state_abv, county):
    """Map a state and a county to an assumed interconnection.

    :param str state_abv: two-letter state abbreviation.
    :param str county: county name.
    :raises ValueError: if the provided state abbreviation isn't present in mappings.
    :return: (*str*) -- interconnection name.
    """
    state_upper = state_abv.upper()
    for region in ("Eastern", "Western"):
        if state_upper in const.interconnect2state[region]:
            return region
    if state_upper in const.interconnect2state["split"]:
        for region in set(const.state_county_splits[state_upper].keys()) - {"default"}:
            if county.upper() in const.state_county_splits[state_upper][region]:
                return region
        return const.state_county_splits[state_upper]["default"]
    raise ValueError(f"Got an unexpected state: {state_abv}")


def distribute_demand_from_zones_to_buses(zone_demand, bus):
    """Decomposes zone demand to bus demand based on bus 'Pd' column.
    :param pandas.DataFrame zone_demand: demand by zone. Index is timestamp, columns are
        zone IDs, values are zone demand (MW).
    :param pandas.DataFrame bus: table of bus data, containing at least 'zone_id' and
        'Pd' columns.
    :return: (*pandas.DataFrame*) -- data frame of demand. Index is timestamp, columns
        are bus IDs, values are bus demand (MW).
    :raises ValueError: if the columns of ``zone_demand`` don't match the set of zone
        IDs within the 'zone_id' column of ``bus``.
    """
    if set(bus["zone_id"].unique()) != set(zone_demand.columns):
        raise ValueError("zones don't match between zone_demand and bus dataframes")
    grouped_buses = bus.groupby("zone_id")
    bus_zone_pd = grouped_buses["Pd"].transform("sum")
    bus_zone_share = pd.concat(
        [pd.Series(bus["Pd"] / bus_zone_pd, name="zone_share"), bus["zone_id"]], axis=1
    )
    zone_bus_shares = bus_zone_share.pivot_table(
        index="bus_id",
        columns="zone_id",
        values="zone_share",
        dropna=False,
        fill_value=0,
    )
    bus_demand = zone_demand.dot(zone_bus_shares.T)

    return bus_demand

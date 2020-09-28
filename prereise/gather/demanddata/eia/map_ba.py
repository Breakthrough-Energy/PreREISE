import pandas as pd
import requests


def transform_ba_to_region(demand, mapping):
    """Transforms column of demand dataframe to regions defined by
        dictionary mapping

    :param demand: dataframe for the demand
    :type demand: pandas.DataFrame
    :param mapping: dictionary mapping of BA columns to regions
    :type mapping: dict
    :return: dataframe with demand columns according to region
    :rtype: pandas.DataFrame
    """
    agg_demand = pd.DataFrame(index=demand.index)
    for key in mapping:
        mapping_bas = mapping[key]
        valid_columns = list(set(mapping_bas) & set(demand.columns))
        if len(valid_columns) < len(mapping_bas):
            print()
            print("******************************")
            print(f"Missing BA columns for {key}!")
            print(f"Original columns: {mapping_bas}")
            print("******************************")

        print(f"{key} regional demand was summed from {valid_columns}")
        print()
        if demand[valid_columns].shape[1] > 1:
            agg_demand[key] = demand[valid_columns].sum(axis=1)
        else:
            agg_demand[key] = demand[valid_columns]
    return agg_demand


def map_to_loadzone(agg_demand, bus_map):
    """Transforms columns of demand dataframe from BA regions to load zones
        according to bus_map

    :param agg_demand: dataframe for the aggregated region demand
    :type agg_demand: pandas.DataFrame
    :param bus_map: dataframe used to map BA regions to load zones using
        Pd weighting
    :type bus_map: pandas.DataFrame
    :return: new dataframe with demand columns according to load_zone
    :rtype: pandas.DataFrame
    """
    ba_agg = bus_map[["BA", "Pd"]].groupby("BA").sum().rename(columns={"Pd": "PdTotal"})

    ba_scaling_factor = bus_map.merge(ba_agg, left_on="BA", right_on="BA")
    ba_scaling_factor = ba_scaling_factor.assign(
        zone_scaling=lambda x: x["Pd"] / x["PdTotal"]
    )
    ba_grouped_scaling = ba_scaling_factor.groupby(["BA", "zone_name"]).sum()

    zone_demand = pd.DataFrame(index=agg_demand.index)
    for ba_name in ba_grouped_scaling.index.unique(level="BA").to_list():
        zone_scaling_df = ba_grouped_scaling.loc[ba_name]
        for zone_name in zone_scaling_df.index.get_level_values(0).to_list():
            if zone_name in zone_demand.columns.to_list():
                zone_demand[zone_name] += (
                    zone_scaling_df.loc[zone_name, "zone_scaling"] * agg_demand[ba_name]
                )
            else:
                zone_demand[zone_name] = (
                    zone_scaling_df.loc[zone_name, "zone_scaling"] * agg_demand[ba_name]
                )
    print(zone_demand.values.T.tolist())
    return zone_demand


def map_grid_buses_to_county(grid):
    """Find the county in the U.S. territory that each load bus
        in the query grid belongs to

    :param grid: the name of the query grid
    :type grid: Grid
    :return: data frame of counties that load buses locate,
        list of bus indexes that no county matches
    :rtype: pandas.DataFrame, list
    """
    bus_ba_map = grid.bus[grid.bus["Pd"] > 0][["Pd", "lat", "lon"]].copy()
    bus_ba_map.loc[:, "County"] = None
    bus_ba_map.loc[:, "BA"] = None
    # api-endpoint
    url = "https://geo.fcc.gov/api/census/block/find"
    # defining a params dict for the parameters to be sent to the API
    bus_no_county_match = []
    for index, row in bus_ba_map.iterrows():
        print(index)
        params = {
            "latitude": row["lat"],
            "longitude": row["lon"],
            "format": "json",
            "showall": True,
        }
        # sending get request and saving the response as response object
        r = requests.get(url=url, params=params).json()
        try:
            county_name = r["County"]["name"] + "__ " + r["State"]["code"]
            bus_ba_map.loc[index, "County"] = county_name
        except KeyError:
            bus_no_county_match.append(index)
    return bus_ba_map, bus_no_county_match

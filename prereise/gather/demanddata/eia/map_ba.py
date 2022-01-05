import inspect
import json
import os

import pandas as pd
import requests
from powersimdata.utility.distance import find_closest_neighbor
from tqdm import tqdm

import prereise


def aggregate_ba_demand(demand, mapping):
    """Aggregate demand in BAs to regions as defined in the mapping dictionary

    :param pandas.DataFrame demand: demand profiles in BAs.
    :param dict mapping: dictionary mapping of BA columns to regions.
    :return: (*pandas.DataFrame*) -- aggregated demand profiles
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


def get_demand_in_loadzone(agg_demand, bus_map):
    """Get demand in loadzones from aggregated demand of BA regions.

    :param pandas.DataFrame agg_demand: demand profiles as returned by
        :py:func:`aggregate_ba_demand`
    :param pandas.DataFrame bus_map: data frame used to map BA regions to
        load zones using real power demand weighting.
    :return: (*pandas.DataFrame*) -- data frame with demand columns according
        to load zone.
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
    return zone_demand


def map_buses_to_county(bus_county_map):
    """Find the county in the U.S. territory that each bus in the query grid
    belongs to.

    :param pandas.DataFrame bus_county_map: data frame contains a list of
        entries with lat and long.
    :return: (*tuple*) -- first element is a data frame of counties that buses
        locate. Second element is a list of bus indices that no county matches.
    """

    # api-endpoint
    url = "https://geo.fcc.gov/api/census/block/find"
    # defining a params dict for the parameters to be sent to the API

    bus_county_map.loc[:, "County"] = None
    bus_county_map.loc[:, "BA"] = None
    bus_no_county_match = []
    for index, row in tqdm(bus_county_map.iterrows(), total=len(bus_county_map)):
        params = {
            "latitude": row["lat"],
            "longitude": row["lon"],
            "format": "json",
            "showall": True,
        }
        # sending get request and saving the response as response object
        r = requests.get(url=url, params=params).json()
        try:
            county_name = r["County"]["name"] + "__" + r["State"]["code"]
            bus_county_map.loc[index, "County"] = county_name
        except TypeError:
            bus_no_county_match.append(index)
    return bus_county_map, bus_no_county_match


def map_buses_to_ba(bus_df):
    """Find the Balancing Authority in the U.S. territory that each query bus belongs to
    based on GIS information.

    :param (*pandas.DataFrame*) bus_df: data frame contains a list of entries with
        lat and long of buses.
    :return: (*tuple*) -- the first entry is the input data frame with two columns,
        "County" and "BA", added for each bus and the second entry is the list of bus
        indices that no county matches based on Census API (counties of such buses are
        assigned based on its nearest neighbour).
    """

    bus_ba_map, bus_no_county_match = map_buses_to_county(bus_df)
    # hard coded fix for county name mismatch between the returns from census API and
    # BA_County_map.json
    bus_ba_map.County.replace(
        {
            "Danville City__VA": "Danville__VA",
            "Harrisonburg City__VA": "Harrisonburg__VA",
            "Franklin City__VA": "Franklin__VA",
        },
        inplace=True,
    )

    # read json file for BA_County Map
    filepath = os.path.join(
        os.path.dirname(inspect.getfile(prereise)),
        "gather",
        "data",
        "BA_County_map.json",
    )
    with open(filepath) as f:
        ba_county_map = json.load(f)

    county_ba_map = {
        value: key for key in ba_county_map for value in ba_county_map[key]
    }

    bus_ba_map["BA"] = bus_ba_map["County"].map(county_ba_map)
    # assign BA to buses without county assigned based on the nearest neighbor
    neighbor = bus_ba_map.query("~County.isna()")
    for bus_id in bus_no_county_match:
        if neighbor.empty:
            print("No reference bus has BA assigned!")
            break
        ind = find_closest_neighbor(
            (bus_ba_map.loc[bus_id, "lon"], bus_ba_map.loc[bus_id, "lat"]),
            neighbor[["lon", "lat"]].values.tolist(),
        )
        bus_ba_map.loc[bus_id, "BA"] = neighbor.iloc[ind]["BA"]
    return bus_ba_map, bus_no_county_match

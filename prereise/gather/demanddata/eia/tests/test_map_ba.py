import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from prereise.gather.demanddata.eia.map_ba import (
    aggregate_ba_demand,
    get_demand_in_loadzone,
    map_buses_to_ba,
    map_buses_to_county,
)


def test_get_demand_in_loadzone_case():
    bus_map, agg_demand = create_loadzone_dataframe()
    zone_demand = get_demand_in_loadzone(agg_demand, bus_map)
    assert zone_demand.values.T.tolist() == [
        [(1 / 4) + (2 / 3)] * 3,
        [(3 / 4) + (4 / 3) + 3] * 3,
    ]


def test_get_demand_in_loadzone_has_equal_total_demand():
    bus_map, agg_demand = create_loadzone_dataframe()
    zone_demand = get_demand_in_loadzone(agg_demand, bus_map)
    assert_series_equal(
        agg_demand.sum(axis=1), zone_demand.sum(axis=1), check_dtype=False
    )


def test_aggregate_ba_demand_sums_first_three_columns():
    initial_df = create_ba_to_region_dataframe()
    mapping = {"ABC": ["A", "B", "C"]}
    result = aggregate_ba_demand(initial_df, mapping)
    assert result["ABC"].tolist() == list(range(30, 60, 3))


def test_aggregate_ba_demand_sums_first_columns_pairs():
    initial_df = create_ba_to_region_dataframe()
    mapping = {"AB": ["A", "B"], "CD": ["C", "D"]}
    result = aggregate_ba_demand(initial_df, mapping)
    assert result["AB"].tolist() == list(range(10, 30, 2))
    assert result["CD"].tolist() == list(range(50, 70, 2))


def create_loadzone_dataframe():
    bus_map_data = {
        "BA": ["A", "A", "B", "A", "B", "C"],
        "zone_name": ["X", "X", "X", "Y", "Y", "Y"],
        "Pd": range(0, 6),
    }
    bus_map = pd.DataFrame.from_dict(bus_map_data)
    agg_demand = pd.DataFrame({"A": [1] * 3, "B": [2] * 3, "C": [3] * 3})
    agg_demand.set_index(
        pd.date_range(start="2016-01-01", periods=3, freq="H"), inplace=True
    )
    return bus_map, agg_demand


def create_ba_to_region_dataframe():
    start_data = {
        "A": range(0, 10),
        "B": range(10, 20),
        "C": range(20, 30),
        "D": range(30, 40),
        "E": range(40, 50),
    }
    initial_df = pd.DataFrame.from_dict(start_data)
    return initial_df


@pytest.mark.skip(reason="Currently failing due to issues with the geo.fcc.gov API")
def test_map_buses_to_county():
    bus_df = pd.DataFrame(
        {
            "lat": [34.0522, 29.7604, 40.7128],
            "lon": [-118.2437, -95.3698, -74.0060],
        },
        index=["CA", "Texas", "NY"],
    )
    expected_res = ["Los Angeles__CA", "Harris__TX", "New York__NY"]
    bus_county, bus_no_county_match = map_buses_to_county(bus_df)
    assert bus_county["County"].tolist() == expected_res
    assert bus_no_county_match == []


@pytest.mark.skip(reason="Currently failing due to issues with the geo.fcc.gov API")
def test_map_buses_to_ba():
    bus_df = pd.DataFrame(
        {
            "lat": [34.0522, 29.7604, 39.9042],
            "lon": [-118.2437, -95.3698, 116.4074],
        },
        index=["CA", "Texas", "Beijing"],
    )
    expected_res = ["LDWP", "ERCOT", "LDWP"]
    bus_ba, bus_no_county_match = map_buses_to_ba(bus_df)
    assert bus_ba["BA"].tolist() == expected_res
    assert bus_no_county_match == ["Beijing"]

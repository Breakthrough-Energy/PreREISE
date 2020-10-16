import pandas as pd
from pandas.testing import assert_series_equal

from prereise.gather.demanddata.eia.map_ba import (
    map_to_loadzone,
    transform_ba_to_region,
)


def test_loadzone_mapping_case():
    bus_map, agg_demand = create_loadzone_dataframe()
    zone_demand = map_to_loadzone(agg_demand, bus_map)
    assert zone_demand.values.T.tolist() == [
        [(1 / 4) + (2 / 3)] * 3,
        [(3 / 4) + (4 / 3) + 3] * 3,
    ]


def test_loadzone_mapping_has_equal_total_demand():
    bus_map, agg_demand = create_loadzone_dataframe()
    zone_demand = map_to_loadzone(agg_demand, bus_map)
    assert_series_equal(
        agg_demand.sum(axis=1), zone_demand.sum(axis=1), check_dtype=False
    )


def test_transform_ba_to_region_sums_first_three_columns():
    initial_df = create_ba_to_region_dataframe()
    mapping = {"ABC": ["A", "B", "C"]}
    result = transform_ba_to_region(initial_df, mapping)
    assert result["ABC"].tolist() == list(range(30, 60, 3))


def test_transform_ba_to_region_sums_first_columns_pairs():
    initial_df = create_ba_to_region_dataframe()
    mapping = {"AB": ["A", "B"], "CD": ["C", "D"]}
    result = transform_ba_to_region(initial_df, mapping)
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

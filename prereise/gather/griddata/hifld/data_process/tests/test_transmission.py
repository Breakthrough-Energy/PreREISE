from unittest.mock import Mock

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from prereise.gather.griddata.hifld import const
from prereise.gather.griddata.hifld.data_process.transmission import (
    add_b2bs_to_dc_lines,
    add_lines_impedances_ratings,
    add_substation_info_to_buses,
    assign_buses_to_lines,
    augment_line_voltages,
    create_buses,
    create_transformers,
    estimate_branch_impedance,
    estimate_branch_rating,
    filter_islands_and_connect_with_mst,
    map_lines_to_substations_using_coords,
    split_lines_to_ac_and_dc,
)


def test_add_b2bs_to_dc_lines():
    dc_lines = pd.DataFrame(
        {"SUB_1_ID": [1, 2], "SUB_2_ID": [3, 4], "Pmax": [5, 6]},
        index=[200, 201],
    )
    substations = pd.DataFrame(
        {"NAME": ["Wango_West", "Jango", "Wango_East", "Tango_South", "Tango_North"]}
    )
    b2b_ratings = {"Wango": 100, "Tango": 200}
    expected_new_rows = pd.DataFrame(
        {"SUB_1_ID": [0, 3], "SUB_2_ID": [2, 4], "Pmax": [100, 200]}, index=[300, 301]
    )
    add_b2bs_to_dc_lines(dc_lines, substations, b2b_ratings)
    assert_frame_equal(dc_lines.iloc[2:], expected_new_rows)


def test_add_lines_impedances_ratings():
    branch = pd.DataFrame(
        {
            "VOLTAGE": [69, 75, 75, 138],
            "length": [10, 20, 100, 50],
            "type": ["Line"] * 4,
        }
    )
    expected_new_columns = pd.DataFrame(
        {
            "x": [0.0963365, 0.163066, 0.813330, 0.122386],
            "rateA": [85.4507, 92.8812, 42.5257, 227.1693],
        }
    )
    expected_modified_branch = pd.concat([branch, expected_new_columns], axis=1)
    add_lines_impedances_ratings(branch)
    assert_frame_equal(branch, expected_modified_branch)


def test_add_substation_info_to_buses():
    bus = pd.DataFrame({"sub_id": [0, 0, 1, 2]})
    substations = pd.DataFrame(
        {
            "interconnect": ["Eastern", "Western", "Western", "Western", "ERCOT"],
            "STATE": ["MT", "MT", "CA", "CA", "TX"],
        }
    )
    zones = pd.DataFrame(
        {
            "state": ["Montana", "Montana", "California", "Texas"],
            "interconnect": ["Western", "Eastern", "Western", "ERCOT"],
            "zone_id": ["MT Western", "MT Eastern", "California", "TX ERCOT"],
        }
    )
    expected_new_columns = pd.DataFrame(
        {
            "interconnect": ["Eastern", "Eastern", "Western", "Western"],
            "zone_id": ["MT Eastern", "MT Eastern", "MT Western", "California"],
        }
    )
    expected_bus = pd.concat([bus, expected_new_columns], axis=1)
    add_substation_info_to_buses(bus, substations, zones)
    assert_frame_equal(bus, expected_bus)


def test_augment_line_voltages_volt_class():
    substations = pd.DataFrame({"STATE": ["CA", "OR", "NV", "WA"]})
    lines_orig = pd.DataFrame(
        {
            "SUB_1_ID": list(range(4)),
            "SUB_2_ID": list(range(1, 4)) + [0],
            "VOLTAGE": [None] * 4,
            "VOLT_CLASS": ["UNDER 100", "220-287", "345", "500"],
        }
    )
    expected_return = pd.Series([69, 230, 345, 500], name="VOLTAGE", dtype=float)
    lines_to_augment = lines_orig.copy()
    with pytest.raises(AssertionError):
        assert_series_equal(lines_to_augment.VOLTAGE, expected_return)
    augment_line_voltages(lines_to_augment, substations)
    assert_series_equal(lines_to_augment.VOLTAGE, expected_return)


def test_augment_lines_voltages_state_class():
    substations = pd.DataFrame({"STATE": ["WA"] * 100})
    lines_orig = pd.DataFrame(
        {
            "SUB_1_ID": list(range(100)),
            "SUB_2_ID": list(range(1, 100)) + [0],
            "VOLTAGE": [115] * 97 + [138, None, 161],
            "VOLT_CLASS": ["100-161"] * 100,
        }
    )
    expected_return = pd.Series(
        [115] * 97 + [138, 115, 161], name="VOLTAGE", dtype=float
    )
    lines_to_augment = lines_orig.copy()
    with pytest.raises(AssertionError):
        assert_series_equal(lines_to_augment.VOLTAGE, expected_return)
    augment_line_voltages(lines_to_augment, substations)
    assert_series_equal(lines_to_augment.VOLTAGE, expected_return)


def test_augment_lines_voltages_neighbor_consensus():
    substations = pd.DataFrame({"STATE": ["CA", "OR", "NV", "WA"]})
    lines_orig = pd.DataFrame(
        {
            "SUB_1_ID": list(range(4)),
            "SUB_2_ID": list(range(1, 4)) + [0],
            "VOLTAGE": [138, 230, None, 230],
            "VOLT_CLASS": ["FOO"] * 4,
        }
    )
    expected_return = pd.Series([138, 230, 230, 230], name="VOLTAGE", dtype=float)
    lines_to_augment = lines_orig.copy()
    with pytest.raises(AssertionError):
        assert_series_equal(lines_to_augment.VOLTAGE, expected_return)
    augment_line_voltages(lines_to_augment, substations)
    assert_series_equal(lines_to_augment.VOLTAGE, expected_return)


def test_augment_lines_voltages_neighbor_minimum():
    substations = pd.DataFrame({"STATE": ["CA", "OR", "NV", "WA"]})
    lines_orig = pd.DataFrame(
        {
            "SUB_1_ID": list(range(4)),
            "SUB_2_ID": list(range(1, 4)) + [0],
            "VOLTAGE": [138, 230, None, 231],
            "VOLT_CLASS": ["FOO"] * 4,
        }
    )
    expected_return = pd.Series([138, 230, 230, 231], name="VOLTAGE", dtype=float)
    lines_to_augment = lines_orig.copy()
    with pytest.raises(AssertionError):
        assert_series_equal(lines_to_augment.VOLTAGE, expected_return)
    augment_line_voltages(lines_to_augment, substations)
    assert_series_equal(lines_to_augment.VOLTAGE, expected_return)


def test_create_buses():
    lines = pd.DataFrame(
        {
            "SUB_1_ID": [1, 2, 3, 3],
            "SUB_2_ID": [2, 3, 4, 1],
            "VOLTAGE": [69, 115, 230, 345],
        }
    )

    expected_return = pd.DataFrame(
        {
            "sub_id": [1, 1, 2, 2, 3, 3, 3, 4],
            "baseKV": [69, 345, 69, 115, 115, 230, 345, 230],
        },
    )
    expected_return.index.name = "bus_id"
    expected_return["baseKV"] = expected_return["baseKV"].astype(float)
    bus = create_buses(lines)
    assert_frame_equal(bus, expected_return)


def test_create_transformers():
    bus = pd.DataFrame(
        {
            "sub_id": [1, 1, 2, 2, 3, 3, 3, 4],
            "baseKV": [69, 345, 69, 115, 115, 230, 345, 230],
        },
        dtype="float",
    )
    expected_transformers = pd.DataFrame(
        {"from_bus_id": [0, 2, 4, 5], "to_bus_id": [1, 3, 5, 6]}
    )
    transformers = create_transformers(bus)
    assert_frame_equal(transformers, expected_transformers)


def test_estimate_branch_impedance_lines():
    resistance = 0.01
    reactance = 0.1
    fake_lines = [Mock(series_impedance=(resistance + 1j * reactance))] * 3
    branch = pd.DataFrame(
        {"VOLTAGE": [69, 70, 345], "type": ["Line"] * 3, "line_object": fake_lines}
    )
    x = estimate_branch_impedance(branch.iloc[0], pd.Series())
    assert x == reactance / (69**2 / const.s_base)
    x = estimate_branch_impedance(branch.iloc[1], pd.Series())
    assert x == reactance / (70**2 / const.s_base)
    x = estimate_branch_impedance(branch.iloc[2], pd.Series())
    assert x == reactance / (345**2 / const.s_base)


def test_estimate_branch_impedance_transformers():
    transformers = pd.DataFrame(
        {"from_bus_id": [0, 1, 2], "to_bus_id": [1, 2, 3], "type": ["Transformer"] * 3}
    )
    bus_voltages = pd.Series([69, 230, 350, 500])
    x = estimate_branch_impedance(transformers.iloc[0], bus_voltages)
    assert x == const.transformer_reactance[(69, 230)]
    x = estimate_branch_impedance(transformers.iloc[1], bus_voltages)
    assert x == const.transformer_reactance[(230, 345)]
    x = estimate_branch_impedance(transformers.iloc[2], bus_voltages)
    assert x == const.transformer_reactance[(345, 500)]


def test_estimate_branch_rating_lines():
    fake_ratings = pd.Series([10, 20, 30, 40])
    fake_thermal_ratings = pd.Series([100, 200, 300, 400])
    fake_lines = [Mock(power_rating=i) for i in fake_ratings]
    branch = pd.DataFrame(
        {
            "VOLTAGE": [69, 140, 345, 499],
            "type": ["Line"] * 4,
            "line_object": fake_lines,
        }
    )
    assert_series_equal(
        fake_ratings,
        branch.apply(estimate_branch_rating, args=[None, fake_thermal_ratings], axis=1),
    )


def test_estimate_branch_rating_transformers():
    thermal_ratings = pd.Series([100, 550, 1655, 2585], index=[69, 230, 345, 500])
    transformers = pd.DataFrame(
        {"from_bus_id": [0, 1, 2], "to_bus_id": [1, 2, 3], "type": ["Transformer"] * 3}
    )
    bus_voltages = pd.Series([69, 230, 350, 500])

    rating = estimate_branch_rating(transformers.iloc[0], bus_voltages, thermal_ratings)
    assert rating == const.transformer_rating
    rating = estimate_branch_rating(transformers.iloc[1], bus_voltages, thermal_ratings)
    assert rating == const.transformer_rating * 3
    rating = estimate_branch_rating(transformers.iloc[2], bus_voltages, thermal_ratings)
    assert rating == const.transformer_rating * 4


def test_filter_islands_and_connect_with_mst():
    lines = pd.DataFrame(
        {
            "SUB_1_ID": ["Seattle", "Oakland", "Chicago"],
            "SUB_2_ID": ["Oakland", "Las Vegas", "New York"],
        }
    )
    substations = pd.DataFrame(
        {
            "LATITUDE": [47.60, 37.81, 36.17, 41.89, 40.71],
            "LONGITUDE": [-122.34, -122.26, -115.14, -87.63, -74.00],
            "STATE": ["WA", "CA", "NV", "IL", "NY"],
        },
        index=["Seattle", "Oakland", "Las Vegas", "Chicago", "New York"],
    )
    state_neighbor = {
        "CA": ["WA", "NV"],
        "IL": ["NV", "NY"],
        "NV": ["CA", "IL", "NY", "WA"],
        "NY": ["IL", "NV"],
        "WA": ["CA", "NV"],
    }
    new_lines, new_substations = filter_islands_and_connect_with_mst(
        lines, substations, state_neighbor=state_neighbor
    )
    assert len(new_lines) == len(lines) + 1
    assert set(new_lines.iloc[-1][["SUB_1_ID", "SUB_2_ID"]]) == {"Chicago", "Las Vegas"}


def test_map_lines_to_substations_using_coords():
    substations = pd.DataFrame(
        {
            # Los Angeles, Miami, Boston, Seattle x2 (slightly different locations)
            "LATITUDE": [34.05, 25.7752, 42.3581, 47.6097, 47.6099],
            "LONGITUDE": [-118.25, -80.2086, -71.0636, -122.3331, -122.3333],
            "TYPE": ["SUBSTATION"] * 5,
            "NAME": ["Los Angeles", "Miami", "Boston", "Seattle", "Seattle B"],
        },
        index=pd.Index([3, 4, 5, 6, 7], name="ID"),
    )
    # One line approximately connects Seattle and Miami
    lines = pd.DataFrame({"COORDINATES": [[(47.61, -122.4), (25.7, -80.3)]]})

    # With default rounding (three decimal places)
    new_lines, new_substations = map_lines_to_substations_using_coords(
        substations, lines
    )
    # Only one line, mapping to two substations, one of which has a secondary substation
    assert len(new_lines) == 1
    assert new_lines.iloc[0]["SUB_1_ID"] == 6  # Seattle
    assert new_lines.iloc[0]["SUB_2_ID"] == 4  # Miami

    assert len(new_substations) == 3
    assert new_substations.loc[6, "OTHER_SUB"] == [7]
    assert all(o is None for i, o in new_substations["OTHER_SUB"].items() if i != 6)

    # With tighter rounding rounding (four decimal places)
    new_lines, new_substations = map_lines_to_substations_using_coords(
        substations, lines, rounding=4
    )
    # Only one line, mapping to two substations
    assert len(new_lines) == 1
    assert new_lines.iloc[0]["SUB_1_ID"] == 7  # Seattle B
    assert new_lines.iloc[0]["SUB_2_ID"] == 4  # Miami

    assert len(new_substations) == 2
    assert all(o is None for o in new_substations["OTHER_SUB"])


def test_assign_buses_to_lines():
    bus = pd.DataFrame(
        {
            "baseKV": [115, 115, 230, 230, 345, 345],
            "sub_id": [30, 31, 31, 32, 40, 41],
        },
        index=pd.Index([300, 310, 311, 320, 400, 410], name="bus_id"),
    )
    ac_lines = pd.DataFrame(
        {
            "SUB_1_ID": [30, 32, 40],
            "SUB_2_ID": [31, 31, 41],
            "VOLTAGE": [115, 230, 345],
        }
    )
    dc_lines = pd.DataFrame({"SUB_1_ID": [31], "SUB_2_ID": [40]})
    assign_buses_to_lines(ac_lines, dc_lines, bus)
    assert ac_lines["from_bus_id"].equals(pd.Series([300, 320, 400]))
    assert ac_lines["to_bus_id"].equals(pd.Series([310, 311, 410]))
    assert dc_lines["from_bus_id"].equals(pd.Series([311]))
    assert dc_lines["to_bus_id"].equals(pd.Series([400]))


def test_split_lines_to_ac_and_dc():
    lines = pd.DataFrame(
        {"TYPE": ["DC; OVERHEAD", "DC; UNDERGROUND", "AC", "AC", "unknown", "unknown"]},
        index=[101, 102, 103, 104, 105, 106],
    )
    dc_override_indices = {105}
    ac_lines, dc_lines = split_lines_to_ac_and_dc(lines, dc_override_indices)
    assert ac_lines.index.tolist() == [103, 104, 106]
    assert dc_lines.index.tolist() == [101, 102, 105]

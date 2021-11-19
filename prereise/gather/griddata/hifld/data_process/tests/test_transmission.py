import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from prereise.gather.griddata.hifld import const
from prereise.gather.griddata.hifld.data_process.transmission import (
    assign_buses_to_lines,
    augment_line_voltages,
    create_buses,
    create_transformers,
    estimate_branch_impedance,
    estimate_branch_rating,
    map_lines_to_substations_using_coords,
)


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
        {"from_bus_id": [0, 2, 4, 5], "to_bus_id": [1, 3, 6, 6]}
    )
    transformers = create_transformers(bus)
    assert_frame_equal(transformers, expected_transformers)


def test_estimate_branch_impedance_lines():
    branch = pd.DataFrame(
        {"VOLTAGE": [69, 70, 345], "type": ["Line"] * 3, "length": [10, 15, 20]}
    )
    x = estimate_branch_impedance(branch.iloc[0], pd.Series())
    assert x == const.line_reactance_per_mile[69] * 10
    x = estimate_branch_impedance(branch.iloc[1], pd.Series())
    assert x == const.line_reactance_per_mile[69] * 15
    x = estimate_branch_impedance(branch.iloc[2], pd.Series())
    assert x == const.line_reactance_per_mile[345] * 20


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
    branch = pd.DataFrame(
        {
            "VOLTAGE": [69, 140, 345, 499],
            "type": ["Line"] * 4,
            "length": [10, 50, 100, 150],
        }
    )
    rating = estimate_branch_rating(branch.iloc[0], pd.Series())
    assert rating == const.line_rating_short[69]
    rating = estimate_branch_rating(branch.iloc[1], pd.Series())
    assert rating == const.line_rating_short[138]
    rating = estimate_branch_rating(branch.iloc[2], pd.Series())
    assert rating == (
        const.line_rating_surge_impedance_loading[345]
        * const.line_rating_surge_impedance_coefficient
        * 100 ** const.line_rating_surge_impedance_exponent
    )
    rating = estimate_branch_rating(branch.iloc[3], pd.Series())
    assert rating == (
        const.line_rating_surge_impedance_loading[500]
        * const.line_rating_surge_impedance_coefficient
        * 150 ** const.line_rating_surge_impedance_exponent
    )


def test_estimate_branch_rating_transformers():
    transformers = pd.DataFrame(
        {"from_bus_id": [0, 1, 2], "to_bus_id": [1, 2, 3], "type": ["Transformer"] * 3}
    )
    bus_voltages = pd.Series([69, 230, 350, 500])

    rating = estimate_branch_rating(transformers.iloc[0], bus_voltages)
    assert rating == const.transformer_rating
    rating = estimate_branch_rating(transformers.iloc[1], bus_voltages)
    assert rating == const.transformer_rating * 3
    rating = estimate_branch_rating(transformers.iloc[2], bus_voltages)
    assert rating == const.transformer_rating * 4


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

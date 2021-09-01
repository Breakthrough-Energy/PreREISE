import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from prereise.gather.griddata.hifld.data_process.transmission import (
    augment_line_voltages,
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

import math
import unittest
from os import path

import numpy as np
import pandas as pd
from numpy.testing import assert_array_almost_equal

from prereise.gather.winddata.power_curves import (
    build_state_curves,
    get_form_860,
    get_power,
    get_state_power_curves,
    get_turbine_power_curves,
    shift_turbine_curve,
)

data_dir = path.abspath(path.join(path.dirname(__file__), "..", "data"))


def _first_one(curve):
    """Takes pandas.Series, returns index entry for first 1 value."""
    return curve.index[np.where(curve.to_numpy() == 1)[0][0]]


def _last_one(curve):
    """Takes pandas.Series, returns index entry for last 1 value."""
    return curve.index[np.where(curve.to_numpy() == 1)[0][-1]]


class TestBuildStateCurves(unittest.TestCase):
    def setUp(self):
        base_height = 262.467
        form_860_columns = (
            "State",
            "Predominant Turbine Manufacturer",
            "Predominant Turbine Model Number",
            "Nameplate Capacity (MW)",
            "Turbine Hub Height (Feet)",
        )
        form_860_data = [
            ["CA", "Vestas", "V80-1.8", 100, base_height],
            ["CA", "Vestas", "V80-1.8", 100, base_height * 1.1],
            ["WY", "Vestas", "V80-1.8", 100, base_height],
            ["TN", "Toyota", "Corolla", 100, base_height],
            ["RI", "IEC", "class 2", 200, base_height],
            ["NY", "GE", "1.5 S", 100, base_height],
            ["NY", "GE", "1.5 S", 0, 1000000],
            ["TX", "GE", "1.5 S", 100, base_height],
            ["TX", "Vestas", "V80-1.8", 100, base_height],
        ]
        form_860 = pd.DataFrame(data=form_860_data, columns=form_860_columns)
        self.form_860 = form_860

    def test_build_state_curves(self):
        power_curves = get_turbine_power_curves()
        maxspd = 25
        new_curve_res = 0.01
        expected_length = math.ceil(maxspd / new_curve_res) + 1
        expected_max = math.ceil(maxspd / new_curve_res) * new_curve_res
        expected_states = list(self.form_860["State"].unique()) + ["Offshore"]
        expected_shape = (expected_length, len(expected_states))

        state_curves = build_state_curves(self.form_860, power_curves, maxspd)

        self.assertIsInstance(state_curves, pd.DataFrame)
        self.assertEqual(state_curves.index.name, "Speed bin (m/s)")
        self.assertEqual(state_curves.index[0], 0)
        self.assertEqual(state_curves.index[-1], expected_max)
        self.assertEqual(state_curves.to_numpy().shape, expected_shape)
        self.assertEqual(set(expected_states), set(state_curves.columns))

        # Make sure California got shifted (lower cutoff from full capacity)
        original = power_curves["Vestas V80-1.8"]
        self.assertTrue(_last_one(state_curves["CA"]) < _last_one(original))

        # Make sure 'Toyota Corolla' deaults to 'IEC class 2'
        assert_array_almost_equal(
            state_curves["TN"].to_numpy(), state_curves["RI"].to_numpy()
        )

        # Make sure that Capacity weighting works properly for NY
        #   (i.e. crazy tall wind farm with 0 capacity doesn't matter)
        original = np.interp(
            state_curves.index.to_numpy(),
            power_curves["GE 1.5 S"].index.to_numpy(),
            power_curves["GE 1.5 S"].to_numpy(),
        )
        assert_array_almost_equal(state_curves["NY"].to_numpy(), original)
        assert_array_almost_equal(state_curves["NY"].to_numpy(), original)

        # Make sure that we can blend two dissimilar turbines for Texas
        expected = (
            1 / 2 * (state_curves["WY"].to_numpy() + state_curves["NY"].to_numpy())
        )
        assert_array_almost_equal(state_curves["TX"].to_numpy(), expected)


class TestShiftTurbineCurve(unittest.TestCase):
    def setUp(self):
        self.power_curves = get_turbine_power_curves()

    def _check_curve_structure(self, shifted_curve, maxspd, new_curve_res):
        expected_length = math.ceil(maxspd / new_curve_res) + 1
        expected_max = math.ceil(maxspd / new_curve_res) * new_curve_res
        self.assertIsInstance(shifted_curve, pd.Series)
        self.assertEqual(shifted_curve.index.name, "Speed bin (m/s)")
        self.assertEqual(shifted_curve.index[0], 0)
        self.assertEqual(shifted_curve.index[-1], expected_max)
        self.assertEqual(shifted_curve.to_numpy().shape, (expected_length,))

    def test_shift_turbine_curve_higher_hub(self):
        original = self.power_curves["IEC class 2"]
        shifted = shift_turbine_curve(
            original, hub_height=270, maxspd=26, new_curve_res=0.01
        )
        self._check_curve_structure(shifted, maxspd=26, new_curve_res=0.01)
        self.assertTrue(_first_one(shifted) < _first_one(original))
        self.assertTrue(_last_one(shifted) < _last_one(original))

    def test_shift_turbine_curve_lower_hub(self):
        original = self.power_curves["IEC class 2"]
        shifted = shift_turbine_curve(
            original, hub_height=260, maxspd=29, new_curve_res=0.02
        )
        self._check_curve_structure(shifted, maxspd=29, new_curve_res=0.02)
        self.assertTrue(_first_one(shifted) > _first_one(original))
        self.assertTrue(_last_one(shifted) > _last_one(original))

    def test_shift_turbine_curve_sameheight_hub(self):
        original = self.power_curves["IEC class 2"]
        shifted = shift_turbine_curve(
            original, hub_height=262.467, maxspd=30, new_curve_res=0.05
        )
        self._check_curve_structure(shifted, maxspd=30, new_curve_res=0.05)
        self.assertTrue(_first_one(shifted) == _first_one(original))
        self.assertTrue(_last_one(shifted) == _last_one(original))


class TestGetPower(unittest.TestCase):
    def setUp(self):
        self.tpc = get_turbine_power_curves()
        self.spc = get_state_power_curves()

    def test_get_power_default_zero(self):
        power = get_power(self.tpc, self.spc, 0, "foo")
        self.assertIsInstance(power, float)
        self.assertEqual(power, 0)

    def test_get_power_default_five(self):
        power = get_power(self.tpc, self.spc, 5, "foo")
        self.assertIsInstance(power, float)
        self.assertEqual(power, 0.1031)

    def test_get_power_default_ten(self):
        power = get_power(self.tpc, self.spc, 10, "foo")
        self.assertIsInstance(power, float)
        self.assertEqual(power, 0.8554)

    def test_get_power_default_twenty(self):
        power = get_power(self.tpc, self.spc, 20, "foo")
        self.assertIsInstance(power, float)
        self.assertEqual(power, 1)

    def test_get_power_default_thirty(self):
        power = get_power(self.tpc, self.spc, 30, "foo")
        self.assertIsInstance(power, float)
        self.assertEqual(power, 0)

    def test_get_power_badstate_ten_different_default(self):
        # Defaults to IEC class 2
        power = get_power(self.tpc, self.spc, 10, "AR", default="GE 1.5 SLE")
        self.assertIsInstance(power, float)
        self.assertEqual(power, 0.802)

    def test_get_power_named_ten(self):
        power = get_power(self.tpc, self.spc, 10, "GE 1.5 SLE")
        self.assertIsInstance(power, float)
        self.assertEqual(power, 0.802)

    def test_get_power_named_ten2(self):
        power = get_power(self.tpc, self.spc, 10, "Vestas V100-1.8")
        self.assertIsInstance(power, float)
        self.assertAlmostEqual(power, 0.971666667)


class TestGetForm860(unittest.TestCase):
    def test_bad_dir(self):
        bad_dir = path.abspath(path.join(path.dirname(__file__), "..", "foo"))
        with self.assertRaises(ValueError):
            get_form_860(bad_dir)

    def test_default_year(self):
        form_860 = get_form_860(data_dir)
        self.assertIsInstance(form_860, pd.DataFrame)

    def test_good_year(self):
        form_860 = get_form_860(data_dir)
        self.assertIsInstance(form_860, pd.DataFrame)

    def test_bad_year(self):
        with self.assertRaises(ValueError):
            get_form_860(data_dir, year=3000)

    def test_year_str(self):
        with self.assertRaises(TypeError):
            get_form_860(data_dir, year="2016")


class TestGetTurbinePowerCurves(unittest.TestCase):
    def test_get_turbine_power_curves(self):
        power_curves = get_turbine_power_curves()
        self.assertIsInstance(power_curves, pd.DataFrame)
        self.assertEqual(power_curves.index.name, "Speed bin (m/s)")


class TestGetStatePowerCurves(unittest.TestCase):
    def test_get_state_power_curves(self):
        state_power_curves = get_state_power_curves()
        self.assertIsInstance(state_power_curves, pd.DataFrame)
        self.assertEqual(state_power_curves.index.name, "Speed bin (m/s)")

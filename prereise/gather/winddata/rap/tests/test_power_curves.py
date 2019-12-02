import math
import unittest

import numpy as np
from numpy.testing import assert_array_almost_equal
import pandas as pd

from prereise.gather.winddata.rap.power_curves import (PowerCurves,
                                                       build_state_curves,
                                                       _shift_turbine_curve)


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
            'State',
            'Predominant Turbine Manufacturer',
            'Predominant Turbine Model Number',
            'Nameplate Capacity (MW)',
            'Turbine Hub Height (Feet)',
            )
        form_860_data = [
            ['CA', 'Vestas', 'V80-1.8', 100, base_height],
            ['CA', 'Vestas', 'V80-1.8', 100, base_height*1.1],
            ['WY', 'Vestas', 'V80-1.8', 100, base_height],
            ['TN', 'Toyota', 'Corolla', 100, base_height],
            ['RI', 'IEC', 'class 2', 200, base_height],
            ['NY', 'GE', '1.5 S', 100, base_height],
            ['NY', 'GE', '1.5 S', 0, 1000000],
            ['TX', 'GE', '1.5 S', 100, base_height],
            ['TX', 'Vestas', 'V80-1.8', 100, base_height],
            ]
        form_860 = pd.DataFrame(data=form_860_data, columns=form_860_columns)
        self.form_860 = form_860

    def test_build_state_curves(self):
        maxspd = 25
        new_curve_res = 0.01
        expected_length = math.ceil(maxspd / new_curve_res) + 1
        expected_max = math.ceil(maxspd / new_curve_res) * new_curve_res
        expected_states = self.form_860['State'].unique()
        expected_shape = (expected_length, len(expected_states))

        state_curves = build_state_curves(self.form_860, PowerCurves, maxspd)

        self.assertIsInstance(state_curves, pd.DataFrame)
        self.assertEqual(state_curves.index.name, 'Speed bin (m/s)')
        self.assertEqual(state_curves.index[0], 0)
        self.assertEqual(state_curves.index[-1], expected_max)
        self.assertEqual(state_curves.to_numpy().shape, expected_shape)
        self.assertEqual(set(expected_states), set(state_curves.columns))

        # Make sure California got shifted (lower cutoff from full capacity)
        original = PowerCurves['Vestas V80-1.8']
        self.assertTrue(_last_one(state_curves['CA']) < _last_one(original))

        # Make sure 'Toyota Corolla' deaults to 'IEC class 2'
        assert_array_almost_equal(
            state_curves['TN'].to_numpy(), state_curves['RI'].to_numpy())

        # Make sure that Capacity weighting works properly for NY
        #   (i.e. crazy tall wind farm with 0 capacity doesn't matter)
        original = np.interp(
            state_curves.index.to_numpy(),
            PowerCurves['GE 1.5 S'].index.to_numpy(),
            PowerCurves['GE 1.5 S'].to_numpy())
        assert_array_almost_equal(state_curves['NY'].to_numpy(), original)
        assert_array_almost_equal(state_curves['NY'].to_numpy(), original)

        # Make sure that we can blend two dissimilar turbines for Texas
        expected = 1/2 * (
            state_curves['WY'].to_numpy() + state_curves['NY'].to_numpy())
        assert_array_almost_equal(state_curves['TX'].to_numpy(), expected)


class TestShiftTurbineCurve(unittest.TestCase):
    
    def _check_curve_structure(self, shifted_curve, maxspd, new_curve_res):
        expected_length = math.ceil(maxspd / new_curve_res) + 1
        expected_max = math.ceil(maxspd / new_curve_res) * new_curve_res
        self.assertIsInstance(shifted_curve, pd.Series)
        self.assertEqual(shifted_curve.index.name, 'Speed bin (m/s)')
        self.assertEqual(shifted_curve.index[0], 0)
        self.assertEqual(shifted_curve.index[-1], expected_max)
        self.assertEqual(shifted_curve.to_numpy().shape, (expected_length,))

    def test_shift_turbine_curve_higher_hub(self):
        original = PowerCurves['IEC class 2']
        shifted = _shift_turbine_curve(
            original, hub_height=270, maxspd=26, new_curve_res=0.01)
        self._check_curve_structure(shifted, maxspd=26, new_curve_res=0.01)
        self.assertTrue(_first_one(shifted) < _first_one(original))
        self.assertTrue(_last_one(shifted) < _last_one(original))

    def test_shift_turbine_curve_lower_hub(self):
        original = PowerCurves['IEC class 2']
        shifted = _shift_turbine_curve(
            original, hub_height=260, maxspd=29, new_curve_res=0.02)
        self._check_curve_structure(shifted, maxspd=29, new_curve_res=0.02)
        self.assertTrue(_first_one(shifted) > _first_one(original))
        self.assertTrue(_last_one(shifted) > _last_one(original))

    def test_shift_turbine_curve_sameheight_hub(self):
        original = PowerCurves['IEC class 2']
        shifted = _shift_turbine_curve(
            original, hub_height=262.467, maxspd=30, new_curve_res=0.05)
        self._check_curve_structure(shifted, maxspd=30, new_curve_res=0.05)
        self.assertTrue(_first_one(shifted) == _first_one(original))
        self.assertTrue(_last_one(shifted) == _last_one(original))

import numpy as np
import pandas as pd

from prereise.gather.demanddata.transportation_electrification.immediate import (  # adjust_bev,
    apply_annual_scaling,
    apply_daily_adjustments,
)


def test_apply_daily_adjustments():
    hourly_profile = np.array([80, 180, 140, 90, 180, 30, 280, 320, 200, 20, 50, 30])
    adjustment_values = pd.DataFrame([0.2, 0.1, 0.4, 0.3])
    num_days_per_year = 4
    num_segments_per_day = 3

    adjustment_result = apply_daily_adjustments(
        hourly_profile, adjustment_values, num_days_per_year, num_segments_per_day
    )

    correct_adjustment = np.array(
        [0.04, 0.09, 0.07, 0.03, 0.06, 0.01, 0.14, 0.16, 0.1, 0.06, 0.15, 0.09]
    )

    print(adjustment_result)

    np.testing.assert_almost_equal(adjustment_result, correct_adjustment)


def test_apply_annual_scaling():
    hourly_profile = np.array(
        [0.04, 0.09, 0.07, 0.03, 0.06, 0.01, 0.14, 0.16, 0.1, 0.06, 0.15, 0.09]
    )
    bev_vmt = 10
    charging_efficiency = 0.9
    kwhmi = 18

    scaling_result = apply_annual_scaling(
        hourly_profile,
        bev_vmt,
        charging_efficiency,
        kwhmi,
    )

    correct_annual_scaling = np.array([8, 18, 14, 6, 12, 2, 28, 32, 20, 12, 30, 18])

    np.testing.assert_almost_equal(scaling_result, correct_annual_scaling)

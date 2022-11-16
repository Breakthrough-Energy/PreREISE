import numpy as np
import pandas as pd

from prereise.gather.demanddata.transportation_electrification.immediate import (  # adjust_bev,
    apply_annual_scaling,
    apply_daily_adjustments,
)


def test_apply_daily_adjustments():
    hourly_profile = np.array([60, 180, 120, 120, 240, 60, 180, 220, 200, 20, 50, 30])
    adjustment_values = pd.DataFrame([0.6, 0.7, 0.3, 0.5])
    num_days_per_year = 4
    num_segments_per_day = 3

    adjustment_result = apply_daily_adjustments(
        hourly_profile, adjustment_values, num_days_per_year, num_segments_per_day
    )

    correct_adjustment = np.array(
        [
            0.1,
            0.3,
            0.2,
            0.2,
            0.4,
            0.1,
            0.09,
            0.11,
            0.1,
            0.1,
            0.25,
            0.15,
        ]
    )

    print(adjustment_result)

    np.testing.assert_almost_equal(adjustment_result, correct_adjustment)


def test_apply_annual_scaling():
    hourly_profile = np.array(
        [
            0.1,
            0.3,
            0.2,
            0.2,
            0.4,
            0.1,
            0.09,
            0.11,
            0.1,
            0.1,
            0.25,
            0.15,
        ]
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

    correct_annual_scaling = np.array([20, 60, 40, 40, 80, 20, 18, 22, 20, 20, 50, 30])

    assert np.array_equal(scaling_result, correct_annual_scaling)

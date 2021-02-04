import pandas as pd
import pytest

from prereise.gather.hydrodata.eia.interpolate_capacity_factors import get_profile


def test_get_profile_argument_type():
    arg = (
        ({1, 2, 3}, pd.Timestamp(2016, 1, 1), pd.Timestamp(2016, 12, 31, 23)),
        ((1, 2, 3), pd.Timestamp(2016, 1, 1), pd.Timestamp(2016, 12, 31, 23)),
        (
            [1, 2, 3],
            "2016-01-01",
            pd.Timestamp(2016, 12, 31, 23),
        ),
        (
            [1, 2, 3],
            pd.Timestamp(2016, 1, 1),
            "2016-12-31-23",
        ),
    )
    for a in arg:
        with pytest.raises(TypeError):
            get_profile(a[0], start=a[1], end=a[2])


def test_get_profile_argument_value():
    arg = (
        (
            [1, 2, 3],
            pd.Timestamp(2012, 12, 31, 23),
            pd.Timestamp(2016, 12, 31, 23),
        ),
        (
            [1, 2, 3],
            pd.Timestamp(2016, 1, 1),
            pd.Timestamp(2020, 12, 31, 23),
        ),
        (
            [1, 2, 3],
            pd.Timestamp(2016, 3, 1),
            pd.Timestamp(2020, 2, 15),
        ),
    )
    for a in arg:
        with pytest.raises(ValueError):
            get_profile(a[0], start=a[1], end=a[2])

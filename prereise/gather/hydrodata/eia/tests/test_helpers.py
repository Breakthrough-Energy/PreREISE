import numpy as np
import pandas as pd
import pytest

from prereise.gather.hydrodata.eia.helpers import scale_profile


def test_scale_profile_argument_type():
    arg = ((pd.DataFrame(), [1] * 12), (pd.Series(dtype=np.float64), set([1] * 12)))
    for a in arg:
        with pytest.raises(TypeError):
            scale_profile(a[0], a[1])


def test_scale_profile_argument_value():
    arg = (
        (
            pd.Series(
                [1] * 12, index=pd.date_range("2016-01-01", periods=12, freq="MS")
            ),
            [1] * 12,
        ),
        (
            pd.Series(
                [1] * 366 * 24,
                index=pd.date_range("2016-01-01", periods=366 * 24, freq="H"),
            ),
            [1] * 6,
        ),
    )
    for a in arg:
        with pytest.raises(ValueError):
            scale_profile(a[0], a[1])


def test_scale_profile():
    arg = (
        pd.Series(
            [1] * 366 * 24,
            index=pd.date_range("2016-01-01", periods=366 * 24, freq="H"),
        ),
        list(range(1, 13)),
    )
    profile = scale_profile(arg[0], arg[1])
    for i, j in zip(profile.resample("MS").sum().values, arg[1]):
        assert round(i) == j

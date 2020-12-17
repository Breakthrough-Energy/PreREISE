import numpy as np
import pandas as pd
import pytest

from prereise.gather.hydrodata.eia.decompose_profile import (
    get_profile_by_state,
)


def test_get_profile_argument_type():
    arg = ((1, "WA"), (pd.Series(dtype=np.float64), 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_profile_by_state(a[0], a[1])


def test_get_profile_argument_value():
    a = (pd.Series(dtype=np.float64), "Canada")
    with pytest.raises(ValueError):
        get_profile_by_state(a[0], a[1])

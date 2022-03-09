import numpy as np
import pandas as pd
import pytest
from powersimdata.tests.mock_grid import MockGrid

from prereise.gather.hydrodata.eia.decompose_profile import (
    get_normalized_profile,
    get_profile_by_plant,
    get_profile_by_state,
)

mock_plant_df = pd.DataFrame(
    {
        "plant_id": [1, 2, 3, 4],
        "Pmax": [10, 10, 20, 20],
        "type": ["hydro", "solar", "wind", "hydro"],
        "zone_name": [
            "Bay Area",
            "Bay Area",
            "Central California",
            "Central " "California",
        ],
    }
)

mock_total_profile = pd.Series(
    [15, 15, 30, 30],
    index=[0, 1, 2, 3],
)
mock_plant_profile = pd.DataFrame(
    {
        1: [5.0, 5.0, 10.0, 10.0],
        4: [10.0, 10.0, 20.0, 20.0],
    },
    index=[0, 1, 2, 3],
)
mock_normalized_profile = pd.DataFrame(
    {
        1: [0.5, 0.5, 1.0, 1.0],
        4: [0.5, 0.5, 1.0, 1.0],
    },
    index=[0, 1, 2, 3],
)


def test_get_profile_by_state_argument_type():
    arg = ((1, "WA"), (pd.Series(dtype=np.float64), 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_profile_by_state(a[0], a[1])


def test_get_profile_by_state_argument_value():
    a = (pd.Series(dtype=np.float64), "Canada")
    with pytest.raises(ValueError):
        get_profile_by_state(a[0], a[1])


def test_get_profile_by_state():
    mock_grid = MockGrid(grid_attrs={"plant": mock_plant_df})
    assert mock_plant_profile.equals(
        get_profile_by_state(mock_total_profile, "CA", mock_grid)
    )


def test_get_profile_by_plant_argument_type():
    arg = ((pd.Series([1, 2]), [10, 20]), (pd.DataFrame({"a": [1, 2]}), [1, "aaa"]))
    for a in arg:
        with pytest.raises(TypeError):
            get_profile_by_plant(a[0], a[1])


def test_get_profile_by_plant_argument_value():
    a = (pd.DataFrame({"a": [1, 2]}), [10, 20])
    with pytest.raises(ValueError):
        get_profile_by_plant(a[0], a[1])


def test_get_profile_by_plant():
    plant_df = mock_plant_df.set_index("plant_id").query("type == 'hydro'")
    assert mock_plant_profile.equals(get_profile_by_plant(plant_df, mock_total_profile))


def test_get_normalized_profile_argument_type():
    arg = (
        (pd.Series(["a", "b"]), pd.DataFrame({"a": [1, 2]})),
        (pd.DataFrame({"a": [1, 2]}), [1, 2]),
    )
    for a in arg:
        with pytest.raises(TypeError):
            get_normalized_profile(a[0], a[1])


def test_get_normalized_profile_argument_value():
    a = (
        pd.DataFrame({"a": [1, 2]}),
        pd.DataFrame({0: [1, 2]}),
        pd.DataFrame({"Pmax": [10, 20]}),
        pd.DataFrame({0: [1, 2]}),
    )
    with pytest.raises(ValueError):
        get_normalized_profile(a[0], a[1])


def test_get_normalized_profile():
    plant_df = mock_plant_df.set_index("plant_id").query("type == 'hydro'")
    assert mock_normalized_profile.equals(
        get_normalized_profile(plant_df, mock_plant_profile)
    )

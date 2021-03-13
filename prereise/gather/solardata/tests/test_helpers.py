import pandas as pd
import pytest

from prereise.gather.solardata.helpers import get_plant_id_unique_location, to_reise


def test_plant_id_unique_location_type():
    arg = (1, (1, 2, 3), {"a", "b", "c"})
    for a in arg:
        with pytest.raises(TypeError, match="plant must be a pandas.DataFrame"):
            get_plant_id_unique_location(a)


def test_plant_id_unique_location_value():
    arg = (
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
        pd.DataFrame({"a": [1, 2, 3], "lon": [4, 5, 6]}),
        pd.DataFrame({"lat": [1, 2, 3], "b": [4, 5, 6]}),
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}).rename_axis("plant_id", axis=0),
        pd.DataFrame({"lat": [1, 2], "b": [3, 4]}).rename_axis("plant_id", axis=0),
        pd.DataFrame({"a": [1, 2], "lon": [3, 4]}).rename_axis("plant_id", axis=0),
    )
    for a in arg:
        with pytest.raises(
            ValueError,
            match="data frame must have plant_id as index and lat and lon among columns",
        ):
            get_plant_id_unique_location(a)


def test_plant_id_unique_location():
    plant = pd.DataFrame(
        {
            "lat": [
                46.6451,
                35.0609,
                45.8849,
                37.7033,
                37.7033,
                35.0609,
                46.6451,
                46.6451,
                35.0609,
                46.6451,
                37.7033,
                45.8849,
                35.0609,
                46.6451,
            ],
            "lon": [
                -119.908,
                -118.292,
                -109.888,
                -102.623,
                -102.623,
                -118.292,
                -119.908,
                -119.908,
                -118.292,
                -119.908,
                -102.623,
                -109.888,
                -118.292,
                -119.908,
            ],
        }
    ).rename_axis("plant_id", axis=0)
    result = get_plant_id_unique_location(plant)
    expected = {
        (-102.623, 37.7033): [3, 4, 10],
        (-109.888, 45.8849): [2, 11],
        (-118.292, 35.0609): [1, 5, 8, 12],
        (-119.908, 46.6451): [0, 6, 7, 9, 13],
    }
    assert result.keys() == expected.keys()
    for k in result:
        assert result[k].values.tolist() == expected[k]


def test_to_reise_type():
    arg = (1, (1, 2, 3), {"a", "b", "c"})
    for a in arg:
        with pytest.raises(TypeError, match="data must be a pandas.DataFrame"):
            to_reise(a)


def test_to_reise_value():
    arg = (
        pd.DataFrame({"a": [1, 2, 3], "Pout": [4, 5, 6]}),
        pd.DataFrame({"plant_id": [1, 2, 3], "Pout": [4, 5, 6]}),
        pd.DataFrame({"ts": [1, 2, 3], "plant_id": [4, 5, 6], "ts_id": [7, 8, 9]}),
        pd.DataFrame({"Pout": [1, 2, 3], "plant_id": [4, 5, 6], "ts_id": [7, 8, 9]}),
    )
    for a in arg:
        with pytest.raises(
            ValueError,
            match="data frame must have Pout, plant_id, ts and ts_id among columns",
        ):
            to_reise(a)


def test_to_reise():
    data = pd.DataFrame(
        {
            "Pout": [
                0.6451,
                0.0609,
                0.8849,
                0.7033,
                0.2033,
                0.3609,
                0.1851,
                0.4551,
                0.6609,
                0.7151,
                0.5333,
                0.3149,
                0.2909,
                0.3456,
                0.8207,
            ],
            "plant_id": [0, 1, 2, 3, 4] * 3,
            "ts": sorted(
                [t for t in pd.date_range(start="2/4/2019", periods=3, freq="H")] * 5
            ),
            "ts_id": sorted([1, 2, 3] * 5),
        }
    )
    expected = pd.DataFrame(
        {i: p for i, p in enumerate(data.Pout.values.reshape(3, 5).T)},
        index=pd.date_range(start="2/4/2019", periods=3, freq="H"),
    ).rename_axis("UTC", axis=0)
    assert to_reise(data).equals(expected)

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from prereise.gather.winddata.hrrr.calculations import (
    calculate_pout,
    find_closest_wind_grids,
)


def test_find_closest_wind_grids():
    wind_farms = MagicMock()
    wind_farms.__len__.return_value = 2
    wind_farms.lat.values = [20, 40]
    wind_farms.lon.values = [20, 40]
    wind_data_lat = MagicMock()
    wind_data_long = MagicMock()

    wind_data_lat.flatten.return_value = [19, 30, 41]
    wind_data_long.flatten.return_value = [19, 30, 41]
    assert np.array_equal(
        np.array([0, 2]),
        find_closest_wind_grids(wind_farms, [wind_data_lat, wind_data_long]),
    )


@patch("prereise.gather.winddata.hrrr.calculations.get_power")
@patch("prereise.gather.winddata.hrrr.calculations.get_wind_data_lat_long")
@patch("prereise.gather.winddata.hrrr.calculations.find_closest_wind_grids")
@patch("prereise.gather.winddata.hrrr.calculations.pygrib")
def test_calculate_pout(
    pygrib, find_closest_wind_grids, get_wind_data_lat_long, get_power
):
    # we assume get_power is well tested and simply return the magnitude value passed in
    # for straightforward testing
    def get_power_mock(
        turbine_power_curves,
        state_power_curves,
        wind_farm_specific_magnitude,
        turbine_types,
    ):
        return wind_farm_specific_magnitude

    get_power.side_effect = get_power_mock
    find_closest_wind_grids.return_value = np.array([1, 2])

    grib_mock = MagicMock()

    grib_mock.select.return_value.__getitem__.return_value.values.flatten.return_value = np.array(
        [0, 1, 2]
    )
    pygrib.open.return_value = grib_mock
    wind_farms = MagicMock()
    wind_farms.index = [0, 1]
    wind_farms.loc.__getitem__.return_value.type = "wind_offshore"
    wind_farms.__len__.return_value = 2
    df = calculate_pout(
        wind_farms,
        datetime.fromisoformat("2016-01-01"),
        datetime.fromisoformat("2016-01-01"),
        "",
    )
    expected_df = pd.DataFrame(
        data=[[np.sqrt(2), np.sqrt(8)]],
        index=[datetime.fromisoformat("2016-01-01")],
        columns=[0, 1],
    )
    assert df.equals(expected_df)

from unittest.mock import MagicMock, patch

import pytest

from prereise.cli.data_sources.tests.conftest import (
    CURRENT_DIRECTORY_FILEPATH,
    STRING_DATE_2021_5_1,
    STRING_DATE_2021_12_1,
    TEXAS_REGION_LIST,
    VALID_GRID_MODEL,
)
from prereise.cli.data_sources.wind_data import WindDataRapidRefresh

NO_IMPUTE = False


@pytest.fixture
def wind_data_object():
    return WindDataRapidRefresh()


def test_winddata_end_date_before_start_date(wind_data_object):
    with pytest.raises(AssertionError):
        wind_data_object.extract(
            TEXAS_REGION_LIST,
            STRING_DATE_2021_12_1,
            STRING_DATE_2021_5_1,
            CURRENT_DIRECTORY_FILEPATH,
            VALID_GRID_MODEL,
            NO_IMPUTE,
        )


@patch("prereise.cli.data_sources.wind_data.rap")
@patch("prereise.cli.data_sources.wind_data.Grid")
def test_winddata_happy_path(grid, rap, wind_data_object):
    grid_mock = MagicMock()
    wind_farms = MagicMock()
    grid_mock.plant.groupby.return_value.get_group.return_value = wind_farms
    data = MagicMock()
    rap.retrieve_data.return_value = (data, [])
    grid.return_value = grid_mock
    wind_data_object.extract(
        TEXAS_REGION_LIST,
        STRING_DATE_2021_5_1,
        STRING_DATE_2021_12_1,
        CURRENT_DIRECTORY_FILEPATH,
        VALID_GRID_MODEL,
        NO_IMPUTE,
    )
    rap.retrieve_data.assert_called_with(
        wind_farms, start_date=STRING_DATE_2021_5_1, end_date=STRING_DATE_2021_12_1
    )
    data.to_pickle.assert_called_with(CURRENT_DIRECTORY_FILEPATH)


@patch("prereise.cli.data_sources.wind_data.rap")
@patch("prereise.cli.data_sources.wind_data.Grid")
@patch("prereise.cli.data_sources.wind_data.logging")
@patch("prereise.cli.data_sources.wind_data.impute")
def test_winddata_missing_files(impute, logging, grid, rap, wind_data_object):
    grid_mock = MagicMock()
    wind_farms = MagicMock()
    grid_mock.plant.groupby.return_value.get_group.return_value = wind_farms
    data = MagicMock()
    rap.retrieve_data.return_value = (data, [None, None])
    grid.return_value = grid_mock
    wind_data_object.extract(
        TEXAS_REGION_LIST,
        STRING_DATE_2021_5_1,
        STRING_DATE_2021_12_1,
        CURRENT_DIRECTORY_FILEPATH,
        VALID_GRID_MODEL,
        NO_IMPUTE,
    )
    rap.retrieve_data.assert_called_with(
        wind_farms, start_date=STRING_DATE_2021_5_1, end_date=STRING_DATE_2021_12_1
    )
    data.to_pickle.assert_called_with(CURRENT_DIRECTORY_FILEPATH)
    impute.gaussian.assert_called_with(data, wind_farms, inplace=True)

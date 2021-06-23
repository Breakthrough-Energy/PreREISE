from unittest.mock import MagicMock, patch

import pytest

from prereise.cli.data_sources.wind_data import WindData

TEXAS_REGION_LIST = ["Texas"]
STRING_DATE_2021_12_1 = "2021-12-1"
STRING_DATE_2021_5_1 = "2019-5-1"
CURRENT_DIRECTORY_FILEPATH = "./"


@pytest.fixture
def wind_data_object():
    return WindData()


def test_winddata_end_date_before_start_date(wind_data_object):
    with pytest.raises(AssertionError):
        wind_data_object.extract(
            TEXAS_REGION_LIST,
            STRING_DATE_2021_12_1,
            STRING_DATE_2021_5_1,
            CURRENT_DIRECTORY_FILEPATH,
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
    )
    rap.retrieve_data.assert_called_with(
        wind_farms, start_date=STRING_DATE_2021_5_1, end_date=STRING_DATE_2021_12_1
    )
    data.to_pickle.assert_called_with(CURRENT_DIRECTORY_FILEPATH)


@patch("prereise.cli.data_sources.wind_data.rap")
@patch("prereise.cli.data_sources.wind_data.Grid")
@patch("prereise.cli.data_sources.wind_data.logging")
def test_winddata_missing_files(logging, grid, rap, wind_data_object):
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
    )
    rap.retrieve_data.assert_called_with(
        wind_farms, start_date=STRING_DATE_2021_5_1, end_date=STRING_DATE_2021_12_1
    )
    data.to_pickle.assert_called_with(CURRENT_DIRECTORY_FILEPATH)
    logging.warning.assert_called_with("There are 2 files missing")


@patch("prereise.cli.data_sources.wind_data.rap")
@patch("prereise.cli.data_sources.wind_data.Grid")
def test_winddata_repeated_regions(grid, rap, wind_data_object):
    rap.retrieve_data.return_value = (MagicMock(), [None, None])
    wind_data_object.extract(
        [TEXAS_REGION_LIST[0], TEXAS_REGION_LIST[0]],
        STRING_DATE_2021_5_1,
        STRING_DATE_2021_12_1,
        CURRENT_DIRECTORY_FILEPATH,
    )
    grid.assert_called_with(TEXAS_REGION_LIST)

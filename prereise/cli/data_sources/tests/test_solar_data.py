from unittest.mock import MagicMock, patch

import pytest

from prereise.cli.data_sources.solar_data import (
    NAIVE_STRING,
    SAM_STRING,
    SolarDataGriddedAtmospheric,
    SolarDataNationalSolarRadiationDatabase,
)
from prereise.cli.data_sources.tests.conftest import (
    API_KEY,
    CURRENT_DIRECTORY_FILEPATH,
    EMAIL,
    INVALID_METHOD,
    STRING_DATE_2021_5_1,
    STRING_DATE_2021_12_1,
    STRING_YEAR_2020,
    TEXAS_REGION_LIST,
    VALID_GRID_MODEL,
)


@pytest.fixture
def solar_data_ga_object():
    return SolarDataGriddedAtmospheric()


@pytest.fixture
def solar_data_nsrdb_object():
    return SolarDataNationalSolarRadiationDatabase()


def test_solar_data_ga_end_date_before_start_date(solar_data_ga_object):
    with pytest.raises(AssertionError):
        solar_data_ga_object.extract(
            TEXAS_REGION_LIST,
            STRING_DATE_2021_12_1,
            STRING_DATE_2021_5_1,
            CURRENT_DIRECTORY_FILEPATH,
            API_KEY,
            VALID_GRID_MODEL,
        )


@patch("prereise.cli.data_sources.solar_data.ga_wind")
@patch("prereise.cli.data_sources.solar_data.Grid")
def test_solar_data_ga_happy_path(grid, ga_wind, solar_data_ga_object):
    solar_farms = MagicMock()
    data = MagicMock()
    ga_wind.retrieve_data.return_value = data
    grid.return_value.plant.groupby.return_value.get_group.return_value = solar_farms
    solar_data_ga_object.extract(
        TEXAS_REGION_LIST,
        STRING_DATE_2021_5_1,
        STRING_DATE_2021_12_1,
        CURRENT_DIRECTORY_FILEPATH,
        API_KEY,
        VALID_GRID_MODEL,
    )
    ga_wind.retrieve_data.assert_called_with(
        solar_farms,
        API_KEY,
        start_date=STRING_DATE_2021_5_1,
        end_date=STRING_DATE_2021_12_1,
    )
    data.to_pickle.assert_called_with(CURRENT_DIRECTORY_FILEPATH)


def test_solar_data_nsrdb_invalid_method(solar_data_nsrdb_object):
    with pytest.raises(ValueError):
        solar_data_nsrdb_object.extract(
            TEXAS_REGION_LIST,
            INVALID_METHOD,
            STRING_YEAR_2020,
            CURRENT_DIRECTORY_FILEPATH,
            EMAIL,
            API_KEY,
            VALID_GRID_MODEL,
        )


@patch("prereise.cli.data_sources.solar_data.Grid")
def test_solar_data_nsrdb_happy_path(grid, solar_data_nsrdb_object):

    methods_to_test = [
        ("prereise.cli.data_sources.solar_data.sam.retrieve_data_blended", SAM_STRING),
        ("prereise.cli.data_sources.solar_data.naive.retrieve_data", NAIVE_STRING),
    ]

    for patch_path, method_string in methods_to_test:
        with patch(patch_path) as method:
            solar_farms = MagicMock()
            data = MagicMock()
            method.return_value = data
            grid.return_value.plant.groupby.return_value.get_group.return_value = (
                solar_farms
            )
            solar_data_nsrdb_object.extract(
                TEXAS_REGION_LIST,
                method_string,
                STRING_YEAR_2020,
                CURRENT_DIRECTORY_FILEPATH,
                EMAIL,
                API_KEY,
                VALID_GRID_MODEL,
            )
            if method_string == SAM_STRING:
                method.assert_called_with(
                    EMAIL, API_KEY, solar_plants=solar_farms, year=STRING_YEAR_2020
                )
            elif method_string == NAIVE_STRING:
                method.assert_called_with(solar_farms, EMAIL, API_KEY, STRING_YEAR_2020)
            else:
                raise Exception("Unknown method_string!")

            data.to_pickle.assert_called_with(CURRENT_DIRECTORY_FILEPATH)

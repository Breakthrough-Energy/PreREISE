from datetime import datetime

from powersimdata.input.grid import Grid

from prereise.cli.constants import (
    DATE_FMT,
    END_DATE_HELP_STRING,
    FILE_PATH_HELP_STRING,
    GRID_MODEL_DEFAULT,
    GRID_MODEL_HELP_STRING,
    REGION_CHOICES,
    START_DATE_HELP_STRING,
)
from prereise.cli.data_sources.data_source import DataSource
from prereise.cli.helpers import validate_date, validate_file_path, validate_year
from prereise.gather.solardata.ga_wind import ga_wind
from prereise.gather.solardata.nsrdb import naive, sam

API_KEY_HELP_STRING = (
    "API key that can be requested at https://developer.nrel.gov/signup/"
)
NAIVE_STRING = "naive"
SAM_STRING = "sam"


class SolarDataGriddedAtmospheric(DataSource):
    @property
    def command_name(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_name`

        :return: (*str*)
        """
        return "solar_data_ga"

    @property
    def command_help(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_help`

        :return: (*str*)
        """
        return "Download solar data from the Gridded Atmospheric Wind Integration National Dataset Toolkit"

    @property
    def extract_arguments(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.extract_arguments`

        :return: (*str*)
        """
        return [
            {
                "command_flags": ["--region", "-r"],
                "required": True,
                "choices": REGION_CHOICES,
                "type": str,
                "action": "append",
            },
            {
                "command_flags": ["--start_date", "-sd"],
                "required": True,
                "type": validate_date,
                "help": START_DATE_HELP_STRING,
            },
            {
                "command_flags": ["--end_date", "-ed"],
                "required": True,
                "type": validate_date,
                "help": END_DATE_HELP_STRING,
            },
            {
                "command_flags": ["--file_path", "-fp"],
                "required": True,
                "type": validate_file_path,
                "help": FILE_PATH_HELP_STRING,
            },
            {
                "command_flags": ["--key", "-k"],
                "required": True,
                "type": str,
                "help": API_KEY_HELP_STRING,
            },
            {
                "command_flags": ["--grid_model", "-gm"],
                "required": False,
                "default": GRID_MODEL_DEFAULT,
                "choices": list(Grid.SUPPORTED_MODELS),
                "help": GRID_MODEL_HELP_STRING,
            },
        ]

    def extract(
        self, region, start_date, end_date, file_path, key, grid_model, **kwargs
    ):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.extract`

        :param list region: list of regions to download data for
        :param str start_date: date designating when to start the data download
        :param str end_date: date designating when to end the data download
        :param str file_path: file location on local filesystem on where to store the data
        :param str key: API key that can be requested at https://developer.nrel.gov/signup/
        :param str grid_model: .mat file path for a grid model or a string supported by
            `powersimdata.input.grid.Grid.SUPPORTED_MODELS`
        """
        assert datetime.strptime(start_date, DATE_FMT) <= datetime.strptime(
            end_date, DATE_FMT
        )
        grid = Grid(region, source=grid_model)
        solar_plants = grid.plant.groupby("type").get_group("solar")
        data = ga_wind.retrieve_data(
            solar_plants, key, start_date=start_date, end_date=end_date
        )
        data.to_pickle(file_path)


class SolarDataNationalSolarRadiationDatabase(DataSource):
    @property
    def command_name(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_name`

        :return: (*str*)
        """
        return "solar_data_nsrdb"

    @property
    def command_help(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_help`

        :return: (*str*)
        """
        return "Download solar data from the National Solar Radiation Database"

    @property
    def extract_arguments(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.extract_arguments`

        :return: (*str*)
        """
        return [
            {
                "command_flags": ["--region", "-r"],
                "required": True,
                "choices": REGION_CHOICES,
                "type": str,
                "action": "append",
            },
            {
                "command_flags": ["--method", "-m"],
                "required": True,
                "choices": [NAIVE_STRING, SAM_STRING],
                "type": str,
            },
            {
                "command_flags": ["--year", "-y"],
                "required": True,
                "type": validate_year,
                "help": "The start date for the data download in format 'YYYY'",
            },
            {
                "command_flags": ["--file_path", "-fp"],
                "required": True,
                "type": validate_file_path,
                "help": FILE_PATH_HELP_STRING,
            },
            {
                "command_flags": ["--email", "-e"],
                "required": True,
                "type": str,
                "help": "Email used to sign up at https://developer.nrel.gov/signup/",
            },
            {
                "command_flags": ["--key", "-k"],
                "required": True,
                "type": str,
                "help": API_KEY_HELP_STRING,
            },
            {
                "command_flags": ["--grid_model", "-gm"],
                "required": False,
                "default": GRID_MODEL_DEFAULT,
                "choices": list(Grid.SUPPORTED_MODELS),
                "help": GRID_MODEL_HELP_STRING,
            },
        ]

    def extract(
        self, region, method, year, file_path, email, key, grid_model, **kwargs
    ):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.extract`

        :param list region: list of regions to download data for
        :param str method: string indicating the modeling for power output
        :param str year: string in the format YYYY denoting year to download from
        :param str file_path: file location on local filesystem on where to store the data
        :param str email: email used to sign up at https://developer.nrel.gov/signup/
        :param str key: API key that can be requested at https://developer.nrel.gov/signup/
        :param str grid_model: .mat file path for a grid model or a string supported by
            `powersimdata.input.grid.Grid.SUPPORTED_MODELS`
        """
        grid = Grid(region, source=grid_model)
        solar_plants = grid.plant.groupby("type").get_group("solar")
        if method == NAIVE_STRING:
            data = naive.retrieve_data(solar_plants, email, key, year)
        elif method == SAM_STRING:
            data = sam.retrieve_data_blended(
                email, key, solar_plants=solar_plants, year=year
            )
        else:
            raise ValueError(f"Unexpected method {method}")
        data.to_pickle(file_path)

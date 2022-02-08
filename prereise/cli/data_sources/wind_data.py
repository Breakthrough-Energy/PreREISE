import logging
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
from prereise.cli.helpers import validate_date, validate_file_path
from prereise.gather.winddata import impute
from prereise.gather.winddata.rap import rap


class WindDataRapidRefresh(DataSource):
    @property
    def command_name(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_name`

        :return: (*str*)
        """
        return "wind_data_rap"

    @property
    def command_help(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_help`

        :return: (*str*)
        """
        return "Download wind data from National Centers for Environmental Prediction"

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
                "command_flags": ["--grid_model", "-gm"],
                "required": False,
                "default": GRID_MODEL_DEFAULT,
                "choices": list(Grid.SUPPORTED_MODELS),
                "help": GRID_MODEL_HELP_STRING,
            },
            {
                "command_flags": ["--no_impute", "-ni"],
                "action": "store_true",
                "help": "Flag used to avoid naive gaussian imputing of missing data",
            },
        ]

    def extract(
        self, region, start_date, end_date, file_path, grid_model, no_impute, **kwargs
    ):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.extract`

        :param list region: list of regions to download wind farm data for
        :param str start_date: date designating when to start the data download
        :param str end_date: date designating when to end the data download
        :param str file_path: file location on local filesystem on where to store the data
        :param str grid_model: .mat file path for a grid model or a string supported by
            `powersimdata.input.grid.Grid.SUPPORTED_MODELS`
        :param bool no_impute: flag used to avoid naive gaussian imputing of missing data
        """
        assert datetime.strptime(start_date, DATE_FMT) <= datetime.strptime(
            end_date, DATE_FMT
        )

        grid = Grid(region, source=grid_model)
        wind_farms = grid.plant.groupby("type").get_group("wind")
        data, missing = rap.retrieve_data(
            wind_farms, start_date=start_date, end_date=end_date
        )
        if len(missing) > 0:
            logging.warning(f"There are {len(missing)} files missing")
            # Imputing any missing data in place
            if not no_impute:
                logging.warning("Performing naive gaussian imputing of missing data")
                impute.gaussian(data, wind_farms, inplace=True)
        data.to_pickle(file_path)

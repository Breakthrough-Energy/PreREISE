import logging
from datetime import datetime

from powersimdata.input.grid import Grid

from prereise.cli.constants import DATE_FMT
from prereise.cli.data_sources.data_source import DataSource
from prereise.cli.helpers import validate_date, validate_file_path
from prereise.gather.winddata.rap import rap


class WindData(DataSource):
    @property
    def command_name(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_name`

        :return: (*str*)
        """
        return "wind_data"

    @property
    def command_help(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.command_help`

        :return: (*str*)
        """
        return "Download wind data"

    @property
    def extract_arguments(self):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.extract_arguments`

        :return: (*str*)
        """
        return [
            {
                "command_flags": ["--region", "-r"],
                "required": True,
                "choices": ["Texas", "Eastern", "Western"],
                "type": str,
                "action": "append",
            },
            {
                "command_flags": ["--start_date", "-sd"],
                "required": True,
                "type": validate_date,
                "help": "The start date for the data download in format 'YYYY-MM-DD'",
            },
            {
                "command_flags": ["--end_date", "-ed"],
                "required": True,
                "type": validate_date,
                "help": "The end date for the data download in format 'YYYY-MM-DD'",
            },
            {
                "command_flags": ["--file_path", "-fp"],
                "required": True,
                "type": validate_file_path,
                "help": "The file path to store the downloaded data. Must include filename "
                "and .pkl file extension.",
            },
        ]

    def extract(self, region, start_date, end_date, file_path, **kwargs):
        """See :py:func:`prereise.cli.data_sources.data_source.DataSource.extract`

        :param list region: list of regions to download wind farm data for
        :param str start_date: date designating when to start the data download
        :param str end_date: date designating when to end the data download
        :param str file_path: file location on local filesystem on where to store the data
        """
        regions = list(set(region))
        assert datetime.strptime(start_date, DATE_FMT) <= datetime.strptime(
            end_date, DATE_FMT
        )

        grid = Grid(regions)
        wind_farms = grid.plant.groupby("type").get_group("wind")
        data, missing = rap.retrieve_data(
            wind_farms, start_date=start_date, end_date=end_date
        )
        if len(missing) > 0:
            logging.warning(f"There are {len(missing)} files missing")
        data.to_pickle(file_path)

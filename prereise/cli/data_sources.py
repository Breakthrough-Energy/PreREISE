import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime

from powersimdata.input.grid import Grid

from prereise.cli.constants import DATE_FMT
from prereise.cli.helpers import validate_date, validate_file_path
from prereise.gather.winddata.rap import rap


class DataSource(metaclass=ABCMeta):
    """Abstract class that defines a strict interface
    that future data sources need to follow in order
    to seamlessly integrate with the parser.

    :param abc.ABCMeta metaclass: defaults to ABCMeta
    """

    @property
    @abstractmethod
    def command_name(self):
        """String command name for argparse. See add_parser function
        at `this link <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_.
        """
        pass

    @property
    @abstractmethod
    def command_help(self):
        """String with a help description for the command. See add_parser function
        at `this link <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_
        for more details
        """
        pass

    @property
    @abstractmethod
    def extract_arguments(self):
        """List of dictionaries defining the various flags and parameters
        the user needs to pass into this command, which are
        subsequently passed to the below extract function.
        See `add_argument <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument>`_
        to understand what is acceptable/unacceptable in these
        dictionaries.
        """
        pass

    @abstractmethod
    def extract(self):
        """Function that takes in the arguments defined in
        the above property extract_arguments and downloads
        the appropriate data and saves it somewhere.
        """
        pass


class WindData(DataSource):
    @property
    def command_name(self):
        """See :py:func:`prereise.cli.data_sources.DataSource.command_name`

        :return: (*str*)
        """
        return "wind_data"

    @property
    def command_help(self):
        """See :py:func:`prereise.cli.data_sources.DataSource.command_help`

        :return: (*str*)
        """
        return "Download wind data"

    @property
    def extract_arguments(self):
        """See :py:func:`prereise.cli.data_sources.DataSource.extract_arguments`

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
        """See :py:func:`prereise.cli.data_sources.DataSource.extract`

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


def get_data_sources_list():
    """Provides list of all data sources

    :return: (*list*)
    """
    return [WindData()]

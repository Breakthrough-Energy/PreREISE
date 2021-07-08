import logging
import os
from datetime import datetime

from powersimdata.input.grid import Grid

from prereise.cli.constants import DATE_FMT, YEAR_FMT


def validate_grid_model(grid_model):
    """Helper function to validate grid model parameter. Does
    NOT validate the actual contents of the grid file.

    :param str grid_model: file path to a .mat file that represents
        the grid, or a supported default grid selection
    :return: (*str*) -- validated grid model
    """
    if grid_model in Grid.SUPPORTED_MODELS:
        return grid_model

    if grid_model.endswith(".mat") and os.path.isfile(grid_model):
        return grid_model

    all_supported_models = ", ".join(Grid.SUPPORTED_MODELS)

    raise ValueError(
        f"grid_model must be either a valid .mat file path or a valid selection of {all_supported_models}"
    )


def validate_date(date_string):
    """Helper function to validate date strings

    :param str date_string: date in string format to be validated
    :return: (*str*) -- validated date string
    """
    datetime.strptime(date_string, DATE_FMT)
    return date_string


def validate_year(year_string):
    """Helper function to validate year strings

    :param str year_string: year in string format to be validated
    :return: (*str*) -- validated year string
    """
    datetime.strptime(year_string, YEAR_FMT)
    return year_string


def validate_file_path(file_path):
    """Helper function to validate file paths

    :param str file_path: path include filename for where
        to save the file
    :raises ValueError: if the provided file path is not accessible
    :return: (*str*) -- validated file path
    """
    if not os.access(os.path.dirname(file_path), os.W_OK):
        raise ValueError("Please choose a valid file path")
    if os.path.isdir(file_path):
        raise ValueError("Please provide a filename with a .pkl extension")
    if os.path.isfile(file_path):
        logging.warning("File exists! Will overwrite file at end of download!")
    return file_path


def add_data_source_to_download_parser(data_source, subparsers):
    """Helper function that adds an additional source of data
    that the user can interact with and download via the
    command line tool

    :param prereise.cli.data_sources.data_source.DataSource data_source: an
        instance of a class that implements the abstract class DataSource
    :param argparse.ArgumentParser subparsers: subparser object that implements command
        line interface functionality
    """
    subparser = subparsers.add_parser(
        data_source.command_name, help=data_source.command_help
    )
    for argument in data_source.extract_arguments:
        command = argument.pop("command_flags")
        subparser.add_argument(*command, **argument)
    subparser.set_defaults(func=data_source.extract)

from unittest.mock import MagicMock, patch

import pytest

from prereise.cli.helpers import (
    add_data_source_to_download_parser,
    validate_date,
    validate_file_path,
)


@pytest.fixture
def data_source():
    data_source_mock = MagicMock()
    data_source_mock.command_name = "command_name"
    data_source_mock.command_help = "command_help"
    data_source_mock.extract_arguments = [
        {"command_flags": ["--command"], "keyarg": "value"}
    ]
    data_source_mock.extract = MagicMock()
    return data_source_mock


def test_validate_date():
    date = "2020-01-03"
    assert validate_date(date) == date


def test_validate_date_bad_date():
    with pytest.raises(ValueError):
        validate_date("2020-01-49")


@patch("prereise.cli.helpers.os")
def test_validate_file_path(os):
    file_path = "somefilepath"
    os.access.return_value = True
    os.path.isdir.return_value = False
    assert validate_file_path(file_path) == file_path


@patch("prereise.cli.helpers.os")
def test_validate_file_path_bad_path(os):
    os.access.return_value = False
    with pytest.raises(ValueError) as e:
        validate_file_path("somefilepath")
    assert "Please choose a valid file path" in str(e.value)


@patch("prereise.cli.helpers.os")
def test_validate_file_path_is_direcotry(os):
    os.access.return_value = True
    os.path.isdir.return_value = True
    with pytest.raises(ValueError) as e:
        validate_file_path("/")
    assert "Please provide a filename with a .pkl extension" in str(e.value)


def test_add_data_source_to_download_parser(data_source):
    parser = MagicMock()
    subparsers = MagicMock()
    subparser = MagicMock()
    subparsers.add_parser.return_value = subparser
    parser.add_subparsers.return_value = subparsers
    add_data_source_to_download_parser(data_source, parser)
    subparsers.add_parser.assert_called_with(
        data_source.command_name, help=data_source.command_help
    )
    subparser.add_argument.assert_called_with("--command", keyarg="value")

import pytest

from prereise.cli.data_sources.exceptions import CommandNotSupportedError
from prereise.cli.data_sources.hydro_data import HydroData


def test_hydro_data_happy_path():
    with pytest.raises(CommandNotSupportedError):
        HydroData().extract()

import pytest

from prereise.cli.data_sources.demand_data import DemandData
from prereise.cli.data_sources.exceptions import CommandNotSupportedError


def test_demand_data_happy_path():
    with pytest.raises(CommandNotSupportedError):
        DemandData().extract()

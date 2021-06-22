from prereise.cli.data_sources import get_data_sources_list
from prereise.cli.data_sources.wind_data import WindData


def test_get_data_sources_list():
    data_sources_list = get_data_sources_list()
    assert isinstance(data_sources_list[0], WindData)

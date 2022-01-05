from prereise.cli.data_sources import get_data_sources_list
from prereise.cli.data_sources.solar_data import (
    SolarDataGriddedAtmospheric,
    SolarDataNationalSolarRadiationDatabase,
)
from prereise.cli.data_sources.wind_data import WindDataRapidRefresh


def test_get_data_sources_list():
    data_sources_list = get_data_sources_list()
    assert isinstance(data_sources_list[0], WindDataRapidRefresh)
    assert isinstance(data_sources_list[1], SolarDataGriddedAtmospheric)
    assert isinstance(data_sources_list[2], SolarDataNationalSolarRadiationDatabase)

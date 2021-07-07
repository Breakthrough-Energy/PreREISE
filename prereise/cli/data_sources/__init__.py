from prereise.cli.data_sources.solar_data import (
    SolarDataGriddedAtmospheric,
    SolarDataNationalSolarRadiationDatabase,
)
from prereise.cli.data_sources.wind_data import WindDataRapidRefresh


def get_data_sources_list():
    """Provides list of all data sources

    :return: (*list*)
    """
    return [
        WindDataRapidRefresh(),
        SolarDataGriddedAtmospheric(),
        SolarDataNationalSolarRadiationDatabase(),
    ]

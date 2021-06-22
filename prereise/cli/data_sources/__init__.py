from prereise.cli.data_sources.wind_data import WindData


def get_data_sources_list():
    """Provides list of all data sources

    :return: (*list*)
    """
    return [WindData()]

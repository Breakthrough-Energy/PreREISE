import pandas as pd


def to_reise(data):
    """Format data for REISE.

    :param pandas.DataFrame data: data frame as returned by
        :func:`prereise.gather.solardata.nsrdb.naive.retrieve_data`,
        :func:`prereise.gather.solardata.ga_wind.ga_wind.retrieve_data`
    :return: (*pandas.DataFrame*) -- data frame formatted for REISE.
    :raises TypeError: if *'data'* is not a data frame.
    :raises ValueError: if *'Pout'*, *'plant_id'*, *'ts'* and *'ts_id'* are not among
        the columns.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas.DataFrame")
    if not {"Pout", "plant_id", "ts", "ts_id"}.issubset(data.columns):
        raise ValueError(
            "data frame must have Pout, plant_id, ts and ts_id among columns"
        )
    ts = data["ts"].unique()
    plant_id = data[data.ts_id == 1].plant_id.values

    profile = None
    for i in range(1, max(data.ts_id) + 1):
        data_tmp = pd.DataFrame(
            {"Pout": data[data.ts_id == i].Pout.values}, index=plant_id
        )
        if i == 1:
            profile = data_tmp.T
        else:
            profile = pd.concat([profile, data_tmp.T], sort=False, ignore_index=True)

    profile.set_index(ts, inplace=True)
    profile.index.name = "UTC"

    return profile


def get_plant_id_unique_location(plant):
    """Identify unique location among plants.

    :param pandas.DataFrame plant: plant data frame.
    :return: (*dict*) -- keys are coordinates. Values is a list of *'plant_id'*.
    :raises TypeError: if *'plant'* is not a data frame.
    :raises ValueError: if *'plant_id'* is not the index and/or *'lat'* and *'lon'* are
        not among the columns.
    """
    if not isinstance(plant, pd.DataFrame):
        raise TypeError("plant must be a pandas.DataFrame")
    if not (plant.index.name == "plant_id" and {"lat", "lon"}.issubset(plant.columns)):
        raise ValueError(
            "data frame must have plant_id as index and lat and lon among columns"
        )
    return plant.groupby(["lon", "lat"]).groups

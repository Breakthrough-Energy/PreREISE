from collections import OrderedDict

import pandas as pd


def to_reise(data):
    """Format data for REISE.

    :param pandas.DataFrame data: data frame as returned by
        :func:`prereise.gather.solardata.nsrdb.naive.retrieve_data`,
        :func:`prereise.gather.solardata.nsrdb.sam.retrieve_data` or
        :func:`prereise.gather.solardata.ga_wind.ga_wind.retrieve_data`
    :return: (*pandas.DataFrame*) -- data frame formatted for REISE.
    """

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
            profile = profile.append(data_tmp.T, sort=False, ignore_index=True)

    profile.set_index(ts, inplace=True)
    profile.index.name = "UTC"

    return profile


def get_plant_info_unique_location(plant):
    """Identify unique location and return relevant information of plants at
        location.

    :param pandas.DataFrame plant: plant data frame.
    :return: (*dict*) -- keys are coordinates of location. Values is a list of
        2-tuple giving the plant id at location along with its capacity.
    """
    n_target = len(plant)

    # Identify unique location
    coord = OrderedDict()
    for i in range(n_target):
        key = (str(plant.lon.values[i]), str(plant.lat.values[i]))
        if key not in coord.keys():
            coord[key] = [(plant.index[i], plant.Pmax.values[i])]
        else:
            coord[key].append((plant.index[i], plant.Pmax.values[i]))

    return coord

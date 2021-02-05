import numpy as np
import pandas as pd
from tqdm import tqdm

from prereise.gather.solardata.helpers import get_plant_id_unique_location
from prereise.gather.solardata.nsrdb.nrel_api import NrelApi


def retrieve_data(solar_plant, email, api_key, year="2016"):
    """Retrieve irradiance data from NSRDB and calculate the power output
    using a simple normalization.

    :param pandas.DataFrame solar_plant: plant data frame.
    :param str email: email used to `sign up <https://developer.nrel.gov/signup/>`_.
    :param str api_key: API key.
    :param str year: year.
    :return: (*pandas.DataFrame*) -- data frame with *'Pout'*, *'plant_id'*,
        *'ts'* and *'ts_id'* as columns. Values are power output for a 1MW generator.
    """

    # Identify unique location
    coord = get_plant_id_unique_location(solar_plant)

    api = NrelApi(email, api_key)

    data = pd.DataFrame({"Pout": [], "plant_id": [], "ts": [], "ts_id": []})

    for key in tqdm(coord.keys(), total=len(coord)):
        lat, lon = key[1], key[0]
        data_loc = api.get_psm3_at(
            lat, lon, attributes="ghi", year=year, leap_day=True
        ).data_resource
        ghi = data_loc.GHI.values
        data_loc = pd.DataFrame({"Pout": ghi})
        data_loc["Pout"] /= max(ghi)
        data_loc["ts_id"] = range(1, len(ghi) + 1)
        data_loc["ts"] = pd.date_range(start=year, end=str(int(year) + 1), freq="H")[
            :-1
        ]

        for i in coord[key]:
            data_site = data_loc.copy()
            data_site["plant_id"] = i

            data = data.append(data_site, ignore_index=True, sort=False)

    data["plant_id"] = data["plant_id"].astype(np.int32)
    data["ts_id"] = data["ts_id"].astype(np.int32)

    data.sort_values(by=["ts_id", "plant_id"], inplace=True)
    data.reset_index(inplace=True, drop=True)

    return data

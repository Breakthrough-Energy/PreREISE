import numpy as np
import pandas as pd
from tqdm import tqdm

from prereise.gather.solardata.helpers import get_plant_info_unique_location


def retrieve_data(solar_plant, email, api_key, year="2016"):
    """Retrieve irradiance data from NSRDB and calculate the power output
    using a simple normalization.

    :param pandas.DataFrame solar_plant: data frame with *'lat'*, *'lon'* and
        *'Pmax' as columns and *'plant_id'* as index.
    :param str email: email used for API key
        `sign up <https://developer.nrel.gov/signup/>`_.
    :param str api_key: API key.
    :param str year: year.
    :return: (*pandas.DataFrame*) -- data frame with *'Pout'*, *'plant_id'*,
        *'ts'* and *'ts_id'* as columns. The power output is in MWh.
    """

    # Identify unique location
    coord = get_plant_info_unique_location(solar_plant)

    # Build query
    attributes = "ghi"
    leap_day = "true"
    interval = "60"
    utc = "true"

    # URL
    url = "http://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv?"
    url = url + "api_key={key}".format(key=api_key)

    payload = (
        "names={year}".format(year=year)
        + "&"
        + "leap_day={leap}".format(leap=leap_day)
        + "&"
        + "interval={interval}".format(interval=interval)
        + "&"
        + "utc={utc}".format(utc=utc)
        + "&"
        + "email={email}".format(email=email)
        + "&"
        + "attributes={attr}".format(attr=attributes)
    )

    data = pd.DataFrame({"Pout": [], "plant_id": [], "ts": [], "ts_id": []})

    for key in tqdm(coord.keys(), total=len(coord)):
        query = "wkt=POINT({lon}%20{lat})".format(lon=key[0], lat=key[1])
        data_loc = pd.read_csv(url + "&" + payload + "&" + query, skiprows=2)
        ghi = data_loc.GHI.values
        data_loc = pd.DataFrame({"Pout": ghi})
        data_loc["Pout"] /= max(ghi)
        data_loc["ts_id"] = range(1, len(ghi) + 1)
        data_loc["ts"] = pd.date_range(start=year, end=str(int(year) + 1), freq="H")[
            :-1
        ]

        for i in coord[key]:
            data_site = data_loc.copy()
            data_site["Pout"] *= i[1]
            data_site["plant_id"] = i[0]

            data = data.append(data_site, ignore_index=True, sort=False)

    data["plant_id"] = data["plant_id"].astype(np.int32)
    data["ts_id"] = data["ts_id"].astype(np.int32)

    data.sort_values(by=["ts_id", "plant_id"], inplace=True)
    data.reset_index(inplace=True, drop=True)

    return data

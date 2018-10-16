from collections import OrderedDict

import dateutil
import h5pyd
import numpy as np
import pandas as pd
from tqdm import tqdm

from .helpers import ll2ij


def retrieve_data(solar_plant, hs_api_key,
                  start_date='2007-01-01',
                  end_date='2014-01-01'):
    """Retrieve irradiance data from Gridded Atmospheric Wind Integration \ 
        National Dataset.

    :param solar_plant: pandas DataFrame of solar plants.
    :param year: year.
    :return: pandas DataFrame with the columns: plant ID, timestamp ID and \ 
        power output (MW).
    """

    # Information on solar plants
    n_target = len(solar_plant)

    # Identify unique location
    coord = OrderedDict()
    for i in range(n_target):
        key = (str(solar_plant.lon.values[i]),
               str(solar_plant.lat.values[i]))
        if key not in coord.keys():
            coord[key] = [(solar_plant.index[i],
                           solar_plant.GenMWMax.values[i])]
        else:
            coord[key].append((solar_plant.index[i],
                               solar_plant.GenMWMax.values[i]))

    # Build query
    hs_endpoint = 'https://developer.nrel.gov/api/hsds/'
    hs_username = None
    hs_password = None

    f = h5pyd.File("/nrel/wtk-us.h5", 'r',
                   username=hs_username,
                   password=hs_password,
                   endpoint=hs_endpoint,
                   api_key=hs_api_key)

    # Get coordinates of nearest location
    lat_origin, lon_origin = f['coordinates'][0][0]
    ij = {}
    for key in coord.keys():
        ij[key] = ll2ij(lon_origin, lat_origin, key[0], key[1])

    # Extract time serie
    dt = f['datetime']
    dt = pd.DataFrame({'datetime': dt[:]})
    dt['datetime'] = dt['datetime'].apply(dateutil.parser.parse)

    dt_range = dt.loc[(dt.datetime >= start_date) & (dt.datetime < end_date)]

    data = pd.DataFrame({'Pout': [], 'plantID': [], 'ts': [], 'tsID': []})

    for (key, val) in tqdm(ij.items(), total=len(ij)):
        ghi = f['GHI'][min(dt_range.index):max(dt_range.index)+1,
                       val[0], val[1]]
        data_loc = pd.DataFrame({'Pout': ghi})
        data_loc['Pout'] /= max(ghi)
        data_loc['tsID'] = range(1, len(ghi)+1)
        data_loc['ts'] = pd.date_range(start=start_date,
                                       end=end_date,
                                       freq='H')[:-1]

        for i in coord[key]:
            data_site = data_loc.copy()
            data_site['Pout'] *= i[1]
            data_site['plantID'] = i[0]

            data = data.append(data_site, ignore_index=True, sort=False)

    data['plantID'] = data['plantID'].astype(np.int32)
    data['tsID'] = data['tsID'].astype(np.int32)

    data.sort_values(by=['tsID', 'plantID'], inplace=True)
    data.reset_index(inplace=True, drop=True)

    return data

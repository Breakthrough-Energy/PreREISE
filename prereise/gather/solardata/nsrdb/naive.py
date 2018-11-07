from collections import OrderedDict

import numpy as np
import pandas as pd
from tqdm import tqdm


def retrieve_data(solar_plant, email, api_key, year='2016'):
    """Retrieve irradiance data from NSRDB and calculate the power output \ 
        using a simple normalization.

    :param pandas solar_plant: data frame with *'lat'*, *'lon'* and \ 
        *'GenMWMax' as columns and *'PlantID'* as index.
    :param string year: year.
    :return: data frame with the following structure: ['Pout', \ 
        'plantID', 'ts', 'tsID']. The power output is in MW.
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
    attributes = 'ghi'
    leap_day = 'true'
    interval = '60'
    utc = 'true'

    # URL
    url = 'http://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv?'
    url = url + 'api_key={key}'.format(key=api_key)

    payload = 'names={year}'.format(year=year) + '&' + \
        'leap_day={leap}'.format(leap=leap_day) + '&' + \
        'interval={interval}'.format(interval=interval) + '&' + \
        'utc={utc}'.format(utc=utc) + '&' + \
        'email={email}'.format(email=email) + '&' + \
        'attributes={attr}'.format(attr=attributes)

    data = pd.DataFrame({'Pout': [], 'plantID': [], 'ts': [], 'tsID': []})

    for key in tqdm(coord.keys(), total=len(coord)):
        query = 'wkt=POINT({lon}%20{lat})'.format(lon=key[0], lat=key[1])
        data_loc = pd.read_csv(url + '&' + payload + '&' + query, skiprows=2)
        ghi = data_loc.GHI.values
        data_loc = pd.DataFrame({'Pout': ghi})
        data_loc['Pout'] /= max(ghi)
        data_loc['tsID'] = range(1, len(ghi)+1)
        data_loc['ts'] = pd.date_range(start=year,
                                       end=str(int(year)+1),
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

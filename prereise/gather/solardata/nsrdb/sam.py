from collections import OrderedDict
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from py3samsdk import PySSC
from tqdm import tqdm

ssc_lib = 'U:\\SAM\\2017-9-5-r4\\win64\\'


def get_frac(zone):
    """Return fraction of solar plants with fix, single-axis, double-axis in \ 
        zone.

    :param string zone: zone.
    :return: list of coefficients.
    """
 
    western = ['Arizona', 'Bay Area', 'Central California', 'Colorado',
               'El Paso', 'Idaho', 'Montana', 'Nevada', 'New Mexico',
               'Northern California', 'Oregon', 'Southeast California',
               'Southwest California', 'Utah', 'Washington', 'Wyoming']
    all = western
    if zone in all:
        return [0.2870468, 0.6745755, 0.0383777]
    else:
        print("%s is incorrect. Possible zones are: %s" % (zone, all))
        raise Exception('Invalid zone')



def retrieve_data(solar_plant, email, api_key, year='2016'):
    """Retrieve irradiance data from NSRDB and calculate the power output \ 
        using the System Advisor Model (SAM).

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
    attributes = 'dhi,dni,wind_speed,air_temperature'
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

    tf = TimezoneFinder()
    for key in tqdm(coord.keys(), total=len(coord)):
        query = 'wkt=POINT({lon}%20{lat})'.format(lon=key[0], lat=key[1])

        info = pd.read_csv(url+'&'+payload+'&'+query, nrows=1)
        timezone, elevation = info['Local Time Zone'], info['Elevation']

        data_loc = pd.read_csv(url + '&' + payload + '&' + query, skiprows=2)

        data_loc = pd.DataFrame({'tsID': range(1, len(ghi)+1)}) 
        data_loc['ts'] = pd.date_range(start=year, end=str(int(year)+1), 
                                       freq='H')[:-1]

        try:
             leap_day = pd.Timestamp('%s-02-29-00' % year).dayofyear * 24
             local_time = data_loc['ts'].values

             local_time[leap_day-24:leap_day] = pd.date_range(
                start='%s-02-28-00' % year, end='%s-02-28-23' % year, freq='H')
        except:
            pass
            
        local_time = data_loc['ts'].values - timedelta(hours=timezone)
        if local_time
        
        # SAM
        ssc = PySSC(ssc_lib)

        resource = ssc.data_create()
        ssc.data_set_number(resource, 'lat', key[1])
        ssc.data_set_number(resource, 'lon', key[0])
        ssc.data_set_number(resource, 'tz', timezone)
        ssc.data_set_number(resource, 'elev', elevation)
        ssc.data_set_array(resource, 'year', local_time.year)
        ssc.data_set_array(resource, 'month', local_time.month)
        ssc.data_set_array(resource, 'day', local_time.day)
        ssc.data_set_array(resource, 'hour', local_time.hour)
        ssc.data_set_array(resource, 'minute', local_time.minute)
        ssc.data_set_array(resource, 'dn', data_loc['DNI'])
        ssc.data_set_array(resource, 'df', data_loc['DHI'])
        ssc.data_set_array(resource, 'wspd', data_loc['Wind Speed'])
        ssc.data_set_array(resource, 'tdry', data_loc['Temperature'])

        for i in coord[key]:
            Pout = 0
            zone = solar_plant.loc[i[0]].ZoneName
            for j, type in enumerate([0, 2, 3]):
                core = ssc.data_create()
                ssc.data_set_table(core, 'solar_resource_data', resource)
                ssc.data_set_number(core, 'system_capacity', i[1])
                ssc.data_set_number(core, 'dc_ac_ratio', 1.1)
                ssc.data_set_number(core, 'tilt', 30)
                ssc.data_set_number(core, 'azimuth', 180)
                ssc.data_set_number(core, 'inv_eff', 94)
                ssc.data_set_number(core, 'losses', 14)
                ssc.data_set_number(core, 'array_type', type)
                ssc.data_set_number(core, 'gcr', 0.4)
                ssc.data_set_number(core, 'adjust:constant', 0)
                
                mod = ssc.module_create('pvwattsv5')
                ssc.module_exec(mod, core)
                Pout += get_frac(zone)[j] * \
                        np.array(ssc.data_get_array(core, 'gen'))
                ssc.data_free(core)
                ssc.module_free(mod)

            data_site = data_loc.copy()
            data_site['Pout'] = Pout
            data_site['plantID'] = i[0]

            data = data.append(data_site, ignore_index=True, sort=False)

        ssc.data_free(resource)

    data['plantID'] = data['plantID'].astype(np.int32)
    data['tsID'] = data['tsID'].astype(np.int32)

    data.sort_values(by=['tsID', 'plantID'], inplace=True)
    data.reset_index(inplace=True, drop=True)

    return data

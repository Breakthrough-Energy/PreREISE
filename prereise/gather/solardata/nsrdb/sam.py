from collections import OrderedDict
from datetime import timedelta

import numpy as np
import pandas as pd
from py3samsdk import PySSC
from tqdm import tqdm


def get_frac(interconnect):
    """Returns fraction of solar plants using no tracking (fix), single-axis or
        double-axis tracking in specified interconnection.

    :param str interconnect: interconnection.
    raise ValueError: if interconnection does not exist.
    :return: (*list*) -- three coefficients. One for each technology.
    """

    if interconnect is 'Western':
        return [0.2870468, 0.6745755, 0.0383777]
    elif interconnect is 'Texas':
        return [0.08, 0.46, 0.46]
    elif interconnect is 'Eastern':
        return [0.713, 0.286, 0.001]
    else:
        raise Exception("Wrong interconnect. "
                        "Choose from Eastern | Western | Texas")


def retrieve_data(solar_plant, email, api_key, ssc_lib, year='2016'):
    """Retrieves irradiance data from NSRDB and calculate the power output using
        the System Adviser Model (SAM).

    :param pandas.DataFrame solar_plant: data frame with *'lat'*, *'lon'* and
        *'GenMWMax' as columns and *'plant_id'* as index.
    :param str email: email used for API key \ 
        `sign up <https://developer.nrel.gov/signup/>`_.
    :param str api_key: API key.
    :param str ssc_lib: path to System Adviser Model (SAM) SAM Simulation Core
        (SSC) library.
    :param str year: year.
    :return: (*pandas.DataFrame*) -- data frame with *'Pout'*, *'plant_id'*,
        *'ts'* and *'ts_id'* as columns. The power output is in MWh.
    """

    # SAM only takes 365 days.
    try:
        leap_day = (pd.Timestamp('%s-02-29-00' % year).dayofyear - 1) * 24
        is_leap_year = True
        dates = pd.date_range(start="%s-01-01-00" % 2015,
                              freq='H', periods=365*24)
        dates = dates.map(lambda t: t.replace(year=int(year)))
    except ValueError:
        leap_day = None
        is_leap_year = False
        dates = pd.date_range(start="%s-01-01-00" % year,
                              freq='H', periods=365*24)

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
    interval = '60'
    utc = 'true'

    # URL
    url = 'http://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv?'
    url = url + 'api_key={key}'.format(key=api_key)

    payload = 'names={year}'.format(year=year) + '&' + \
        'leap_day={leap}'.format(leap='false') + '&' + \
        'interval={interval}'.format(interval=interval) + '&' + \
        'utc={utc}'.format(utc=utc) + '&' + \
        'email={email}'.format(email=email) + '&' + \
        'attributes={attr}'.format(attr=attributes)

    data = pd.DataFrame({'Pout': [], 'plant_id': [], 'ts': [], 'ts_id': []})

    for key in tqdm(coord.keys(), total=len(coord)):
        query = 'wkt=POINT({lon}%20{lat})'.format(lon=key[0], lat=key[1])

        info = pd.read_csv(url+'&'+payload+'&'+query, nrows=1)
        tz, elevation = info['Local Time Zone'], info['Elevation']

        data_resource = pd.read_csv(url + '&' + payload + '&' + query,
                                    skiprows=2)
        data_resource.set_index(dates + timedelta(hours=int(tz.values[0])),
                                inplace=True)

        # SAM
        ssc = PySSC(ssc_lib)

        resource = ssc.data_create()
        ssc.data_set_number(resource, 'lat', float(key[1]))
        ssc.data_set_number(resource, 'lon', float(key[0]))
        ssc.data_set_number(resource, 'tz', tz)
        ssc.data_set_number(resource, 'elev', elevation)
        ssc.data_set_array(resource, 'year', data_resource.index.year)
        ssc.data_set_array(resource, 'month', data_resource.index.month)
        ssc.data_set_array(resource, 'day', data_resource.index.day)
        ssc.data_set_array(resource, 'hour', data_resource.index.hour)
        ssc.data_set_array(resource, 'minute', data_resource.index.minute)
        ssc.data_set_array(resource, 'dn', data_resource['DNI'])
        ssc.data_set_array(resource, 'df', data_resource['DHI'])
        ssc.data_set_array(resource, 'wspd', data_resource['Wind Speed'])
        ssc.data_set_array(resource, 'tdry', data_resource['Temperature'])

        for i in coord[key]:
            data_site = pd.DataFrame({'ts': pd.date_range(
                                                start='%s-01-01-00' % year,
                                                end='%s-12-31-23' % year,
                                                freq='H')})
            data_site['ts_id'] = range(1, len(data_site)+1)
            data_site['plant_id'] = i[0]
            interconnect = solar_plant.loc[i[0]].interconnect

            power = 0
            for j, axis in enumerate([0, 2, 4]):
                core = ssc.data_create()
                ssc.data_set_table(core, 'solar_resource_data', resource)
                ssc.data_set_number(core, 'system_capacity', i[1] * 1000.)
                ssc.data_set_number(core, 'dc_ac_ratio', 1.1)
                ssc.data_set_number(core, 'tilt', 30)
                ssc.data_set_number(core, 'azimuth', 180)
                ssc.data_set_number(core, 'inv_eff', 94)
                ssc.data_set_number(core, 'losses', 14)
                ssc.data_set_number(core, 'array_type', axis)
                ssc.data_set_number(core, 'gcr', 0.4)
                ssc.data_set_number(core, 'adjust:constant', 0)

                mod = ssc.module_create('pvwattsv5')
                ssc.module_exec(mod, core)

                if j == 0:
                    power = get_frac(interconnect)[j] * \
                            np.array(ssc.data_get_array(core, 'gen')) / 1000
                else:
                    power = power + get_frac(interconnect)[j] * \
                            np.array(ssc.data_get_array(core, 'gen')) / 1000

                ssc.data_free(core)
                ssc.module_free(mod)

            if is_leap_year is True:
                data_site['Pout'] = np.insert(power, leap_day,
                                              power[leap_day-24:leap_day])
            else:
                data_site['Pout'] = power

            data = data.append(data_site, ignore_index=True, sort=False)

        ssc.data_free(resource)

    data['plant_id'] = data['plant_id'].astype(np.int32)
    data['ts_id'] = data['ts_id'].astype(np.int32)

    data.sort_values(by=['ts_id', 'plant_id'], inplace=True)
    data.reset_index(inplace=True, drop=True)

    return data

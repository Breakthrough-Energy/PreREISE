import datetime
import os
import time
from collections import OrderedDict

import numpy as np
import pandas as pd
import requests
from netCDF4 import Dataset
from tqdm import tqdm

from prereise.gather.winddata.rap.helpers import ll2uv, angular_distance
from prereise.gather.winddata.rap.power_curves import get_power
from prereise.gather.winddata.rap.power_curves import get_turbine_power_curves
from prereise.gather.winddata.rap.power_curves import get_state_power_curves
from powersimdata.utility.constants import ZONE_ID_TO_STATE


def retrieve_data(wind_farm, start_date='2016-01-01', end_date='2016-12-31'):
    """Retrieve wind speed data from NOAA's server.

    :param pandas.DataFrame wind_farm: data frame with *'lat'*, *'lon'*,
        *'Pmax'*, and *'type'* as columns and *'plant_id'*  as index.
    :param str start_date: start date.
    :param str end_date: end date (inclusive).
    :return: (*tuple*) -- First element is a pandas data frame with
        *'plant_id'*, *'U'*, *'V'*, *'Pout'*, *'ts'* and *'ts_id'* as columns.
        The power output is in MWh and the U and V component of the wind speed
        80-m above ground level are in m/s. Second element is a list of missing
        files.
    """
    # Define query box boundaries using the most northern, southern, eastern
    # and western. Add 1deg in each direction
    north_box = wind_farm.lat.max() + 1
    south_box = wind_farm.lat.min() - 1
    west_box = wind_farm.lon.min() - 1
    east_box = wind_farm.lon.max() + 1

    # Information on wind turbines & state average tubrine curves
    tpc = get_turbine_power_curves()
    spc = get_state_power_curves()

    # Information on wind farms
    n_target = len(wind_farm)

    lon_target = wind_farm.lon.values
    lat_target = wind_farm.lat.values
    id_target = wind_farm.index.values
    capacity_target = wind_farm.Pmax.values
    state_target = ['Offshore' if wind_farm.loc[i].type == 'wind_offshore'
                    else ZONE_ID_TO_STATE[wind_farm.loc[i].zone_id]
                    for i in id_target]

    # Build query
    link = 'https://www.ncdc.noaa.gov/thredds/ncss/rap130anl/'

    start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    step = datetime.timedelta(days=1)

    files = []
    while start <= end:
        ts = start.strftime('%Y%m%d')
        url = link + ts[:6] + '/' + ts + '/rap_130_' + ts
        for h in range(10000, 12400, 100):
            files.append(url + '_' + str(h)[1:] + '_000.grb2?')
        start += step

    var_u = 'u-component_of_wind_height_above_ground'
    var_v = 'v-component_of_wind_height_above_ground'
    var = 'var=' + var_u + '&' + 'var=' + var_v

    box = 'north=%s&west=%s&east=%s&south=%s' % \
          (north_box, west_box, east_box, south_box) + '&' + \
          'disableProjSubset=on&horizStride=1&addLatLon=true'

    extension = 'accept=netCDF'

    # Download files and fill out data frame
    missing = []
    target2grid = OrderedDict()
    data = pd.DataFrame({'plant_id': [],
                         'U': [],
                         'V': [],
                         'Pout': [],
                         'ts': [],
                         'ts_id': []})
    dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    step = datetime.timedelta(hours=1)

    for i, file in tqdm(enumerate(files), total=len(files)):
        if i != 0 and i % 2500 == 0:
            time.sleep(300)
        query = file + var + '&' + box + '&' + extension
        request = requests.get(query)

        data_tmp = pd.DataFrame({'plant_id': id_target,
                                 'ts': [dt] * n_target,
                                 'ts_id': [i+1] * n_target})

        if request.status_code == 200:
            with open('tmp.nc', 'wb') as f:
                f.write(request.content)
            tmp = Dataset('tmp.nc', 'r')
            lon_grid = tmp.variables['lon'][:].flatten()
            lat_grid = tmp.variables['lat'][:].flatten()
            u_wsp = tmp.variables[var_u][0, 1, :, :].flatten()
            v_wsp = tmp.variables[var_v][0, 1, :, :].flatten()

            n_grid = len(lon_grid)
            if data.empty:
                # The angular distance is calculated once. The target to grid
                # correspondence is stored in a dictionary.
                for j in range(n_target):
                    uv_target = ll2uv(lon_target[j], lat_target[j])
                    angle = [angular_distance(uv_target,
                             ll2uv(lon_grid[k], lat_grid[k]))
                             for k in range(n_grid)]
                    target2grid[id_target[j]] = np.argmin(angle)

            data_tmp['U'] = [u_wsp[target2grid[id_target[j]]]
                             for j in range(n_target)]
            data_tmp['V'] = [v_wsp[target2grid[id_target[j]]]
                             for j in range(n_target)]
            wspd_target = np.sqrt(pow(data_tmp['U'], 2) + pow(data_tmp['V'], 2))
            power = [capacity_target[j] *
                     get_power(tpc, spc, wspd_target[j], state_target[j])
                     for j in range(n_target)]
            data_tmp['Pout'] = power

            tmp.close()
            os.remove('tmp.nc')
        else:
            missing.append(file)

            # missing data are set to NaN.
            data_tmp['U'] = [np.nan] * n_target
            data_tmp['V'] = [np.nan] * n_target
            data_tmp['Pout'] = [np.nan] * n_target

        data = data.append(data_tmp, ignore_index=True, sort=False)
        dt += step

    # Format data frame
    data['plant_id'] = data['plant_id'].astype(np.int32)
    data['ts_id'] = data['ts_id'].astype(np.int32)

    data.sort_values(by=['ts_id', 'plant_id'], inplace=True)
    data.reset_index(inplace=True, drop=True)

    return data, missing

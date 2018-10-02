import numpy as np
import pandas as pd
import datetime
import math
import requests
import time
import os
from netCDF4 import Dataset
from collections import OrderedDict
from tqdm import tqdm


"""
Collect a set of wind speed data fields from the Rapid Refresh (RAP)
dataset.
Website: https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/rapid-refresh-rap
API: https://www.unidata.ucar.edu/software/thredds/current/tds/reference/NetcdfSubsetServiceReference.html

For each wind farm location in the network, the closest point on the
RAP grid is located and the U and V components of the wind speed at
80-m above ground is retrieved. This operation is repeated for each
1-hour data point. Note that that there are some missing data.
"""



#############
# Functions #
#############

def ll2uv(lon, lat):
    """Convert (longitude, latitude) to unit vector.

    Arguments:
        lon: longitude of the site (in deg.) measured eastward from Greenwich.
        lat: latitude of the site (in deg.). Equator is the zero point.

    Returns:
        3-components (x,y,z) unit vector.
    """
    cos_lat = math.cos(math.radians(lat))
    sin_lat = math.sin(math.radians(lat))
    cos_lon = math.cos(math.radians(lon))
    sin_lon = math.sin(math.radians(lon))

    uv = []
    uv.append(cos_lat * cos_lon)
    uv.append(cos_lat * sin_lon)
    uv.append(sin_lat)

    return uv



def angular_distance(uv1, uv2):
    """Calculate the angular distance between two vectors.

    Arguments:
        uv1: 3-components vector.
        uv2: 3-components vector.

    Returns:
        Angle in degrees.
    """
    cos_angle = uv1[0]*uv2[0] + uv1[1]*uv2[1] + uv1[2]*uv2[2]
    if cos_angle >= 1:
        cos_angle = 1
    if cos_angle <= -1:
        cos_angle = -1
    angle = math.degrees(math.acos(cos_angle))

    return angle



def get_power(wspd, turbine):
    """Convert wind speed to power using NREL turbine power curves.

    Arguments:
        wspd: wind speed (in m/s).
        turbine: class of turbine.

    Returns:
        Normalized power.
    """
    match  = (PowerCurves['Speed bin (m/s)'] <= np.ceil(wspd)) & (PowerCurves['Speed bin (m/s)'] >= np.floor(wspd))
    if not match.any():
        return 0
    values = PowerCurves[turbine][match]
    return np.interp(wspd,PowerCurves[turbine][match].index.values,PowerCurves[turbine][match].values)



###############################################
# Get the plants coordinates, id and GenMWMax #
###############################################

import westernintnet
grid = westernintnet.WesternIntNet()

wind_farm = grid.genbus.groupby('type').get_group('wind')
n_target = len(wind_farm)
print("There are %d wind farms in the Western grid." % n_target)

lon_target = wind_farm.lon.values
lat_target = wind_farm.lat.values
id_target  = wind_farm.index.values
capacity_target = wind_farm.GenMWMax.values

###############
# Build query #
###############

path = 'https://www.ncei.noaa.gov/thredds/ncss/rap130anl/'

start = datetime.datetime.strptime('2016-01-01', '%Y-%m-%d')
end = datetime.datetime.strptime('2016-12-31', '%Y-%m-%d')
step = datetime.timedelta(days=1)

files = []
while start <= end:
    ts = start.strftime('%Y%m%d')
    url = path + '2016'+ ts[4:6] + '/' + ts + '/'
    for h in range(10000,12400,100):
        files.append(url + 'rap_130_' + ts + '_' + str(h)[1:] + '_000.grb2?')
    start += step
print("There are %d files" % len(files))

# Variables
var = 'var=u-component_of_wind_height_above_ground' + '&' + \
      'var=v-component_of_wind_height_above_ground'

# Bounding Box
box = 'north=49&west=-122&east=-102&south=32&disableProjSubset=on&horizStride=1&addLatLon=true'

# Data Format
extension = 'accept=netCDF'



#########################################
# Download files and fill out dataframe #
#########################################


PowerCurves = pd.read_csv('../IECPowerCurves.csv')

missing = []
target2grid = OrderedDict()
data = pd.DataFrame({'plantID':[], 'U':[], 'V':[], 'Pout':[], 'ts':[], 'tsID':[]})
dt = datetime.datetime.strptime('2016-01-01', '%Y-%m-%d')
step = datetime.timedelta(hours=1)


for i, file in tqdm(enumerate(files)):
    if i != 0 and i % 1000 == 0:
        time.sleep(300)
    query = file + var + '&' + box + '&' + extension
    request = requests.get(query)

    data_tmp = pd.DataFrame({'plantID':id_target, 'ts':[dt]*n_target, 'tsID':[i+1]*n_target})

    if request.status_code == 200:
        with open('tmp.nc', 'wb') as f:
            f.write(request.content)
        tmp = Dataset('tmp.nc', 'r')
        lon_grid = tmp.variables['lon'][:].flatten()
        lat_grid = tmp.variables['lat'][:].flatten()
        u_wsp = tmp.variables['u-component_of_wind_height_above_ground'][0,1,:,:].flatten()
        v_wsp = tmp.variables['v-component_of_wind_height_above_ground'][0,1,:,:].flatten()

        n_grid = len(lon_grid)
        if data.empty:
            # The angular distance is calculated once. The target to grid correspondence is stored in a dictionary.
            for j in range(n_target):
                uv_target = ll2uv(lon_target[j], lat_target[j])
                distance = [angular_distance(uv_target, ll2uv(lon_grid[k],lat_grid[k])) for k in range(n_grid)]
                target2grid[id_target[j]] = np.argmin(distance)

        data_tmp['U'] = [u_wsp[target2grid[id_target[j]]] for j in range(n_target)]
        data_tmp['V'] = [v_wsp[target2grid[id_target[j]]] for j in range(n_target)]
        data_tmp['Pout'] = np.sqrt(pow(data_tmp['U'],2) + pow(data_tmp['V'],2))
        data_tmp['Pout'] = [get_power(val, 'IEC class 2')*capacity_target[j] for j, val in enumerate(data_tmp['Pout'].values)]

        tmp.close()
        os.remove('tmp.nc')
    else:
        print("File %s is missing" % file.split('/')[-1])
        missing.append(file)

        # missing data are set to -99.
        data_tmp['U'] = [-99] * n_target
        data_tmp['V'] = [-99] * n_target
        data_tmp['Pout'] = [-99] * n_target

    data = data.append(data_tmp, ignore_index=True, sort=False)

    dt += step

data['plantID'] = data['plantID'].astype(np.int32)
data['tsID'] = data['tsID'].astype(np.int32)

data.sort_values(by=['tsID', 'plantID'], inplace=True)
data.reset_index(inplace=True, drop=True)

data.to_pickle('western_wind_output_2016_unfilled.pkl')

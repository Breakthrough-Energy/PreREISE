import h5pyd
import numpy as np
import pandas as pd
from collections import OrderedDict

"""
Collect a set of solar and meteoroligical data fields from the Wind Integration
National Dataset (WIND).
Website: https://www.nrel.gov/grid/wind-toolkit.html
API: https://developer.nrel.gov/docs/wind/wind-toolkit/wind-toolkit-extract/

Calculate the solar power output for a given plant based on the naive
assumption that it is equal to the maximum capacity of the plant (GenMWMax)
at maximum irradiance (GHI) over the time period considered.
"""

###############################################
# Get the plants coordinates, id and GenMWMax #
###############################################
import westernintnet
grid = westernintnet.WesternIntNet()

solar_plant = grid.genbus.groupby('type').get_group('solar')
print("There are %d solar plants in the Western grid." % len(solar_plant))

coord = OrderedDict()
for i in range(len(solar_plant)):
    key = (solar_plant.lon.values[i],solar_plant.lat.values[i])
    if key not in coord.keys():
        coord[key] = [(solar_plant.index[i],solar_plant.GenMWMax.values[i])]
    else:
        coord[key].append((solar_plant.index[i],solar_plant.GenMWMax.values[i]))

print("There are %d unique locations." % len(coord.keys()))

########################################
# Extract Global Horizontal Irradiance #
########################################
import dateutil
from common import *

hs_endpoint = 'https://developer.nrel.gov/api/hsds/'
hs_username = None
hs_password = None
hs_api_key  = '3K3JQbjZmWctY0xmIfSYvYgtIcM3CN0cb1Y2w9bf'

f = h5pyd.File("/nrel/wtk-us.h5", 'r',
               username=hs_username,
               password=hs_password,
               endpoint=hs_endpoint,
               api_key=hs_api_key)

## Get Coordinates of Nearest Location
lat_origin, lon_origin = f['coordinates'][0][0] # origin of the database
ij = {}
for key in coord.keys():
    ij[key] = ll2ij(lon_origin, lat_origin, key[0], key[1])

## Extract Time Serie
dt = f['datetime']
dt = pd.DataFrame({'datetime': dt[:]})
dt['datetime'] = dt['datetime'].apply(dateutil.parser.parse)

start = '2010-01-01'
end   = '2013-01-01'
dt_range = dt.loc[(dt.datetime >= start) & (dt.datetime < end)]

data = pd.DataFrame({'Pout':[], 'plantID':[], 'tsID':[]})

for i, (key, val) in enumerate(ij.items()):
    print("Loading information for location #%d" % (i+1))
    ghi =  f['GHI'][min(dt_range.index):max(dt_range.index)+1, val[0], val[1]]
    data_loc = pd.DataFrame({'Pout':ghi})
    data_loc['Pout'] /= max(ghi)
    data_loc['tsID'] = range(1,len(ghi)+1)

    for i in coord[key]:
        data_site = data_loc.copy()
        data_site['Pout'] *= i[1]
        data_site['plantID'] = i[0]

        data = data.append(data_site, ignore_index = True, sort = False)

data['plantID'] = data['plantID'].astype(np.int32)
data['tsID'] = data['tsID'].astype(np.int32)

data.sort_values(by=['tsID', 'plantID'], inplace=True)
data.reset_index(inplace=True, drop=True)

# Write File
name = "western_Pout_%d.txt" % (year)
data.to_csv(name, header=None, index=False, columns=['tsID','plantID','Pout'])

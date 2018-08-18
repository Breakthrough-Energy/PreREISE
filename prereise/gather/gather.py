#import matplotlib.pyplot as plt # Maybe not needed
from math import *
import pandas as pd
import requests
import sys
import numpy as np
from pywtk.site_lookup import get_3tiersites_from_wkt
from pywtk.wtk_api import get_nc_data, get_nc_data_from_url, WIND_MET_NC_DIR
WTK_URL = "https://h2oq9ul559.execute-api.us-west-2.amazonaws.com/dev"

# Import state data
from bokeh.sampledata.us_states import data as states
# Import western interconnect data
from westernintnet.westernintnet import WesternIntNet
from inspect import formatannotationrelativeto
win = WesternIntNet()

def _greatCircleDistance(lat1, lon1, lat2, lon2):
    R = 6368
    def haversin(x):
        return sin(x/2)**2
    return R*2 * asin(sqrt(
          haversin(lat2-lat1) +
          cos(lat1) * cos(lat2) * haversin(lon2-lon1)))

def get_all_NREL_siteID_for_states(states_list):
    """Retrieve all siteID's for wind farms in states in states_list.
    Returns Pandas DataFrame with columns ['site_id', 'lat', 'lon', 'capacity', 'capacity_factor'].
    """
    nrel_sites = None

    for state in states_list:
        coords = np.column_stack((states[state]['lons'],states[state]['lats']))

        # Prepare coordinates for call
        # Convert into string format
        out_tot = []
        for i in coords:
            out = str(i[0]) + ' ' + str(i[1]) + ','
            out_tot.append(out)
        out = str(coords[0][0]) + ' ' + str(coords[0][1])
        out_tot.append(out)
        str1 = ''.join(out_tot)
        str_final = 'POLYGON((' + str1 + '))'
        print('Retrieving nrel sites for '+state)
        site_df = get_3tiersites_from_wkt(str_final)
        print('Got ' + str(site_df.shape[0]) + ' sites for '+state)
        site_df = site_df.reset_index()
        if nrel_sites is not None:
            nrel_sites = nrel_sites.append(site_df[['site_id', 'lat', 'lon', 'capacity', 'capacity_factor']])
        else:
            nrel_sites = site_df[['site_id', 'lat', 'lon', 'capacity', 'capacity_factor']].copy()
    return nrel_sites

# Find NREL siteID closest to wind farms
def find_NREL_siteID_closest_to_windfarm(nrel_sites, wind_farm_bus):
    """Takes Pandas DataFrame nrel_sites that needs the columns ['site_id', 'lat', 'lon','capacity']
    and wind_farm_bus as Pandas DataFrame with the following structure: ['plantID'(index), 'lat', 'lon'].
    The order of the columns plantID(index), lat and lon is important.
    Returns Pandas Series with plantID as index, siteID and capacity as value.
    """
    closest_NREL_siteID = pd.DataFrame(index = wind_farm_bus.index,columns = ['siteID', 'capacity'])
    # Iterate trough wind farms and find closest NREL site
    for i,row in enumerate(wind_farm_bus.itertuples()):
        dist = nrel_sites.apply(lambda row_sites : _greatCircleDistance(row_sites['lat'], row_sites['lon'],row[1],row[2]),axis=1)
        #r_sq = (nrel_sites['lat']-row[1])*(nrel_sites['lat']-row[1]) + (nrel_sites['lon']-row[2])*(nrel_sites['lon']-row[2])
        print(dist.min())
        closest_NREL_siteID.iloc[i].siteID = (nrel_sites['site_id'][dist == dist.min()].values[0])
        closest_NREL_siteID.iloc[i].capacity = (nrel_sites['capacity'][dist == dist.min()].values[0])
    closest_NREL_siteID.index.name = 'plantID'
    closest_NREL_siteID.siteID = closest_NREL_siteID.siteID.astype(int)
    closest_NREL_siteID.capacity = closest_NREL_siteID.capacity.astype(float)
    return closest_NREL_siteID

def get_data_from_NREL_server(siteIDs, data_range):
    """Takes Pandas DataFrame with siteIDs and capacity as values. It also takes
    the pandas data_range as input. freq needs to be 5min.
    Returns a 2D dict containing Pandas DataFrame with index date
    and columns power and wind_speed. The data is normalized using the capacity.
    The 1. key is the month like '2010-10'
    The 2. key is the siteID like 121409
    So the class site_dict['2012-12'][121409] returns the DataFrame.
    """
    # Retrieving data from NREL server
    utc = True
    leap_day = True
    # We use a dict because the output is a tensor
    # 1: siteIDs 2: date(month) 3: attribute(power, wind_speed)
    sites_dict = {}
    # Use helper DataFrame to specifie download interval
    helper_df = pd.DataFrame(index=data_range)

    for y in helper_df.index.year.unique():
        for m in helper_df[str(y)].index.month.unique():
            if(m<10):
                month = str(y) + '-0' + str(m)
            else:
                month = str(y) + '-' + str(m)
            sites_dict[month] = {}
            start = helper_df[month].index[0]
            end = helper_df[month].index[-1]
            attributes = ["power", "wind_speed"]
            #for site_id in siteIDs.iloc[0:1].siteID:
            #    print('Call ' + str(site_id) + ' ' + str(start) + ' ' + str(end))
            #    sites_dict[month][site_id] = get_nc_data_from_url(WTK_URL+"/met", site_id, start, end, attributes, utc=utc,leap_day=leap_day)
            for row in siteIDs.drop_duplicates(subset='siteID').itertuples():
                site_id_i = row[1]
                capacity_i = row[2]
                print('Call ' + str(site_id_i) + ' ' + str(start) + ' ' + str(end))
                sites_dict[month][site_id_i] = get_nc_data_from_url(WTK_URL+"/met", site_id_i, start, end, attributes, utc=utc,leap_day=leap_day)/capacity_i
    print('Done retrieving data from NREL server')
    return sites_dict

def dict_to_DataFrame(data, data_range, closest_NREL_siteID):
    """Input the 2D dict containing Pandas DataFrame with index date
    and columns power and wind_speed. It also takes the pandas data_range of
    the data and the closest_NREL_siteID.

    The 1. key is the month like '2010-10'
    The 2. key is the siteID like 121409

    Returns two DataFrames, one for power and one for wind speed

    """
    NREL_power = pd.DataFrame(index=data_range,columns=closest_NREL_siteID['siteID'].drop_duplicates(),dtype=float)
    NREL_windspeed = pd.DataFrame(index=data_range,columns=closest_NREL_siteID['siteID'].drop_duplicates(),dtype=float)

    for month in data:
        print(month)
        for siteID in data[month]:
            print(siteID)
            NREL_power.loc[month,siteID] = data[month][siteID]['power'].values
            NREL_windspeed.loc[month,siteID] = data[month][siteID]['wind_speed'].values
    return [NREL_power, NREL_windspeed]

def scale_and_save_power_for_matpower(NREL_power, wind_farm_bus, closest_NREL_siteID):
    """ Input data in 2D dict format containing normalized wind power time series
    as well as wind_farm_bus containing information of the relation between siteID
    and plantID(index in genbus) as well as Pmax of the plant in order to scale
    the wind power.
    """
    wind_farm_power = pd.DataFrame(index=NREL_power.index,columns=wind_farm_bus.index.values)
    for plantID, Pmax in wind_farm_bus['Pmax'].iteritems():
        siteID = closest_NREL_siteID.loc[plantID,'siteID']
        wind_farm_power[plantID] = NREL_power[siteID]*Pmax

    wind_farm_power_series_hourly = wind_farm_power.resample('H').mean()
    numb_farms = wind_farm_power_series_hourly.shape[1]
    mp_power = []
    mp_index = []
    mp_plantID = []
    for i,row in enumerate(wind_farm_power_series_hourly.itertuples()):
        mp_index = mp_index + [i+1] * numb_farms
        mp_plantID = wind_farm_bus.index.values.tolist() + mp_plantID
        mp_power = mp_power + list(row[1:])

    mp_wind_input = pd.DataFrame(index=mp_index,columns = ['plantID','power'])
    mp_wind_input['plantID'] = mp_plantID
    mp_wind_input['power'] = mp_power
    mp_wind_input.index.name = 'period_hour'
    return mp_wind_input

def get_and_save_NREL_data():

    all_siteID_NREL  = get_all_NREL_siteID_for_states(['WA'])#(WI.states_abbrev)
    #Pandas DataFrame with subID of wind farm as index and with column label lat and lon
    #windfarm_subID = win.sub.loc[win.bus2sub.subID[win.genbus.groupby('type').get_group('wind').busID],['lat','lon']].drop_duplicates()
    wind_farm_bus = win.genbus.groupby('type').get_group('wind')
    #returns map between subID (index) and NREL siteID (column)
    closest_NREL_siteID = find_NREL_siteID_closest_to_windfarm(all_siteID_NREL, wind_farm_bus[['lat','lon']])
    # Create data frame for power and wind speed
    data_start = pd.Timestamp('2010-01-01')
    data_end = pd.Timestamp('2010-01-01 23:55:00')
    #data_end = pd.Timestamp('2012-12-31 23:55:00')
    # The server provides data in 5min intervals
    data_range = pd.date_range(data_start, data_end,freq = '5min')
    data = get_data_from_NREL_server(closest_NREL_siteID, data_range)

    [power,wind_speed] = dict_to_DataFrame(data, data_range, closest_NREL_siteID)
    mp = scale_and_save_power_for_matpower(power, wind_farm_bus, closest_NREL_siteID)
    mp.to_csv('PowerForMatPowerImport.csv')
    #save_sites_dict_to_csvL(data)

import matplotlib.pyplot as plt # Maybe not needed
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

# Retrieve all siteID's for wind farms in states part of the western interconnect network
def get_all_NREL_siteID_for_states(states_list):
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
def find_NREL_siteID_closest_to_windfarm(nrel_sites, windfarm_subID):
    closest_NREL_siteID = pd.Series(index = windfarm_subID.index)
    # Iterate trough wind farms and find closest NREL site
    for i,row in enumerate(windfarm_subID.itertuples()): 
        r_sq = (nrel_sites['lat']-row[1])*(nrel_sites['lat']-row[1]) + (nrel_sites['lon']-row[2])*(nrel_sites['lon']-row[2])
        closest_NREL_siteID.iloc[i] = int(nrel_sites['site_id'][r_sq == r_sq.min()].values[0])
    closest_NREL_siteID=closest_NREL_siteID.astype(int)
    closest_NREL_siteID.index.name = 'subID'
    closest_NREL_siteID.name = 'siteID'
    return closest_NREL_siteID

def get_data_from_NREL_server(siteIDs):
    # Create data frame for power and wind speed
    data_start = pd.Timestamp('2010-01-01')
    data_end = pd.Timestamp('2012-12-31 23:55:00')
    data_range = pd.date_range(data_start, data_end,freq = '5min')
    NREL_power = pd.DataFrame(index=data_range,columns=siteIDs)
    NREL_windspeed = pd.DataFrame(index=data_range,columns=sitesIDs)
    
    # Retrieving data from NREL server
    utc = True
    leap_day = True
    sites_dict = {}
    for y in data_range.year.unique():
        for m in range(1,13):
            if(m<10):
                month = str(y) + '-0' + str(m)
            else:
                month = str(y) + '-' + str(m)
            sites_dict[month] = {}
            start = NREL_power[month].index[0]
            end = NREL_power[month].index[-1]     
            attributes = ["power", "wind_speed"]
            for site_id in siteIDs:
                print('Call ' + str(site_id) + ' ' + str(start) + ' ' + str(end))
                sites_dict[month][site_id] = get_nc_data_from_url(WTK_URL+"/met", site_id, start, end, attributes, utc=utc,leap_day=leap_day)
    print('Done retrieving data from NREL server')
    return sites_dict

def save_sites_dict_to_csv(data):
# Save data in csv file
    for y in data_range.year.unique():
        for m in range(1,13):
            if(m<10):
                month = str(y) + '-0' + str(m)
            else:
                month = str(y) + '-' + str(m)
            NREL_power.loc[month,site_id] = sites_dict[month][site_id]['power'].values
            NREL_windspeed.loc[month,site_id] = sites_dict[month][site_id]['wind_speed'].values
    NREL_power.to_csv('WIN-NREL2010-2012_power.csv')
    NREL_windspeed.to_csv('WIN-NREL2010-2012_windspeed.csv')

def get_and_save_NREL_data():
    
    all_siteID_NREL  = get_NREL_siteID_for_states(WI.states_abbrev)
    #Pandas DataFrame with subID of wind farm as index and with column label lat and lon
    windfarm_subID = WI.sub.loc[WI.bus2sub.subID[WI.genbus.groupby('type').get_group('wind').busID],['lat','lon']].drop_duplicates()
    #returns map between subID (index) and NREL siteID (column)
    closest_NREL_siteID = find_NREL_siteID_closest_to_windfarm(all_siteID_NREL, windfarm_subID)
    data = get_data_from_NREL_server(closest_NREL_siteID)
    save_sites_dict_to_csvL(data)
    

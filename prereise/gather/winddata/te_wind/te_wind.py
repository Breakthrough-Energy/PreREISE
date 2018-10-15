
import math
import sys

import numpy as np
import pandas as pd
import requests
from bokeh.sampledata.us_states import data as states

from pywtk.site_lookup import get_3tiersites_from_wkt
from pywtk.wtk_api import WIND_MET_NC_DIR, get_nc_data, get_nc_data_from_url
from tqdm import tqdm


def _greatCircleDistance(lat1, lon1, lat2, lon2):
    R = 6368

    def haversin(x):
        return math.sin(x/2)**2
    return R*2 * math.asin(math.sqrt(
        haversin(lat2-lat1) +
        math.cos(lat1) * math.cos(lat2) * haversin(lon2-lon1)))


def get_all_NREL_siteID_for_states(states_list):
    """Retrieve ID's of wind farms in given states.

    :param states_list: list object containing state abbreviation.
    :return: Pandas DataFrame with columns ['site_id', 'lat', 'lon', \ 
    'capacity', 'capacity_factor']
    """
    nrel_sites = None

    for state in states_list:
        coords = np.column_stack(
            (states[state]['lons'], states[state]['lats']))

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
            nrel_sites = nrel_sites.append(
                site_df[['site_id', 'lat', 'lon',
                         'capacity', 'capacity_factor']]
            )
        else:
            nrel_sites = site_df[['site_id', 'lat', 'lon', 'capacity',
                                  'capacity_factor']].copy()
    return nrel_sites


def find_NREL_siteID_closest_to_windfarm(nrel_sites, wind_farm_bus):
    """Find NREL site closest to wind farm.

    :param nrel_sites: Pandas DataFrame that needs the columns \ 
        ['site_id', 'lat', 'lon','capacity'] as returned by \ 
        :py:func:`get_all_NREL_siteID_for_states`.
    :param wind_farm_bus: Pandas DataFrame with the following structure: \ 
        ['plantID'(index), 'lat', 'lon']. The order of the columns \ 
        plantID(index), lat and lon is important.
    :return: Pandas Series with plantID as index, siteID and capacity as value.
    """
    closest_NREL_siteID = pd.DataFrame(index=wind_farm_bus.index,
                                       columns=['siteID', 'capacity', 'dist'])
    # Iterate trough wind farms and find closest NREL site
    for i, row in enumerate(tqdm(wind_farm_bus.itertuples(),
                                 total=wind_farm_bus.shape[0])):
        dist = nrel_sites.apply(lambda row_sites:
                                _greatCircleDistance(
                                    row_sites['lat'], row_sites['lon'],
                                    row[1], row[2]), axis=1
                                )
        closest_NREL_siteID.iloc[i].dist = dist.min()
        closest_NREL_siteID.iloc[i].siteID = (
            nrel_sites['site_id'][dist == dist.min()].values[0]
        )
        closest_NREL_siteID.iloc[i].capacity = (
            nrel_sites['capacity'][dist == dist.min()].values[0]
        )
    closest_NREL_siteID.index.name = 'plantID'
    closest_NREL_siteID.siteID = closest_NREL_siteID.siteID.astype(int)
    closest_NREL_siteID.capacity = closest_NREL_siteID.capacity.astype(float)
    closest_NREL_siteID.dist = closest_NREL_siteID.dist.astype(float)
    return closest_NREL_siteID


def get_data_from_NREL_server(siteIDs, data_range):
    """Get power and wind speed data from NREL server.

    :param siteIDs: Pandas DataFrame with siteIDs and capacity as values, \ 
        as returned by :py:func:`find_NREL_siteID_closest_to_windfarm`
    :param data_range: Pandas data_range, freq needs to be 5min.
    :return: 2D dict containing Pandas DataFrame with index date \ 
        and columns power and wind_speed. \ 
        The data is normalized using the capacity. \ 
        The 1. key is the month like '2010-10' \ 
        The 2. key is the siteID like 121409 \ 
        So the class site_dict['2012-12'][121409] returns the DataFrame.
    """

    wtk_url = "https://h2oq9ul559.execute-api.us-west-2.amazonaws.com/dev"

    # Retrieving data from NREL server
    utc = True
    leap_day = True
    # We use a dict because the output is a tensor
    # 1: siteIDs 2: date(month) 3: attribute(power, wind_speed)
    sites_dict = {}
    # Use helper DataFrame to specifie download interval
    helper_df = pd.DataFrame(index=data_range)

    for y in tqdm(helper_df.index.year.unique()):
        for m in tqdm(helper_df[str(y)].index.month.unique(), desc=str(y)):
            if(m < 10):
                month = str(y) + '-0' + str(m)
            else:
                month = str(y) + '-' + str(m)
            sites_dict[month] = {}
            start = helper_df[month].index[0]
            end = helper_df[month].index[-1]
            attributes = ["power", "wind_speed"]

            for row in tqdm(
                siteIDs.drop_duplicates(subset='siteID').itertuples(),
                desc=month,
                total=siteIDs.drop_duplicates(subset='siteID').shape[0]
            ):
                site_id_i = row[1]
                capacity_i = row[2]
                tqdm.write('Call ' + str(site_id_i) + ' ' +
                           str(start) + ' ' + str(end))
                sites_dict[month][site_id_i] = get_nc_data_from_url(
                    wtk_url+"/met",
                    site_id_i, start, end, attributes,
                    utc=utc, leap_day=leap_day
                )/capacity_i
    print('Done retrieving data from NREL server')
    return sites_dict


def dict_to_DataFrame(data, data_range, closest_NREL_siteID):
    """Converts the dict into two DataFrames. One for power and one for wind
    speed.

    :param data: 2D dict containing Pandas DataFrame with index date \ 
        and columns power and wind_speed. The 1. key is the month like \ 
        '2010-10'. The 2. key is the siteID like 121409. \ 
        The dict structure is as returend by \ 
        :py:func:`get_data_from_NREL_server`.
    :param data_range: Pandas data_range of the data.
    :param closest_NREL_siteID: Pandas Series with plantID as index, \ 
        siteID and capacity as value. The structure is as returned by \ 
        :py:func:`find_NREL_siteID_closest_to_windfarm`.
    :return: Two DataFrames, one for power and one for wind speed. Index is \ 
        data_range and columns are site_IDs
    """
    NREL_power = pd.DataFrame(index=data_range,
                              columns=closest_NREL_siteID[
                                  'siteID'
                              ].drop_duplicates(), dtype=float)
    NREL_windspeed = pd.DataFrame(index=data_range,
                                  columns=closest_NREL_siteID[
                                      'siteID'
                                  ].drop_duplicates(), dtype=float)

    for month in data:
        print(month)
        for siteID in tqdm(data[month]):
            NREL_power.loc[month, siteID] = data[month][siteID]['power'].values
            NREL_windspeed.loc[month, siteID] = \
                data[month][siteID]['wind_speed'].values
    return [NREL_power, NREL_windspeed]


def scale_power_to_plant_capacity(NREL_power,
                                  wind_farm_bus,
                                  closest_NREL_siteID):
    """ Scales power to plant capacity

    :param NREL_power: Pandas DataFrame index data_range and columns siteID. \ 
        The structure the same as the one of the first variable returned by \ 
        :py:func:`dict_to_DataFrame`.
    :param wind_farm_bus: Pandas DataFrame containing plantID and GenMWMax. \ 
    :param closest_NREL_siteID: Pandas DataFrame containing siteID as \ 
        as returned by :py:func`find_NREL_siteID_closest_to_windfarm`. \ 
    :return: Pandas DataFrame with data_range as well as plantID containing \ 
        the power.
    """
    wind_farm_power = pd.DataFrame(index=NREL_power.index,
                                   columns=wind_farm_bus.index.values)
    for plantID, GenMWMax in wind_farm_bus['GenMWMax'].iteritems():
        siteID = closest_NREL_siteID.loc[plantID, 'siteID']
        wind_farm_power[plantID] = NREL_power[siteID]*GenMWMax

    wind_farm_power_series_hourly = wind_farm_power.resample('H').mean()
    return wind_farm_power_series_hourly

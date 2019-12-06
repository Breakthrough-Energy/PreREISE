	
import requests
import pandas as pd
def map_grid_buses_to_county(grid):
	"""
	Find the county in the U.S. territory that each load bus in the query grid belongs to
	:param Grid grid: the name of the query grid

	Returns
	:return: (*pandas.DataFrame*) bus_ba_map -- data frame of counties that load buses locate
	:return: (*list*) bus_no_county_match -- list of bus indexes that no county matches
	"""
	bus_ba_map = grid.bus[grid.bus['Pd']>0][['Pd','lat','lon']].copy()
	bus_ba_map.loc[:,'County'] = None
	bus_ba_map.loc[:,'BA'] = None
	# api-endpoint 
	URL = "https://geo.fcc.gov/api/census/block/find"
	# defining a params dict for the parameters to be sent to the API
	bus_no_county_match = []
	for index,row in bus_ba_map.iterrows():
	    print(index)
	    PARAMS = {'latitude':row['lat'], 'longitude':row['lon'], 'format':'json', 'showall': True} 
	    # sending get request and saving the response as response object 
	    r = requests.get(url = URL, params = PARAMS).json()
	    try:
	        county_name = r['County']['name']+'__'+r['State']['code']
	        bus_ba_map.loc[index,'County'] = county_name
	    except:
	        bus_no_county_match.append(index)
	return bus_ba_map, bus_no_county_match
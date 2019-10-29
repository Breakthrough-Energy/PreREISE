import pandas as pd
import numpy as np
import requests
import json
import pickle
from collections import Counter
from collections import defaultdict
from powersimdata.input.grid import Grid


eastern = Grid(['Eastern'])

# Warning: this step takes around 3 hours to finish. The results are stored in bus_ba_map.csv for future use.

bus_ba_map = eastern.bus[eastern.bus['Pd']>0][['Pd','lat','lon']].copy()
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


data = json.load(open('EasternBAtoCountyDraft6.txt'))
# df = pd.DataFrame(data['groups']['#cc3333']['paths'])
# bus_ba_map = pd.read_csv('bus_ba_map.csv',index_col=0)


ba_county_list = {}
for val in data['groups'].values():
    ba_county_list[val['label']] = set(val['paths'])


for index,row in bus_ba_map.iterrows():
    for BA,clist in ba_county_list.items():
        try:
            county = row['County'].replace(' ','_')
            county = county.replace('.','')
            county = county.replace('-','')
            county = county.replace('\'','_')
            if row['County'] == 'LaSalle__IL':
                county = 'La_Salle__IL'
            if row['County'] == 'Lac Qui Parle__MN':
                county = 'Lac_qui_Parle__MN'
            if row['County'] == 'Baltimore__MD':
                county = 'Baltimore_County__MD'
            if row['County'] == 'District of Columbia__DC':
                county = 'Washington__DC'
            if row['County'] == 'St. Louis City__MO':
                county = 'St_Louis_Co__MO'
            if county in clist:
                bus_ba_map.loc[index,'BA'] = BA
                break
        except:
            continue

# bus_no_BA_match = list(bus_ba_map[~bus_ba_map['BA'].astype(bool)].index)
bus_no_BA_match = list(bus_ba_map[bus_ba_map['BA'].isna()].index)
bus_no_county_match = list(bus_ba_map[bus_ba_map['County'].isna()].index)

# Add zone name into the data frame for reference
bus_ba_map.loc[:,'zone_name'] = eastern.bus[eastern.bus['Pd']>0]['zone_id'].apply(lambda x: eastern.id2zone[x])

# Fix mismatch county names in Virginia and Maryland
for ind in bus_no_BA_match:
    if bus_ba_map.loc[ind,'zone_name'] in {'Virginia Mountains','West Virginia','Virginia Tidewater','Maryland'}:
        bus_ba_map.loc[ind,'BA'] = 'PJM'
        
# Manually assign outliers (outside US territory) to the nearest BA
# bus no county match: [91: ISNE, 7991: NYIS, 7992: NYIS, 8707: NYIS, 8708: NYIS, 40644: MISO]
bus_ba_map.loc[91,'BA'] = 'ISNE'
bus_ba_map.loc[7991,'BA'] = 'NYIS'
bus_ba_map.loc[7992,'BA'] = 'NYIS'
bus_ba_map.loc[8707,'BA'] = 'NYIS'
bus_ba_map.loc[8708,'BA'] = 'NYIS'
bus_ba_map.loc[40644,'BA'] = 'MISO'

# Assign the rest no-ba-match buses to SWPP
for ind in bus_no_BA_match:
    bus_ba_map.loc[ind,'BA'] = 'SWPP'

# Assign buses in ERCOT Texas to SWPP or MISO based on the location by observation
miso_tx_ind = bus_ba_map[(bus_ba_map['BA']=='ERCOT Texas') & (bus_ba_map['zone_name']=='East Texas') & ((bus_ba_map['County']=='Montgomery__TX') | (bus_ba_map['County']=='Walker__TX'))].index
for ind in bus_ba_map[bus_ba_map['BA']=='ERCOT Texas'].index:
    if ind in miso_tx_ind:
        bus_ba_map.loc[ind,'BA']='MISO'
    else:
        bus_ba_map.loc[ind,'BA']='SWPP'

# Make BA Code consistent with EIA data source
ba_code_fix = {'ISONE':'ISNE','NYISO':'NYIS'}
bus_ba_map.replace(ba_code_fix,inplace=True)

bus_ba_map.to_csv('bus_ba_map.csv')
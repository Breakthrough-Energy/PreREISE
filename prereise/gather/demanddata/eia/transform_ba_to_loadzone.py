import pandas as pd
import os

bus_map = pd.read_csv('bus_ba_map.csv')
bus_map.set_index('bus_id')
agg_demand = pd.read_pickle("C:\\Users\\dmuldrew\\Dropbox (IVL)\\Explorations\\DanM\\demand_interpolated.pkl")

def map_to_loadzone(agg_demand, bus_map):
    BA_agg = bus_map[['BA','Pd']].groupby('BA').sum()

    bus_map.BA.apply(lambda x: BA_agg.loc[x,'Pd'])

    BA_scaling_factor = bus_map.merge(BA_agg, left_on='BA', right_on='BA')

    BA_scaling_factor = BA_scaling_factor.assign(zone_scaling = lambda x: x['Pd_x']/x['Pd_y'])

    BA_grouped_scaling = BA_scaling_factor.groupby(['BA','zone_name']).sum()

    zone_demand = pd.DataFrame(index=agg_demand.index)

    for ba_name in BA_grouped_scaling.index.unique(level = 'BA').to_list():
        zone_scaling_df = BA_grouped_scaling.loc[ba_name]
        for zone_name in zone_scaling_df.index.get_level_values(0).to_list():
            if zone_name in zone_demand.columns:
                zone_demand[zone_name] += (zone_scaling_df.loc[zone_name,'zone_scaling']*eastern_agg_demand[ba_name])
            else:
                zone_demand[zone_name] = (zone_scaling_df.loc[zone_name,'zone_scaling']*eastern_agg_demand[ba_name])
                
    return zone_demand
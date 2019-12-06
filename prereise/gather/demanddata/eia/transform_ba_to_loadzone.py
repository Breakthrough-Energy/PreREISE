import pandas as pd
import os

def map_to_loadzone(agg_demand, bus_map):
    """ Transforms columns of demand dataframe from BA regions to load zones according to bus_map
        :params pandas.DataFrame agg_demand: dataframe for the aggregated region demand
        :params pandas.DataFrame bus_map: dataframe used to map BA regions to load zones using Pd weighting
        :return: (*pandas.DataFrame*) -- new dataframe with demand columns according to load_zone
    """
    BA_agg = bus_map[['BA','Pd']].groupby('BA').sum().rename(columns={'Pd':'PdTotal'})

    BA_scaling_factor = bus_map.merge(BA_agg, left_on='BA', right_on='BA')
    BA_scaling_factor = BA_scaling_factor.assign(zone_scaling = lambda x: x['Pd']/x['PdTotal'])
    BA_grouped_scaling = BA_scaling_factor.groupby(['BA','zone_name']).sum()

    zone_demand = pd.DataFrame(index=agg_demand.index)
    for ba_name in BA_grouped_scaling.index.unique(level = 'BA').to_list():
        zone_scaling_df = BA_grouped_scaling.loc[ba_name]
        for zone_name in zone_scaling_df.index.get_level_values(0).to_list():
            if zone_name in zone_demand.columns.to_list():
                zone_demand[zone_name] += (zone_scaling_df.loc[zone_name,'zone_scaling']*agg_demand[ba_name])
            else:
                zone_demand[zone_name] = (zone_scaling_df.loc[zone_name,'zone_scaling']*agg_demand[ba_name])
    print(zone_demand.values.T.tolist())
    return zone_demand
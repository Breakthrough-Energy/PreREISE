import pandas as pd
import numpy as np


def get_monthly_net_generation(state,filename,fuel_type,trim_eia_form_923):
    """Get monthly total net generation for the query fuel type in the query state in 2016 from EIA923
    :param str state: the query state
    :param str filename: name of the reference file
    :param str fuel_type: the query type of fuel
    :return: (*list*) EIA_net_generation -- monthly net generation of the query fuel type in the query 
        state in a list of length 12
    :raise ValueError: if state is invalid.
    :raise ValueError: if fuel_type is invalid.
    """
    
    state_name = ['WA','OR', 'CA', 'NV', 'AZ', 'UT', 'NM', 'CO', 'WY', 'ID', 'MT']
    if state not in state_name:
        print("%s is incorrect. Possible states are: %s" %
              (state, state_name))
        raise ValueError('Invalid state')
    
    all_fuel_type = {'solar':{'SUN'},
                     'coal':{'COL'},
                     'dfo':{'DFO'},
                     'geothermal':{'GEO'},
                     'hydro':{'HYC','HPS'}, # Hydroelectric Conventional, Hydroelectric Pumped Storage
                     'ng':{'NG'},
                     'nuclear':{'NUC'},
                     'wind':{'WND'},
                     }
    if fuel_type not in all_fuel_type:
        print("%s is incorrect. Possible fuel types are: %s" %
              (fuel_type, list(all_fuel_type.keys())))
        raise ValueError('Invalid fuel_type')
    
    # Get trimmed EIA form 923 with only necessary columns
    plant_generation = trim_eia_form_923(filename)
    
    # Filter by state and fuel type
    net_generation_by_plant = plant_generation[(plant_generation['Plant State'] == state) &
                                               (plant_generation['AER\nFuel Type Code']. \
                                               isin(all_fuel_type[fuel_type]))].copy()
    
    # Drop unnecessary columns, plant ID, etc..
    net_generation = net_generation_by_plant.drop(net_generation_by_plant.columns[[0,1,2,3,4]], axis=1)
    net_generation = net_generation.replace('.',0)
    
    # Get monthly total net generation by summing up across plants with all positive values 
    # Note that negative ones are included in actual demand
    EIA_net_generation = list(net_generation.apply(lambda x: x[x>0].sum()).values)
    
    # If there is no such generator in the query state, the function will return a list of 0.0 instead of nan
    EIA_net_generation = list(np.nan_to_num(EIA_net_generation))
    
    return EIA_net_generation
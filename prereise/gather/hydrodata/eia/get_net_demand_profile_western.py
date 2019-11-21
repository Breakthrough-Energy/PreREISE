from powersimdata.input.grid import Grid


def get_net_demand_profile_western(state,s):
    """Get the net demand profile of a specific state based on Western basecase scenario 2016
    :param str state: the query state
    :param powersimdata.scenario.scenario.Scenario s: scenario instance
    :return: (*list*) netdemand -- net demand profile of the query state in a list of length 8784
    :raise ValueError: if state is invalid.
    """
    
    state_name = {'WA':{'Washington'},
                  'OR':{'Oregon'},
                  'CA':{'Northern California','Bay Area','Central California',
                        'Southwest California','Southeast California'},
                  'NV':{'Nevada'},
                  'AZ':{'Arizona'},
                  'UT':{'Utah'},
                  'NM':{'New Mexico Western'},
                  'CO':{'Colorado'},
                  'WY':{'Wyoming'},
                  'ID':{'Idaho'},
                  'MT':{'Montana Western'},
                  }
              
    if state not in state_name:
        print("%s is incorrect. Possible states are: %s" %
              (state, list(state_name.keys())))
        raise ValueError('Invalid state')
        
    # load Western basecase scenario 2016 and the corresponding profiles
    wind = s.state.get_wind()
    solar = s.state.get_solar()
    demand = s.state.get_demand()
    western = Grid(['Western'])
    plant = western.plant
                  
    wind_plant_id_list = list(plant[(plant.type == 'wind') & (plant.zone_name.isin(state_name[state]))].index)
    solar_plant_id_list = list(plant[(plant.type == 'solar') & (plant.zone_name.isin(state_name[state]))].index)
    windsum = wind[wind_plant_id_list].sum(axis = 1)
    solarsum = solar[solar_plant_id_list].sum(axis = 1)
    
    zone_id_list = [western.zone2id[zonename] for zonename in state_name[state]]
    demandsum = demand[zone_id_list].sum(axis = 1)
    netdemand = [demandsum[i] - windsum[i] - solarsum[i] for i in demandsum.index]
    
    return netdemand
    
    
    
    
    
    
    
    
    
    
    
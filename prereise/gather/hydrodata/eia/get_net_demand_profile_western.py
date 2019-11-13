from powersimdata.scenario.scenario import Scenario
from powersimdata.input.grid import Grid
def get_net_demand_profile_western(state):
    """Get the net demand profile of a specific state based on Western basecase scenario 2016
    :param str state: the query state
    :return: (*list*) netdemand -- net demand profile of the query state in a list of length 8784
    :raise Exception: if state is invalid.
    """
    
    state_name = {'WA':{'Washington'},
              'OR':{'Oregon'},
              'CA':{'Northern California','Bay Area','Central California','Southwest California','Southeast California'},
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
        raise Exception('Invalid state')
        
    #load Western basecase scenario 2016 and the corresponding profiles
    s = Scenario("87")
    wind = s.state.get_wind()
    solar = s.state.get_solar()
    demand = s.state.get_demand()
    western = Grid(['Western'])
    plant = western.plant
                  
    wind_plant_id_list = []
    for plantid in wind.columns:
        if plant.loc[plantid]['zone_name'] in state_name[state]:
            wind_plant_id_list.append(plantid)
    solar_plant_id_list = []
    for plantid in solar.columns:
        if plant.loc[plantid]['zone_name'] in state_name[state]:
            solar_plant_id_list.append(plantid)
            
    windsum = wind[wind_plant_id_list].sum(axis = 1)
    solarsum = solar[solar_plant_id_list].sum(axis = 1)
    
    zone_id_list = []
    for zonename in state_name[state]:
        zone_id_list.append(western.zone2id[zonename])
    demandsum = demand[zone_id_list].sum(axis = 1)
    netdemand = [demandsum[i] - windsum[i] - solarsum[i] for i in demandsum.index]
    
    return netdemand
    
    
    
    
    
    
    
    
    
    
    
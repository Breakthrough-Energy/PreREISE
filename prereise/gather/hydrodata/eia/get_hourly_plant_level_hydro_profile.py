import pandas as pd
from powersimdata.input.grid import Grid
def get_hourly_plant_level_hydro_profile(total_profile,state):
    """Decompose total hydro profile into plant level profile based on hydro generator capacities in the query state
    :param list total_profile: total hydro profile in the query state
    :param str state: the query state
    :return: (*pandas.DataFrame*) hydro_v2 -- hourly hydro profile for each plant in the query state
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

    western = Grid(['Western'])
    # Group hydro plants in the query state from the plant DataFrame of the Grid object.
    plant = western.plant[(western.plant.type == 'hydro') & (western.plant['zone_name'].isin(state_name[state]))]
    total_hydro_capacity = plant['GenMWMax'].sum()
    hydro_v2 = pd.DataFrame(columns = plant.index)
    for plantid in hydro_v2.columns:
        factor = plant.loc[plantid]['GenMWMax']/total_hydro_capacity
        plant_profile = [val*factor for val in total_profile]
        hydro_v2[plantid] = plant_profile.copy()
    return hydro_v2
    
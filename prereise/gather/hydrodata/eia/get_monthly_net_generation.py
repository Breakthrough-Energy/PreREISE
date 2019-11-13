import pandas as pd
def get_monthly_net_generation(state):
    """Get monthly total hydro net generation for the query state in 2016 from EIA923
    :param str state: the query state
    :return: (*list*) EIA_net_generation -- monthly hydro net generation of the query state in a list  
        of length 12
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
     
    filename = 'EIA923_Schedules_2_3_4_5_M_12_2016_Final_Revision.xlsx'
    # filedir = './f923_2016/'
    filedir = './'
    plant_generation = pd.read_excel(io = filedir + filename, header = 0, usecols = 'A,D,G,I,P,CB:CM',skiprows = range(5))
    # Filter by state and fuel type, HYC: conventional; hydro HPS: pump hydro
    net_generation_by_plant = plant_generation[(plant_generation['Plant State'] == state) & ((plant_generation['AER\nFuel Type Code'] == 'HYC')|(plant_generation['AER\nFuel Type Code'] == 'HPS'))].copy()
    # Drop unnecessary columns, plant ID, etc..
    net_generation = net_generation_by_plant.drop(net_generation_by_plant.columns[[0,1,2,3,4]], axis=1)
    net_generation = net_generation.replace('.',0)
    # Get monthly total net generation by summing up across plants with all positive values, note that negative ones are included in actual demand
    EIA_net_generation = list(net_generation.apply(lambda x: x[x>0].sum()).values)
    return EIA_net_generation
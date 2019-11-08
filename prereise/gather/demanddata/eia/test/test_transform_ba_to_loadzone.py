import pandas as pd
from prereise.gather.demanddata.eia.transform_ba_to_loadzone import map_to_loadzone

def test_loadzone_mapping():
    bus_map, agg_demand = create_fake_dataframe()
    zone_demand = map_to_loadzone(agg_demand, bus_map)

def create_fake_dataframe():
    bus_map_data = {'BA': ['A','A','B','B','B','C','C','D','E','E'], 'Pd': range(0,10), 'zone_scaling': range(20,30)}
    bus_map = pd.DataFrame.from_dict(bus_map_data)
    agg_demand_data = {'BA': [], 'A': range(0,10), 'B': range(10,20), 'C': range(20,30)}
    agg_demand = pd.DataFrame.from_dict(agg_demand_data)
    return bus_map, agg_demand
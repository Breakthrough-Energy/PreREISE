import pandas as pd
from prereise.gather.demanddata.eia.transform_ba_to_loadzone import map_to_loadzone
from pandas.util.testing import assert_series_equal

def test_loadzone_mapping_case():
    bus_map, agg_demand = create_fake_dataframe()
    zone_demand = map_to_loadzone(agg_demand, bus_map)
    assert(zone_demand.values.T.tolist() == [[(1/4)+(2/3)]*3, [(3/4)+(4/3)+3]*3]) 

def test_loadzone_mapping_has_equal_total_demand():
    bus_map, agg_demand = create_fake_dataframe()
    zone_demand = map_to_loadzone(agg_demand, bus_map)
    assert_series_equal(agg_demand.sum(axis=1), zone_demand.sum(axis=1), check_dtype=False)

def create_fake_dataframe():
    bus_map_data = {'BA': ['A','A','B','A','B','C'], 'zone_name': ['X','X','X','Y','Y','Y'], 'Pd': range(0,6)}
    bus_map = pd.DataFrame.from_dict(bus_map_data)
    agg_demand = pd.DataFrame({'A':[1]*3,'B':[2]*3,'C':[3]*3})
    agg_demand.set_index(pd.date_range(start='2016-01-01', periods=3, freq='H'),inplace=True)
    return bus_map, agg_demand
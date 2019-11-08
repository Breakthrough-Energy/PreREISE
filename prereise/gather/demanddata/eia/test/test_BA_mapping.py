import pandas as pd
from prereise.gather.demanddata.eia.transform_demand_to_region import transform_ba_to_region

def test_sum_first_three_columns():
    initial_df = create_fake_dataframe()
    mapping = {'ABC': ['A','B','C']}
    result = transform_ba_to_region(initial_df, mapping)
    assert(result['ABC'].tolist() == list(range(30,60,3)))

def test_sum_first_columns_pairs():
    initial_df = create_fake_dataframe()
    mapping = {'AB': ['A','B'], 'CD': ['C','D']}
    result = transform_ba_to_region(initial_df, mapping)
    assert(result['AB'].tolist() == list(range(10,30,2)))
    assert(result['CD'].tolist() == list(range(50,70,2)))

def create_fake_dataframe():
    start_data = {'A': range(0,10), 'B': range(10,20), 'C': range(20,30), 'D': range(30,40), 'E': range(40,50)}
    initial_df = pd.DataFrame.from_dict(start_data)
    return initial_df
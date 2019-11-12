import pandas as pd

def transform_ba_to_region(demand, mapping):
    """ Transforms column of demand dataframe to regions defined by dictionary mapping
        :params pandas.DataFrame demand: dataframe for the demand
        :params dict mapping: dictionary mapping of BA columns to regions
        :return: (*pandas.DataFrame*) -- dataframe with demand columns according to region
    """
    agg_demand = pd.DataFrame(index=demand.index)
    for key in mapping:
        print(f'{key} regional demand was summed from {mapping[key]}')
        if demand[mapping[key]].shape[1] > 1:
            agg_demand[key] = demand[mapping[key]].sum(axis=1)
        else:
            agg_demand[key] = demand[mapping[key]]
    return agg_demand
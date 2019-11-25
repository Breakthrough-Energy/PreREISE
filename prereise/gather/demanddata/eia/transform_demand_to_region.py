import pandas as pd

def transform_ba_to_region(demand, mapping):
    """ Transforms column of demand dataframe to regions defined by dictionary mapping
        :params pandas.DataFrame demand: dataframe for the demand
        :params dict mapping: dictionary mapping of BA columns to regions
        :return: (*pandas.DataFrame*) -- dataframe with demand columns according to region
    """
    agg_demand = pd.DataFrame(index=demand.index)
    for key in mapping:
        mapping_BAs = mapping[key]
        validColumns = list(set(mapping_BAs) & set(demand.columns))
        if len(validColumns) < len(mapping_BAs):
            print()
            print('******************************')
            print(f'Missing BA columns for {key}!')
            print(f'Original columns: {mapping_BAs}')
            print('******************************')

        print(f'{key} regional demand was summed from {validColumns}')
        print()
        if demand[validColumns].shape[1] > 1:
            agg_demand[key] = demand[validColumns].sum(axis=1)
        else:
            agg_demand[key] = demand[validColumns]
    return agg_demand
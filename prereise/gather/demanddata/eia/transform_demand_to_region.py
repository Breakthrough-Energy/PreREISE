import pandas as pd


def transform_ba_to_region(demand, mapping):
    """ Transforms column of demand dataframe to regions defined by dictionary mapping
        :params pandas.DataFrame demand: dataframe for the demand
        :params dict mapping: dictionary mapping of BA columns to regions
        :return: (*pandas.DataFrame*) -- dataframe with demand columns according to region
    """
    agg_demand = pd.DataFrame(index=demand.index)
    for key in mapping:
        mapping_bas = mapping[key]
        valid_columns = list(set(mapping_bas) & set(demand.columns))
        if len(valid_columns) < len(mapping_bas):
            print()
            print('******************************')
            print(f'Missing BA columns for {key}!')
            print(f'Original columns: {mapping_bas}')
            print('******************************')

        print(f'{key} regional demand was summed from {valid_columns}')
        print()
        if demand[valid_columns].shape[1] > 1:
            agg_demand[key] = demand[valid_columns].sum(axis=1)
        else:
            agg_demand[key] = demand[valid_columns]
    return agg_demand

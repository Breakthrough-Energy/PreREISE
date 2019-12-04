import pandas as pd


def replace_with_shifted_demand(demand, start, end):
    """ Replaces missing data within overall demand dataframe with averages of nearby shifted demand
        :param pandas.DataFrame demand: Dataframe with hourly demand where the columns are BA regions
        :param datetime.datetime start: Datetime for start of period of interest
        :param datetime.datetime end: Datetime for end of period of interest
        :return: (*pandas.DataFrame*) -- Data frame with missing demand data filled in
    """
    look_back1day = demand.shift(1, freq='D')
    look_back2day = demand.shift(2, freq='D')
    look_back1week = demand.shift(7, freq='D')
    look_forward1day = demand.shift(-1, freq='D')
    look_forward2day = demand.shift(-2, freq='D')
    look_forward1week = demand.shift(-7, freq='D')

    shifted_demand = pd.concat([demand, look_back1day, look_forward1day, look_back2day, look_forward2day,
                                look_back1week, look_forward1week], axis=1)
    shifted_demand = shifted_demand.loc[start:end]
    shifted_demand['dayofweek'] = shifted_demand.index.dayofweek 
    column_names = ['look_back1day', 'look_forward1day', 'look_back2day', 'look_forward2day', 'look_back1week',
                    'look_forward1week', 'dayofweek']

    day_map = {0: 'look_forward1day', 1: ['look_forward1day', 'look_back1day'], 2: ['look_forward1day', 'look_back1day'],
               3: ['look_forward1day', 'look_back1day'], 4: 'look_back1day', 5: 'look_forward1day', 6: 'look_back1day'}
    more_days_map = {0: 'look_forward2day', 1: 'look_forward2day', 2: ['look_back2day', 'look_forward2day'],
                     3: 'look_back2day', 4: 'look_back2day', 5: ['look_back1week', 'look_forward1week'],
                     6: ['look_back1week', 'look_forward1week']}
    more_more_days_map = {0: ['look_back1week', 'look_forward1week'], 1: ['look_back1week', 'look_forward1week'],
                          2: ['look_back1week', 'look_forward1week'], 3: ['look_back1week', 'look_forward1week'],
                          4: ['look_back1week', 'look_forward1week'], 5: ['look_back1week', 'look_forward1week'],
                          6: ['look_back1week', 'look_forward1week']}

    filled_demand = pd.DataFrame(index=demand.index)
    for baName in demand.columns:
        shifted_demand_ba = shifted_demand[[baName, 'dayofweek']]
        shifted_demand_ba.columns = [baName] + column_names
        shifted_demand_ba[baName] = fill_ba_demand(shifted_demand_ba, baName, day_map)
        shifted_demand_ba[baName] = fill_ba_demand(shifted_demand_ba, baName, more_days_map)
        filled_demand[baName] = fill_ba_demand(shifted_demand_ba, baName, more_more_days_map)
    return filled_demand


def fill_ba_demand(df_ba, ba_name, day_map):
    """ Replaces missing data in BA demand and returns result
        :param pandas.DataFrame df_ba: dataframe for BA demand, shifted demand, and day of the week
        :param str ba_name: Name of the BA in dataframe
        :param dict day_map: Mapping for replacing missing demand data with shifted demand
        :return: (*pandas.DataFrame*) --  BA dataseries with demand filled in 
    """
    for day in range(0, 7):
        if len(df_ba[day_map[day]].shape) > 1:
            df_ba.loc[(df_ba.dayofweek == day) & (df_ba[ba_name].isna()), ba_name] = df_ba[day_map[day]].mean(axis=1)
        else:
            df_ba.loc[(df_ba.dayofweek == day) & (df_ba[ba_name].isna()), ba_name] = df_ba[day_map[day]]
    return df_ba[ba_name]

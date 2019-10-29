import pandas as pd

def replace_with_shifted_demand(demand, start, end):
    """ Downloads the demand between the start and end dates for a list of BAs
        :param dataframe demand Dataframe with hourly demand where the columns are BA regions
        :param datetime start Datetime for start of period of interest
        :param datetime end Datetime for end of period of interest
    """
    look_back1day = demand.shift(1, freq ='D')
    look_back2day = demand.shift(2, freq ='D') 
    look_back1week = demand.shift(7, freq ='D') 
    look_forward1day = demand.shift(-1, freq ='D')
    look_forward2day = demand.shift(-2, freq ='D')
    look_forward1week = demand.shift(-7, freq ='D') 

    shifted_demand = pd.concat([demand, look_back1day, look_forward1day, look_back2day, look_forward2day, look_back1week, look_forward1week], axis = 1)
    shifted_demand = shifted_demand.loc[start:end]
    shifted_demand['dayofweek'] = shifted_demand.index.dayofweek 
    columnNames = ['look_back1day', 'look_forward1day', 'look_back2day', 'look_forward2day', 'look_back1week', 'look_forward1week','dayofweek']

    dayMap = {0: 'look_forward1day', 1: ['look_forward1day','look_back1day'], 2: ['look_forward1day','look_back1day'], 3: ['look_forward1day','look_back1day'], 4: 'look_back1day', 5: 'look_forward1day', 6: 'look_back1day'}
    moreDaysMap = {0:'look_forward2day', 1: 'look_forward2day', 2: ['look_back2day', 'look_forward2day'], 3: 'look_back2day', 4: 'look_back2day', 5: ['look_back1week', 'look_forward1week'], 6: ['look_back1week', 'look_forward1week']}
    moreMoreDaysMap = {0: ['look_back1week', 'look_forward1week'], 1: ['look_back1week', 'look_forward1week'], 2: ['look_back1week', 'look_forward1week'], 3: ['look_back1week', 'look_forward1week'], 4: ['look_back1week', 'look_forward1week'], 5: ['look_back1week', 'look_forward1week'], 6: ['look_back1week', 'look_forward1week']}

    filled_demand = pd.DataFrame(index=demand.index)
    for baName in demand.columns:
        shifted_demand_BA = shifted_demand[[baName, 'dayofweek']]
        shifted_demand_BA.columns = [baName] + columnNames
        shifted_demand_BA[baName] = fill_ba_demand(shifted_demand_BA, baName, dayMap)
        shifted_demand_BA[baName] = fill_ba_demand(shifted_demand_BA, baName, moreDaysMap)
        filled_demand[baName] = fill_ba_demand(shifted_demand_BA, baName, moreMoreDaysMap)
    return filled_demand

def fill_ba_demand(df_BA, baName, dayMap):
    """ Downloads the demand between the start and end dates for a list of BAs
        :param dataframe df_BA Dataframe for BA demand, shifted demand, and day of the week
        :param str baName Name of the BA in dataframe
        :param dict dayMap Mapping for replacing missing demand data with shifted demand
    """
    for day in range(0,7):
        if len(df_BA[dayMap[day]].shape) > 1:
            df_BA.loc[(df_BA.dayofweek == day) & (df_BA[baName].isna()) , baName] = df_BA[dayMap[day]].mean(axis = 1)
        else:
            df_BA.loc[(df_BA.dayofweek == day) & (df_BA[baName].isna()) , baName] = df_BA[dayMap[day]]
    return df_BA[baName]
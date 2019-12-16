import pandas as pd
import requests as r
from pandas.io.json import json_normalize


def get_BA_demand(ba_code_list, start_date, end_date, api_key):
    """ Downloads the demand between the start and end dates for a list of BAs
        :param pandas.DataFrame ba_code_list: List of balancing authorities to download from eia
        :param datetime.datetime start_date: beginning bound for the demand dataframe
        :param datetime.datetime end_date: end bound for the demand dataframe
        :return: (*pandas.DataFrame*) -- dataframe with columns of demand by BA
    """
    time_interval = pd.date_range(start_date, end_date, tz="UTC", freq='H')
    df_all = pd.DataFrame(index=time_interval)
    
    for ba in ba_code_list:
        try:
            response = r.get('https://api.eia.gov/series/?api_key=' + api_key + '&series_id=EBA.' + ba + '-ALL.D.H')

            df = json_normalize(response.json(), ['series', 'data'])
            df.columns = ['datetime', ba]

            df.index = pd.to_datetime(df['datetime'])
            df.drop(columns=['datetime'], inplace=True)
            df_all = pd.concat([df_all, df], join='outer', axis=1)
            
        except Exception as e:
            print(ba + ' not found')
    
    return df_all

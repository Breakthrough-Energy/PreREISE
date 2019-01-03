import os
import pandas as pd
from westernintnet.westernintnet import win_data


def get_profile(start='2016-01-01-00', end='2016-12-31-23'):
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)

    scaler = pd.read_csv(os.path.dirname(__file__) + '/cf.csv', header=None,
                         index_col=0, names=['timestamp', 'cf'])
    scaler.index = pd.to_datetime(scaler.index)
    scaler = scaler.reindex(pd.date_range(start=scaler.index[0],
                                          end=scaler.index[-1],
                                          freq='H'))
                                          
    if scaler.index.contains(start) is False:
            print("Starting date must be within [2015-01-15, 2017-12-15]")
            raise Exception("Invalid start date")

    if scaler.index.contains(end) is False:
            print("Ending date must be within [2015-01-15, 2017-12-15]")
            raise Exception("Invalid end date")

    if  start >=  end:
            print("Starting date must be greater than ending date")
            raise Exception("Invalid end date")

    scaler.interpolate(method='time', inplace=True)    
    scaler = scaler[start:end]

    hydro_plant = win_data.genbus.groupby('type').get_group('hydro')

    data = scaler.copy()
    for i in hydro_plant.index:
        data[i] = data.cf * hydro_plant.loc[i].GenMWMax

    data.drop('cf', inplace=True, axis=1)
    
    return data

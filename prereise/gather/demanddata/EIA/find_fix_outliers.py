import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from dateutil.parser import parse

sys.path.append("..")


def slope_interpolate(ba_df, threshold):
    '''
    Look for demand outliers by applying a zscore
    threshold to the demand slope

    Replace anomalous values by linear interpolation
    Loop through all the outliers in the outlier_index_list
    Determine the non-outlier edgepoints, then interpolate
    a line joining these 2 edgepoints. Use the line value at
    the timestamp of the the outlier event to replace the
    anomalous value.

    :param dataframe ba_df: demand pandas dataframe with \ 
    UTC Time as index and BA name as column name
    :param float threshold: absolute value of z-score, \ 
    above which a data point is considered an outlier

    :return: data frame indexed with hourly UTC time and \ 
    with anomalous demand values replaced be interpolated \ 
    values.

    It is implicitly assumed that
    1) demand is correlated with temperature, and temperature rise
    is limited by heat capacity which is finite and generally uniform
    across region; hence, temperature dependent derivative spikes are
    unphysical
    2) there is indeed nothing anomalous that happened to electrical
    usage in the relevant time range, so using a line to estimate the 
    correct value is reasonable.

    To do: If there are more than a few hours (say > 4) of anomalous
    behavior, linear interpolation may give a bad estimate.
    Non-linear interpolation methods should be considered, and
    other  information may be needed to interpolate properly,
    for example, the temperature data or other relevant profiles.

    '''
    df = ba_df.copy()
    ba_name = df.columns[0]

    df['delta'] = df[ba_name].diff()
    delta_mu = df['delta'].describe().loc['mean']
    delta_sigma = df['delta'].describe().loc['std']
    df['delta_zscore'] = np.abs((df['delta'] - delta_mu)/delta_sigma)

    # Find the outliers
    outlier_index_list = df.loc[df['delta_zscore'] > 3].index

    # Replace outliers
    hour_save = -1
    for i in outlier_index_list:
        hour_index = df.index.get_loc(i)
        if hour_save == -1:
            hour_save = hour_index
            next_save = hour_index + 1
            continue
        if hour_index == next_save:
            next_save = next_save + 1
            continue
        num = next_save - hour_save
        start = df.iloc[hour_save-1][ba_name]
        dee = (df.iloc[next_save-1][ba_name] - start)/num
        for j in range(hour_save-1, next_save):
            save_me = df.iloc[j][ba_name]
            df.iloc[j][ba_name] = start + (j - hour_save + 1)*dee
            print(j, save_me, df.iloc[j][ba_name])
        hour_save = hour_index
        next_save = hour_index + 1
    if hour_save != -1:
        num = next_save - hour_save
        start = df.iloc[hour_save-1][ba_name]
        dee = (df.iloc[next_save-1][ba_name] - start)/num
        for j in range(hour_save-1, next_save):
            save_me = df.iloc[j][ba_name]
            df.iloc[j][ba_name] = start + (j - hour_save + 1)*dee
            print(j, save_me, df.iloc[j][ba_name])

    return df

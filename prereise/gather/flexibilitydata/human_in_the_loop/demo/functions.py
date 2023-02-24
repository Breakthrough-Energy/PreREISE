import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from tslearn.utils import to_time_series_dataset
from tslearn.clustering import TimeSeriesKMeans
import torch
import torch.nn as nn

def scale_df(df):
    
    time = df.index
    users = df.columns

    scaler = StandardScaler()
    scaler = scaler.fit(df)
    df_scaled = pd.DataFrame(scaler.transform(df))
    df_scaled.columns = users
    df_scaled.index = time
    
    return df_scaled

def get_cluster_ts(df, start, end, ts_length):

    
    df_norm = df.iloc[:, :-1].copy()
    temp = df_norm.loc[(df_norm.index.hour >= start) & (df_norm.index.hour <= end)].copy()
    
    arr = []
    idx = []
    for i in range(0, len(temp), ts_length):
        arr.append(temp.iloc[i:i+ts_length])
        idx.append(temp.index[i:i+ts_length])
    
    formatted_dataset = to_time_series_dataset(arr)

    return formatted_dataset, idx

def similar_day(df, user, weather, idx, y_pred, cluster_num, title, ts_length, mean=True):
    
    cluster = np.where(y_pred == cluster_num)[0]
      
    if len(cluster) != 0:
        temp_idx = np.array(idx)[cluster]
        
        cluster_weather_idx = pd.DataFrame()
        for i in temp_idx:
            cluster_weather_idx = pd.concat((cluster_weather_idx, pd.DataFrame(i)))
        
        cluster_weather_idx = pd.to_datetime(cluster_weather_idx.iloc[:, 0].astype(str))
        
        cluster_weather = weather.loc[weather.index.intersection(cluster_weather_idx)].copy()
        
        if len(cluster_weather) < ts_length*20:
            alpha=1
            lw=1
        else:
            alpha=0.2
            lw=0.5
        
        # plt.figure(figsize=(10,5))
        # for i in range(0, len(cluster_weather), ts_length):
        #     temp_temp = cluster_weather['Temperature'].iloc[i:i+ts_length].copy()
        #     wind_temp = cluster_weather['Wind Speed'].iloc[i:i+ts_length].copy()
        #     hum_temp = cluster_weather['Relative Humidity'].iloc[i:i+ts_length].copy()
        #     # print(temp.describe())label='humidity', label='wind speed'
        #     plt.plot(temp_temp.values, c='red', alpha=alpha, lw=lw)
        #     plt.plot(hum_temp.values, c='blue', alpha=alpha, lw=lw)
        #     plt.plot(wind_temp.values, c='green', alpha=alpha, lw=lw)
        #     plt.xlabel(f'Hours (total {ts_length/4} hours, 15-min interval)')
        #     plt.title(f'Cluster {cluster_num} Weather for {title}')  
        user_similar_day = df[user].loc[df.index.intersection(cluster_weather_idx)].copy()
        
        period = user_similar_day.index.to_series().apply(lambda x: x.replace(hour=0, minute=0)).to_frame()
        period.columns = ['new time']
        period = period.set_index('new time').index.drop_duplicates(keep='first')
        
        temp = pd.DataFrame()
        j=0
        for i in period:
            start = i
            end = start + timedelta(days=1)
            if (user_similar_day.loc[(user_similar_day.index >= start) & (user_similar_day.index < end)].mean() != 0) and (len(user_similar_day.loc[(user_similar_day.index >= start) & (user_similar_day.index < end)]) == 24):
                new_day = user_similar_day.loc[(user_similar_day.index >= start) & (user_similar_day.index < end)]
                new_day.columns = [start.strftime('%Y-%m-%d')]
                # temp = pd.concat([temp, new_day], axis=1)
                temp.insert(0, start.strftime('%Y-%m-%d'), user_similar_day.loc[(user_similar_day.index >= start) & (user_similar_day.index < end)].values)
                j+=1
            
        if mean == True:
            return temp.mean(axis=1)
        else:
            return temp

def train(weather, cluster_num, season, dayofweek, time, ts_length):
    
    if dayofweek == 'Weekday':
        weather_temp = weather.loc[(weather['day of week'] != 'Saturday') & (weather['day of week'] != 'Sunday')]
    elif dayofweek == 'Weekend':
        weather_temp = weather.loc[(weather['day of week'] == 'Saturday') | (weather['day of week'] == 'Sunday')]
    
    if season == 'Summer':
        weather_temp = weather_temp.loc[(weather_temp.index.month >= 5) & (weather_temp.index.month <= 10)]
    elif season == 'Winter':
        weather_temp = weather_temp.loc[(weather_temp.index.month < 5) | (weather_temp.index.month > 10)]
        
    if time == 'Morning':
        weather_time, time_idx = get_cluster_ts(weather_temp, 0, 5, ts_length)
    elif time == 'Noon':
        weather_time, time_idx = get_cluster_ts(weather_temp, 6, 11, ts_length)
    elif time == 'Evening':
        weather_time, time_idx = get_cluster_ts(weather_temp, 12, 17, ts_length)
    elif time == 'Night':
        weather_time, time_idx = get_cluster_ts(weather_temp, 18, 23, ts_length)

    seed = 42
    km = TimeSeriesKMeans(n_clusters=cluster_num, random_state=seed)
    
    y_pred = km.fit_predict(weather_time)
    
    return time_idx, km, y_pred

def predict(weather, km, season, dayofweek, time, ts_length):
    
    if dayofweek == 'Weekday':
        weather_temp = weather.loc[(weather['day of week'] != 'Saturday') & (weather['day of week'] != 'Sunday')]
    elif dayofweek == 'Weekend':
        weather_temp = weather.loc[(weather['day of week'] == 'Saturday') | (weather['day of week'] == 'Sunday')]
    
    if season == 'Summer':
        weather_temp = weather_temp.loc[(weather_temp.index.month >= 5) & (weather_temp.index.month <= 10)]
    elif season == 'Winter':
        weather_temp = weather_temp.loc[(weather_temp.index.month < 5) | (weather_temp.index.month > 10)]
          
    if time == 'Morning':
        weather_time, time_idx = get_cluster_ts(weather_temp, 0, 5, ts_length)
    elif time == 'Noon':
        weather_time, time_idx = get_cluster_ts(weather_temp, 6, 11, ts_length)
    elif time == 'Evening':
        weather_time, time_idx = get_cluster_ts(weather_temp, 12, 17, ts_length)
    elif time == 'Night':
        weather_time, time_idx = get_cluster_ts(weather_temp, 18, 23, ts_length)
    
    y_pred = km.predict(weather_time)
    
    return time_idx, km, y_pred

def plot_flex_label(df, Y, arr, plot_profile=True, plot_ratio=True):
    
    if len(arr) == 1:
        size = 1
        
        temp_df = pd.DataFrame()
        j=0
        for i in range(0, len(df.columns)):
            temp = df.iloc[:, i].copy()
            if temp.iloc[-3] == arr[0]:
                temp_df.insert(0, j, df.iloc[:, i])
                j+=1
    else:
        if len(arr) == 2:
            size = 2
        elif len(arr) == 3:
            size = 3
    
        temp_df = pd.DataFrame()
        j=0
        for i in range(0, len(df.columns)):
            temp = df.iloc[:, i].copy()
            if sum(temp.iloc[-size:].values == arr) == size:
                temp_df.insert(0, j, df.iloc[:, i])
                j+=1
    
    flex_label = temp_df.iloc[-3, :].copy()
    
    if plot_profile:
        # plt.plot(temp_df.iloc[:-3, :], c='red', lw=0.2, alpha=0.2)
        plt.plot(temp_df.iloc[:-3, :].mean(axis=1), c='red')
        plt.title(f'Original - {arr}')
        plt.xlabel('Time (hours)')
        plt.ylabel('Flexibility')
        plt.show()
        plt.close('all')
    
    if plot_ratio:
        high = sum(flex_label == 2)
        med = sum(flex_label == 1)
        low = sum(flex_label == 0)
        
        ratio = np.array([round((high/temp_df.shape[1])*100, 2), round((med/temp_df.shape[1])*100, 2), round((low/temp_df.shape[1])*100, 2)])
        
        plt.figure(figsize=(7,7))
        plt.pie(ratio, labels=[f'high: {ratio[0]}%', f'medium: {ratio[1]}%', f'low: {ratio[2]}%'])
        plt.legend()
        plt.title(f'Original distribution for {arr}; totally {j} samples')
        plt.show()
        plt.close('all')
        

def get_gen_flex_label(generated, seq_num, arr, plot=True):
    flex_label = []
    
    for i in generated.columns:
        flex_avg = generated[i].iloc[15:19].copy()
        flex_avg.loc[flex_avg == 0] = np.NaN
        flex_avg = flex_avg.mean()
        
        other_avg = generated[i].loc[np.r_[0:14, 18:-1]].mean()
        delta = other_avg - flex_avg 
        
        if delta >= 0.5:
            flex_label = np.append(flex_label, 2)
        elif delta < 0.5 and delta >= 0.2:
            flex_label = np.append(flex_label, 1)
        elif delta < 0.2:
            flex_label = np.append(flex_label, 0)
    
    generated.loc[len(generated)]= flex_label

    if plot:
        high = sum(generated.iloc[-1, :] == 2)
        med = sum(generated.iloc[-1, :] == 1)
        low = sum(generated.iloc[-1, :] == 0)
        
        ratio = np.array([round((high/seq_num)*100, 2), round((med/seq_num)*100, 2), round((low/seq_num)*100, 2)])
        
        plt.figure(figsize=(7,7))
        plt.pie(ratio, labels=[f'high: {ratio[0]}', f'medium: {ratio[1]}', f'low: {ratio[2]}'])
        plt.legend()
        plt.title(f'Generated distribution for {arr}')
        plt.show()
        plt.close('all')

def get_x_and_y(df, norm=True, standard=False):
    X = df.iloc[:-3, :].copy()
    Y = df.iloc[-3:, :].copy()
    
    if norm == True:
        x_max = X.max()
        x_min = X.min()
        
        X = (X-x_min) / (x_max - x_min)

    if standard:
        
        x_max = X.mean()
        x_min = X.std()
        X = (X - x_max) / x_min
        
    else:
        x_max = None
        x_min = None
        
    X = X.values.T
    Y = Y.values.T
    
    return X, Y, x_max, x_min
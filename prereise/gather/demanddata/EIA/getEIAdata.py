import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import numpy as np
import pandas as pd
from dateutil.parser import parse
from pandas.tseries.offsets import DateOffset 


def from_download(tok, startdate, enddate, offsetdays, serieslist):
    '''
    Download and assemble dataset of demand data per balancing authority
    for desired date range.

    :param string tok: token obtained by registering with EIA
    :param timestamp start: start date
    :param timestamp end: end data
    :param list serieslist: list of demand series names provided by EIA,
    e.g., ['EBA.AVA-ALL.D.H', 'EBA.AZPS-ALL.D.H']
    :param int offsetdays: number of business days for data to stabilize
    :return: return Dataframe indexed with hourly UTC time and BA series
    name for column names

    '''
    df = {}

    for x in serieslist:
        BA = x
        print('Downloading', BA)
        d = EIAgov(tok, [x])
        df[BA] = d.GetData()
        df[BA].index = pd.to_datetime(df[BA]['Date'])
        df[BA].drop(columns=['Date'], inplace=True)

    timespan = pd.date_range(startdate,
                             enddate - DateOffset(days=offsetdays),
                             freq='H')

    df_all = pd.DataFrame(index=timespan)
    for x in serieslist:
        df_all = pd.concat([df_all, df[x]], axis=1)

    return df_all


def from_excel(directory, serieslist, startdate, enddate):
    '''
    Assemble EIA balancing authority (BA) data from pre-downloaded
    Excel spreadsheets. The spreadsheets contain data from July 2015
    to present.

    :param string directory: location of Excel files
    :param list serieslist: list of BA initials, e.g., ['PSE',BPAT','CISO']
    :param timestamp startdate: desired start of dataset
    :param timestamp enddate: desired end of dataset
    :return: return Dataframe indexed with hourly UTC time and
               BA series name for column names

    '''

    df = {}

    for x in serieslist:
        print(x)
        filename = x + '.xlsx'
        df[x] = pd.read_excel(io=directory + "/" + filename,
                              header=0, usecols='B,U')
        df[x].index = pd.to_datetime(df[x]['UTC Time'])
        df[x] = df[x].resample('H').asfreq()  # Fill missing times
        df[x].drop(columns=['UTC Time'], inplace=True)
        df[x].rename(columns={"Published D": x}, inplace=True)

    timespan = pd.date_range(startdate, enddate, freq='H')

    df_all = pd.DataFrame(index=timespan)
    for x in serieslist:
        df_all = pd.concat([df_all, df[x]], join='inner', axis=1)

    return df_all


'''
Class EIAgov copied from
https://quantcorner.wordpress.com/2014/11/18/downloading-eias-data-with-python/
on 8/13/2018
'''


class EIAgov(object):
    def __init__(self, token, series):
        '''
        Purpose:
        Initialise the EIAgov class by requesting:
        - EIA token
        - id code(s) of the series to be downloaded

        :param string token: string
        :param list series: string or list of strings


        '''
        self.token = token
        self.series = series

    def Raw(self, ser):
        '''
        Download json files from EIA

        :param list ser: list of filenames
        :raises keyError: when URL or file are not found or
        are not valid

        '''

        url = ('http://api.eia.gov/series/?api_key='
               + self.token + '&series_id=' + ser.upper())

        try:
            response = urlopen(url)
            raw_byte = response.read()
            raw_string = str(raw_byte, 'utf-8-sig')
            jso = json.loads(raw_string)
            return jso

        except HTTPError as e:
            print('HTTP error type.')
            print('Error code: ', e.code)

        except URLError as e:
            print('URL type error.')
            print('Reason: ', e.reason)

    def GetData(self):
        '''
        Convert json files into pandas Dataframe
        
        '''
        date_ = self.Raw(self.series[0])
        date_series = date_['series'][0]['data']
        endi = len(date_series)
        date = []
        for i in range(endi):
            date.append(date_series[i][0])

        df = pd.DataFrame(data=date)
        df.columns = ['Date']

        lenj = len(self.series)
        for j in range(lenj):
            data_ = self.Raw(self.series[j])
            data_series = data_['series'][0]['data']
            data = []
            endk = len(date_series)
            for k in range(endk):
                data.append(data_series[k][1])
            df[self.series[j]] = data

        return df

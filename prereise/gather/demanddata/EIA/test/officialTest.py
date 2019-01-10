
# coding: utf-8

# TODO: why is the download version ignoring the start/end dates?

# In[13]:


import json
import numpy as np
import pandas as pd
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

from datetime import datetime, timedelta

import sys
sys.path.append("..")

import getEIAdata

def test_EIAdownload():
    token = '6d666bb7097e41102ef69a35aa1edb2b'
    offset = 3    
    start = pd.to_datetime('2018-07-01 00:00:00')
    end = pd.to_datetime('2018-10-01 00:00:00')
    timediff = pd.Period(end, freq='H') - pd.Period(start, freq='H')

    demand_list = [
                   'EBA.BANC-ALL.D.H',
                   'EBA.BPAT-ALL.D.H',
                   'EBA.CHPD-ALL.D.H',
                   'EBA.CISO-ALL.D.H'
                  ]
    this = getEIAdata.from_download(token, start, end, offset, demand_list)
    assert all(len(this.columns) == len(demand_list))

def test_from_excel():
    dir1 = 'L:\\Renewable Energy\\EnergyGridModeling\\Data\\Western\\demand_data\\raw\\WECC_demand_2015-2018'

    start = pd.to_datetime('2018-07-01 07:00:00')
    end = pd.to_datetime('2018-10-01 07:00:00')
    BA_list = ['BPAT','CISO','EPE']

    BA_from_excel = getEIAdata.from_excel(dir1, BA_list, start, end)
    assert (len(BA_from_excel.columns) == len(BA_list))


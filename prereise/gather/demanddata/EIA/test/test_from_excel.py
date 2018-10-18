import pytest

import json
import numpy as np
import pandas as pd
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

from datetime import datetime, timedelta
from .. import getEIAdata


def test_from_excel():
    dir1 = 'L:\\Renewable Energy\\EnergyGridModeling\\Data\\Western\\demand_data\\raw\\WECC_demand_2015-2018'

    start = pd.to_datetime('2018-07-01 07:00:00')
    end = pd.to_datetime('2018-10-01 07:00:00')
    BA_list = ['BPAT','CISO','EPE']

    BA_from_excel = getEIAdata.from_excel(dir1, BA_list, start, end)
    assert (len(BA_from_excel.columns) == len(BA_list))


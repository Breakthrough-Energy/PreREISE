import json
import os
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import numpy as np
import pandas as pd
import pytest

from .. import get_eia_data


def test_from_excel():
    """Tests data frame assembled from Excel spreadsheets manually \ 
        downloaded from EIA. Test checks that correct number of columns are \ 
        created.
    """

    dir1 = os.path.join(os.path.dirname(__file__), 'data')

    start = pd.to_datetime('2018-07-01 07:00:00')
    end = pd.to_datetime('2018-10-01 07:00:00')
    ba_list = ['BPAT', 'CISO', 'EPE']

    ba_from_excel = get_eia_data.from_excel(dir1, ba_list, start, end)
    assert (len(ba_from_excel.columns) == len(ba_list))

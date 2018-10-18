import pytest

import json
import numpy as np
import pandas as pd
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

from datetime import datetime

from .. import getEIAdata



def test_EIAdownload():
    token = '6d666bb7097e41102ef69a35aa1edb2b'
    offset = 3    
    start = pd.to_datetime('2018-07-01 07:00:00')
    end = datetime.today()

    demand_list = [
                   'EBA.BANC-ALL.D.H',
                   'EBA.BPAT-ALL.D.H',
                   'EBA.CHPD-ALL.D.H',
                   'EBA.CISO-ALL.D.H'
                  ]
    this = getEIAdata.from_download(token, start, end, offset, demand_list)
    
    assert len(this.columns) == (len(demand_list))



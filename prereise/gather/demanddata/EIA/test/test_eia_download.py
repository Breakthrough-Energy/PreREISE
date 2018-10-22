import getpass
import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import numpy as np
import pandas as pd
import pytest

from .. import get_eia_data


@pytest.mark.skip(reason="Need API key")
def test_eia_download():
    '''
    Check pandas DataFrame assembled from data download \ 
    by API call from EIA. Test checks that the correct \ 
    number of files are downloaded and correct number of \ 
    columns are created.

    Token string can be obtained by registering in 
    https://www.eia.gov/opendata/

    '''
    print(
        'A API key is required for the API download. The key '
        'can be obtained by a user by registering at '
        'https://www.eia.gov/opendata/.'
    )
    token = getpass.getpass(prompt='API key=')

    offset = 3
    start = pd.to_datetime('2018-07-01 07:00:00')
    end = datetime.today()

    demand_list = [
        'EBA.BANC-ALL.D.H',
        'EBA.BPAT-ALL.D.H',
        'EBA.CHPD-ALL.D.H',
        'EBA.CISO-ALL.D.H'
    ]
    this = get_eia_data.from_download(token, start, end, offset, demand_list)

    assert len(this.columns) == (len(demand_list))

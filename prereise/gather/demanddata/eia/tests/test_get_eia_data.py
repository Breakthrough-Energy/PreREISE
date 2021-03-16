import getpass
import os
from datetime import datetime

import pandas as pd
import pytest

from prereise.gather.demanddata.eia import get_eia_data


@pytest.mark.skip(reason="Need API key")
def test_eia_download():
    """Check data frame assembled from data download by API call from EIA. Test
    checks that the correct number of files are downloaded and correct
    number of columns are created.

    Token string can be obtained by registering
    `here <https://www.eia.gov/opendata/>`_.
    """
    print(
        "A API key is required for the API download. The key "
        "can be obtained by a user by registering at "
        "https://www.eia.gov/opendata/."
    )
    token = getpass.getpass(prompt="API key=")

    offset = 3
    start = pd.to_datetime("2018-07-01 07:00:00")
    end = datetime.today()

    demand_list = [
        "EBA.BANC-ALL.D.H",
        "EBA.BPAT-ALL.D.H",
        "EBA.CHPD-ALL.D.H",
        "EBA.CISO-ALL.D.H",
    ]
    this = get_eia_data.from_download(token, start, end, offset, demand_list)

    assert len(this.columns) == (len(demand_list))


def test_from_excel():
    """Tests data frame assembled from Excel spreadsheets manually downloaded
    from EIA. Test checks that correct number of columns are created.
    """

    dir1 = os.path.join(os.path.dirname(__file__), "data")

    start = pd.to_datetime("2018-07-01 07:00:00")
    end = pd.to_datetime("2018-10-01 07:00:00")
    ba_list = ["BPAT", "CISO", "EPE"]

    ba_from_excel = get_eia_data.from_excel(dir1, ba_list, start, end)
    assert len(ba_from_excel.columns) == len(ba_list)

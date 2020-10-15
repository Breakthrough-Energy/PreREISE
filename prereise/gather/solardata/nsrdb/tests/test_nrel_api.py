from datetime import datetime, timedelta

import pandas as pd
import pytest

from prereise.gather.solardata.nsrdb.nrel_api import Psm3Data


def test_check_attrs():
    Psm3Data.check_attrs("dhi,dni,wind_speed,air_temperature,ghi")

    with pytest.raises(ValueError):
        Psm3Data.check_attrs("foo,bar,dhi")


def test_psm3_to_dict():
    date_today = datetime.now()
    df = pd.DataFrame(
        {
            "DNI": [1, 2, 3, 4],
            "Wind Speed": [4, 4, 3, 2],
            "idx": pd.date_range(date_today, date_today + timedelta(3), freq="D"),
        }
    )
    df.set_index("idx", inplace=True)
    psm3 = Psm3Data(1, 2, 8, 8, df)
    psm3_dict = psm3.to_dict()
    for k in ("tz", "elev", "day", "month", "year", "dn", "wspd"):
        assert k in psm3_dict.keys()

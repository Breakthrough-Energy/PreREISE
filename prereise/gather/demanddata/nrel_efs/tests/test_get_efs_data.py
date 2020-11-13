import pandas as pd
from pandas.testing import assert_frame_equal
from powersimdata.network.usa_tamu.constants.zones import abv2state

from prereise.gather.demanddata.nrel_efs.get_efs_data import (
    account_for_leap_year,
    download_data,
    partition_by_sector,
)


def test_download_data():
    pass


def test_partition_by_sector():
    pass


def test_account_for_leap_year():
    # Create dummy aggregate demand DataFrame and obtain the demand mapped to loadzones
    cont_states = sorted(list(set(abv2state) - {"AK", "HI"}))
    dem = pd.DataFrame(
        1,
        index=list(range(8760)),
        columns=cont_states,
    )
    dem.iloc[24:48] += 1
    test_dem = account_for_leap_year(dem)

    # Create the expected result
    exp_dem = pd.DataFrame(
        1,
        index=list(range(8784)),
        columns=cont_states,
    )
    exp_dem.iloc[24:48] += 1
    exp_dem.iloc[8760:8784] += 1

    # Compate the two results
    assert_frame_equal(exp_dem, test_dem)

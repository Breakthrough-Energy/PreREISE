import pandas as pd
from pandas.testing import assert_series_equal
from powersimdata.network.usa_tamu.constants.zones import abv2state

from prereise.gather.demanddata.nrel_efs.map_states import map_to_loadzone


def test_map_to_loadzone():
    # Create dummy aggregate demand DataFrame and obtain the demand mapped to loadzones
    cont_states = sorted(list(set(abv2state) - {"AK", "HI"}))
    agg_dem = pd.DataFrame(
        1,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", closed="left"),
        columns=cont_states,
    )
    agg_dem.index.name = "UTC Time"
    test_agg_dem = map_to_loadzone(agg_dem).round(5)

    # Create the expected result for demand percentage in loadzone 7 (NY)
    exp_agg_dem = pd.Series(
        0.67803,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", closed="left"),
        name=7,
    )
    exp_agg_dem.index.name = "UTC Time"

    # Compare the two results
    assert_series_equal(exp_agg_dem, test_agg_dem[7])

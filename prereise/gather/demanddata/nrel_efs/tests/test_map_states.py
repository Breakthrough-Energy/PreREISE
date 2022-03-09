import pandas as pd
from pandas.testing import assert_series_equal
from powersimdata.network.usa_tamu.constants.zones import abv2state, id2abv

from prereise.gather.demanddata.nrel_efs.map_states import (
    decompose_demand_profile_by_state_to_loadzone,
    shift_local_time_by_loadzone_to_utc,
)


def test_decompose_demand_profile_by_state_to_loadzone():
    # Create dummy aggregate demand DataFrame
    cont_states = sorted(set(abv2state) - {"AK", "HI"})
    agg_dem = pd.DataFrame(
        1,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
        columns=cont_states,
    )
    agg_dem.index.name = "Local Time"

    # Generate the test result
    test_agg_dem = decompose_demand_profile_by_state_to_loadzone(
        agg_dem, "demand"
    ).round(5)

    # Create the expected result for demand percentage in load zone 7 (NY)
    exp_agg_dem = pd.Series(
        0.67803,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
        name=7,
    )
    exp_agg_dem.index.name = "UTC Time"

    # Compare the two results
    assert_series_equal(exp_agg_dem, test_agg_dem[7])


def test_shift_local_time_by_loadzone_to_utc():
    # Create dummy DataFrame
    agg_dem = pd.DataFrame(
        1,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
        columns=set(id2abv),
    )
    agg_dem.index.name = "Local Time"
    agg_dem.iloc[8712:8736] += 1.0

    # Generate the test result
    test_agg_dem = shift_local_time_by_loadzone_to_utc(agg_dem)

    # Create the expected result for UTC-shifted demand in load zone 1 (ME)
    exp_agg_dem = pd.Series(
        1.0,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
        name=1,
    )
    exp_agg_dem.index.name = "UTC Time"
    exp_agg_dem.iloc[0:5] += 1
    exp_agg_dem.iloc[8717:8741] += 1

    # Compare the two results
    assert_series_equal(exp_agg_dem, test_agg_dem[1])

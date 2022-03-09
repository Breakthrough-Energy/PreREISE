import pandas as pd
from pandas.testing import assert_frame_equal
from powersimdata.network.usa_tamu.constants.zones import abv2state

from prereise.gather.demanddata.nrel_efs.aggregate_demand import combine_efs_demand


def test_combine_efs_demand():
    # Create a dummy data set
    cont_states = sorted(set(abv2state) - {"AK", "HI"})
    dummy_data = pd.DataFrame(
        1,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
        columns=cont_states,
    )
    dummy_data.index.name = "Local Time"

    # Create a dict containing four instances of dummy_data
    dummy_dict = {}
    for i in {"Transportation", "Residential", "Commercial", "Industrial"}:
        dummy_dict[i] = dummy_data

    # Generate the test result
    test_agg_dem = combine_efs_demand(efs_dem=dummy_dict)

    # Create the expected result
    exp_agg_dem = pd.DataFrame(
        4,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
        columns=cont_states,
    )
    exp_agg_dem.index.name = "Local Time"

    # Compare the two DataFrames
    assert_frame_equal(exp_agg_dem, test_agg_dem)

import os

import pandas as pd
from pandas.testing import assert_frame_equal
from powersimdata.network.usa_tamu.constants.zones import abv2state

from prereise.gather.demanddata.nrel_efs.aggregate_demand import (
    combine_efs_demand,
)


def test_combine_efs_demand():
    # Create a dummy data set
    cont_states = sorted(list(set(abv2state) - {"AK", "HI"}))
    dummy_data = pd.DataFrame(
        1,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", closed="left"),
        columns=cont_states,
    )
    dummy_data.index.name = "Local Time"

    # Create dummy sectoral demand data sets
    dummy_data.to_csv("Commercial_Demand_Medium_Moderate_2050.csv")
    dummy_data.to_csv("Industrial_Demand_Medium_Moderate_2050.csv")
    dummy_data.to_csv("Residential_Demand_Medium_Moderate_2050.csv")
    dummy_data.to_csv("Transportation_Demand_Medium_Moderate_2050.csv")

    # Generate the test result
    test_agg_dem = combine_efs_demand(
        es="Medium",
        ta="Moderate",
        year=2050,
        local_sects={"All"},
        local_paths={
            "Commercial_Demand_Medium_Moderate_2050.csv",
            "Industrial_Demand_Medium_Moderate_2050.csv",
            "Residential_Demand_Medium_Moderate_2050.csv",
            "Transportation_Demand_Medium_Moderate_2050.csv",
        },
    )

    # Create the expected result
    exp_agg_dem = pd.DataFrame(
        4,
        index=pd.read_csv(
            "Commercial_Demand_Medium_Moderate_2050.csv", index_col="Local Time"
        ).index,
        columns=cont_states,
    )
    exp_agg_dem.index.name = "Local Time"

    # Compare the two DataFrames
    assert_frame_equal(exp_agg_dem, test_agg_dem, check_index_type=False)

    # Remove the dummy data sets
    os.remove("Commercial_Demand_Medium_Moderate_2050.csv")
    os.remove("Industrial_Demand_Medium_Moderate_2050.csv")
    os.remove("Residential_Demand_Medium_Moderate_2050.csv")
    os.remove("Transportation_Demand_Medium_Moderate_2050.csv")

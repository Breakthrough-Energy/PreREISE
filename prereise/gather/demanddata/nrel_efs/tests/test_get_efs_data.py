import os

import pandas as pd
from pandas.testing import assert_frame_equal
from powersimdata.network.usa_tamu.constants.zones import abv2state

from prereise.gather.demanddata.nrel_efs.get_efs_data import (
    account_for_leap_year,
    download_data,
    partition_by_sector,
)


def test_download_data():
    # Download one of the EFS data sets
    download_data(es={"Reference"}, ta={"Slow"}, fpath="")

    try:
        # Load the downloaded EFS data set
        df = pd.read_csv("EFSLoadProfile_Reference_Slow.csv")

        # Access the columns
        test_cols = list(df.columns)
        exp_cols = [
            "Electrification",
            "TechnologyAdvancement",
            "Year",
            "LocalHourID",
            "State",
            "Sector",
            "Subsector",
            "LoadMW",
        ]

        # Compare the two values
        assert len(test_cols) == len(exp_cols)

        # Remove the downloaded EFS data set
        os.remove("EFSLoadProfile_Reference_Slow.csv")

    except FileNotFoundError:
        # If the automated extraction did not work, check that the .zip file was created
        assert os.path.isfile("EFSLoadProfile_Reference_Slow.zip")

        # Remove the downloaded .zip file
        os.remove("EFSLoadProfile_Reference_Slow.zip")


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

    # Compare the two values
    assert_frame_equal(exp_dem, test_dem)

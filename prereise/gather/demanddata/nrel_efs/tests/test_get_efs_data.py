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
    download_data(es={"Reference"}, ta={"Slow"})

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


def test_partition_by_sector():
    # Create a dummy data set
    cont_states = sorted(list(set(abv2state) - {"AK", "HI"}))
    dummy_data = {
        "Electrification": [1] * 4 * 48 * 8760,
        "TechnologyAdvancement": [1] * 4 * 48 * 8760,
        "Year": [2030] * 4 * 48 * 8760,
        "LocalHourID": sorted([i for i in range(1, 8761)] * 4 * 48),
        "State": sorted([i for i in cont_states] * 4) * 8760,
        "Sector": ["Commercial", "Industrial", "Residential", "Transportation"]
        * 48
        * 8760,
        "LoadMW": [1, 2, 3, 4] * 48 * 8760,
    }
    dummy_df = pd.DataFrame(data=dummy_data)
    dummy_df.to_csv("EFSLoadProfile_High_Rapid.csv", index=False)

    # Generate the test results
    test_sect_dem = partition_by_sector(es="High", ta="Rapid", year=2030, save=False)

    # Create the expected results
    exp_res_dem = pd.DataFrame(
        3,
        index=pd.date_range("2016-01-01", "2017-01-01", freq="H", closed="left"),
        columns=cont_states,
    )
    exp_res_dem.index.name = "Local Time"

    # Compare the two DataFrames
    assert_frame_equal(exp_res_dem, test_sect_dem["Residential"])


def test_account_for_leap_year():
    # Create dummy aggregate demand DataFrame
    cont_states = sorted(list(set(abv2state) - {"AK", "HI"}))
    dem = pd.DataFrame(
        1,
        index=list(range(8760)),
        columns=cont_states,
    )
    dem.iloc[24:48] += 1

    # Generate the test result
    test_dem = account_for_leap_year(dem)

    # Create the expected result
    exp_dem = pd.DataFrame(
        1,
        index=list(range(8784)),
        columns=cont_states,
    )
    exp_dem.iloc[24:48] += 1
    exp_dem.iloc[8760:8784] += 1

    # Compare the two DataFrames
    assert_frame_equal(exp_dem, test_dem)

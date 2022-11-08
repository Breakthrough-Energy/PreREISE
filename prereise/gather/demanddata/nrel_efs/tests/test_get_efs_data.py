import os
import zipfile

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from powersimdata.network.model import ModelImmutables

from prereise.gather.demanddata.nrel_efs.get_efs_data import (
    _check_electrification_scenarios_for_download,
    _check_path,
    _check_technology_advancements_for_download,
    _download_data,
    _extract_data,
    account_for_leap_year,
    partition_demand_by_sector,
    partition_flexibility_by_sector,
)

mi = ModelImmutables("usa_tamu")
abv2state = mi.zones["abv2state"]


def test_check_electrification_scenarios_for_download():
    # Run the check
    test_es = _check_electrification_scenarios_for_download(es={"All"})

    # Specify the expected values
    exp_es = {"Reference", "Medium", "High"}

    # Compare the two sets
    assert test_es == exp_es


def test_check_technology_advancements_for_download():
    # Run the check
    test_ta = _check_technology_advancements_for_download(ta={"All"})

    # Specify the expected values
    exp_ta = {"Slow", "Moderate", "Rapid"}

    # Compare the two sets
    assert test_ta == exp_ta


def test_check_path():
    # Run check
    test_fpath = _check_path(fpath="")

    # Specify the expected file path
    exp_fpath = os.getcwd()

    # Compare the two file paths
    assert test_fpath == exp_fpath


@pytest.mark.integration
def test_download_data():
    try:
        # Download a file using _download_data
        _download_data(
            zip_name="project_resstock_efs_2013.zip",
            url="https://data.nrel.gov/system/files/128/project_resstock_efs_2013.zip",
            fpath="",
        )

        # Check that the expected .zip file was downloaded
        assert os.path.isfile("project_resstock_efs_2013.zip")

    finally:
        # Remove the downloaded .zip file
        os.remove("project_resstock_efs_2013.zip")


@pytest.mark.integration
def test_extract_data():
    # Create a dummy demand data set
    cont_states = sorted(set(abv2state) - {"AK", "HI"})
    dummy_demand_data = {
        "Electrification": ["High"] * 4 * 48 * 8760,
        "TechnologyAdvancement": ["Rapid"] * 4 * 48 * 8760,
        "Year": [2030] * 4 * 48 * 8760,
        "LocalHourID": sorted(list(range(1, 8761)) * 4 * 48),
        "State": sorted(list(cont_states) * 4) * 8760,
        "Sector": ["Commercial", "Industrial", "Residential", "Transportation"]
        * 48
        * 8760,
        "LoadMW": [1, 2, 3, 4] * 48 * 8760,
    }
    dummy_demand_df = pd.DataFrame(data=dummy_demand_data)
    dummy_demand_df.to_csv("test_demand.csv", index=False)

    # Create a .zip file of the dummy demand data set
    with zipfile.ZipFile("test_demand.zip", "w") as z:
        z.write("test_demand.csv")
    os.remove("test_demand.csv")

    try:
        # Try extracting the dummy .csv file from the dummy .zip file
        _extract_data(
            z=None,
            zf_works=False,
            zip_name="test_demand.zip",
            csv_name="test_demand.csv",
            fpath=os.getcwd(),
            sz_path="C:/Program Files/7-Zip/7z.exe",
        )

        # Load the downloaded EFS demand data set
        df = pd.read_csv("test_demand.csv")

        # Access the columns
        test_cols = list(df.columns)
        exp_cols = [
            "Electrification",
            "TechnologyAdvancement",
            "Year",
            "LocalHourID",
            "State",
            "Sector",
            "LoadMW",
        ]

        # Compare the two values
        assert len(test_cols) == len(exp_cols)

    except FileNotFoundError:
        # If the automated extraction did not work, check that the .zip file was created
        assert os.path.isfile("test_demand.zip")

        # Remove the downloaded .zip file
        os.remove("test_demand.zip")

    finally:
        # Remove the downloaded EFS data set
        os.remove("test_demand.csv")


@pytest.mark.integration
def test_partition_demand_by_sector():
    # Create a dummy demand data set
    cont_states = sorted(set(abv2state) - {"AK", "HI"})
    dummy_demand_data = {
        "Electrification": ["High"] * 4 * 48 * 8760,
        "TechnologyAdvancement": ["Rapid"] * 4 * 48 * 8760,
        "Year": [2030] * 4 * 48 * 8760,
        "LocalHourID": sorted(list(range(1, 8761)) * 4 * 48),
        "State": sorted(list(cont_states) * 4) * 8760,
        "Sector": ["Commercial", "Industrial", "Residential", "Transportation"]
        * 48
        * 8760,
        "LoadMW": [1, 2, 3, 4] * 48 * 8760,
    }
    dummy_demand_df = pd.DataFrame(data=dummy_demand_data)
    dummy_demand_df.to_csv("EFSLoadProfile_High_Rapid.csv", index=False)

    try:
        # Generate the test results
        test_sect_dem = partition_demand_by_sector(
            es="High", ta="Rapid", year=2030, save=False
        )

        # Create the expected results
        exp_res_dem = pd.DataFrame(
            3,
            index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
            columns=cont_states,
        )
        exp_res_dem.index.name = "Local Time"

        # Compare the two DataFrames
        assert_frame_equal(exp_res_dem, test_sect_dem["Residential"], check_names=False)

    finally:
        # Delete the test .csv file
        os.remove("EFSLoadProfile_High_Rapid.csv")


@pytest.mark.integration
def test_partition_flexibility_by_sector():
    # Create a dummy flexibility data set
    cont_states = sorted(set(abv2state) - {"AK", "HI"})
    dummy_flex_data = {
        "Electrification": ["High"] * 4 * 48 * 8760,
        "TechnologyAdvancement": ["Rapid"] * 4 * 48 * 8760,
        "Flexibility": ["Base"] * 4 * 48 * 8760,
        "Year": [2030] * 4 * 48 * 8760,
        "LocalHourID": sorted(list(range(1, 8761)) * 4 * 48),
        "State": sorted(list(cont_states) * 4) * 8760,
        "Sector": ["Commercial", "Industrial", "Residential", "Transportation"]
        * 48
        * 8760,
        "LoadMW": [1, 2, 3, 4] * 48 * 8760,
    }
    dummy_flex_df = pd.DataFrame(data=dummy_flex_data)
    dummy_flex_df.to_csv("EFSFlexLoadProfiles_High.csv", index=False)

    try:
        # Generate the test results
        test_sect_flex = partition_flexibility_by_sector(
            es="High", ta="Rapid", flex="Base", year=2030, save=False
        )

        # Create the expected results
        exp_res_flex = pd.DataFrame(
            3,
            index=pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
            columns=cont_states,
        )
        exp_res_flex.index.name = "Local Time"

        # Compare the two DataFrames
        assert_frame_equal(
            exp_res_flex, test_sect_flex["Residential"], check_names=False
        )

    finally:
        # Delete the test .csv file
        os.remove("EFSFlexLoadProfiles_High.csv")


def test_account_for_leap_year():
    # Create dummy aggregate demand DataFrame
    cont_states = sorted(set(abv2state) - {"AK", "HI"})
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

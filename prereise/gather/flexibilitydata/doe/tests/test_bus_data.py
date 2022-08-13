import os
import pickle as pkl

import pandas as pd

from prereise.gather.flexibilitydata.doe.bus_data import get_bus_fips, get_bus_zip


def test_get_bus_fips():
    """Test the FCC Area API using constant dataframe"""
    bus_pos_dict = {
        "bus_id": [1, 2, 3],
        "lat": [29.7404, 38.8977, 30.6066],
        "lon": [-95.3698, -77.0365, -96.3568],
    }
    bus_pos = pd.DataFrame.from_dict(bus_pos_dict)

    # query for fips data, stored in same folder
    get_bus_fips(bus_pos, "")

    # check result
    with open("bus_fips.pkl", "rb") as fh:
        bus_fips = pkl.load(fh)

    assert bus_fips["fips"] == [48201, 11001, 48041]

    # delete file
    os.remove("bus_fips.pkl")


def test_get_bus_zip():
    """Test the geopy OSM query using constant dataframe"""
    bus_pos_dict = {
        "bus_id": [1, 2, 3],
        "lat": [29.7404, 38.8977, 30.6066],
        "lon": [-95.3698, -77.0365, -96.3568],
    }
    bus_pos = pd.DataFrame.from_dict(bus_pos_dict)

    # query for fips data, stored in same folder
    get_bus_zip(bus_pos, "")

    # check result
    with open("bus_zip.pkl", "rb") as fh:
        bus_zip = pkl.load(fh)

    assert bus_zip["zip"] == [77004, 20500, 77845]

    # delete file
    os.remove("bus_zip.pkl")

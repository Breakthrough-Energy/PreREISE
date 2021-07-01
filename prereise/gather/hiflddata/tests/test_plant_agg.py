from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from prereise.gather.hiflddata.plant_agg import (
    cal_pmin,
    clean_p,
    get_loc_of_plant,
    loc_of_sub,
)


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_clean_p(read_csv):
    csv_data_path = "General_Units.csv"
    csv_data = {"STATE": ["AL", "AR"], "STATUS": ["OP", "Other"]}
    read_csv.return_value = pd.DataFrame(data=csv_data)
    clean_data = clean_p(csv_data_path)
    expected_csv_data = {
        "STATE": ["AL"],
        "STATUS": ["OP"],
    }
    expected_result = pd.DataFrame(data=expected_csv_data)
    assert_frame_equal(expected_result, clean_data)


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_loc_of_sub(read_csv):
    csv_data_path = "bus.csv"
    csv_data = {
        "sub_id": ["1-Feb", "1-Mar"],
        "interconnect": ["Eastern", "Western"],
        "zip": ["35476", "36512"],
        "lat": [45.768423361, 45.538501812],
        "lon": [-91.864744373, -90.311812314],
    }
    read_csv.return_value = pd.DataFrame(data=csv_data)
    loc_of_sub_dict, zip_of_sub_dict = loc_of_sub(csv_data_path)
    expected_loc_of_sub_dict = {
        "1-Feb": (45.768423361, -91.864744373),
        "1-Mar": (45.538501812, -90.311812314),
    }
    expected_zip_of_sub_dict = {
        "Eastern": {"35476": ["1-Feb"]},
        "Texas": {},
        "Western": {"36512": ["1-Mar"]},
    }
    assert loc_of_sub_dict == expected_loc_of_sub_dict
    assert zip_of_sub_dict == expected_zip_of_sub_dict


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_cal_pmin(read_csv):
    csv_data_path = "Generator_Y2019.csv"
    csv_data = {
        "Plant Name": ["Sand Point", "Barry"],
        "Minimum Load (MW)": [0.4, 55],
        "Energy Source 1": ["Wind", "Solar"],
    }
    read_csv.return_value = pd.DataFrame(data=csv_data)
    p_min = cal_pmin(csv_data_path)
    expected_pmin = {("SAND POINT", "Wind"): 0.4, ("BARRY", "Solar"): 55.0}
    assert p_min == expected_pmin


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_loc_of_plant(read_csv):
    csv_data = {
        "NAME": ["AMALGAMATED", "CASTLE"],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
    }
    read_csv.return_value = pd.DataFrame(data=csv_data)
    loc_of_plant = get_loc_of_plant()
    expected_loc_of_plant = {
        "AMALGAMATED": (45.76842336, -91.86474437),
        "CASTLE": (45.53850181, -90.31181231),
    }
    assert loc_of_plant == expected_loc_of_plant

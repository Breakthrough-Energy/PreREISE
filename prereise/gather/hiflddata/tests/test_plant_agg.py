# -*- coding: utf-8 -*-
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from prereise.gather.hiflddata.plant_agg import (
    Cal_P,
    Clean_p,
    Loc_of_plant,
    LocOfsub,
    Plant_agg,
)


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_clean_p(read_csv):
    csv_data_path = "General_Units.csv"
    csv_data = {"STATE": ["AL", "AR"], "STATUS": ["OP", "Other"]}
    read_csv.return_value = pd.DataFrame(data=csv_data)
    clean_data = Clean_p(csv_data_path)
    expected_csv_data = {
        "STATE": ["AL"],
        "STATUS": ["OP"],
    }
    expected_result = pd.DataFrame(data=expected_csv_data)
    assert_frame_equal(expected_result, clean_data)


def test_locOfsub():
    csv_data = {
        "ID": ["1-Feb", "1-Mar"],
        "STATE": ["AL", "AR"],
        "ZIP": ["35476", "36512"],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
        "STATUS": ["OP", "OP"],
    }
    clean_data = pd.DataFrame(data=csv_data)
    locOfsub_dict, zipOfsub_dict = LocOfsub(clean_data)
    expected_locOfsub_dict = {
        "1-Feb": ("45.768423360", "-91.864744370"),
        "1-Mar": ("45.538501810", "-90.311812310"),
    }
    expected_zipOfsub_dict = {"35476": ["1-Feb"], "36512": ["1-Mar"]}
    assert locOfsub_dict == expected_locOfsub_dict
    assert zipOfsub_dict == expected_zipOfsub_dict


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_cal_p(read_csv):
    csv_data_path = "Generator_Y2019.csv"
    csv_data = {"Plant Name": ["Sand Point", "Barry"], "Minimum Load (MW)": [0.4, 55]}
    read_csv.return_value = pd.DataFrame(data=csv_data)
    pmin = Cal_P(csv_data_path)
    expected_pmin = {"SAND POINT": 0.4, "BARRY": 55.0}
    assert pmin == expected_pmin


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_loc_of_plant(read_csv):
    csv_data = {
        "NAME": ["AMALGAMATED", "CASTLE"],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
    }
    read_csv.return_value = pd.DataFrame(data=csv_data)
    loc_of_plant = Loc_of_plant()
    expected_loc_of_plant = {
        "AMALGAMATED": ("45.768423360", "-91.864744370"),
        "CASTLE": ("45.538501810", "-90.311812310"),
    }
    assert loc_of_plant == expected_loc_of_plant


def test_plant_agg_when_clean_data_is_empty():
    clean_data = pd.DataFrame(data={})
    actual_result = Plant_agg(clean_data, None, None, None, None)
    assert actual_result == {}


def test_plant_agg_normal_case():
    clean_data = pd.DataFrame(
        data={
            "ZIP": ["35476", "36512"],
            "PLANT": ["BANKHEAD DAM", "BARRY"],
            "TYPE": ["CONVENTIONAL HYDROELECTRIC", "NATURAL GAS STEAM TURBINE"],
            "WINTER_CAP": [53, 55.5],
            "SUMMER_CAP": [53, 55.5],
        }
    )
    pmin = {"BANKHEAD DAM": 0.4, "BARRY": 55.0}
    loc_of_plant = {
        "BANKHEAD DAM": ("45.768423360", "-91.864744370"),
        "BARRY": ("45.538501810", "-90.311812310"),
    }
    locOfsub_dict = {
        "1-Feb": ("45.768423360", "-91.864744370"),
        "1-Mar": ("45.538501810", "-90.311812310"),
    }
    zipOfsub_dict = {"35476": ["1-Feb"], "36512": ["1-Mar"]}
    actual_plant_dict = Plant_agg(
        clean_data, zipOfsub_dict, loc_of_plant, locOfsub_dict, pmin
    )
    expected_plant_dict = {
        ("BANKHEAD DAM", "CONVENTIONAL HYDROELECTRIC"): ["1-Feb", 53.0, 53.0, 0.4],
        ("BARRY", "NATURAL GAS STEAM TURBINE"): ["1-Mar", 55.5, 55.5, 55.0],
    }
    assert actual_plant_dict == expected_plant_dict


def test_plant_agg_when_plant_and_type_in_plant_dict():
    clean_data = pd.DataFrame(
        data={
            "ZIP": ["35476", "35476"],
            "PLANT": ["BANKHEAD DAM", "BANKHEAD DAM"],
            "TYPE": ["CONVENTIONAL HYDROELECTRIC", "CONVENTIONAL HYDROELECTRIC"],
            "WINTER_CAP": [53, 53],
            "SUMMER_CAP": [53, 53],
        }
    )
    pmin = {"BANKHEAD DAM": 0.4, "BANKHEAD DAM": 0.4}
    loc_of_plant = {
        "BANKHEAD DAM": ("45.768423360", "-91.864744370"),
        "BARRY": ("45.538501810", "-90.311812310"),
    }
    locOfsub_dict = {
        "1-Feb": ("45.768423360", "-91.864744370"),
        "1-Mar": ("45.538501810", "-90.311812310"),
    }
    zipOfsub_dict = {"35476": ["1-Feb"], "36512": ["1-Mar"]}
    actual_plant_dict = Plant_agg(
        clean_data, zipOfsub_dict, loc_of_plant, locOfsub_dict, pmin
    )
    expected_plant_dict = {
        ("BANKHEAD DAM", "CONVENTIONAL HYDROELECTRIC"): ["1-Feb", 106, 106, 0.4],
    }
    assert actual_plant_dict == expected_plant_dict

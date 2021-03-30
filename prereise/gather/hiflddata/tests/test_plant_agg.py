# -*- coding: utf-8 -*-
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from prereise.gather.hiflddata.plant_agg import (
    cal_p,
    clean_p,
    loc_of_sub,
    location_of_plant,
    plant_agg,
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


def test_loc_of_sub():
    csv_data = {
        "ID": ["1-Feb", "1-Mar"],
        "STATE": ["AL", "AR"],
        "ZIP": ["35476", "36512"],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
        "STATUS": ["OP", "OP"],
    }
    clean_data = pd.DataFrame(data=csv_data)
    loc_of_sub_dict, zip_of_sub_dict = loc_of_sub(clean_data)
    expected_loc_of_sub_dict = {
        "1-Feb": (45.768423360, -91.864744370),
        "1-Mar": (45.538501810, -90.311812310),
    }
    expected_zip_of_sub_dict = {"35476": ["1-Feb"], "36512": ["1-Mar"]}
    assert loc_of_sub_dict == expected_loc_of_sub_dict
    assert zip_of_sub_dict == expected_zip_of_sub_dict


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_cal_p(read_csv):
    csv_data_path = "Generator_Y2019.csv"
    csv_data = {"Plant Name": ["Sand Point", "Barry"], "Minimum Load (MW)": [0.4, 55]}
    read_csv.return_value = pd.DataFrame(data=csv_data)
    p_min = cal_p(csv_data_path)
    expected_pmin = {"SAND POINT": 0.4, "BARRY": 55.0}
    assert p_min == expected_pmin


@patch("prereise.gather.hiflddata.plant_agg.pd.read_csv")
def test_loc_of_plant(read_csv):
    csv_data = {
        "NAME": ["AMALGAMATED", "CASTLE"],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
    }
    read_csv.return_value = pd.DataFrame(data=csv_data)
    loc_of_plant = location_of_plant()
    expected_loc_of_plant = {
        "AMALGAMATED": (45.768423360, -91.864744370),
        "CASTLE": (45.538501810, -90.311812310),
    }
    assert loc_of_plant == expected_loc_of_plant


def test_plant_agg_when_clean_data_is_empty():
    clean_data = pd.DataFrame(data={})
    actual_result = plant_agg(clean_data, None, None, None, None)
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
        "BANKHEAD DAM": (45.768423360, -91.864744370),
        "BARRY": (45.538501810, -90.311812310),
    }
    loc_of_sub_dict = {
        "1-Feb": (45.768423360, -91.864744370),
        "1-Mar": (45.538501810, -90.311812310),
    }
    zip_of_sub_dict = {"35476": ["1-Feb"], "36512": ["1-Mar"]}
    actual_plant_dict = plant_agg(
        clean_data, zip_of_sub_dict, loc_of_plant, loc_of_sub_dict, pmin
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
        "BANKHEAD DAM": (45.768423360, -91.864744370),
        "BARRY": (45.538501810, -90.311812310),
    }
    loc_of_sub_dict = {
        "1-Feb": (45.768423360, -91.864744370),
        "1-Mar": (45.538501810, -90.311812310),
    }
    zip_of_sub_dict = {"35476": ["1-Feb"], "36512": ["1-Mar"]}
    actual_plant_dict = plant_agg(
        clean_data, zip_of_sub_dict, loc_of_plant, loc_of_sub_dict, pmin
    )
    expected_plant_dict = {
        ("BANKHEAD DAM", "CONVENTIONAL HYDROELECTRIC"): ["1-Feb", 106, 106, 0.4],
    }
    assert actual_plant_dict == expected_plant_dict

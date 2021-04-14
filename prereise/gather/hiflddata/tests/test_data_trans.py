# -*- coding: utf-8 -*-
from unittest.mock import patch

import pandas as pd
from haversine import Unit, haversine
from pandas.testing import assert_frame_equal

from prereise.gather.hiflddata.data_trans import (
    Cal_KV,
    Clean,
    GetMaxIsland,
    GraphOfNet,
    InitKV,
    computeGeoDist,
    get_neigbors,
    get_Zone,
    lineFromCSV,
    meter2Mile,
)


@patch("prereise.gather.hiflddata.data_trans.pd.read_csv")
def test_get_zone(read_csv):
    zone_file_path = "zone.csv"
    read_csv.return_value = pd.DataFrame(data={"STATE": ["AL", "AR"], "ID": [1, 2]})
    zone_dict = get_Zone(zone_file_path)
    expected_result = {"AL": 1, "AR": 2}
    assert zone_dict == expected_result


@patch("prereise.gather.hiflddata.data_trans.pd.read_csv")
def test_clean(read_csv):
    csv_data_path = "Electric_Substations.csv"
    csv_data = {
        "STATE": ["AL", "AR"],
        "STATUS": ["IN SERVICE", "OUTAGE"],
        "LINES": [5, 3],
    }
    zone_dict = {"AL": 1, "AR": 2}
    read_csv.return_value = pd.DataFrame(data=csv_data)
    clean_data = Clean(csv_data_path, zone_dict)
    expected_csv_data = {"STATE": ["AL"], "STATUS": ["IN SERVICE"], "LINES": [5]}
    expected_result = pd.DataFrame(data=expected_csv_data)
    assert_frame_equal(expected_result, clean_data)


@patch("prereise.gather.hiflddata.data_trans.pd.read_csv")
def test_lineFromCSV(read_csv):
    t_file_path = "Electric_Power_Transmission_Lines.csv"
    read_csv.return_value = pd.DataFrame(
        data={
            "TYPE": ["AC; OVERHEAD", "AC; OVERHEAD"],
            "ID": [1, 2],
            "VOLTAGE": [69, 230],
        }
    )

    raw_lines = lineFromCSV(t_file_path)
    expected_result = {
        "TYPE": {"1": "AC; OVERHEAD", "2": "AC; OVERHEAD"},
        "VOLTAGE": {"1": 69, "2": 230},
    }
    assert raw_lines == expected_result


def test_meter2Mile():
    actual_result = meter2Mile(12335.89)
    expected_result = 12335.89 / 1609.34
    assert expected_result == actual_result


def test_computeGeoDist():
    sub1 = (45.76842336, -91.86474437)
    sub2 = (29.99917553, -82.93498639)
    actual_result = computeGeoDist(sub1, sub2)
    expected_result = haversine(sub1, sub2, Unit.MILES)
    assert actual_result == expected_result


def test_GetMaxIsland():
    nodes = [1, 2, 3, 4, 5, 6]
    N_dict = {
        1: [2, 3],
        2: [1, 4],
        3: [1],
        4: [2],
        5: [6],
        6: [5],
    }
    G = GraphOfNet(nodes, N_dict)
    max_nodeSet = GetMaxIsland(G)
    expected_result = [1, 2, 3, 4]
    assert list(max_nodeSet) == expected_result


def test_InitKV():
    csv_data = {
        "MIN_VOLT": [69, 69],
        "MAX_VOLT": [161, 115],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
    }
    clean_data = pd.DataFrame(data=csv_data)
    KV_dict, to_cal = InitKV(clean_data)
    expected_KV_dict = {
        (45.76842336, -91.86474437): 115.0,
        (45.53850181, -90.31181231): 92.0,
    }
    expected_to_cal = []
    assert KV_dict == expected_KV_dict
    assert to_cal == expected_to_cal

    csv_data = {
        "MIN_VOLT": [4000, 69],
        "MAX_VOLT": [5000, 3],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
    }
    clean_data = pd.DataFrame(data=csv_data)
    KV_dict, to_cal = InitKV(clean_data)
    expected_KV_dict = {(45.53850181, -90.31181231): 36.0}
    expected_to_cal = [(45.76842336, -91.86474437)]
    assert KV_dict == expected_KV_dict
    assert to_cal == expected_to_cal


def test_get_neigbors():
    nodes = [1, 2, 3, 4, 5, 6]
    N_dict = {
        1: [2, 3],
        2: [1, 4],
        3: [1],
        4: [2],
        5: [6],
        6: [5],
    }
    G = GraphOfNet(nodes, N_dict)
    neis = get_neigbors(G, 1, depth=1)
    expected_neis = {1: [2, 3]}
    assert neis == expected_neis

    neis = get_neigbors(G, 1, depth=2)
    expected_neis = {1: [2, 3], 2: [4]}
    assert neis == expected_neis


def test_Cal_KV():
    nodes = [1, 2, 3, 4, 5, 6]
    N_dict = {
        1: [2, 3],
        2: [1, 4],
        3: [1],
        4: [2],
        5: [6],
        6: [5],
    }
    G = GraphOfNet(nodes, N_dict)
    KV_dict = {
        1: 115.0,
        2: 92.0,
        7: 80.0,
    }
    to_cal = [1]

    Cal_KV(N_dict, G, KV_dict, to_cal)
    expected_kv_dict = {1: 92.0, 2: 92.0, 7: 80.0}
    assert KV_dict == expected_kv_dict

    KV_dict = {
        1: 115.0,
        7: 90.0,
    }
    to_cal = [1]

    Cal_KV(N_dict, G, KV_dict, to_cal)
    expected_kv_dict = {1: -999999, 7: 90.0}
    assert KV_dict == expected_kv_dict

from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from prereise.gather.hiflddata.data_trans import (
    cal_kv,
    clean,
    get_max_island,
    get_neighbors,
    get_zone,
    graph_of_net,
    init_kv,
    line_from_csv,
    meter_to_mile,
)


@patch("prereise.gather.hiflddata.data_trans.pd.read_csv")
def test_get_zone(read_csv):
    zone_file_path = "zone.csv"
    read_csv.return_value = pd.DataFrame(
        data={
            "zone_name": ["AL", "AR"],
            "zone_id": [1, 2],
            "interconnect": ["West", "West"],
        }
    )
    zone_dict, zone_dict1 = get_zone(zone_file_path)
    expected_result = {"AL": 1, "AR": 2}
    assert zone_dict == expected_result


@patch("prereise.gather.hiflddata.data_trans.pd.read_csv")
def test_clean(read_csv):
    csv_data_path = "Electric_Substations.csv"
    csv_data = {
        "STATE": ["AL", "AR"],
        "STATUS": ["IN SERVICE", "OUTAGE"],
        "LINES": [5, 0],
    }
    zone_dict = {"AL": 1, "AR": 2}
    read_csv.return_value = pd.DataFrame(data=csv_data)
    clean_data = clean(csv_data_path, zone_dict)
    expected_csv_data = {"STATE": ["AL"], "STATUS": ["IN SERVICE"], "LINES": [5]}
    expected_result = pd.DataFrame(data=expected_csv_data)
    assert_frame_equal(expected_result, clean_data)


@patch("prereise.gather.hiflddata.data_trans.pd.read_csv")
def test_line_from_csv(read_csv):
    t_file_path = "Electric_Power_Transmission_Lines.csv"
    read_csv.return_value = pd.DataFrame(
        data={
            "TYPE": ["AC; OVERHEAD", "AC; OVERHEAD"],
            "ID": [1, 2],
            "VOLTAGE": [69, 230],
        }
    )

    raw_lines = line_from_csv(t_file_path)
    expected_result = {
        "TYPE": {"1": "AC; OVERHEAD", "2": "AC; OVERHEAD"},
        "VOLTAGE": {"1": 69, "2": 230},
    }
    assert raw_lines == expected_result


def test_meter_to_mile():
    actual_result = meter_to_mile(12335.89)
    expected_result = 12335.89 / 1609.34
    assert expected_result == actual_result


def test_get_max_island():
    n_dict = {
        1: [2, 3],
        2: [1, 4],
        3: [1],
        4: [2],
        5: [6],
        6: [5],
    }
    graph = graph_of_net(n_dict)
    max_node_set = get_max_island(graph)
    expected_result = [1, 2, 3, 4]
    assert list(max_node_set) == expected_result


def test_init_kv():
    csv_data = {
        "MIN_VOLT": [69, 69],
        "MAX_VOLT": [161, 115],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
    }
    clean_data = pd.DataFrame(data=csv_data)
    kv_dict, to_cal = init_kv(clean_data)
    expected_kv_dict = {
        (45.76842336, -91.86474437): 115.0,
        (45.53850181, -90.31181231): 92.0,
    }
    expected_to_cal = []
    assert kv_dict == expected_kv_dict
    assert to_cal == expected_to_cal

    csv_data = {
        "MIN_VOLT": [4000, 69],
        "MAX_VOLT": [5000, 3],
        "LATITUDE": [45.76842336, 45.53850181],
        "LONGITUDE": [-91.86474437, -90.31181231],
    }
    clean_data = pd.DataFrame(data=csv_data)
    kv_dict, to_cal = init_kv(clean_data)
    expected_kv_dict = {(45.53850181, -90.31181231): 36.0}
    expected_to_cal = [(45.76842336, -91.86474437)]
    assert kv_dict == expected_kv_dict
    assert to_cal == expected_to_cal


def test_get_neighbors():
    n_dict = {
        1: [2, 3],
        2: [1, 4],
        3: [1],
        4: [2],
        5: [6],
        6: [5],
    }
    graph = graph_of_net(n_dict)
    neis = get_neighbors(graph, 1, depth=1)
    expected_neis = {1: [2, 3]}
    assert neis == expected_neis

    neis = get_neighbors(graph, 1, depth=2)
    expected_neis = {1: [2, 3], 2: [4]}
    assert neis == expected_neis


def test_cal_kv():
    n_dict = {
        1: [2, 3],
        2: [1, 4],
        3: [1],
        4: [2],
        5: [6],
        6: [5],
    }
    graph = graph_of_net(n_dict)
    kv_dict = {
        1: 115.0,
        2: 92.0,
        7: 80.0,
    }
    to_cal = [1]

    cal_kv(n_dict, graph, kv_dict, to_cal)
    expected_kv_dict = {1: 92.0, 2: 92.0, 7: 80.0}
    assert kv_dict == expected_kv_dict

    kv_dict = {
        1: 115.0,
        7: 90.0,
    }
    to_cal = [1]

    cal_kv(n_dict, graph, kv_dict, to_cal)
    expected_kv_dict = {1: 115, 7: 90.0}
    assert kv_dict == expected_kv_dict

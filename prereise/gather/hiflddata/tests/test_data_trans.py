from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from prereise.gather.hiflddata.data_trans import clean, get_zone, line_from_csv


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

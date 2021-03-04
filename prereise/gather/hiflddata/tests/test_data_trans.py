# -*- coding: utf-8 -*-
from unittest.mock import Mock
import pandas as pd
from pandas.testing import assert_frame_equal
from prereise.gather.hiflddata.data_trans import get_Zone, Clean

def test_get_zone():
    zone_file_path = "zone.csv"
    pd.read_csv = Mock(return_value = pd.DataFrame(data={'STATE': ['AL', 'AR'], 'ID': [1, 2]}))
    zone_dict = get_Zone(zone_file_path)
    expected_result = {'AL': 1, 'AR': 2}
    assert zone_dict == expected_result

def test_clean():
    csv_data_path = "Electric_Substations.csv"
    csv_data = {
        'STATE': ['AL', 'AR'],
        'STATUS': ['IN SERVICE', 'OUTAGE'],
        'LINES': [5, 3]
    }
    zone_dict = {'AL': 1, 'AR': 2}
    pd.read_csv = Mock(return_value = pd.DataFrame(data=csv_data))
    clean_data = Clean(csv_data_path, zone_dict)
    expected_csv_data = {
        'STATE': ['AL'],
        'STATUS': ['IN SERVICE'],
        'LINES': [5]
    }
    expected_result = pd.DataFrame(data = expected_csv_data)
    assert_frame_equal(expected_result, clean_data)
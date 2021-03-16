import pandas as pd


def create_mock_pv_info():
    """Creates PV info data frame.

    :return: (*pandas.DataFrame*) -- mock PV info.
    """
    plant_code = [1, 2, 3, 4, 5]
    state = ["UT", "WA", "CA", "CA", "CA"]
    capacity = [10, 5, 1, 2, 3]
    single = ["N", "Y", "Y", "Y", "Y"]
    dual = ["Y", "N", "N", "N", "Y"]
    fix = ["N", "Y", "Y", "N", "N"]

    pv_info = pd.DataFrame(
        {
            "State": state,
            "Nameplate Capacity (MW)": capacity,
            "Single-Axis Tracking?": single,
            "Dual-Axis Tracking?": dual,
            "Fixed Tilt?": fix,
            "Plant Code": plant_code,
        }
    )

    return pv_info

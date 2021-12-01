import os

import pandas as pd

from prereise.gather.const import abv2state


def get_pv_tracking_data():
    """Load solar PV information from EIA860 for all plants installed in 2016.

    :return: (*pandas.DataFrame*) -- solar pv plant information as found in
        form EIA860
    """
    file = os.path.join(os.path.dirname(__file__), "data", "3_3_Solar_Y2016.csv")

    solar_plant_info = pd.read_csv(
        file,
        skiprows=range(1),
        usecols=[
            "Plant Code",
            "State",
            "Prime Mover",
            "Nameplate Capacity (MW)",
            "Single-Axis Tracking?",
            "Dual-Axis Tracking?",
            "Fixed Tilt?",
        ],
    ).fillna("N")
    pv_info = solar_plant_info[solar_plant_info["Prime Mover"] == "PV"].copy()
    pv_info.drop("Prime Mover", axis=1, inplace=True)

    return pv_info


def get_pv_tracking_ratio_state(pv_info, state):
    """Get solar PV tracking technology ratios for the query state in 2016 from EIA860

    :param pandas.DataFrame pv_info: solar pv plant information as found in
        form EIA860 as returned by :func:`get_pv_tracking_data`.
    :param list state: the query state(s).
    :return: (*tuple*) -- tracking technology proportion (fix, 1-axis, 2-axis)
        for the query state in 2016.
    :raise ValueError: if state is invalid.
    """

    if not isinstance(state, list):
        raise TypeError("state must be a list")

    for s in state:
        if s not in abv2state.keys():
            raise ValueError("Invalid State: %s" % s)

    pv_info_state = pv_info[pv_info["State"].isin(state)].copy()

    if pv_info_state.empty:
        print("No solar PV plant in %s" % ", ".join(state))
        return

    fix = 0
    single = 0
    dual = 0
    total_capacity = 0
    for i in pv_info_state.index:
        capacity = pv_info_state.loc[i]["Nameplate Capacity (MW)"]
        if pv_info_state.loc[i]["Single-Axis Tracking?"] == "Y":
            single += capacity
            total_capacity += capacity
        if pv_info_state.loc[i]["Dual-Axis Tracking?"] == "Y":
            dual += capacity
            total_capacity += capacity
        if pv_info_state.loc[i]["Fixed Tilt?"] == "Y":
            fix += capacity
            total_capacity += capacity

    return fix / total_capacity, single / total_capacity, dual / total_capacity

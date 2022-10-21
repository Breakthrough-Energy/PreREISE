import os

import numpy as np

import prereise.gather.demanddata.transportation_electrification.immediate_charging_HDV as immediate_charging_HDV
from prereise.gather.demanddata.transportation_electrification import const
from prereise.gather.demanddata.transportation_electrification.data_helper import (
    load_urbanized_scaling_factor,
)
from prereise.gather.demanddata.transportation_electrification.immediate import (
    immediate_charging,
)


def test_immediate_charging_region1():
    immediate_charging(
        census_region=1,
        model_year=2017,
        veh_range=100,
        kwhmi=0.242,
        power=6.6,
        location_strategy=2,
        veh_type="LDV",
        filepath=os.path.join(
            const.data_folder_path,
            "nhts_census_updated_dwell",
        ),
    )


def test_immediate_charging_mdv():

    result = immediate_charging_HDV.immediate_charging(
        model_year=2050,
        veh_range=200,
        power=80,
        location_strategy=1,
        veh_type="MDV",
        filepath=os.path.join(
            const.data_folder_path,
            "fdata_v10st.mat",
        ),
        trip_strategy=1,
    )
    bev_vmt = load_urbanized_scaling_factor(
        model_year=2050,
        veh_type="MDV",
        veh_range=200,
        urbanized_area="Antioch",
        state="CA",
        filepath=os.path.join(
            const.data_folder_path,
            "regional_scaling_factors",
            "Regional_scaling_factors_UA_",
        ),
    )
    final_result = immediate_charging_HDV.adjust_bev(
        model_year=2050,
        veh_type="MDV",
        veh_range=200,
        model_year_profile=result,
        bev_vmt=bev_vmt,
        charging_efficiency=0.95,
    )

    correct_cumsum = np.array(
        [
            5.61689215500168,
            10942.68623,
            21951.59332,
            32980.21489,
            43904.32619,
            54934.05497,
            65925.06389,
            76881.00051,
        ],
    )

    np.testing.assert_allclose(final_result.cumsum()[::1095], correct_cumsum)


def test_immediate_charging_hdv():

    result = immediate_charging_HDV.immediate_charging(
        model_year=2050,
        veh_range=200,
        power=80,
        location_strategy=1,
        veh_type="HDV",
        filepath=os.path.join(
            const.data_folder_path,
            "fdata_v10st.mat",
        ),
        trip_strategy=1,
    )
    bev_vmt = load_urbanized_scaling_factor(
        model_year=2050,
        veh_type="HDV",
        veh_range=200,
        urbanized_area="Antioch",
        state="CA",
        filepath=os.path.join(
            const.data_folder_path,
            "regional_scaling_factors",
            "Regional_scaling_factors_UA_",
        ),
    )
    final_result = immediate_charging_HDV.adjust_bev(
        model_year=2050,
        veh_type="HDV",
        veh_range=200,
        model_year_profile=result,
        bev_vmt=bev_vmt,
        charging_efficiency=0.95,
    )

    correct_cumsum = np.array(
        [
            10.8255287099344,
            10458.16992,
            20964.88916,
            31443.09284,
            41900.81189,
            52407.05727,
            62866.27995,
            73352.53979,
        ],
    )

    np.testing.assert_allclose(final_result.cumsum()[::1095], correct_cumsum)

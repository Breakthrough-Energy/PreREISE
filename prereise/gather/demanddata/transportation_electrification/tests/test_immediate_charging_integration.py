import os

import numpy as np

import prereise.gather.demanddata.transportation_electrification.immediate_charging_HDV as immediate_charging_HDV
from prereise.gather.demanddata.transportation_electrification import const
from prereise.gather.demanddata.transportation_electrification.data_helper import (
    generate_daily_weighting,
    load_urbanized_scaling_factor,
)
from prereise.gather.demanddata.transportation_electrification.immediate import (
    adjust_bev,
    immediate_charging,
)


def test_immediate_charging_region1():
    result = immediate_charging(
        census_region=1,
        model_year=2017,
        veh_range=100,
        power=6.6,
        location_strategy=2,
        veh_type="LDV",
        filepath=os.path.join(
            const.data_folder_path,
            "nhts_census_updated_dwell",
        ),
    )
    bev_vmt = load_urbanized_scaling_factor(
        model_year=2017,
        veh_type="LDV",
        veh_range=100,
        urbanized_area="Antioch",
        state="CA",
        filepath=os.path.join(
            const.data_folder_path,
            "regional_scaling_factors",
            "Regional_scaling_factors_UA_",
        ),
    )

    daily_values = generate_daily_weighting(2017)

    final_result = adjust_bev(
        hourly_profile=result,
        adjustment_values=daily_values,
        model_year=2017,
        veh_type="LDV",
        veh_range=100,
        bev_vmt=bev_vmt,
        charging_efficiency=0.95,
    )

    correct_cumsum = np.array(
        [
            5.77314880e01,
            1.06704314e05,
            2.21298833e05,
            3.46061958e05,
            4.73804702e05,
            6.07778242e05,
            7.36039206e05,
            8.58406341e05,
        ],
    )

    np.testing.assert_allclose(final_result.cumsum()[::1095], correct_cumsum)


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

    daily_values = generate_daily_weighting(2017)

    final_result = adjust_bev(
        hourly_profile=result,
        adjustment_values=daily_values,
        model_year=2017,
        veh_type="MDV",
        veh_range=100,
        bev_vmt=bev_vmt,
        charging_efficiency=0.95,
    )

    correct_cumsum = np.array(
        [
            6.25888979e00,
            1.49132922e04,
            3.10476159e04,
            4.85031512e04,
            6.64076921e04,
            8.52221916e04,
            1.03157417e05,
            1.20314233e05,
        ],
    )

    print(final_result.cumsum()[::1095])

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

    daily_values = generate_daily_weighting(2017)

    final_result = adjust_bev(
        hourly_profile=result,
        adjustment_values=daily_values,
        model_year=2017,
        veh_type="HDV",
        veh_range=100,
        bev_vmt=bev_vmt,
        charging_efficiency=0.95,
    )

    correct_cumsum = np.array(
        [
            1.14074474e01,
            1.34817274e04,
            2.80378297e04,
            4.37284949e04,
            5.99307996e04,
            7.68898286e04,
            9.30264299e04,
            1.08557058e05,
        ]
    )

    np.testing.assert_allclose(final_result.cumsum()[::1095], correct_cumsum)

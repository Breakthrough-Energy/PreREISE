import os

import numpy as np

import prereise.gather.demanddata.transportation_electrification.immediate_charging_HDV as immediate_charging_HDV
from prereise.gather.demanddata.transportation_electrification import const
from prereise.gather.demanddata.transportation_electrification.data_helper import (
    generate_daily_weighting,
    get_total_daily_vmt,
    load_urbanized_scaling_factor,
)
from prereise.gather.demanddata.transportation_electrification.immediate import (
    adjust_bev,
    immediate_charging,
)


def test_immediate_charging_ldv_2days():
    first_two_input_days = [1, 2]
    kwhmi = 0.242

    _, output_load_sum_list, trip_data = immediate_charging(
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

    veh_type = "LDV"
    daily_vmt = get_total_daily_vmt(trip_data, first_two_input_days, veh_type.lower())

    output_load_sum_array = np.array(output_load_sum_list)
    daily_vmt_array = np.array(daily_vmt)
    charging_efficiency = 0.9

    assert (
        abs(
            (
                (output_load_sum_array.sum() * charging_efficiency)
                / (daily_vmt_array.sum() * kwhmi)
            )
            - 1
        )
        < 0.03
    )


def test_immediate_charging_mdv_1day():
    veh_type = "MDV"
    kwhmi = 2.13

    (
        _,
        output_load_sum_list,
        trip_data,
    ) = immediate_charging_HDV.immediate_hdv_charging(
        model_year=2017,
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

    daily_vmt = get_total_daily_vmt(trip_data, [1], veh_type.lower())

    output_load_sum_array = np.array(output_load_sum_list)
    daily_vmt_array = np.array(daily_vmt)
    charging_efficiency = 0.95

    assert (
        abs(
            (
                (output_load_sum_array.sum() * charging_efficiency)
                / (daily_vmt_array.sum() * kwhmi)
            )
            - 1
        )
        < 0.03
    )


def test_immediate_charging_hdv_1day():
    veh_type = "HDV"
    kwhmi = 2.72

    _, output_load_sum_list, trip_data = immediate_charging_HDV.immediate_hdv_charging(
        model_year=2017,
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

    daily_vmt = get_total_daily_vmt(trip_data, [1], veh_type.lower())

    output_load_sum_array = np.array(output_load_sum_list)
    daily_vmt_array = np.array(daily_vmt)
    charging_efficiency = 0.95

    assert (
        abs(
            (
                (output_load_sum_array.sum() * charging_efficiency)
                / (daily_vmt_array.sum() * kwhmi)
            )
            - 1
        )
        < 0.03
    )


def test_immediate_charging_region1():
    result, _, _ = immediate_charging(
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

    adjust_bev(
        hourly_profile=result,
        adjustment_values=daily_values,
        model_year=2017,
        veh_type="LDV",
        veh_range=100,
        bev_vmt=bev_vmt,
        charging_efficiency=0.95,
    )


def test_immediate_charging_mdv():
    result, _, _ = immediate_charging_HDV.immediate_hdv_charging(
        model_year=2017,
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
        model_year=2017,
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

    adjust_bev(
        hourly_profile=result,
        adjustment_values=daily_values,
        model_year=2017,
        veh_type="MDV",
        veh_range=200,
        bev_vmt=bev_vmt,
        charging_efficiency=0.95,
    )


def test_immediate_charging_hdv():
    result, _, _ = immediate_charging_HDV.immediate_hdv_charging(
        model_year=2017,
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
        model_year=2017,
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

    adjust_bev(
        hourly_profile=result,
        adjustment_values=daily_values,
        model_year=2017,
        veh_type="HDV",
        veh_range=200,
        bev_vmt=bev_vmt,
        charging_efficiency=0.95,
    )

import os

import numpy as np
from scipy.io import loadmat

from prereise.gather.demanddata.transportation_electrification import (
    const,
    smart_charging,
)
from prereise.gather.demanddata.transportation_electrification.data_helper import (
    generate_daily_weighting,
    get_total_daily_vmt,
)


def test_smart_charging_ldv_2days():
    data_dir = os.path.join(
        const.data_folder_path,
        "CAISO_sample_load_2019.mat",
    )
    load_demand = loadmat(data_dir)["load_demand"].flatten()

    daily_values = generate_daily_weighting(2017)

    first_two_input_days = [1, 2]
    kwhmi = 0.242

    _, output_load_sum_list, trip_data = smart_charging.smart_charging(
        census_region=1,
        model_year=2017,
        veh_range=100,
        kwhmi=kwhmi,
        power=6.6,
        location_strategy=2,
        veh_type="LDV",
        filepath=os.path.join(
            const.data_folder_path,
            "nhts_census_updated_dwell.mat",
        ),
        daily_values=daily_values,
        external_signal=load_demand,
        bev_vmt=const.emfacvmt,
        trip_strategy=1,
        input_day=first_two_input_days,
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


def test_smart_charging_mdv_2days():
    data_dir = os.path.join(
        const.data_folder_path,
        "CAISO_sample_load_2019.mat",
    )
    load_demand = loadmat(data_dir)["load_demand"].flatten()

    daily_values = generate_daily_weighting(2017)

    first_two_input_days = [1, 2]
    veh_type = "MDV"
    kwhmi = 2.13

    _, output_load_sum_list, trip_data = smart_charging.smart_charging(
        model_year=2017,
        veh_range=200,
        power=80,
        kwhmi=kwhmi,
        location_strategy=1,
        veh_type=veh_type,
        filepath=os.path.join(
            const.data_folder_path,
            "fdata_v10st.mat",
        ),
        external_signal=load_demand,
        bev_vmt=const.emfacvmt,
        daily_values=daily_values,
        trip_strategy=1,
        input_day=first_two_input_days,
    )

    daily_vmt = get_total_daily_vmt(trip_data, first_two_input_days, veh_type.lower())

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


def test_smart_charging_hdv_2days():
    data_dir = os.path.join(
        const.data_folder_path,
        "CAISO_sample_load_2019.mat",
    )
    load_demand = loadmat(data_dir)["load_demand"].flatten()

    daily_values = generate_daily_weighting(2017)

    first_two_input_days = [1, 2]
    veh_type = "HDV"
    kwhmi = 2.72

    _, output_load_sum_list, trip_data = smart_charging.smart_charging(
        model_year=2017,
        veh_range=200,
        power=80,
        kwhmi=kwhmi,
        location_strategy=1,
        veh_type=veh_type,
        filepath=os.path.join(
            const.data_folder_path,
            "fdata_v10st.mat",
        ),
        external_signal=load_demand,
        bev_vmt=const.emfacvmt,
        daily_values=daily_values,
        trip_strategy=1,
        input_day=first_two_input_days,
    )

    daily_vmt = get_total_daily_vmt(trip_data, first_two_input_days, veh_type.lower())

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

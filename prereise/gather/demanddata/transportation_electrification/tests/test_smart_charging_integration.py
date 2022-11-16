import os

import numpy as np
from scipy.io import loadmat

from prereise.gather.demanddata.transportation_electrification import (
    const,
    data_helper,
    smart_charging,
    smart_charging_HDV,
)
from prereise.gather.demanddata.transportation_electrification.data_helper import (
    generate_daily_weighting,
)


def test_smart_charging():
    data_dir = os.path.join(
        const.data_folder_path,
        "CAISO_sample_load_2019.mat",
    )
    load_demand = loadmat(data_dir)["load_demand"].flatten()

    daily_values = generate_daily_weighting(2017)

    result = smart_charging.smart_charging(
        census_region=1,
        model_year=2017,
        veh_range=100,
        kwhmi=0.242,
        power=6.6,
        location_strategy=2,
        veh_type="LDV",
        filepath=os.path.join(
            const.test_folder_path,
            "ldv_test_data.csv",
        ),
        daily_values=daily_values,
        load_demand=load_demand,
        bev_vmt=const.emfacvmt,
        trip_strategy=1,
    )

    correct_cumsum = np.array(
        [
            0.0,
            9796092.83844097,
            19198735.09458018,
            27636677.75177433,
            36032644.7281563,
            44112809.4024421,
            52256940.31259822,
            61077768.57472202,
        ]
    )

    np.testing.assert_allclose(result.cumsum()[::1095], correct_cumsum)


def test_smart_charging_hdv():
    data_dir = os.path.join(
        const.data_folder_path,
        "CAISO_sample_load_2019.mat",
    )
    load_demand = loadmat(data_dir)["load_demand"].flatten()

    bev_vmt = data_helper.load_urbanized_scaling_factor(
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
    result = smart_charging_HDV.smart_charging(
        model_year=2050,
        veh_range=200,
        power=80,
        location_strategy=1,
        veh_type="HDV",
        filepath=os.path.join(
            const.test_folder_path,
            "hdv_test_data.csv",
        ),
        initial_load=load_demand,
        bev_vmt=bev_vmt,
        trip_strategy=1,
    )

    correct_cumsum = np.array(
        [
            0.0,
            3856.38868062,
            7712.77736124,
            11485.33150533,
            15341.72018595,
            19197.26691589,
            22970.66301066,
            26827.05169128,
        ]
    )

    np.testing.assert_allclose(result.cumsum()[::1095], correct_cumsum)


def test_smart_charging_mdv():
    data_dir = os.path.join(
        const.data_folder_path,
        "CAISO_sample_load_2019.mat",
    )
    load_demand = loadmat(data_dir)["load_demand"].flatten()

    bev_vmt = data_helper.load_urbanized_scaling_factor(
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
    result = smart_charging_HDV.smart_charging(
        model_year=2050,
        veh_range=200,
        power=80,
        location_strategy=1,
        veh_type="MDV",
        filepath=os.path.join(
            const.test_folder_path,
            "mdv_test_data.csv",
        ),
        initial_load=load_demand,
        bev_vmt=bev_vmt,
        trip_strategy=1,
    )

    correct_cumsum = np.array(
        [
            0.0,
            4043.9900878,
            8087.9801756,
            12044.05743541,
            16088.04752321,
            20132.03761101,
            24088.11487082,
            28132.10495862,
        ]
    )

    np.testing.assert_allclose(result.cumsum()[::1095], correct_cumsum)

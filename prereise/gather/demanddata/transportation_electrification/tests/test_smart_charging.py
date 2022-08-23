import inspect
import os

import numpy as np
from scipy.io import loadmat

import prereise
from prereise.gather.demanddata.transportation_electrification.data_helper import (
    generate_daily_weighting,
)
from prereise.gather.demanddata.transportation_electrification.immediate import (
    immediate_charging,
)
from prereise.gather.demanddata.transportation_electrification.smart_charging import (
    smart_charging,
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
            os.path.dirname(inspect.getsourcefile(prereise)),
            "gather",
            "demanddata",
            "transportation_electrification",
            "nhts_census_updated_dwell",
        ),
    )


def test_smart_charging():
    run_smart_charging()


def run_smart_charging():
    data_dir = os.path.join(
        os.path.dirname(inspect.getsourcefile(prereise)),
        "gather",
        "demanddata",
        "transportation_electrification",
        "CAISO_sample_load_2019.mat",
    )
    load_demand = loadmat(data_dir)["load_demand"].flatten()

    daily_values = generate_daily_weighting(2017)

    result = smart_charging(
        census_region=1,
        model_year=2017,
        veh_range=100,
        kwhmi=0.242,
        power=6.6,
        location_strategy=2,
        veh_type="LDV",
        filepath=os.path.join(
            os.path.dirname(inspect.getsourcefile(prereise)),
            "gather",
            "demanddata",
            "transportation_electrification",
            "tests",
            "test_census_data.csv",
        ),
        daily_values=daily_values,
        load_demand=load_demand,
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


if __name__ == "__main__":
    run_smart_charging()

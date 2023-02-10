import os

from prereise.gather.demanddata.transportation_electrification import const
from prereise.gather.demanddata.transportation_electrification.generate_BEV_vehicle_profiles import (
    generate_bev_vehicle_profiles,
)


def test_ldv_immediate_runs():
    state_demand_df = generate_bev_vehicle_profiles(
        vehicle_trip_data_filepath=os.path.join(
            const.data_folder_path,
            "nhts_census_updated_dwell.mat",
        ),
        charging_strategy="immediate",
        veh_type="ldv",
        veh_range=100,
        projection_year=2017,
        state="AL",
        power=6.6,
        location_strategy=2,
        trip_strategy=1,
    )

    assert len(state_demand_df) == 8760
    assert len(state_demand_df.columns) == 15

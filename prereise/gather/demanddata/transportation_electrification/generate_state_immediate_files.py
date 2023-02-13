import os
import time

from prereise.gather.const import abv2state
from prereise.gather.demanddata.transportation_electrification import const
from prereise.gather.demanddata.transportation_electrification.generate_BEV_vehicle_profiles import (
    generate_bev_vehicle_profiles,
)

def write_state_demand_files(
    demand_output, state, dir_path=None
):
    """Create files for each state

    :param dict demand_output: 
    :param str state: 
    :param str dir_path: path to folder wher files will be written. Default to *'data/
        regional_scaling_factors'* in current directory.
    """
    if dir_path is None:
        dir_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "output",
        )
    os.makedirs(dir_path, exist_ok=True)
    print(f"Writing state demand files in {dir_path}")

    demand_output.to_pickle(
        os.path.join(dir_path, f"immediate_{state}.pkl")
    )


if __name__ == "__main__":

    state_set = set(abv2state.keys()) - {"AK", "HI", "VT"}

    state_list = ["VT"] + list(state_set)

    print("State order:")
    print(state_list)

    for state in state_list:
        print(f"Current state: {state}")

        tic = time.perf_counter()

        state_demand_df = generate_bev_vehicle_profiles(
            vehicle_trip_data_filepath=os.path.join(
                const.data_folder_path,
                "nhts_census_updated_dwell.mat",
            ),
            charging_strategy="immediate",
            veh_type="ldv",
            veh_range=100,
            projection_year=2024,
            state=state,
            power=6.6,
            location_strategy=2,
            trip_strategy=1,
        )

        write_state_demand_files(state_demand_df, state)

        toc = time.perf_counter()

        print(f"State {state} ran in {toc - tic:0.4f} seconds\n")

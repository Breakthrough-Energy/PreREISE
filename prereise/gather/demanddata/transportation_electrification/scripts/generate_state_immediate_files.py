import os
import time

from prereise.gather.const import abv2state
from prereise.gather.demanddata.transportation_electrification import const
from prereise.gather.demanddata.transportation_electrification.generate_BEV_vehicle_profiles import (
    generate_bev_vehicle_profiles,
)


def write_state_demand_files(
    demand_output, veh_type, veh_range, projection_year, dir_path=None
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
            "demand",
            f"{veh_type}_{veh_range}",
        )
    os.makedirs(dir_path, exist_ok=True)
    print(f"Writing state demand files in {dir_path}")

    demand_output.to_csv(
        os.path.join(
            dir_path, f"immediate_{veh_type}_{veh_range}_{projection_year}.csv"
        )
    )


if __name__ == "__main__":
    veh_types = ["ldv", "ldv", "ldv", "ldt", "ldt", "ldt", "mdv", "hdv"]
    veh_ranges = [100, 200, 300, 100, 200, 300, 200, 200]

    projection_years = [2017] + list(range(2020, 2051, 5))

    us_states = abv2state.keys()
    contiguous_states = [state for state in us_states if (state not in ["AK", "HI"])]

    print("States to process:")
    print(contiguous_states)

    for i in range(len(veh_types)):
        veh_type = veh_types[i]
        veh_range = veh_ranges[i]
        print(f"Running for vehicle type {veh_type} with range {veh_range}")

        if veh_type.lower() in {"ldv", "ldt"}:
            vehicle_trip_data_filepath = os.path.join(
                const.data_folder_path,
                "nhts_census_updated_dwell.mat",
            )
            power = 6.6
            location_strategy = 2

        elif veh_type.lower() in {"mdv", "hdv"}:
            vehicle_trip_data_filepath = os.path.join(
                const.data_folder_path,
                "fdata_v10st.mat",
            )
            power = 80
            location_strategy = 1

        for projection_year in projection_years:
            print(f"Projection year: {projection_year}")

            tic = time.perf_counter()

            state_demand_df = generate_bev_vehicle_profiles(
                vehicle_trip_data_filepath=vehicle_trip_data_filepath,
                charging_strategy="immediate",
                veh_type=veh_type,
                veh_range=veh_range,
                projection_year=projection_year,
                states=contiguous_states,
                power=power,
                location_strategy=location_strategy,
            )

            write_state_demand_files(
                state_demand_df, veh_type, veh_range, projection_year
            )

            toc = time.perf_counter()

            print(
                f"Year {projection_year} for vehicle type {veh_type} & vehicle range {veh_range} ran in {toc - tic:0.4f} seconds\n"
            )

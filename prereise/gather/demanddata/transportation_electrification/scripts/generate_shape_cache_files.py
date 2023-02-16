import os
import sys
import time

import pandas as pd

from prereise.gather.demanddata.transportation_electrification import (
    const,
    immediate,
    immediate_charging_HDV,
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
            "output",
            str(f"{veh_type}_{str(veh_range)}"),
        )
    print(dir_path)
    os.makedirs(dir_path, exist_ok=True)
    print(f"Writing state demand files in {dir_path}")

    demand_output.to_pickle(
        os.path.join(
            dir_path,
            f"{projection_year}_immediate_{veh_type}_{veh_range}.pkl",
        )
    )


if __name__ == "__main__":
    veh_type = sys.argv[1]
    print(f"vehicle type: {veh_type}")
    veh_range = int(sys.argv[2])
    print(f"vehicle range: {veh_range}\n")

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

    charging_strategy = "immediate"

    projection_years = [2017] + list(range(2020, 2051, 5))

    for projection_year in projection_years:
        print(f"Current projection year: {projection_year}")

        demand_shapes = {}

        if veh_type.lower() in {"ldv", "ldt"}:
            for census_region in range(1, 10):
                tic = time.perf_counter()

                print(f"Current census region: {census_region}")

                normalized_demand, _, _ = immediate.immediate_charging(
                    census_region=census_region,
                    model_year=projection_year,
                    veh_range=veh_range,
                    power=power,
                    location_strategy=location_strategy,
                    veh_type=veh_type,
                    filepath=vehicle_trip_data_filepath,
                )
            demand_shapes.update(
                {f"{veh_type}_region_{census_region}": normalized_demand}
            )

            toc = time.perf_counter()
            print(
                f"Vehicle type {veh_type} for census region {census_region} ran in {toc - tic:0.4f} seconds\n"
            )

        elif veh_type.lower() in {"mdv", "hdv"}:
            tic = time.perf_counter()

            normalized_demand, _, _ = immediate_charging_HDV.immediate_hdv_charging(
                model_year=projection_year,
                veh_range=veh_range,
                power=power,
                location_strategy=location_strategy,
                veh_type=veh_type,
                filepath=vehicle_trip_data_filepath,
            )
            demand_shapes.update({f"{veh_type}_demand_shape": normalized_demand})

            toc = time.perf_counter()
            print(f"Vehicle type {veh_type} ran in {toc - tic:0.4f} seconds\n")

        demand_shapes_df = pd.DataFrame(
            demand_shapes,
            index=pd.date_range(
                start=f"{projection_year}-01-01 00:00:00",
                end=f"{projection_year}-12-31 23:00:00",
                freq="H",
            ),
        )

        write_state_demand_files(
            demand_shapes_df, veh_type, veh_range, projection_year
        )

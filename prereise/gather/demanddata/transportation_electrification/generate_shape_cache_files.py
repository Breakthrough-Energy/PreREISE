import os
import time
import sys

import pandas as pd

from prereise.gather.demanddata.transportation_electrification import (
    const,
    immediate,
    immediate_charging_HDV,
)


def write_state_demand_files(demand_output, census_region, veh_type, veh_range, projection_year, dir_path=None):
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
            f"{veh_type}{veh_range}",
        )
    os.makedirs(dir_path, exist_ok=True)
    print(f"Writing state demand files in {dir_path}")

    demand_output.to_pickle(os.path.join(dir_path, f"{projection_year}_immediate_census_{census_region}_{veh_type}{veh_range}.pkl"))


if __name__ == "__main__":

    veh_type = sys.argv[1]
    veh_range = sys.argv[2]

    vehicle_trip_data_filepath=os.path.join(
        const.data_folder_path,
        "nhts_census_updated_dwell.mat",
    )
    charging_strategy="immediate"
    veh_type="ldv"
    power=6.6
    location_strategy=2

    for projection_year in range(2020,2051,5):
        print(f"Current projection year: {projection_year}")

        census_shapes = {}
        for census_region in range(1,10):
            print(f"Current census region: {census_region}")

            tic = time.perf_counter()

            if veh_type.lower() in {"ldv", "ldt"}:
                normalized_demand, _, _ = immediate.immediate_charging(
                    census_region=census_region,
                    model_year=projection_year,
                    veh_range=veh_range,
                    power=power,
                    location_strategy=location_strategy,
                    veh_type=veh_type,
                    filepath=vehicle_trip_data_filepath,
                )
            elif veh_type.lower() in {"mdv", "hdv"}:
                normalized_demand, _, _ = immediate_charging_HDV.immediate_charging(
                    model_year=projection_year,
                    veh_range=veh_range,
                    power=power,
                    location_strategy=location_strategy,
                    veh_type=veh_type,
                    filepath=vehicle_trip_data_filepath,
                )

            census_shapes.update({f"census_region_{census_region}": normalized_demand})

        census_shapes_df = pd.DataFrame(
            census_shapes,
            index=pd.date_range(
                start=f"{projection_year}-01-01 00:00:00",
                end=f"{projection_year}-12-31 23:00:00",
                freq="H",
            ),
        )

        write_state_demand_files(census_shapes_df, census_region, veh_type, veh_range, projection_year)

        toc = time.perf_counter()

        print(f"Census region {census_region} ran in {toc - tic:0.4f} seconds\n")

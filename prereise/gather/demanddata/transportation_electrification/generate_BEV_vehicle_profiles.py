import os

import pandas as pd

from prereise.gather.const import abv2state
from prereise.gather.demanddata.transportation_electrification import (
    const,
    immediate,
    immediate_charging_HDV,
    smart_charging,
)
from prereise.gather.demanddata.transportation_electrification.data_helper import (
    generate_daily_weighting,
    get_kwhmi,
    load_rural_scaling_factor,
    load_urbanized_scaling_factor,
)


def generate_bev_vehicle_profiles(
    vehicle_trip_data_filepath,
    charging_strategy,
    veh_type,
    veh_range,
    projection_year,
    state,
    external_signal=None,
    power=6.6,
    location_strategy=2,
    trip_strategy=1,
):
    """Generate Battery Electric Vehicle (BEV) profiles

    :param str vehicle_trip_data_filepath: filepath of collected trip data from external sources
        representing driving patterns
    :param str charging_strategy: establishes whether charging happens immediately ("immediate")
         or optimize based on external signals, i.e. smart charging ("smart")
    :param str veh_type: vehicle category: LDV: light duty vehicle, LDT: light duty truck,
        MDV: medium duty vehicle, HDV: heavy duty vehicle
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on
        single charge in miles.
    :param int projection_year: year that is being modelled/projected to, 2017, 2030, 2040,
        2050.
    :param str state: US state abbreviation
    :param numpy.ndarray (optional) external_signal: initial load demand (MW for each hour)
    :param int power: (optional) charger power, EVSE kW; default value: 6.6 kW;
    :param int location_strategy: (optional) where the vehicle can charge-1, 2, 3, 4, or 5;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school.
        default value: 2
    :param int trip_strategy: (optional) determine to charge after any trip (1) or only after the
        last trip (2); default value: 1
    :return: (*pandas.DataFrame*) -- yearly charging profiles for all urban areas and the rural area
        in each state (MW for each hour)
    """

    census_region = const.state2census_region[state]
    kwhmi = get_kwhmi(projection_year, veh_type, veh_range)

    daily_values = generate_daily_weighting(projection_year)

    if power > 19.2:
        charging_efficiency = 0.95
    else:
        charging_efficiency = 0.9

    geographic_area_bev_vmt = {}

    urban_scaling_filepath = os.path.join(
        const.data_folder_path,
        "regional_scaling_factors",
        "Regional_scaling_factors_UA_",
    )
    urban_scaling_factors = pd.read_csv(
        urban_scaling_filepath + str(projection_year) + ".csv", index_col="State"
    )
    state_urban_areas = urban_scaling_factors.loc[state.upper(), "UA"]

    # scaling factors for listed urban areas
    for urban_area in state_urban_areas.to_list():
        urban_bev_vmt = load_urbanized_scaling_factor(
            model_year=projection_year,
            veh_type=veh_type,
            veh_range=veh_range,
            urbanized_area=urban_area,
            state=state,
            filepath=urban_scaling_filepath,
        )
        geographic_area_bev_vmt.update({f"{state}_{urban_area}": urban_bev_vmt})

    # scaling factors for rural areas
    rural_bev_vmt = load_rural_scaling_factor(
        projection_year,
        veh_type,
        veh_range,
        abv2state[state.upper()].upper(),
        filepath=os.path.join(
            const.data_folder_path,
            "regional_scaling_factors",
            "Regional_scaling_factors_RA_",
        ),
    )
    geographic_area_bev_vmt.update({f"{state}_rural": rural_bev_vmt})

    # calculate demand for all geographic areas with scaling factors
    state_demand_profiles = {}
    for geographic_area, bev_vmt in geographic_area_bev_vmt.items():
        if charging_strategy == "immediate":
            if veh_type.lower() in {"ldv", "ldt"}:
                normalized_demand = immediate.immediate_charging(
                    census_region=census_region,
                    model_year=projection_year,
                    veh_range=veh_range,
                    power=power,
                    location_strategy=location_strategy,
                    veh_type=veh_type,
                    filepath=vehicle_trip_data_filepath,
                )
            elif veh_type.lower() in {"mdv", "hdv"}:
                normalized_demand = immediate_charging_HDV.immediate_charging(
                    model_year=projection_year,
                    veh_range=veh_range,
                    power=power,
                    location_strategy=location_strategy,
                    veh_type=veh_type,
                    filepath=vehicle_trip_data_filepath,
                )

            final_demand = immediate.adjust_bev(
                hourly_profile=normalized_demand,
                adjustment_values=daily_values,
                model_year=projection_year,
                veh_type=veh_type,
                veh_range=veh_range,
                bev_vmt=bev_vmt,
                charging_efficiency=charging_efficiency,
            )

        elif charging_strategy == "smart":
            final_demand = smart_charging.smart_charging(
                census_region=census_region,
                model_year=projection_year,
                veh_range=veh_range,
                kwhmi=kwhmi,
                power=power,
                location_strategy=location_strategy,
                veh_type=veh_type,
                filepath=vehicle_trip_data_filepath,
                daily_values=daily_values,
                external_signal=external_signal,
                bev_vmt=bev_vmt,
                trip_strategy=trip_strategy,
            )

        state_demand_profiles.update({geographic_area: final_demand})

        state_demand_profiles_df = pd.DataFrame(
            state_demand_profiles,
            index=pd.date_range(
                start=f"{projection_year}-01-01 00:00:00",
                end=f"{projection_year}-12-31 23:00:00",
                freq="H",
            ),
        )
    return state_demand_profiles_df

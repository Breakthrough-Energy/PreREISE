import math

import numpy as np
from scipy.optimize import linprog

from prereise.gather.demanddata.transportation_electrification import (
    charging_optimization,
    const,
    daily_trip_charging,
    data_helper,
    dwelling,
)


def smart_charging(
    census_region,
    model_year,
    veh_range,
    kwhmi,
    power,
    location_strategy,
    veh_type,
    filepath,
    daily_values,
    load_demand,
    bev_vmt,
    trip_strategy=1,
):
    """Smart charging function

    :param int census_region: any of the 9 census regions defined by US census bureau.
    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040,
        2050.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on
        single charge.
    :param int kwhmi: fuel efficiency, should vary based on vehicle type and model_year.
    :param int power: charger power, EVSE kW.
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, or 5;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school.
    :param str veh_type: determine which category (LDV or LDT) to produce charging
        profiles for
    :param str filepath: the path to the nhts mat file.
    :param pandas.Series daily_values: daily weight factors returned from
        :func:`generate_daily_weighting`.
    :param np.array load_demand: the initial load demand
    :param int trip_strategy: determine to charge after any trip (1) or only after the
        last trip (2)
    :return: (*numpy.ndarray*) -- charging profiles.
    """

    # load NHTS data from function
    if veh_type.lower() == "ldv":
        newdata = data_helper.remove_ldt(data_helper.load_data(census_region, filepath))
    elif veh_type.lower() == "ldt":
        newdata = data_helper.remove_ldv(data_helper.load_data(census_region, filepath))
    elif veh_type.lower() == "mdv":
        newdata = data_helper.load_hdv_data("mhdv", filepath)
    elif veh_type.lower() == "hdv":
        newdata = data_helper.load_hdv_data("hhdv", filepath)

    # updates the weekend and weekday values in the nhts data
    newdata = data_helper.update_if_weekend(newdata)

    new_columns = [
        "trip start battery charge",
        "trip end battery charge",
        "BEV could be used",
        "Battery size",
        "Electricity cost",
        "Battery discharge",
        "Battery charge",
        "trip_number",
    ]
    newdata = newdata.reindex(list(newdata.columns) + new_columns, axis=1, fill_value=0)

    newdata["trip_number"] = newdata.groupby("vehicle_number").cumcount() + 1

    input_day = data_helper.get_input_day(data_helper.get_model_year_dti(model_year))

    model_year_profile = np.zeros(24 * len(input_day))
    data_day = data_helper.get_data_day(newdata)

    daily_vmt_total = data_helper.get_total_daily_vmt(newdata, input_day, daily_values)

    kwh = kwhmi * veh_range
    if power > 19.2:
        charging_efficiency = 0.95
    else:
        charging_efficiency = 0.9

    newdata = charging_optimization.get_constraints(
        newdata,
        kwhmi,
        power,
        trip_strategy,
        location_strategy,
        const.ldv_location_allowed,
        charging_efficiency,
    )

    day_num = len(input_day)
    for day_iter in range(day_num):

        adjusted_load = load_demand + model_year_profile

        trip_window_indices = np.arange(day_iter * 24, day_iter * 24 + 72) % len(
            model_year_profile
        )

        outputelectricload = daily_trip_charging.calculate_daily_smart_charging_trips(
            newdata,
            input_day,
            day_iter,
            data_day,
            adjusted_load[trip_window_indices],
            charging_efficiency,
            daily_vmt_total,
            kwh,
            bev_vmt,
        )

        model_year_profile[trip_window_indices] += (
            outputelectricload / (daily_vmt_total[day_iter] * 1000) * bev_vmt
        )

    return model_year_profile

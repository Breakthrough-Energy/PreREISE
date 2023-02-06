import numpy as np
import pandas as pd

from prereise.gather.demanddata.transportation_electrification import const, data_helper

allowed_locations_by_strategy = {
    1: {1},  # home only
    2: set(range(1, 13)),  # home and go to work related (1-12, inclusive)
    # We don't need to set the strategy for 3 (everywhere), it's handled elsewhere
    4: {1, 21},  # home and school only
    5: {1, 11, 12, 21},  # home and work and school
}


def calculate_charging(
    trips, charging_power, battery_capacity, kwhmi, charging_efficiency
):
    """Parse travel patterns to estimate charging and state-of-charge after each trip.

    :param pandas.DataFrame trips: trip data.
    :param int/float charging_power: charging power (kW).
    :param int/float battery_capacity: battery capacity (kWh).
    :param int/float kwhmi: vehicle electricity consumption (kWh/ mile).
    :param int/float charging_efficiency: from grid to battery efficiency.
    """
    # Add trip_number entries
    trips["trip_number"] = trips.groupby("vehicle_number").cumcount() + 1

    grouped_trips = trips.groupby("trip_number")
    for trip_num, group in grouped_trips:
        if trip_num == 1:
            # For the first trip, we assume that the vehicle starts with a full battery
            trips.loc[group.index, "trip start battery charge"] = battery_capacity
        else:
            # For subsequent trips, the starting SoC depends on the previous trip
            relevant_vehicles = group["vehicle_number"]
            previous_group = grouped_trips.get_group(trip_num - 1)
            start_soc = (
                previous_group["trip end battery charge"]
                + previous_group["charging consumption"]
            )
            trips.loc[group.index, "trip start battery charge"] = start_soc.values[
                previous_group["vehicle_number"].isin(relevant_vehicles)
            ]
        # For all trips, update ending state of charge
        trips.loc[group.index, "trip end battery charge"] = (
            trips.loc[group.index, "trip start battery charge"]
            - group["trip_miles"] * kwhmi * const.ER
        )
        # Calculate charging duration/energy for the trips that can charge
        trips.loc[group.index, "full_charge_time"] = (
            battery_capacity - trips["trip end battery charge"]
        ) / (charging_power * charging_efficiency)
        trips.loc[group.index, "charging time"] = trips["charging_allowed"] * (
            trips[["full_charge_time", "dwell_time"]].apply(min, axis=1)
        )
        trips.loc[group.index, "charging consumption"] = (
            trips["charging time"] * charging_power * charging_efficiency
        )


def resample_daily_charging(trips, charging_power):
    """Translate start and end times and power to a 72-hour output array.

    :param pandas.DataFrame trips: trip data with trip-end and charge-time columns.
    :param int/float charging_power: charging power (kW).
    :return: (*numpy.array*) -- hourly total charging power for the 72-hour span.
    """
    fine_resolution = 7200
    coarse_resolution = 72
    ratio = int(fine_resolution / coarse_resolution)
    # determine timing of charging
    augmented_trips = trips.assign(
        start_point=(ratio * trips["trip_end"]).map(round),
        elapsed=(ratio * trips["charging time"]).map(round),
        end_point=lambda x: x["start_point"] + x["elapsed"],
    )
    # Translate times to fine-resolution arrays
    indiv_charging_profiles = np.zeros((len(trips), fine_resolution), dtype=bool)
    for i, (trip_id, trip) in enumerate(augmented_trips.iterrows()):
        indiv_charging_profiles[i, trip["start_point"] : trip["end_point"]] = True
    # Sum fine-resolution arrays for each trip into one aggregate array
    total_profile = indiv_charging_profiles.sum(axis=0) * charging_power

    # Resample fine-resolution arrays into a coarse-resolution array
    output_array = np.zeros(coarse_resolution)
    for k in range(coarse_resolution):
        if k == 0:
            # First hour, normal sum
            output_array[k] = sum(total_profile[:ratio]) / ratio
        elif k == coarse_resolution - 1:
            # Last hour, normal sum
            output_array[k] = sum(total_profile[(-1 * ratio) :]) / ratio
        else:
            # Every other hour: sum from the half hour before to the half hour after
            output_array[k] = (
                sum(total_profile[int((k - 0.5) * ratio) : int((k + 0.5) * ratio)])
                / 100
            )

    return output_array


def immediate_charging(
    census_region,
    model_year,
    veh_range,
    power,
    location_strategy,
    veh_type,
    filepath,
    trip_strategy=1,
    input_day=None,
):
    """Immediate charging function

    :param int census_region: any of the 9 census regions defined by US census bureau.
    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040, 2050.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :param int power: charger power, EVSE kW.
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, or 5;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school.
    :param str veh_type: determine which category (LDV or LDT) to produce charging profiles for
    :param str filepath: the path to the nhts mat file.
    :param int trip_strategy: determine to charge after any trip (1) or only after the last trip (2)
    :return: (*numpy.ndarray*) -- charging profiles.
    """
    if veh_type.lower() == "ldv":
        trips = data_helper.remove_ldt(data_helper.load_data(census_region, filepath))
    elif veh_type.lower() == "ldt":
        trips = data_helper.remove_ldv(data_helper.load_data(census_region, filepath))
    elif veh_type.lower() == "mdv":
        trips = data_helper.load_hdv_data("mhdv", filepath)
    elif veh_type.lower() == "hdv":
        trips = data_helper.load_hdv_data("hhdv", filepath)

    # filter for cyclical trips
    nd_len = len(trips)
    filtered_census_data = pd.DataFrame(columns=const.nhts_census_column_names)
    i = 0
    while i < nd_len:
        total_trips = int(trips.iloc[i, trips.columns.get_loc("total_trips")])
        # copy one vehicle information to the block
        individual = trips.iloc[i : i + total_trips].copy()
        if (
            individual["why_from"].head(1).values[0]
            == individual["dwell_location"].tail(1).values[0]
        ):
            filtered_census_data = pd.concat(
                [filtered_census_data, individual], ignore_index=True
            )
        i += total_trips
    del trips
    trips = filtered_census_data

    print(f"updated data length:{nd_len}")
    #####

    # Constants
    kwhmi = data_helper.get_kwhmi(model_year, veh_type, veh_range)
    battery_capacity = kwhmi * veh_range

    if input_day is None:
        input_day = data_helper.get_input_day(
            data_helper.get_model_year_dti(model_year)
        )

    # updates the weekend and weekday values in the nhts data
    trips = data_helper.update_if_weekend(trips)

    if power > 19.2:
        charging_efficiency = 0.95
    else:
        charging_efficiency = 0.9

    # add new columns to newdata to store data that is not in NHTS data
    new_columns = [
        "trip start battery charge",
        "trip end battery charge",
        "charging power",
        "charging time",
        "charging consumption",
        "BEV could be used",
        "trip_number",
    ]
    trips = trips.reindex(list(trips.columns) + new_columns, axis=1, fill_value=0)
    # Add flag for whether the total mileage is within the vehicle's range
    trips["BEV could be used"] = (
        trips["total vehicle miles traveled"] < veh_range * const.ER
    )
    # Add booleans for whether the location allows charging
    if location_strategy == 3:
        trips["location_allowed"] = True
    else:
        allowed = allowed_locations_by_strategy[location_strategy]
        trips["location_allowed"] = trips["dwell_location"].isin(allowed)
    # Add booleans for whether the trip_number (compared to total trips) allows charging
    if trip_strategy == 1:
        trips["trip_allowed"] = True
    elif trip_strategy == 2:
        trips["trip_allowed"] = trips["trip_number"] == trips["total_trips"]
    # Add booleans for whether the dell time is long enough to allow charging
    trips["dwell_allowed"] = trips["dwell_time"] > 0.2
    # Add boolean for whether this trip allows charging
    allowed_cols = [
        "location_allowed",
        "trip_allowed",
        "dwell_allowed",
    ]
    trips["charging_allowed"] = trips[allowed_cols].apply(all, axis=1)

    trips["dwell_charging"] = (
        trips["charging_allowed"] * trips["dwell_time"] * power * charging_efficiency
    )

    grouped_trips = trips.groupby("vehicle_number")
    for vehicle_num, group in grouped_trips:
        trips.loc[group.index, "max_charging"] = trips.loc[
            group.index, "dwell_charging"
        ].sum()
        trips.loc[group.index, "required_charging"] = (
            trips.loc[group.index, "trip_miles"].sum() * kwhmi
        )

    # Filter for whenever available charging is insufficient to meet required charging
    trips = trips.loc[(trips["required_charging"] <= trips["max_charging"])]

    # Filter by vehicle range
    trips = trips.loc[trips["total vehicle miles traveled"] < veh_range * const.ER]

    # Evaluate weekend vs. weekday for each trip
    data_day = data_helper.get_data_day(trips)
    weekday_trips = trips.loc[data_day == 2].copy()
    weekend_trips = trips.loc[data_day == 1].copy()

    # Calculate the charge times and SOC for each trip, then resample resolution
    calculate_charging(
        weekday_trips, power, battery_capacity, kwhmi, charging_efficiency
    )
    calculate_charging(
        weekend_trips, power, battery_capacity, kwhmi, charging_efficiency
    )
    daily_resampled_profiles = {
        "weekday": resample_daily_charging(weekday_trips, power),
        "weekend": resample_daily_charging(weekend_trips, power),
    }

    model_year_profile = np.zeros(24 * len(input_day))
    flag_translation = {1: "weekend", 2: "weekday"}
    for i, weekday_flag in enumerate(input_day):
        daily_profile = daily_resampled_profiles[flag_translation[weekday_flag]]
        # print(f"day: {i}")
        # print(f"daily sum: {np.sum(daily_profile)}")

        # create wrap-around indexing function
        trip_window_indices = np.arange(i * 24, i * 24 + 72) % len(model_year_profile)

        # MW
        model_year_profile[trip_window_indices] += daily_profile

    # Normalize the output so that it sums to 1
    summed_profile = model_year_profile / model_year_profile.sum()

    output_load_sum_list = [
        np.sum(daily_resampled_profiles["weekend"]),
        np.sum(daily_resampled_profiles["weekday"]),
    ]
    print(np.sum(daily_resampled_profiles["weekend"]))
    print(np.sum(daily_resampled_profiles["weekday"]))
    print(output_load_sum_list)

    return summed_profile, output_load_sum_list, trips


def adjust_bev(
    hourly_profile,
    adjustment_values,
    model_year,
    veh_type,
    veh_range,
    bev_vmt,
    charging_efficiency,
):
    """Adjusts the charging profiles by applying weighting factors based on
    seasonal/monthly values

    :param numpy.ndarray hourly_profile: normalized charging profiles
    :param pandas.DataFrame adjustment_values: weighting factors for each
        day of the year loaded from month_info_nhts.mat.
    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040, 2050.
    :param str veh_type: determine which category (MDV or HDV) to produce charging profiles for
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :param int/float bev_vmt: BEV VMT value / scaling factor loaded from Regional_scaling_factors.csv
    :param float charging_efficiency: from grid to battery efficiency.
    :return: (*numpy.ndarray*) -- final adjusted charging profiles.
    """
    kwhmi = data_helper.get_kwhmi(model_year, veh_type, veh_range)

    # weekday/weekend, monthly urban and rural moves scaling
    adjusted_load = apply_daily_adjustments(
        hourly_profile,
        adjustment_values,
    )

    # simulation year urban and rural scaling specific to region
    simulation_hourly_profile = apply_annual_scaling(
        adjusted_load,
        bev_vmt,
        charging_efficiency,
        kwhmi,
    )

    return simulation_hourly_profile


def apply_daily_adjustments(
    hourly_profile,
    adjustment_values,
    num_days_per_year=365,
    num_segments_per_day=24,
):
    """Adjusts the charging profiles by applying weighting factors based on
    annual vehicle miles traveled (VMT) for battery electric vehicles in a specific geographic region

    :param numpy.ndarray hourly_profile: normalized charging profiles
    :param pandas.DataFrame adjustment_values: weighting factors for each
        day of the year loaded from month_info_nhts.mat.
    :param int num_days_per_year: optional year parameter to facilite easier testing
    :param int num_segments_per_day: optional specification of hours per day
    :return: (*numpy.ndarray*) -- adjusted charging profile
    """
    # weekday/weekend, monthly urban and rural moves scaling
    adj_vals = adjustment_values.transpose().to_numpy()
    profiles = hourly_profile.reshape(
        (num_segments_per_day, num_days_per_year), order="F"
    )

    pr = profiles / np.sum(profiles, axis=0)
    adjusted = np.multiply(pr, adj_vals)

    adjusted_load = adjusted.T.flatten()

    return adjusted_load


def apply_annual_scaling(
    hourly_profile,
    bev_vmt,
    charging_efficiency,
    kwhmi,
):
    """Adjusts the charging profiles by applying weighting factors based on
    seasonal/monthly values

    :param numpy.ndarray hourly_profile: hourly charging profile
    :param int/float bev_vmt: BEV VMT value / scaling factor loaded from Regional_scaling_factors.csv
    :param float charging_efficiency: from grid to battery efficiency.
    :param int kwhmi: fuel efficiency, should vary based on vehicle type and model_year.
    :return: (*numpy.ndarray*) -- adjusted charging profile
    """
    bev_annual_load = bev_vmt * kwhmi / charging_efficiency

    simulation_hourly_profile = bev_annual_load * hourly_profile

    return simulation_hourly_profile

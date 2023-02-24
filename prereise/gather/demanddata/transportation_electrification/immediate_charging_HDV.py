import numpy as np

from prereise.gather.demanddata.transportation_electrification import const, data_helper

allowed_locations_by_strategy = {
    1: {1},  # base only
}


def calculate_charging_helper(
    group, battery_capacity, kwhmi, charging_power, charging_efficiency
):
    """Calculates the charging and state-of-charge after each trip.

    :param pandas.DataFrame group: group of trips from one vehicle.
    :param int/float battery_capacity: battery capacity (kWh).
    :param int/float kwhmi: vehicle electricity consumption (kWh/ mile).
    :param int/float charging_power: charging power (kW).
    :param float charging_efficiency: from grid to battery efficiency.
    :return: (*pandas.DataFrame*) -- the updated data with the charging and SOC values
        for one group of trips.
    """

    # -- setting values for the first of the group --
    # first trip of the vehicle_number isn't always listed as trip_number 1
    group.loc[group.index[0], "trip start battery charge"] = battery_capacity

    group.loc[group.index[0], "trip end battery charge"] = (
        group.loc[group.index[0], "trip start battery charge"]
        - group.loc[group.index[0], "trip_miles"] * kwhmi * const.ER
    )

    # Calculate charging duration/energy for the trips that can charge
    group.loc[group.index[0], "full_charge_time"] = (
        battery_capacity - group.loc[group.index[0], "trip end battery charge"]
    ) / (charging_power * charging_efficiency)

    group.loc[group.index[0], "charging time"] = group.loc[
        group.index[0], "charging_allowed"
    ] * (
        min(
            group.loc[group.index[0], "full_charge_time"],
            group.loc[group.index[0], "dwell_time"],
        )
    )

    group.loc[group.index, "charging consumption"] = (
        group.loc[group.index[0], "charging time"]
        * charging_power
        * charging_efficiency
    )

    # -- setting values in the group whose trip_number == 1 --
    # they don't necessarily have to be the first in the group bc of how they were grouped
    group1 = group["trip_number"] == 1
    group.loc[group1, "trip start battery charge"] = battery_capacity

    group.loc[group1, "trip end battery charge"] = (
        group.loc[group1, "trip start battery charge"]
        - group.loc[group1, "trip_miles"] * kwhmi * const.ER
    )

    group.loc[group1, "full_charge_time"] = (
        battery_capacity - group.loc[group1, "trip end battery charge"]
    ) / (charging_power * charging_efficiency)

    tmp = group[group1]
    group.loc[group1, "charging time"] = tmp["charging_allowed"] * (
        tmp[["full_charge_time", "dwell_time"]].apply(min, axis=1)
    )

    group.loc[group1, "charging consumption"] = (
        group.loc[group1, "charging time"] * charging_power * charging_efficiency
    )

    # -- setting the values in the rest of the trips --
    pos = group.columns.get_loc("trip start battery charge")
    for i in range(1, len(group)):
        # setting the remaining trips' start SOC with the end SOC from the previous trip
        # this will skip over the entries that are trip_number 1 since those already have a "trip start battery charge"
        if group.iloc[i, group.columns.get_loc("trip_number")] != 1:
            group.iloc[i, pos] = (
                group.iloc[i - 1, group.columns.get_loc("trip end battery charge")]
                + group.iloc[i - 1, group.columns.get_loc("charging consumption")]
            )

            group.iloc[i, group.columns.get_loc("trip end battery charge")] = (
                group.iloc[i, group.columns.get_loc("trip start battery charge")]
                - group.iloc[i, group.columns.get_loc("trip_miles")] * kwhmi * const.ER
            )

            group.iloc[i, group.columns.get_loc("full_charge_time")] = (
                battery_capacity
                - group.iloc[i, group.columns.get_loc("trip end battery charge")]
            ) / (charging_power * charging_efficiency)

            group.loc[group.index, "charging time"] = group["charging_allowed"] * (
                group[["full_charge_time", "dwell_time"]].apply(min, axis=1)
            )

            group.loc[group.index, "charging consumption"] = (
                group["charging time"] * charging_power * charging_efficiency
            )

    return group


def calculate_charging(
    trips, charging_power, battery_capacity, kwhmi, charging_efficiency
):
    """Parse travel patterns to estimate charging and state-of-charge after each trip.

    :param pandas.DataFrame trips: trip data.
    :param int/float charging_power: charging power (kW).
    :param int/float battery_capacity: battery capacity (kWh).
    :param int/float kwhmi: vehicle electricity consumption (kWh/ mile).
    :return: (*pandas.DataFrame*) -- the updated data with the charging and SOC values
        for all vehicles.
    """
    trips = trips.groupby("vehicle_number", sort=False).apply(
        lambda x: calculate_charging_helper(
            x, battery_capacity, kwhmi, charging_power, charging_efficiency
        )
    )

    return trips


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


def immediate_hdv_charging(
    model_year,
    veh_range,
    power,
    location_strategy,
    veh_type,
    filepath,
    trip_strategy=1,
):
    """Immediate charging function

    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040,
        2050.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on
        single charge.
    :param int power: charger power, EVSE kW.
    :param int location_strategy: where the vehicle can charge - 1 or 3;
        1-base only, 3-anywhere if possibile.
    :param str veh_type: determine which category (MDV or HDV) to produce charging
        profiles for
    :param str filepath: the path to the HDV data file.
    :param int trip_strategy: determine to charge after any trip (1) or only after the
        last trip (2)
    :return: (*numpy.ndarray*) -- charging profiles.
    """
    # load NHTS data from function
    if veh_type.lower() == "mdv":
        trips = data_helper.load_hdv_data("mhdv", filepath)
    elif veh_type.lower() == "hdv":
        trips = data_helper.load_hdv_data("hhdv", filepath)

    # Constants
    kwhmi = data_helper.get_kwhmi(model_year, veh_type, veh_range)
    battery_capacity = kwhmi * veh_range
    model_year_len = 365

    # charging_efficiency val used to be in const.py
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
    ]
    trips = trips.reindex(list(trips.columns) + new_columns, axis=1, fill_value=0)

    trips["BEV could be used"] = 1

    # setting if allowed power based on home base (1/0)
    trips["power_allowed"] = trips["dwell_location"] == 1

    # Add booleans for whether the location allows charging -- (2)
    if location_strategy == 3:
        trips["location_allowed"] = True
    else:
        allowed = allowed_locations_by_strategy[location_strategy]
        trips["location_allowed"] = trips["dwell_location"].map(lambda x: x in allowed)

    # Add booleans for whether the trip_number (compared to total trips) allows charging -- (3)
    if trip_strategy == 1:
        trips["trip_allowed"] = True
    elif trip_strategy == 2:
        trips["trip_allowed"] = trips["trip_number"] == trips["total_trips"]

    # Add booleans for whether the dell time is long enough to allow charging -- (1)
    trips["dwell_allowed"] = trips["dwell_time"] > 0.2

    # Add boolean for whether this trip allows charging
    allowed_cols = [
        "power_allowed",
        "location_allowed",
        "trip_allowed",
        "dwell_allowed",
    ]
    trips["charging_allowed"] = trips[allowed_cols].apply(all, axis=1)

    trips.loc[trips["charging_allowed"], "charging power"] = power

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

    # Filter for vehicle's battery range
    trips = trips.loc[(trips["total vehicle miles traveled"] < veh_range)]

    hdv_trips = trips.copy()

    # Calculate the charge times and SOC for each trip, then resample resolution
    hdv_trips = calculate_charging(
        hdv_trips, power, battery_capacity, kwhmi, charging_efficiency
    )

    daily_profile = resample_daily_charging(hdv_trips, power)

    model_year_profile = np.zeros(24 * model_year_len)

    for i in range(model_year_len):
        # create wrap-around indexing function
        trip_window_indices = np.arange(i * 24, i * 24 + 72) % len(model_year_profile)

        # MW
        model_year_profile[trip_window_indices] += daily_profile

    # Normalize the output so that it sums to 1
    summed_profile = model_year_profile / model_year_profile.sum()

    return summed_profile, daily_profile, trips

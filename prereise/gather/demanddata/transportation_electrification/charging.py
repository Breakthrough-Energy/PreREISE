def get_charging_power(power, trip_strategy, location_strategy, kwh, trip_data):
    """Determines the charging power. Returns either param power or 0.

    :param int power: charger power, EVSE kW.
    :param int trip_strategy: a flag that determines which trips to consider, 1-anytrip number, 2-last trip.
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, or 5;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school.
    :param float kwh: kwhmi * veh_range, amount of energy needed to charge vehicle.
    :param pandas.Series trip_data: Row of DataFrame that has data for the trip we are calculating for.
    :return: (*float*) -- charging power.
    """

    dwelling = trip_data["Dwell time (hour decimal)"] > 0.2
    location = get_location(location_strategy, trip_data["why to"])

    trip = consider_trip_number(
        trip_strategy, trip_data["total vehicle trips"], trip_data["trip number"]
    )

    battery = get_battery_SOC(trip_data["trip end battery charge"], kwh)

    if not all([dwelling, location, trip, battery]):
        return 0

    return power


def get_charging_time(charging_power, kwh, battery_SOC, charging_efficiency, trip_data):
    """Calculates time needed to charge.

    :param float charging_power: charging power.
    :param float kwh: kwhmi * veh_range, amount of energy needed to charge vehicle.
    :param float battery_SOC: battery charge at end of trip.
    :param float charging_efficiency: grid to battery efficiency.
    :return: (*float*) -- charging time in decimal format.
    """
    if charging_power == 0:
        charging_time = 0
    else:
        charging_time = (kwh - battery_SOC) / (charging_power * charging_efficiency)

    if charging_time > trip_data["Dwell time (hour decimal)"]:
        charging_time = trip_data["Dwell time (hour decimal)"]

    return charging_time


def get_location(location_strategy, dwell_location):
    """Determines if the vehicle can be charged given location strategy and dwelling location

    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, or 5;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school.
    :param int dwell_location: location the vehicle dwells
    :return: (*bool*) -- a boolean that represents whether or not the vehicle can charge
    """
    location_allowed = {
        1: dwell_location == 1,  # only home
        2: dwell_location < 13,  # home & go to work related
        3: True,  # anywhere if possible
        4: dwell_location in {1, 21},  # home and school only
        5: dwell_location in {1, 11, 12, 21},  # home and work and school
    }
    return location_allowed[location_strategy]


def consider_trip_number(trip_strategy, total_trips, trip_num):
    """Determines if the vehicle should charge given trip strategy and current trip

    :param int trip_strategy: a toggle that determines if should charge on any trip or only
        after last trip (1-anytrip number, 2-last trip)
    :param int total_trips: total trips that the vehicle makes
    :param int trip_num: the trip number of the current trip
    :return: (*bool*) -- boolean that represents if the vehicle should charge
    """
    if trip_strategy == 1:
        return True

    elif trip_strategy == 2:
        return total_trips == trip_num


def get_battery_SOC(battery_SOC, kwh):
    """Determines if the vehicle needs to charge

    :param float battery_SOC: vehicle battery at end of trip
    :param float kwh: kwhmi * veh_range, amount of energy needed to charge vehicle.
    :return: (*bool*) -- boolean that represents if battery needs to be charged
    """
    return battery_SOC < kwh

def get_segment(dwelling_start_time, total_dwell_period):
    """Get dwelling activity segment.

    :param float s1: dwelling start time.
    :param float sn: dwelling end time.
    :return: (*int*) -- the amount of the rates (cost function) segments the dwelling activity possess.
    """
    return total_dwell_period - dwelling_start_time + 1


def get_location(location_strategy, dwell_location):
    """Determines if the vehicle can be charged given location strategy and dwelling location

    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, 5, or 6;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school, 6-only work
    :param int dwell_location: location the vehicle dwells
    :return: (*bool*) -- a boolean that represents whether or not the vehicle can charge
    """
    location_allowed = {
        1: dwell_location == 1,
        2: dwell_location < 13,
        3: True,
        4: dwell_location in {1, 21},
        5: dwell_location in {1, 11, 12, 21},
        6: (dwell_location >= 10) or (dwell_location < 13),
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


# 1.2.3.4 are to determine if charging (x/power)
def get_charging_power(power, trip_strategy, location_strategy, trip_data):
    """Determines the charging power. Returns either param power or 0.

    :param int power: charger power, EVSE kW.
    :param int trip_strategy: a flag that determines which trips to consider, 1-anytrip number, 2-last trip.
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, 5, or 6;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school, 6-only work
    :param pandas.Series trip_data: Row of DataFrame that has data for the trip we are calculating for.
    :return: (*float*) -- charging power.
    """
    dwelling = trip_data["Dwell time (hour decimal)"] > 0.2
    location = get_location(location_strategy, trip_data["why to"])
    trip = consider_trip_number(
        trip_strategy, trip_data["total vehicle trips"], trip_data["trip number"]
    )
    battery = 1

    if not all([dwelling, location, trip, battery]):
        return 0

    return power


def get_energy_limit(
    power, segment, dwelling_start_time, dwelling_length, total_dwell_period
):
    """Determines the energy limit

    :param int power: charger power, EVSE kW.
    :param segment: the amount of the rates segments the dwelling activity possess.
    :param float dwelling_start_time: dwelling start time.
    :param float dwelling_length: dwelling end time.
    :param float total_dwell_period: the total dwelling period.
    :return: (*list*) -- list of energy limits during the time span of available charging
    """
    t1 = dwelling_start_time + 1 - dwelling_start_time
    tn = dwelling_start_time + dwelling_length - total_dwell_period

    if segment == 1:
        energy_limit = [power * dwelling_length]

    elif segment == 2:
        energy_limit = [power * t1, power * tn]

    else:
        energy_limit = [power * t1]
        energy_limit += [power for s in range(segment - 1)]
        energy_limit += [power * tn]

    return energy_limit

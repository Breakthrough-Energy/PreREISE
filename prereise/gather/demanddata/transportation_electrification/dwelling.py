import math

import numpy as np


def get_segment(dwelling_start_time, dwelling_length):
    """Get dwelling activity segment.

    :param float dwelling_start_time: dwelling start time.
    :param float dwelling_length: length of dwell time.
    :return: (*int*) -- the amount of the rates (cost function) segments the dwelling
        activity possess.
    """
    total_dwell_period = dwelling_start_time + dwelling_length
    return np.floor(total_dwell_period) - np.floor(dwelling_start_time) + 1


def get_energy_limit(
    power, segment, dwelling_start_time, dwelling_length, charging_efficiency
):
    """Determines the energy limit for the entire dwelling period. Takes into
    consideration if charging does not start or end directly on the hour.

    :param int power: charger power, EVSE kW.
    :param int segment: the amount of the rates segments the dwelling activity possess.
    :param float dwelling_start_time: dwelling start time.
    :param float dwelling_length: length of dwell time.
    :param float charging_efficiency: grid to battery efficiency.
    :return: (*list*) -- list of energy limits during the time span of available charging
    """
    total_dwell_period = dwelling_start_time + dwelling_length
    partial_start_time = math.floor(dwelling_start_time) + 1 - dwelling_start_time
    partial_end_time = (
        dwelling_start_time + dwelling_length - math.floor(total_dwell_period)
    )

    energy = power * charging_efficiency

    if segment == 1:
        energy_limit = [energy * dwelling_length]

    elif segment == 2:
        energy_limit = [energy * partial_start_time, energy * partial_end_time]

    else:
        energy_limit = [energy * partial_start_time]
        energy_limit += [energy] * (int(segment) - 2)
        energy_limit += [energy * partial_end_time]

    return energy_limit


def get_rates(cost, dwelling_start_time, dwelling_length):
    """Determine the rates that will be used for the cost function.

    :param numpy.array cost: cost function
    :param float dwelling_start_time: dwelling start time.
    :param float dwelling_length: length of dwell time.
    :return: (*numpy.array*) -- rates for the corresponding dwelling period
    """
    total_dwell_period = dwelling_start_time + dwelling_length
    return cost[math.floor(dwelling_start_time) : math.floor(total_dwell_period) + 1]

import numpy as np

def get_segment(dwelling_start_time, total_dwell_period):
    """Get dwelling activity segment.

    :param float dwelling_start_time: dwelling start time.
    :param float total_dwell_period: dwelling end time.
    :return: (*int*) -- the amount of the rates (cost function) segments the dwelling activity possess.
    """
    return round(total_dwell_period) - round(dwelling_start_time) + 1


def get_energy_limit(
    power, segment, dwelling_start_time, dwelling_length, total_dwell_period
):
    """Determines the energy limit for the entire dwelling period. Takes into
    consideration if charging does not start or end directly on the hour.

    :param int power: charger power, EVSE kW.
    :param int segment: the amount of the rates segments the dwelling activity possess.
    :param float dwelling_start_time: dwelling start time.
    :param float dwelling_length: dwelling end time.
    :param float total_dwell_period: the total dwelling period.
    :return: (*list*) -- list of energy limits during the time span of available charging
    """
    partial_start_time = round(dwelling_start_time) + 1 - dwelling_start_time
    partial_end_time = dwelling_start_time + dwelling_length - round(total_dwell_period)

    if segment == 1:
        energy_limit = [power * dwelling_length]

    elif segment == 2:
        energy_limit = [power * partial_start_time, power * partial_end_time]

    else:
        energy_limit = [power * partial_start_time]
        energy_limit += [power for s in range(segment - 1)]
        energy_limit += [power * partial_end_time]

    return energy_limit


def get_rates(cost, dwelling_start_time, dwelling_length):
    """Determine the rates that will be used for the cost function.

    :param numpy.array cost: cost function
    :param float dwelling_start_time: dwelling start time.
    :param float dwelling_length: dwelling end time.
    :return: (*numpy.array*) -- rates for the corresponding dwelling period
    """
    total_dwell_period = dwelling_start_time + dwelling_length
    return cost[round(dwelling_start_time):round(total_dwell_period)+1]

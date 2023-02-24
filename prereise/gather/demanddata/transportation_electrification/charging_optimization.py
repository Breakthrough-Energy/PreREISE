import numpy as np
import pandas as pd

from prereise.gather.demanddata.transportation_electrification import const, dwelling


def get_constraints(
    constraints_df,
    kwhmi,
    power,
    trip_strategy,
    location_strategy,
    location_allowed,
    charging_efficiency,
):
    """Determine the consumption and charging constraints for each trip (hour segment)

    :param pandas.DataFrame constraints_df: trip data of vehicles for optimization constraints
    :param int kwhmi: fuel efficiency, should vary based on vehicle type and model_year.
    :param float power: charger power, EVSE kW.
    :param int trip_strategy: a toggle that determines if should charge on any trip or
        only after last trip (1-anytrip number, 2-last trip)
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, 5, or 6;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school, 6-only work
    :param dict location_allowed: starting locations allowed in the dataset
    :param float charging_efficiency: from grid to battery efficiency.
    :return: (*pandas.DataFrame*) -- a DataFrame adding the calculated constraints
        to an individual vehicle's data
    """
    grouped_trips = constraints_df.groupby("vehicle_number")

    constraints_df.loc[
        constraints_df["dwell_location"].isin(const.dwell_location_list),
        "power_allowed",
    ] = power
    constraints_df["power_allowed"].fillna(0, inplace=True)

    # for "power" - location
    if location_strategy == 3:
        constraints_df["location_allowed"] = True
    else:
        allowed = location_allowed[location_strategy]
        constraints_df["location_allowed"] = constraints_df["dwell_location"].map(
            lambda x: x in allowed
        )

    # for "power" - trip_number
    if trip_strategy == 1:
        constraints_df["trip_allowed"] = True
    elif trip_strategy == 2:
        constraints_df["trip_allowed"] = (
            constraints_df["trip_number"] == constraints_df["total_trips"]
        )

    # for "power" - dwell
    constraints_df["dwell_allowed"] = constraints_df["dwell_time"] > 0.2

    # for "power" - determine if can charge
    allowed_cols = [
        "power_allowed",
        "location_allowed",
        "trip_allowed",
        "dwell_allowed",
    ]
    constraints_df["charging_allowed"] = constraints_df[allowed_cols].apply(all, axis=1)

    for trip_num, group in grouped_trips:
        constraints_df.loc[group.index, "charging consumption"] = (
            constraints_df.loc[group.index, "trip_miles"] * kwhmi * -1
        )
        constraints_df.loc[group.index, "seg"] = dwelling.get_segment(
            constraints_df.loc[group.index, "trip_end"],
            constraints_df.loc[group.index, "dwell_time"],
        )

    constraints_df.loc[
        constraints_df["charging_allowed"] == True, "power"  # noqa: E712
    ] = constraints_df["power_allowed"]
    constraints_df["power"].fillna(0, inplace=True)

    constraints_df["segcum"] = constraints_df["seg"].transform(pd.Series.cumsum)

    constraints_df["energy limit"] = constraints_df.apply(
        lambda d: dwelling.get_energy_limit(
            d["power"],
            d["seg"],
            d["trip_end"],
            d["dwell_time"],
            charging_efficiency,
        ),
        axis=1,
    )

    return constraints_df


def calculate_optimization(
    charging_consumption,
    rates,
    elimit,
    seg,
    total_trips,
    kwh,
    charging_efficiency,
):
    """Calculates the minimized charging cost during a specific dwelling activity

    :param list charging_consumption: the charging consumption for each trip
    :param list rates: rates to be used for the cost function
    :param list elimit: energy limits during the time span of available charging
    :param list seg: the amount of the segments in the dwelling activity
    :param int total_trips: total number of trips for the current vehicle
    :param float kwh: kwhmi * veh_range, amount of energy needed to charge vehicle.
    :param float charging_efficiency: from grid to battery efficiency.
    :return: (*dict*) -- contains the necessary inputs for the linprog optimization
    """

    segsum = np.sum(seg)
    segcum = np.cumsum(seg)

    f = np.array(rates) 

    # form all the constraints
    # equality constraint
    Aeq = np.ones((1, segsum))  # noqa: N806

    # equality constraint
    Beq = -sum(charging_consumption)  # noqa: N806

    # G2V power upper bound in DC
    ub = elimit
    lb = [0] * segsum
    bounds = list(zip(lb, ub))

    # formulate the constraints matrix in Ax <= b, A can be divided into m
    # generate the cumulative sum array of seg in segcum

    # the amount of trips. submatrix dimension is m-1 * m
    m = total_trips

    # 'a' is a m-1 * segsum matrix
    a = np.zeros((m - 1, segsum))
    Aineq = np.zeros(((m - 1) * m, segsum))  # noqa: N806

    b = np.tril(np.ones((m - 1, m)), 1)
    Bineq = np.zeros((m * (m - 1), 1))  # noqa: N806

    for j in range(m):
        # part of the A matrix
        a = np.zeros((m - 1, segsum))

        if j > 0:
            # switch components in b matrix
            bb = np.concatenate((b[:, m - j : m], b[:, : m - j]), axis=1)

        else:
            # do not switch if j is 0
            bb = b

        charging_consumption = np.array(charging_consumption)
        cc = charging_consumption.reshape((charging_consumption.shape[0], 1))

        # set the constraints in DC
        Bineq[(m - 1) * j : (m - 1) * (j + 1), :] = kwh + (np.dot(bb, cc))

        for ii in range(m - 1):
            # indicate the number of the trips
            k = j + ii

            if k < m:
                # ones part of the column
                a[ii : m - 1, segcum[k] - seg[k] : segcum[k]] = 1

            else:
                k = k - m
                # ones part of the column
                a[ii : m - 1, segcum[k] - seg[k] : segcum[k]] = 1

        Aineq[(m - 1) * j : (m - 1) * (j + 1), :] = -a

    return {
        "c": f,
        "A_ub": Aineq,
        "b_ub": Bineq,
        "A_eq": Aeq,
        "b_eq": Beq,
        "bounds": bounds,
    }

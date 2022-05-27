import math

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from prereise.gather.demanddata.transportation_electrification import (
    const,
    data_helper,
    dwelling,
)

location_allowed = {
    1: {1},  # home only
    2: set(range(1, 13)),  # home and go to work related
    4: {1, 21},  # home and school only
    5: {1, 11, 12, 21},  # home and work and school
    6: {10, 11, 12},  # only work
}

why_to_list = [
    1,
    53,  # home related
    10,
    11,
    12,  # work related
    13,
    14,
    17,
    20,
    21,
    22,
    23,  # other
    24,
    30,
    40,
    41,
    42,
    50,
    51,
    52,
    53,
    54,
    55,
    60,
    61,
    62,
    63,
    64,
    65,
    80,
    81,
    82,
    83,
]


def get_constraints(individual, kwhmi, power, trip_strategy, location_strategy, cost):
    """Determine the consumption and charging constraints for each trip (hour segment)

    :param pandas.DataFrame individual: trip data of an individual vehicle
    :param int kwhmi: fuel efficiency, should vary based on vehicle type and model_year.
    :param float power: charger power, EVSE kW.
    :param int trip_strategy: a toggle that determines if should charge on any trip or
        only after last trip (1-anytrip number, 2-last trip)
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, 5, or 6;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school, 6-only work
    :param numpy.array cost: cost function
    :return: (*pandas.DataFrame*) -- a DataFrame adding the calculated constraints
        to an individual vehicle's data
    """
    constraints_df = individual.copy()
    grouped_trips = individual.groupby("sample vehicle number")

    # for "power" - setting power value based on "why to"
    constraints_df.loc[
        constraints_df["why to"].isin(why_to_list), "power_allowed"
    ] = power
    constraints_df["power_allowed"].fillna(0, inplace=True)

    # for "power" - location
    if location_strategy == 3:
        constraints_df["location_allowed"] = True
    else:
        allowed = location_allowed[location_strategy]
        constraints_df["location_allowed"] = constraints_df["why to"].map(
            lambda x: x in allowed
        )

    # for "power" - trip number
    if trip_strategy == 1:
        constraints_df["trip_allowed"] = True
    elif trip_strategy == 2:
        constraints_df["trip_allowed"] = (
            constraints_df["trip number"] == constraints_df["total vehicle trips"]
        )

    # for "power" - dwell
    constraints_df["dwell_allowed"] = constraints_df["Dwell time (hour decimal)"] > 0.2

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
            constraints_df.loc[group.index, "Miles traveled"] * kwhmi * -1
        )
        constraints_df.loc[group.index, "seg"] = dwelling.get_segment(
            constraints_df.loc[group.index, "End time (hour decimal)"],
            constraints_df.loc[group.index, "Dwell time (hour decimal)"],
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
            d["End time (hour decimal)"],
            d["Dwell time (hour decimal)"],
            const.charging_efficiency,
        ),
        axis=1,
    )

    constraints_df["rates"] = constraints_df.apply(
        lambda d: dwelling.get_rates(
            cost, d["End time (hour decimal)"], d["Dwell time (hour decimal)"]
        ),
        axis=1,
    )

    return constraints_df


def calculate_optimization(
    charging_consumption, rates, elimit, seg, segsum, segcum, total_trips, kwh
):
    """Calculates the minimized charging cost during a specific dwelling activity

    :param list charging_consumption: the charging consumption for each trip
    :param list rates: rates to be used for the cost function
    :param list elimit: energy limits during the time span of available charging
    :param list seg: the amount of the segments in the dwelling activity
    :param int segsum: the overall total of segments
    :param list segcum: cumulative sum of the segments
    :param int total_trips: total number of trips for the current vehicle
    :param float kwh: kwhmi * veh_range, amount of energy needed to charge vehicle.
    :return: (*scipy.optimize.OptimizeResult*) -- contains the result from the
        optimization, such as "x", an array of the optimal values, and "status", which
        tells the exit status of the algorithm.
    """
    f = np.array(rates) / const.charging_efficiency

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

    return linprog(
        c=f,
        A_ub=Aineq,
        b_ub=Bineq,
        A_eq=Aeq,
        b_eq=Beq,
        bounds=bounds,
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
    :param np.array LOAD: the initial load demand
    :param int trip_strategy: determine to charge after any trip (1) or only after the
        last trip (2)
    :return: (*numpy.ndarray*) -- charging profiles.
    """

    # load NHTS data from function
    if veh_type.lower() == "ldv":
        newdata = data_helper.remove_ldt(data_helper.load_data(census_region, filepath))

    elif veh_type.lower() == "ldt":
        newdata = data_helper.remove_ldv(data_helper.load_data(census_region, filepath))

    # updates the weekend and weekday values in the nhts data
    newdata = data_helper.update_if_weekend(newdata)

    new_columns = [
        "trip start battery charge",
        "trip end battery charge",
        "BEV could be used",
        "trip number",
        "Electricity cost",
        "Battery discharge",
        "Battery charge",
        "Battery size",
    ]
    newdata = newdata.reindex(list(newdata.columns) + new_columns, axis=1, fill_value=0)

    newdata["trip number"] = newdata.groupby("sample vehicle number").cumcount() + 1

    input_day = data_helper.get_input_day(data_helper.get_model_year_dti(model_year))

    model_year_profile = np.zeros(24 * len(input_day))
    data_day = data_helper.get_data_day(newdata)

    daily_vmt_total = data_helper.get_total_daily_vmt(newdata, input_day, daily_values)

    kwh = kwhmi * veh_range
    emfacvmt = 758118400

    nd_len = len(newdata)

    for day_iter in range(len(input_day)):

        if day_iter == len(input_day) - 1:
            adjusted_load = [
                load_demand[i] + model_year_profile[i]
                for i in range(day_iter * 24, (day_iter + 1) * 24)
            ]
            adjusted_load += [load_demand[i] + model_year_profile[i] for i in range(24)]
        else:
            adjusted_load = [
                load_demand[i] + model_year_profile[i]
                for i in range(day_iter * 24, day_iter * 24 + 48)
            ]

        cost = np.array(adjusted_load)

        g2v_load = np.zeros((100, 48))
        individual_g2v_load = np.zeros((nd_len, 48))

        i = 0

        while i < nd_len:

            # trip amount for each vehicle
            total_trips = int(
                newdata.iloc[i, newdata.columns.get_loc("total vehicle trips")]
            )

            if data_day[i] == input_day[day_iter]:

                # only home based trips
                if (
                    newdata.iloc[i, newdata.columns.get_loc("why from")]
                    * newdata.iloc[
                        i + total_trips - 1, newdata.columns.get_loc("why to")
                    ]
                    == 1
                ):

                    # copy one vehicle information to the block
                    individual = newdata[i : i + total_trips]

                    constraints = get_constraints(
                        individual, kwhmi, power, trip_strategy, location_strategy, cost
                    )

                    charging_consumption = constraints["charging consumption"].tolist()

                    rates = constraints["rates"]
                    rates = [r for trip_rates in rates for r in trip_rates]

                    elimit = constraints["energy limit"]
                    elimit = [el for energy_lim in elimit for el in energy_lim]

                    seg = constraints["seg"].apply(int).tolist()

                    segsum = sum(seg)
                    segcum = np.cumsum(seg)

                    linprog_result = calculate_optimization(
                        charging_consumption,
                        rates,
                        elimit,
                        seg,
                        segsum,
                        segcum,
                        total_trips,
                        kwh,
                    )

                    # fval is the value of the final cost, exitflag is the reason why the optimization terminates
                    # 0-success, 1-limit reached, 2-problem infeasible, 3-problem unbounded, 4-numerical difficulties
                    x = np.array(linprog_result.x)
                    exitflag = linprog_result.status

                    state_of_charge = np.zeros((total_trips, 2))

                    # find the feasible points
                    if exitflag == 0:

                        # can be an EV
                        individual = individual.copy()
                        individual.iloc[
                            :, newdata.columns.get_loc("BEV could be used")
                        ] = 1

                        for n in range(total_trips):
                            # SOC drop in kwh, from driving
                            individual.iloc[
                                n, newdata.columns.get_loc("Battery discharge")
                            ] = charging_consumption[n]

                            # G2V results
                            # define the G2V load during a trip
                            trip_g2v_load = np.zeros((1, 48))
                            start = math.floor(
                                individual.iloc[
                                    n,
                                    individual.columns.get_loc(
                                        "End time (hour decimal)"
                                    ),
                                ]
                            )
                            end = math.floor(
                                individual.iloc[
                                    n,
                                    individual.columns.get_loc(
                                        "End time (hour decimal)"
                                    ),
                                ]
                                + individual.iloc[
                                    n,
                                    individual.columns.get_loc(
                                        "Dwell time (hour decimal)"
                                    ),
                                ]
                            )

                            why_to = int(
                                individual.iloc[n, newdata.columns.get_loc("why to")]
                            )

                            trip_g2v_load[:, start : end + 1] = (
                                x[segcum[n] - seg[n] : segcum[n]]
                                / const.charging_efficiency
                            )
                            g2v_load[why_to, :] += trip_g2v_load[0, :]
                            individual_g2v_load[i + n][:] = trip_g2v_load
                            trip_g2v_cost = np.matmul(trip_g2v_load, cost)[0]

                            # charging charge. in DC
                            charge = sum(x[segcum[n] - seg[n] : segcum[n]])

                            # V2G results
                            trip_v2g_load = np.zeros((1, 48))

                            electricitycost = trip_g2v_cost
                            tripload = trip_v2g_load + trip_g2v_load

                            # update the cost function and vonvert from KW to MW
                            cost += (
                                tripload / 1000 / daily_vmt_total[day_iter] * emfacvmt
                            )[0, :]

                            # SOC rise in kwh, from charging
                            individual.iloc[
                                n, newdata.columns.get_loc("Battery charge")
                            ] = charge

                            if n == 0:
                                state_of_charge[n][0] = charging_consumption[n]
                                state_of_charge[n][1] = state_of_charge[n][0] + charge
                            else:
                                state_of_charge[n][0] = (
                                    state_of_charge[n - 1][1] + charging_consumption[n]
                                )
                                state_of_charge[n][1] = state_of_charge[n][0] + charge

                            individual.iloc[
                                n, newdata.columns.get_loc("Electricity cost")
                            ] = electricitycost

                            # copy SOC back
                            individual.iloc[
                                n, newdata.columns.get_loc("trip start battery charge")
                            ] = state_of_charge[n, 0]
                            individual.iloc[
                                n, newdata.columns.get_loc("trip end battery charge")
                            ] = state_of_charge[n, 1]

                        # find the acutal battery size, in DC
                        batterysize = max(state_of_charge[:, 1]) - min(
                            state_of_charge[:, 0]
                        )

                        # copy to individual
                        individual.iloc[
                            :, newdata.columns.get_loc("Battery size")
                        ] = batterysize

                        # copy individual back to newdata if it can be an EV
                        newdata[i : i + total_trips] = individual

            # update the counter to the next vehicle
            i += total_trips

        outputelectricload = sum(g2v_load)

        if day_iter == len(input_day) - 1:
            # MW
            model_year_profile[day_iter * 24 :] += (
                outputelectricload[:24] / (daily_vmt_total[day_iter] * 1000) * emfacvmt
            )
            model_year_profile[:24] += (
                outputelectricload[24:48]
                / (daily_vmt_total[day_iter] * 1000)
                * emfacvmt
            )

        else:
            # MW
            model_year_profile[day_iter * 24 : day_iter * 24 + 48] += (
                outputelectricload / (daily_vmt_total[day_iter] * 1000) * emfacvmt
            )

    return model_year_profile

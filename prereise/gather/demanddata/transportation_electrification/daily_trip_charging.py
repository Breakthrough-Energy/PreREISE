import math

import numpy as np
from scipy.optimize import linprog

from prereise.gather.demanddata.transportation_electrification import (
    charging_optimization,
    dwelling,
)


def calculate_daily_smart_charging_trips(
    newdata,
    input_day,
    day_iter,
    data_day,
    adjusted_load,
    charging_efficiency,
    daily_vmt_total,
    kwh,
    bev_vmt,
):
    """Calculate smart charging strategy for a trip window starting at particular day

    :param pandas.DataFrame newdata: trip data
    :param numpy.array input_day:
    :param int day_iter: 
    :param numpy.array data_day: 
    :param int/float charging_efficiency: from grid to battery efficiency.
    """
    cost = np.array(adjusted_load)
    nd_len = len(newdata)
    g2v_load = np.zeros((100, 72))
    individual_g2v_load = np.zeros((nd_len, 72))

    i = 0
    optimization_fail = 0
    missed_vmt = 0

    while i < nd_len:

        # trip amount for each vehicle
        total_trips = int(newdata.iloc[i, newdata.columns.get_loc("total_trips")])

        if data_day[i] == input_day[day_iter]:

            # only home based trips
            if (
                newdata.iloc[i, newdata.columns.get_loc("why_from")]
                * newdata.iloc[
                    i + total_trips - 1, newdata.columns.get_loc("dwell_location")
                ]
                == 1
            ):

                # copy one vehicle information to the block
                individual = newdata.iloc[i : i + total_trips].copy()

                individual["rates"] = individual.apply(
                    lambda d: dwelling.get_rates(
                        cost,
                        d["trip_end"],
                        d["dwell_time"],
                    ),
                    axis=1,
                )

                charging_consumption = individual["charging consumption"].to_numpy()

                rates = individual["rates"]
                rates = [r for trip_rates in rates for r in trip_rates]

                elimit = individual["energy limit"]
                elimit = [el for energy_lim in elimit for el in energy_lim]

                seg = individual["seg"].apply(int).to_numpy()

                linprog_inputs = charging_optimization.calculate_optimization(
                    charging_consumption,
                    rates,
                    elimit,
                    seg,
                    total_trips,
                    kwh,
                    charging_efficiency,
                )

                linprog_result = linprog(**linprog_inputs)

                # fval is the value of the final cost, exitflag is the reason why the optimization terminates
                # 0-success, 1-limit reached, 2-problem infeasible, 3-problem unbounded, 4-numerical difficulties
                x = np.array(linprog_result.x)
                exitflag = linprog_result.status

                state_of_charge = np.zeros((total_trips, 2))

                # find the feasible points
                if exitflag == 0:

                    # can be an EV
                    individual.iloc[:, newdata.columns.get_loc("BEV could be used")] = 1

                    for n in range(total_trips):
                        # SOC drop in kwh, from driving
                        individual.iloc[
                            n, newdata.columns.get_loc("Battery discharge")
                        ] = charging_consumption[n]

                        # G2V results
                        # define the G2V load during a trip
                        trip_g2v_load = np.zeros((1, 72))
                        start = math.floor(
                            individual.iloc[
                                n,
                                individual.columns.get_loc("trip_end"),
                            ]
                        )
                        end = math.floor(
                            individual.iloc[
                                n,
                                individual.columns.get_loc("trip_end"),
                            ]
                            + individual.iloc[
                                n,
                                individual.columns.get_loc("dwell_time"),
                            ]
                        )

                        dwell_location = int(
                            individual.iloc[
                                n, newdata.columns.get_loc("dwell_location")
                            ]
                        )

                        segcum = np.cumsum(seg)
                        trip_g2v_load[:, start : end + 1] = (
                            #  possibly? x[segcum[n] - seg[n] + 1 : segcum[n]] / charging_efficiency
                            x[segcum[n] - seg[n] : segcum[n]]
                            / charging_efficiency
                        )
                        g2v_load[dwell_location, :] += trip_g2v_load[0, :]
                        individual_g2v_load[i + n][:] = trip_g2v_load
                        trip_g2v_cost = np.matmul(trip_g2v_load, cost)[0]

                        # charging charge. in DC
                        charge = sum(x[segcum[n] - seg[n] : segcum[n]])

                        # V2G results
                        trip_v2g_load = np.zeros((1, 72))

                        electricitycost = trip_g2v_cost
                        tripload = trip_v2g_load + trip_g2v_load

                        # update the cost function and convert from KW to MW
                        cost += (tripload / 1000 / daily_vmt_total[day_iter] * bev_vmt)[
                            0, :
                        ]

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
            else:
                optimization_fail += 1
                missed_vmt += individual["total vehicle miles traveled"].sum()

        # update the counter to the next vehicle
        i += total_trips

    outputelectricload = sum(g2v_load)

    print(f"Optimization failures: {optimization_fail}")
    print(f"missed_vmt: {missed_vmt}")

    return outputelectricload

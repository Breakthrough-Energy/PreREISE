import math

import numpy as np
from scipy.optimize import linprog

from prereise.gather.demanddata.transportation_electrification import (
    charging_optimization,
    data_helper,
    dwelling,
)

location_allowed = {
    1: {1},  # base only
}


def smart_charging(
    model_year,
    veh_range,
    power,
    location_strategy,
    veh_type,
    filepath,
    initial_load,
    bev_vmt,
    trip_strategy=1,
):
    """Smart charging function

    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on
        single charge.
    :param int kwhmi_f: fuel efficiency, should vary based on vehicle type and model_year.
    :param int power: charger power, EVSE kW.
    :param int location_strategy: where the vehicle can charge - 1 or 3;
        1-base only, 3-anywhere if possibile.
    :param str veh_type: determine which category (LHDV, MHDV, or HHDT) to produce charging
        profiles for
    :param str filepath: the path to the HDV data file.
    :param np.array initial_load: the initial load demand
    :param int hdv_year: index of input year from this list [2005,2012,2030,2035,2040,2050].
    :param list hdv_penetration: penetration value for each category; LHDV, MHDV, HHDV.
    :param int trip_strategy: determine to charge after any trip (1) or only after the
        last trip (2)
    :return: (*numpy.ndarray*) -- charging profiles.
    """

    # load NHTS data from function
    if veh_type.lower() == "ldv":
        newdata = data_helper.load_hdv_data("lhdv", filepath)
        # hdv_cat = 1
    if veh_type.lower() == "mdv":
        newdata = data_helper.load_hdv_data("mhdv", filepath)
        # hdv_cat = 2
    elif veh_type.lower() == "hdv":
        newdata = data_helper.load_hdv_data("hhdv", filepath)
        # hdv_cat = 3

    new_columns = [
        "trip start battery charge",
        "trip end battery charge",
        "BEV could be used",
        "Battery size",
        "Electricity cost",
        "Battery discharge",
        "Battery charge",
    ]
    newdata = newdata.reindex(list(newdata.columns) + new_columns, axis=1, fill_value=0)

    # used to be input_day
    model_year_len = 365

    load_demand = -min(initial_load) + initial_load
    model_year_profile = np.zeros(24 * model_year_len)

    daily_vmt_total = data_helper.get_total_hdv_daily_vmt(newdata, veh_range)

    kwhmi = data_helper.get_kwhmi(model_year, veh_type, veh_range)
    kwh = kwhmi * veh_range

    # charging_efficiency value used to be in const.py
    if power > 19.2:
        charging_efficiency = 0.95
    else:
        charging_efficiency = 0.9

    nd_len = len(newdata)

    newdata = charging_optimization.get_constraints(
        newdata,
        kwhmi,
        power,
        trip_strategy,
        location_strategy,
        location_allowed,
        charging_efficiency,
    )

    day_num = model_year_len
    for day_iter in range(day_num):

        adjusted_load = [
            load_demand[i] + model_year_profile[i]
            for i in range(
                day_iter * 24, (day_iter + 1) * 24 + min(day_num - day_iter - 1, 2) * 24
            )
        ]

        if 3 - day_num + day_iter > 0:
            adjusted_load += [
                load_demand[i] + model_year_profile[i]
                for i in range(24 * (3 - day_num + day_iter))
            ]

        cost = np.array(adjusted_load)

        g2v_load = np.zeros((100, 72))
        individual_g2v_load = np.zeros((nd_len, 72))

        i = 0

        while i < nd_len:

            # trip amount for each vehicle
            total_trips = int(newdata.iloc[i, newdata.columns.get_loc("total_trips")])

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
            segcum = np.cumsum(seg)

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

                    why_to = int(
                        individual.iloc[n, newdata.columns.get_loc("Destination to")]
                    )

                    trip_g2v_load[:, start : end + 1] = (
                        x[segcum[n] - seg[n] : segcum[n]] / charging_efficiency
                    )
                    g2v_load[why_to, :] += trip_g2v_load[0, :]
                    individual_g2v_load[i + n][:] = trip_g2v_load
                    trip_g2v_cost = np.matmul(trip_g2v_load, cost)[0]

                    # charging charge. in DC
                    charge = sum(x[segcum[n] - seg[n] : segcum[n]])

                    # V2G results
                    trip_v2g_load = np.zeros((1, 72))

                    electricitycost = trip_g2v_cost
                    tripload = trip_v2g_load + trip_g2v_load

                    # update the cost function and vonvert from KW to MW
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
                batterysize = max(state_of_charge[:, 1]) - min(state_of_charge[:, 0])

                # copy to individual
                individual.iloc[
                    :, newdata.columns.get_loc("Battery size")
                ] = batterysize

                # # copy individual back to newdata if it can be an EV
                # newdata.iloc[i : i + total_trips] = individual

            # update the counter to the next vehicle
            i += total_trips

        outputelectricload = sum(g2v_load)

        # create wrap-around indexing function
        trip_window_indices = np.arange(day_iter * 24, day_iter * 24 + 72) % len(
            model_year_profile
        )

        # MW
        model_year_profile[trip_window_indices] += (
            outputelectricload / (daily_vmt_total[day_iter] * 1000) * bev_vmt
        )

    return model_year_profile

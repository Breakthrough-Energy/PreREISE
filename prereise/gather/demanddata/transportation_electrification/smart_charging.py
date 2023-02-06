import gc
import math
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from prereise.gather.demanddata.transportation_electrification import (
    charging_optimization,
    const,
    data_helper,
    dwelling,
)

warnings.simplefilter(action="ignore", category=FutureWarning)


def ldv_weekday_weekend_check(x, y):
    """Helper function to select weekday/weekend data rows

    :param int x: data weekday/weekend value
    :param int y: model year weekday/weekend value
    :return: (*bool*) -- if data row matches whether the current day is a weekday/weekend
    """
    return x == y


def hdv_use_all_data_rows(x, y):
    """Helper function to select weekday/weekend data rows

    :param int x: data weekday/weekend value
    :param int y: model year weekday/weekend value
    :return: (*bool*) -- always returns true to use all data rows
    """
    return True


def smart_charging(
    model_year,
    veh_range,
    power,
    location_strategy,
    veh_type,
    filepath,
    external_signal,
    bev_vmt,
    census_region=None,
    daily_values=None,
    kwhmi=None,
    trip_strategy=1,
    input_day=None,
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
    :param np.array load_demand: the initial load demand
    :param int trip_strategy: determine to charge after any trip (1) or only after the
        last trip (2)
    :return: (*numpy.ndarray*) -- charging profiles.
    """

    # for code developer debugging printouts (1 = yes, 0 = no)
    debug_printout = 0

    # load NHTS data from function
    if veh_type.lower() == "ldv":
        newdata1 = data_helper.remove_ldt(
            data_helper.load_data(census_region, filepath)
        )
        # updates the weekend and weekday values in the nhts data
        newdata1 = data_helper.update_if_weekend(newdata1)
    elif veh_type.lower() == "ldt":
        newdata1 = data_helper.remove_ldv(
            data_helper.load_data(census_region, filepath)
        )
        # updates the weekend and weekday values in the nhts data
        newdata1 = data_helper.update_if_weekend(newdata1)
    elif veh_type.lower() == "mdv":
        newdata1 = data_helper.load_hdv_data("mhdv", filepath)
    elif veh_type.lower() == "hdv":
        newdata1 = data_helper.load_hdv_data("hhdv", filepath)

    new_columns = [
        "trip start battery charge",
        "trip end battery charge",
        "BEV could be used",
        "Battery size",
        "Electricity cost",
        "Battery discharge",
        "Battery charge",
        "trip_number",
    ]
    newdata1 = newdata1.reindex(
        list(newdata1.columns) + new_columns, axis=1, fill_value=0
    )

    newdata1["trip_number"] = newdata1.groupby("vehicle_number").cumcount() + 1

    if input_day is None:
        input_day = data_helper.get_input_day(
            data_helper.get_model_year_dti(model_year)
        )

    external_signal = -min(external_signal) + external_signal

    if kwhmi is None:
        kwhmi = data_helper.get_kwhmi(model_year, veh_type, veh_range)
    kwh = kwhmi * veh_range
    if power > 19.2:
        charging_efficiency = 0.95
    else:
        charging_efficiency = 0.9

    # Add booleans for whether the location allows charging
    if location_strategy == 3:
        newdata1["location_allowed"] = True
    else:
        if veh_type.lower() in {"ldv", "ldt"}:
            allowed = const.ldv_location_allowed[location_strategy]
            newdata1["location_allowed"] = newdata1["dwell_location"].isin(allowed)
        elif veh_type.lower() in {"mdv", "hdv"}:
            allowed = const.hdv_location_allowed[location_strategy]
            newdata1["location_allowed"] = newdata1["dwell_location"].isin(allowed)

    # Add booleans for whether the trip_number (compared to total trips) allows charging
    if trip_strategy == 1:
        newdata1["trip_allowed"] = True
    elif trip_strategy == 2:
        newdata1["trip_allowed"] = newdata1["trip_number"] == newdata1["total_trips"]

    # Add booleans for whether the dwell time is long enough to allow charging
    newdata1["dwell_allowed"] = newdata1["dwell_time"] > 0.2

    # Add boolean for whether this trip allows charging
    allowed_cols = [
        "location_allowed",
        "trip_allowed",
        "dwell_allowed",
    ]
    newdata1["charging_allowed"] = newdata1[allowed_cols].apply(all, axis=1)

    newdata1["dwell_charging"] = (
        newdata1["charging_allowed"]
        * newdata1["dwell_time"]
        * power
        * charging_efficiency
    )

    grouped_trips = newdata1.groupby("vehicle_number")
    for vehicle_num, group in grouped_trips:
        newdata1.loc[group.index, "max_charging"] = newdata1.loc[
            group.index, "dwell_charging"
        ].sum()
        newdata1.loc[group.index, "required_charging"] = (
            newdata1.loc[group.index, "trip_miles"].sum() * kwhmi
        )

    # Filter for whenever available charging is insufficient to meet required charging
    newdata = newdata1.loc[
        (newdata1["required_charging"] <= newdata1["max_charging"])
    ].copy()

    # Filter for vehicle's battery range
    newdata = newdata.loc[(newdata["total vehicle miles traveled"] < veh_range)]

    nd_len = len(newdata)

    # LDV and LDT filter for cyclical trips
    if veh_type.lower() in {"ldv", "ldt"}:
        filtered_census_data = pd.DataFrame(columns=const.nhts_census_column_names)
        i = 0
        while i < nd_len:
            total_trips = int(newdata.iloc[i, newdata.columns.get_loc("total_trips")])
            # copy one vehicle information to the block
            individual = newdata.iloc[i : i + total_trips].copy()
            if (
                individual["why_from"].head(1).values[0]
                == individual["dwell_location"].tail(1).values[0]
            ):
                filtered_census_data = pd.concat(
                    [filtered_census_data, individual], ignore_index=True
                )
            i += total_trips
        del newdata
        gc.collect()
        newdata = filtered_census_data

    model_year_profile = np.zeros(24 * len(input_day))
    if veh_type.lower() in {"ldv", "ldt"}:
        data_day = data_helper.get_data_day(newdata)
    elif veh_type.lower() in {"mdv", "hdv"}:
        data_day = np.ones(len(newdata)) + 1

    daily_vmt_total = data_helper.get_total_daily_vmt(
        newdata, input_day, veh_type.lower()
    )

    nd_len = len(newdata)

    if veh_type.lower() in {"ldv", "ldt"}:
        location_allowed = const.ldv_location_allowed
        use_data_row = ldv_weekday_weekend_check
    elif veh_type.lower() in {"mdv", "hdv"}:
        location_allowed = const.hdv_location_allowed
        use_data_row = hdv_use_all_data_rows

    newdata = charging_optimization.get_constraints(
        newdata,
        kwhmi,
        power,
        trip_strategy,
        location_strategy,
        location_allowed,
        charging_efficiency,
    )

    output_load_sum_list = []

    day_num = len(input_day)
    for day_iter in range(day_num):
        print(f"Day: {day_iter}")
        gc.collect()

        adjusted_load = [
            external_signal[i] + model_year_profile[i]
            for i in range(
                day_iter * 24, (day_iter + 1) * 24 + min(day_num - day_iter - 1, 2) * 24
            )
        ]

        if 3 - day_num + day_iter > 0:
            adjusted_load += [
                external_signal[i] + model_year_profile[i]
                for i in range(24 * (3 - day_num + day_iter))
            ]

        cost = np.array(adjusted_load)

        g2v_load = np.zeros((100, 72))
        individual_g2v_load = np.zeros((nd_len, 72))

        # code developer debugging variables
        individual_vmt = 0
        individual_trip_miles = 0
        linprog_charge_results = 0
        optimization_fail = 0
        flag_1_fail = 0
        flag_2_fail = 0
        flag_3_fail = 0
        flag_4_fail = 0
        missed_vmt = 0
        # if veh_type.lower() in {"ldv", "ldt"}:
        #     missed_vehicles = pd.DataFrame(
        #         columns=const.nhts_census_column_names
        #     ).astype("int64")
        # elif veh_type.lower() in {"mdv", "hdv"}:
        #     missed_vehicles = pd.DataFrame(
        #         columns=list(newdata.columns)
        #         + [
        #             "power_allowed",
        #             "charging consumption",
        #             "seg",
        #             "power",
        #             "segcum",
        #             "energy limit",
        #             "rates",
        #         ]
        #     )

        i = 0

        while i < nd_len:
            # trip amount for each vehicle
            total_trips = int(newdata.iloc[i, newdata.columns.get_loc("total_trips")])

            if use_data_row(data_day[i], input_day[day_iter]):
                # copy one vehicle information to the block
                individual = newdata.iloc[i : i + total_trips].copy()

                individual_vmt += float(
                    individual.iloc[
                        0, individual.columns.get_loc("total vehicle miles traveled")
                    ]
                )
                individual_trip_miles += float(
                    individual.iloc[:, individual.columns.get_loc("trip_miles")].sum()
                )

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

                exitflag = linprog_result.status

                state_of_charge = np.zeros((total_trips, 2))

                # find the feasible points
                if exitflag == 0:
                    # fval is the value of the final cost, exitflag is the reason why the optimization terminates
                    # 0-success, 1-limit reached, 2-problem infeasible, 3-problem unbounded, 4-numerical difficulties
                    x_array = np.array(linprog_result.x)

                    # DANL EDITS
                    linprog_charge_results += x_array.sum().sum()

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
                            x_array[segcum[n] - seg[n] : segcum[n]]
                            / charging_efficiency
                        )
                        g2v_load[dwell_location, :] += trip_g2v_load[0, :]
                        individual_g2v_load[i + n][:] = trip_g2v_load
                        trip_g2v_cost = np.matmul(trip_g2v_load, cost)[0]

                        # charging charge. in DC
                        charge = sum(x_array[segcum[n] - seg[n] : segcum[n]])

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
                    # collected for debugging if desired
                    optimization_fail += 1
                    # agg_col_set = set(missed_vehicles.columns.to_list())
                    # ind_col_set = set(individual.columns.to_list())
                    # print(ind_col_set - agg_col_set)
                    # print(missed_vehicles.index)
                    # print(individual.index)
                    # missed_vehicles = pd.concat(
                    #     [missed_vehicles, individual], ignore_index=True
                    # )
                    missed_vmt += individual["trip_miles"].sum()
                    if exitflag == 1:
                        flag_1_fail += 1
                    elif exitflag == 2:
                        flag_2_fail += 1
                    elif exitflag == 3:
                        flag_3_fail += 1
                    elif exitflag == 4:
                        flag_4_fail += 1

            # update the counter to the next vehicle
            i += total_trips

        outputelectricload = sum(g2v_load)

        output_load_sum_list.append(np.sum(outputelectricload))

        # create wrap-around indexing function
        trip_window_indices = np.arange(day_iter * 24, day_iter * 24 + 72) % len(
            model_year_profile
        )

        # MW

        scaled_output = (
            outputelectricload
            * daily_values[day_iter]
            / (daily_vmt_total[day_iter] * 1000)
            * bev_vmt
        )

        if debug_printout == 1:
            output_check_array = (
                outputelectricload
                / kwhmi
                / daily_vmt_total[day_iter]
                * charging_efficiency
            )
            output_check_sum = output_check_array.sum()

            print(
                f"Unscaling the optimiation output should be close to or equal to 1 and is : {output_check_sum}"
            )
            print(
                f"Original vmt sum via the column total vehicle miles traveled was : {individual_vmt}"
            )
            print(
                f"Original vmt sum via the column trip miles sum was : {individual_trip_miles}"
            )
            print(
                f"Charging summation from linprog_x directly is : {linprog_charge_results}"
            )
            print(f"optimization output sum: {np.sum(outputelectricload)}")
            print(f"scaled output sum: {np.sum(scaled_output)}")

            print(f"Vmt missed in optimization: {missed_vmt}")
            print(f"Exit Flag 1: {flag_1_fail}")
            print(f"Exit Flag 2: {flag_2_fail}")
            print(f"Exit Flag 3: {flag_3_fail}")
            print(f"Exit Flag 4: {flag_4_fail}")

            # print(
            #     missed_vehicles[
            #         [
            #             "dwell_time",
            #             "total vehicle miles traveled",
            #             "dwell_location",
            #             "vehicle_number",
            #             "location_allowed",
            #             "trip_allowed",
            #             "dwell_allowed",
            #             "charging_allowed",
            #             "dwell_charging",
            #             "required_charging",
            #             "max_charging",
            #             # ,"trip_number","Date","Day of Week",
            #             # "If Weekend","Trip start time (HHMM)","Trip end time (HHMM)","Travel Minutes",
            #             # "trip_miles","Vehicle miles traveled","why_from",
            #         ]
            #     ]
            # )

        model_year_profile[trip_window_indices] += scaled_output

    return model_year_profile, output_load_sum_list, newdata

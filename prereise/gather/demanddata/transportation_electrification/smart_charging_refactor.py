from prereise.gather.demanddata.transportation_electrification import (
    const,
    data_helper,
    dwelling,
)
import pandas as pd
import numpy as np
from scipy.optimize import linprog


def get_constraints(trips, kwhmi, power, cost):
    """Determine the consumption and charging constraints for each trip (hour segment)
    
    :param pandas.DataFrame trips: trip data
    :param int kwhmi: fuel efficiency, should vary based on vehicle type and model_year.
    :param numpy.array cost: cost function
    """
    grouped_trips = trips.groupby("sample vehicle number")

    for trip_num, group in grouped_trips:
        trips.loc[group.index, "charge consumption"] = trips.loc[group.index, "Miles traveld"] * kwhmi * -1
        trips.loc[group.index, "seg"] = dwelling.get_segment(trips.loc[group.index, "End time (hour decimal)"], trips.loc[group.index, "Dwell time (hour decimal)"])

    # power = dwelling.get_charging_power

    trips["segcum"] = grouped_trips["seg"].transform(pd.Series.cumsum)
    trips["energy limit"] = trips.apply(lambda d: dwelling.get_energy_limit(power, d["seg"], d["End time (hour decimal)"], d["Dwell time (hour decimal)"], const.charging_efficiency), axis=1)
    trips["rates"] = trips.apply(lambda d: dwelling.get_rates(cost, d["End time (hour decimal)"], d["Dwell time (hour decimal)"]) / const.charging_efficiency, axis=1)
    
    # breakdown 'energy limit' and 'rates' lists
    # cols = trips.columns.values.tolist()
    # trips = trips.set_index(cols[:-2]).apply(pd.Series.explode).reset_index()


def calculate_charging(trips, optimized_values, cost):
    """Calculate charging, SOC, electricity cost, battery size for each trip 

    :param pandas.DataFrame trips: trip data
    :param numpy.array optimized_values: optimal values from linear optimization
    :param numpy.array cost: cost function
    """
    # still need G2Vload, tripload, cost

    # -- battery charge --
    trips["Battery charge"] = trips.apply(lambda d: sum(dwelling.get_optimized_values(optimized_values, d["segcum"], d["seg"])), axis=1)

    # -- SOC & trip start/end battery charge --
    trip_grouping = trips.groupby("trip number")
    for trip, group in trip_grouping:
        if trip == 1:
            trips.loc[group.index, "start_SOC"] = trips.loc[group.index, "charging consumption"]
            trips.loc[group.index, "end_SOC"] = trips.loc[group.index, "charging consumption"] + trips.loc[group.index, "Battery charge"]
        else:
            relevant_vehicles = group["samp #"]
            previous_group = trip_grouping.get_group(trip - 1)
            start_soc = previous_group["end_SOC"] * 10
            trips.loc[group.index, "start_SOC"] = start_soc.values[
                previous_group["samp #"].isin(relevant_vehicles)
            ]
            trips.loc[group.index, "end_SOC"] = trips.loc[group.index, "start_SOC"] + trips.loc[group.index, "Battery charge"]

    trips["trip start battery charge"] = trips["start_SOC"]
    trips["trip end battery charge"] = trips["end_SOC"]

    # -- electricity cost --
    # tripG2Vload = np.zeros((1,48))
    tripG2Vload = np.zeros(48)
    trips["Electricity cost"] = trips.apply(lambda d: dwelling.get_elecricity_cost(optimized_values, cost, tripG2Vload, d["segcum"], d["seg"], d["End time (hour decimal)"], d["Dwell time (hour decimal)"], const.charging_efficiency), axis=1)

    # -- battery size --
    veh_grouping = trips.groupby("sample vehicle number")
    for veh_num, group in veh_grouping:
        trips.loc[group.index, "Battery size"] = group["end_SOC"].max() - group["start_SOC"].min()



def smart_charging(census_region, model_year, veh_range, kwhmi, power, location_strategy, veh_type, filepath, comm_type, trip_strategy=1): 
    """Smart charging function

    :param int census_region: any of the 9 census regions defined by US census bureau.
    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040, 2050.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :param int kwhmi: fuel efficiency, should vary based on vehicle type and model_year.
    :param int power: charger power, EVSE kW.
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, or 5; 1-home only, 2-home and work related, 3-anywhere if possibile, 4-home and school only, 5-home and work and school.
    :param str veh_type: determine which category (LDV or LDT) to produce charging profiles for
    :param str filepath: the path to the nhts mat file.
    :param int comm_type: the type of Commute
    :param int trip_strategy: determine to charge after any trip (1) or only after the last trip (2)
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
        "BEV could be used",
        "trip number", 
        "Electricity cost",
        "Battery discharge",
        "Battery charge",
        "Battery size"
    ]
    newdata = newdata.reindex(list(newdata.columns) + new_columns, axis=1, fill_value=0)

    input_day = data_helper.get_input_day(data_helper.get_model_year_dti(model_year))

    TRANS_charge = np.zeros(24 * len(input_day))
    data_day = data_helper.get_data_day(newdata)

    daily_vmt_total = data_helper.get_total_daily_vmt(newdata, comm_type, location_strategy, input_day, data_day)

    kwh = kwhmi * veh_range
    emfacvmt = 758118400        # get from regional_scaling_factors.xlsx

    LOAD = np.ones(24 * len(input_day))

    nd_len = len(newdata)

    newdata["trip number"] = newdata.groupby("sample vehicle number").cumcount() + 1

    for day_iter in range(len(input_day)):

        if day_iter == len(input_day) - 1:
            LOAD_adj = [LOAD[i] + TRANS_charge[i] for i in range(day_iter * 24, (day_iter+1) * 24)]
            LOAD_adj += [LOAD[i] + TRANS_charge[i] for i in range(24)]
        else:
            LOAD_adj = [LOAD[i] + TRANS_charge[i] for i in range(day_iter * 24, day_iter * 24 + 48)]
        
    cost = LOAD_adj

    G2Vload = np.zeros((100, 48))
    individualG2Vload = np.zeros((nd_len, 48))

    weekend_trips = newdata.loc[(data_day == 2)].copy()
    weekday_trips = newdata.loc[(data_day == 1)].copy()

    get_constraints(weekend_trips, kwhmi, power, cost)
    get_constraints(weekday_trips, kwhmi, power, cost)

    while i < nd_len:
        total_trips = int(newdata.iloc[i, newdata.columns.get_loc("total vehicle trips")])

        segsum = sum(newdata.iloc[i:total_trips, newdata.columns.get_loc("total vehicle trips")])

        # calculate optimization inputs -- f, A_coeff, B_coeff, Aeq, Beq, bounds

        linprog_result = linprog(f, A_coeff, B_coeff, Aeq, Beq, bounds)
        x = np.array(linprog_result.x)
        optimized_values = np.array(linprog_result.x)
        exitflag = linprog_result.status  # have exitflag be a column 

        i += total_trips

    newdata["BEV could be used"] = (newdata["exitflag"] == 1)
    newdata.loc[newdata["BEV could be used"] == True, "Battery discharge"] = newdata["charging consumption"]

    calculate_charging(weekend_trips, optimized_values, cost) # if newdata["exitflag"] == 1
    calculate_charging(weekday_trips, optimized_values, cost) # if newdata["exitflag"] == 1

    for day_iter in range(len(input_day)):

        outputelectricload = sum(G2Vload)

        if day_iter == len(input_day) - 1:
            # MW
            TRANS_charge[day_iter*24:day_iter*24+24] += (outputelectricload[:24] / (daily_vmt_total[day_iter][0] * 1000) * emfacvmt)
            TRANS_charge[:24] += (outputelectricload[24:48] / (daily_vmt_total[day_iter,0]*1000)*emfacvmt)

        else:
            #MW
            TRANS_charge[day_iter*24:day_iter*24+24] += (outputelectricload / (daily_vmt_total[day_iter,0]*1000)*emfacvmt)

    return TRANS_charge

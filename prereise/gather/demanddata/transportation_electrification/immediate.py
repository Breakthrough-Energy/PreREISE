# DELETED: comm_type, LOAD, vmtsc

import prereise/gather/demanddata/transportation_electrification/mileage
import prereise/gather/demanddata/transportation_electrification/charging
import numpy as np


def immediate_charging(
    census_region, model_year, veh_range, kwhmi, power, location_strategy
):
    """Immediate charging function

    :param int census_region: any of the 9 census regions defined by US census bureau.
    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040, 2050.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :param int kwhmi: fuel efficiency, should vary based on vehicle type and model_year.
    :param int power: charger power, EVSE kW.
    :param int location_strategy: where the vehicle can charge-1, 2, or 3; 1 = home only, 2 = home and work, 3 = everywhere
    :return: (*numpy.ndarray*) -- charging profiles.
    """
    # load NHTS data from function
    newdata = mileage.remove_ldt(mileage.load_data(census_region))
    # add new columns to newdata to store data that is not in NHTS data
    newdata['trip start battery charge'] = 0
    newdata['trip end battery charge'] = 0
    newdata['charging power'] = 0
    newdata['charging time'] = 0
    # jx: never actually used... delete?
    newdata['charging consumption'] = 0  # needs double check
    newdata['BEV could be used'] = 0
    newdata['trip number'] = 0

    input_day = mileage.get_input_day(mileage.get_model_year_dti(model_year))

    TRANS_charge = np.zeros(24 * len(input_day))

    data_day = mileage.get_data_day(newdata)

    actual_vmt = 0
    potential_vmt = 0

    # charging when SOC less than batterstrategy
    battery_strategy = 1

    # 1-anytrip number, 2-last trip
    trip_strategy = 1

    kwh = kwhmi * veh_range

    for day_iter in range(len(input_day)):

        electricload = np.zeros(4800)
        # initializes electricload_old

        # vmt, trip amount, vehicle amount
        info1 = [0] * 3

        # meh: better names for counters
        trip_num = 1  # trip number for current vehicle
        # charging start and end points
        start_point = 0
        end_point = 0

        # flag to see if the trip is the first for the vheicle, '1' yes, '0' no
        firstrip = 0

        # meh: day2 = data_day, month2 = data_month
        for i in range(len(newdata)):
            if data_day[i] == input_day[day_iter]:
                if (
                    i > 0
                    and newdata.loc[i]["sample vehicle number"]
                    == newdata.loc[i - 1]["sample vehicle number"]
                ):
                    newdata.loc[i]["trip start battery charge"] = (
                        newdata.loc[i - 1]["trip end battery charge"]
                        + newdata.loc[i - 1]["depleting time"]
                    )
                    # trip number
                    trip_num += 1
                    newdata.loc[i]["trip number"] = trip_num
                else:
                    newdata.loc[i]["trip start battery charge"] = kwh
                    trip_num = 1
                    # trip number
                    newdata.loc[i]["trip number"] = trip_num

                # battery electric vehicle
                # pure electric
                ER = 1

                # 1 is the safety coefficient
                if newdata.loc[i]["total vehicle miles traveled"] < veh_range * const.safety_coefficient:
                    # 1 means the day trip could be used in battery electric vehicle
                    newdata.loc[i]["BEV could be used"] = 1
                    # trip end battery charge
                    newdata.loc[i]["trip end battery charge"] = (
                        newdata.loc[i]["trip start battery charge"]
                        - newdata[i]["Miles traveled"] * kwhmi * ER
                    )
                    # period when battery is discharging. depleting time
                    newdata.loc[i]["depleting time"] = newdata.loc[i][
                        "Travel time (hour decimal)"
                    ]

                else:
                    # 0 means the day trip could not be used in battery electric vehicle
                    newdata.loc[i]["BEV could be used"] = 0

                # data for this trip
                trip_data = newdata.loc[i]

                # charging power
                newdata.loc[i]["charging power"] = charging.get_charging_power(
                    power,
                    battery_strategy,
                    trip_strategy,
                    location_strategy,
                    kwh,
                    trip_data,
                )
                # charging time
                newdata.loc[i]["charging time"] = charging.get_charging_time(
                    newdata.loc[i]["charging power"],
                    kwh,
                    newdata.loc[i]["trip end battery charge"],
                    charging_efficiency,
                )
                # charging consumption
                newdata.loc[i][
                    "charging consumption"
                ] = charging.get_charging_consumption(
                    newdata.loc[i]["charging power"],
                    newdata.loc[i]["charging time"],
                    charging_efficiency,
                )

                # charging start point
                start_point = round(newdata.loc[i]["End time (hour decimal)"] * 100)
                # charging end point
                end_point = start_point + round(newdata.loc[i]["charging time"] * 100)
                electricload[start_point:end_point] += newdata.loc[i]["charging power"]

                info1[0] += newdata.loc[i]["Miles traveled"]
                info1[1] += 1

                if firstrip != 0:
                    info1[2] += 1

            if newdata[i]["BEV could be used"] == 1:
                actual_vmt += newdata.loc[i]["Miles traveled"]

            potential_vmt += newdata.loc[i]["Miles traveled"]

        # change resolution to 1 hour using midpoint average
        outputelectricload = np.zeros(4800)

        for k in range(48):
            if k == 0:
                # kW
                outputelectricload[k] = sum(electricload[:100]) / 100
            elif k == 47:
                # kW
                outputelectricload[k] = sum(electricload[4700:]) / 100
            else:
                outputelectricload[k] = (
                    sum(electricload[(k + 1) * 100 - 150 : (k + 1) * 100 - 50]) / 100
                )

        # only used as "test" output variables
        # output_load.append(outputelectricload)
        # info_out.append(info1)

        if day_iter == len(input_day) - 1:
            # MW
            TRANS_charge[day_iter:][0] += outputelectricload[:24] / (info1[0] * 1000)
            TRANS_charge[:24][0] += outputelectricload[24:48] / (info1[0] * 1000)
        else:
            TRANS_charge[day_iter * 24 : day_iter * 24 + 48][
                0
            ] += outputelectricload / (info1[0] * 1000)

    return TRANS_charge


# TESTING notes
# days are correct, Expected values are correct/match
# confirm that vehicle trips picked are viable - consumption variable comes in here, to make sure everything is valid

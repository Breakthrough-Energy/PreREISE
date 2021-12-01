from prereise.gather.demanddata.transportation_electrification import const
from prereise.gather.demanddata.transportation_electrification import mileage
from prereise.gather.demanddata.transportation_electrification import charging
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
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, or 5; 1-home only, 2-home and work related, 3-anywhere if possibile, 4-home and school only, 5-home and work and school.
    :return: (*numpy.ndarray*) -- charging profiles.
    """
    # load NHTS data from function
    newdata = mileage.remove_ldt(mileage.load_data(census_region))
    print(newdata)
    # add new columns to newdata to store data that is not in NHTS data
    newdata['trip start battery charge'] = 0
    newdata['trip end battery charge'] = 0
    newdata['charging power'] = 0
    newdata['charging time'] = 0

    newdata['charging consumption'] = 0  
    newdata['BEV could be used'] = 0
    newdata['trip number'] = 0

    input_day = mileage.get_input_day(mileage.get_model_year_dti(model_year))
    #2 is a weekday
    print(input_day.shape)

    TRANS_charge = np.zeros(24 * len(input_day))

    data_day = mileage.get_data_day(newdata)

    # 1-anytrip number, 2-last trip
    trip_strategy = 1

    kwh = kwhmi * veh_range

    weekday_electricload, weekend_electricload = np.zeros(4800), np.zeros(4800)

    #weekday first
    weekday_info1 = 0
    trip_num = 1
    start_point = 0
    end_point = 0

    for i in range(len(newdata)):
        if data_day[i] == 2:
            if (
                i > 0
                and newdata.iloc[i, newdata.columns.get_loc("sample vehicle number")]
                == newdata.iloc[i, newdata.columns.get_loc("sample vehicle number")]
            ):
                newdata.iloc[i, newdata.columns.get_loc("trip start battery charge")] = (
                    newdata.iloc[i - 1, newdata.columns.get_loc("trip end battery charge")]
                    + newdata.iloc[i - 1, newdata.columns.get_loc("charging consumption")] 
                )
                # trip number
                trip_num += 1
                newdata.iloc[i, newdata.columns.get_loc("trip number")] = trip_num
            else:
                newdata.iloc[i, newdata.columns.get_loc("trip start battery charge")] = kwh
                trip_num = 1
                # trip number
                newdata.iloc[i, newdata.columns.get_loc("trip number")] = trip_num

            # 1 is the safety coefficient
            if newdata.iloc[i, newdata.columns.get_loc("total vehicle miles traveled")] < veh_range * const.safety_coefficient:
                # 1 means the day trip could be used in battery electric vehicle
                newdata.iloc[i, newdata.columns.get_loc("BEV could be used")] = 1
                # trip end battery charge
                newdata.iloc[i, newdata.columns.get_loc("trip end battery charge")] = (
                    newdata.iloc[i, newdata.columns.get_loc("trip start battery charge")]
                    - newdata.iloc[i, newdata.columns.get_loc("Miles traveled")] * kwhmi * const.ER
                )
                """maybe unnecesesarry
                # period when battery is discharging. depleting time
                newdata.iloc[i, newdata.columns.get_loc("depleting time")] = newdata.iloc[i, 
                    newdata.columns.get_loc("Travel time (hour decimal)")
                ]"""

            else:
                # 0 means the day trip could not be used in battery electric vehicle
                newdata.iloc[i, newdata.columns.get_loc("BEV could be used")] = 0

            # data for this trip
            trip_data = newdata.iloc[i]

            # charging power
            newdata.iloc[i, newdata.columns.get_loc("charging power")] = charging.get_charging_power(
                power,
                trip_strategy,
                location_strategy,
                kwh,
                trip_data,
            )
            # charging time
            newdata.iloc[i, newdata.columns.get_loc("charging time")] = charging.get_charging_time(
                newdata.iloc[i, newdata.columns.get_loc("charging power")],
                kwh,
                newdata.iloc[i, newdata.columns.get_loc("trip end battery charge")],
                const.charging_efficiency,
            )
            # charging consumption
            newdata.iloc[i, newdata.columns.get_loc("charging consumption")] = newdata.iloc[i, newdata.columns.get_loc("charging power")]  * newdata.iloc[i, newdata.columns.get_loc("charging time")] * const.charging_efficiency

            # charging start point
            start_point = round(newdata.iloc[i, newdata.columns.get_loc("End time (hour decimal)")] * 100)
            # charging end point
            end_point = start_point + round(newdata.iloc[i, newdata.columns.get_loc("charging time")] * 100)
            weekday_electricload[start_point:end_point] += newdata.iloc[i, newdata.columns.get_loc("charging power")]

            weekday_info1 += newdata.iloc[i, newdata.columns.get_loc("Miles traveled")]
    
    weekday_output_electricload = np.zeros(48)
    for k in range(48):
        if k == 0:
            # kW
            weekday_output_electricload[k] = sum(weekday_electricload[:100]) / 100
        elif k == 47:
            # kW
            weekday_output_electricload[k] = sum(weekday_electricload[4700:]) / 100
        else:
            weekday_output_electricload[k] = (
                sum(weekday_electricload[(k + 1) * 100 - 150 : (k + 1) * 100 - 50]) / 100
            )
    
    print('done with weekday')

    #now weekend
    weekend_info1 = 0
    trip_num = 1
    start_point = 0
    end_point = 0

    for i in range(len(newdata)):
        if data_day[i] == 1:
            if (
                i > 0
                and newdata.iloc[i, newdata.columns.get_loc("sample vehicle number")]
                == newdata.iloc[i, newdata.columns.get_loc("sample vehicle number")]
            ):
                newdata.iloc[i, newdata.columns.get_loc("trip start battery charge")] = (
                    newdata.iloc[i - 1, newdata.columns.get_loc("trip end battery charge")]
                    + newdata.iloc[i - 1, newdata.columns.get_loc("charging consumption")] 
                )
                # trip number
                trip_num += 1
                newdata.iloc[i, newdata.columns.get_loc("trip number")] = trip_num
            else:
                newdata.iloc[i, newdata.columns.get_loc("trip start battery charge")] = kwh
                trip_num = 1
                # trip number
                newdata.iloc[i, newdata.columns.get_loc("trip number")] = trip_num

            # 1 is the safety coefficient
            if newdata.iloc[i, newdata.columns.get_loc("total vehicle miles traveled")] < veh_range * const.safety_coefficient:
                # 1 means the day trip could be used in battery electric vehicle
                newdata.iloc[i, newdata.columns.get_loc("BEV could be used")] = 1
                # trip end battery charge
                newdata.iloc[i, newdata.columns.get_loc("trip end battery charge")] = (
                    newdata.iloc[i, newdata.columns.get_loc("trip start battery charge")]
                    - newdata.iloc[i, newdata.columns.get_loc("Miles traveled")] * kwhmi * const.ER
                )
                """maybe unnecesesarry
                # period when battery is discharging. depleting time
                newdata.iloc[i, newdata.columns.get_loc("depleting time")] = newdata.iloc[i, 
                    newdata.columns.get_loc("Travel time (hour decimal)")
                ]"""

            else:
                # 0 means the day trip could not be used in battery electric vehicle
                newdata.iloc[i, newdata.columns.get_loc("BEV could be used")] = 0

            # data for this trip
            trip_data = newdata.iloc[i]

            # charging power
            newdata.iloc[i, newdata.columns.get_loc("charging power")] = charging.get_charging_power(
                power,
                trip_strategy,
                location_strategy,
                kwh,
                trip_data,
            )
            # charging time
            newdata.iloc[i, newdata.columns.get_loc("charging time")] = charging.get_charging_time(
                newdata.iloc[i, newdata.columns.get_loc("charging power")],
                kwh,
                newdata.iloc[i, newdata.columns.get_loc("trip end battery charge")],
                const.charging_efficiency,
            )
            # charging consumption
            newdata.iloc[i, newdata.columns.get_loc("charging consumption")] = newdata.iloc[i, newdata.columns.get_loc("charging power")]  * newdata.iloc[i, newdata.columns.get_loc("charging time")] * const.charging_efficiency

            # charging start point
            start_point = round(newdata.iloc[i, newdata.columns.get_loc("End time (hour decimal)")] * 100)
            # charging end point
            end_point = start_point + round(newdata.iloc[i, newdata.columns.get_loc("charging time")] * 100)
            weekend_electricload[start_point:end_point] += newdata.iloc[i, newdata.columns.get_loc("charging power")]

            weekend_info1 += newdata.iloc[i, newdata.columns.get_loc("Miles traveled")]

    weekend_output_electricload = np.zeros(48)
    for k in range(48):
        if k == 0:
            # kW
            weekend_output_electricload[k] = sum(weekend_electricload[:100]) / 100
        elif k == 47:
            # kW
            weekend_output_electricload[k] = sum(weekend_electricload[4700:]) / 100
        else:
            weekend_output_electricload[k] = (
                sum(weekend_electricload[(k + 1) * 100 - 150 : (k + 1) * 100 - 50]) / 100    
            )

    print('done with weekend')

    outputs= [weekend_output_electricload, weekday_output_electricload,]
    info1s = [weekend_info1, weekday_info1]

    for day_iter in range(len(input_day)):
        #weekday = 1 if weekday, 0 if not weekday
        weekday = input_day[day_iter] - 1
        if day_iter == len(input_day) - 1:
            TRANS_charge[day_iter*24:] += outputs[weekday][:24] / (info1s[weekday] * 1000)
            TRANS_charge[:24] += outputs[weekday][24:48] / (info1s[weekday] * 1000)

        else:
            TRANS_charge[day_iter * 24 : day_iter * 24 + 48] += outputs[weekday] / (info1s[weekday] * 1000)
        
    return TRANS_charge
    



# TESTING notes
# days are correct, Expected values are correct/match
# confirm that vehicle trips picked are viable - consumption variable comes in here, to make sure everything is valid

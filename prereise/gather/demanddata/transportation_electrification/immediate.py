import numpy as np

from prereise.gather.demanddata.transportation_electrification import (
    charging,
    const,
    data_helper,
)


def immediate_charging(
    census_region,
    model_year,
    veh_range,
    kwhmi,
    power,
    location_strategy,
    veh_type,
    filepath,
):
    """Immediate charging function

    :param int census_region: any of the 9 census regions defined by US census bureau.
    :param int model_year: year that is being modelled/projected to, 2017, 2030, 2040, 2050.
    :param int veh_range: 100, 200, or 300, represents how far vehicle can travel on single charge.
    :param int kwhmi: fuel efficiency, should vary based on vehicle type and model_year.
    :param int power: charger power, EVSE kW.
    :param int location_strategy: where the vehicle can charge-1, 2, 3, 4, or 5;
        1-home only, 2-home and work related, 3-anywhere if possibile,
        4-home and school only, 5-home and work and school.
    :param str veh_type: determine which category (LDV or LDT) to produce charging profiles for
    :param str filepath: the path to the NHTS mat file.
    :return: (*numpy.ndarray*) -- charging profiles.
    """

    # load NHTS data from function
    if veh_type.lower() == "ldv":
        newdata = data_helper.remove_ldt(data_helper.load_data(census_region, filepath))

    elif veh_type.lower() == "ldt":
        newdata = data_helper.remove_ldv(data_helper.load_data(census_region, filepath))

    # updates the weekend and weekday values in the nhts data
    newdata = data_helper.update_if_weekend(newdata)

    # add new columns to newdata to store data that is not in NHTS data
    newdata = newdata.reindex(
        list(newdata.columns)
        + [
            "trip start battery charge",
            "trip end battery charge",
            "charging power",
            "charging time",
            "charging consumption",
            "BEV could be used",
            "trip number",
        ],
        axis="columns",
        fill_value=0,
    )

    input_day = data_helper.get_input_day(data_helper.get_model_year_dti(model_year))

    TRANS_charge = np.zeros(24 * len(input_day))
    data_day = data_helper.get_data_day(newdata)

    trip_strategy = 1
    kwh = kwhmi * veh_range
    weekday_electricload, weekend_electricload = np.zeros(4800), np.zeros(4800)

    l = len(newdata)

    # weekday first
    trip_num = 1
    start_point = 0
    end_point = 0

    for i in range(l):
        if data_day[i] == 2:  # 2 is weekday
            if (
                i > 0
                and newdata.iloc[i, newdata.columns.get_loc("sample vehicle number")]
                == newdata.iloc[i - 1, newdata.columns.get_loc("sample vehicle number")]
            ):
                newdata.iloc[
                    i, newdata.columns.get_loc("trip start battery charge")
                ] = (
                    newdata.iloc[
                        i - 1, newdata.columns.get_loc("trip end battery charge")
                    ]
                    + newdata.iloc[
                        i - 1, newdata.columns.get_loc("charging consumption")
                    ]
                )
                trip_num += 1
                newdata.iloc[i, newdata.columns.get_loc("trip number")] = trip_num

            else:
                newdata.iloc[
                    i, newdata.columns.get_loc("trip start battery charge")
                ] = kwh
                trip_num = 1
                newdata.iloc[i, newdata.columns.get_loc("trip number")] = trip_num

            if (
                newdata.iloc[i, newdata.columns.get_loc("total vehicle miles traveled")]
                < veh_range * const.ER
            ):
                newdata.iloc[i, newdata.columns.get_loc("BEV could be used")] = 1
                newdata.iloc[i, newdata.columns.get_loc("trip end battery charge")] = (
                    newdata.iloc[
                        i, newdata.columns.get_loc("trip start battery charge")
                    ]
                    - newdata.iloc[i, newdata.columns.get_loc("Miles traveled")]
                    * kwhmi
                    * const.ER
                )
            else:
                newdata.iloc[i, newdata.columns.get_loc("BEV could be used")] = 0

            trip_data = newdata.iloc[i]

            newdata.iloc[
                i, newdata.columns.get_loc("charging power")
            ] = charging.get_charging_power(
                power,
                trip_strategy,
                location_strategy,
                kwh,
                trip_data,
            )

            newdata.iloc[
                i, newdata.columns.get_loc("charging time")
            ] = charging.get_charging_time(
                newdata.iloc[i, newdata.columns.get_loc("charging power")],
                kwh,
                newdata.iloc[i, newdata.columns.get_loc("trip end battery charge")],
                const.charging_efficiency,
                trip_data,
            )

            newdata.iloc[i, newdata.columns.get_loc("charging consumption")] = (
                newdata.iloc[i, newdata.columns.get_loc("charging power")]
                * newdata.iloc[i, newdata.columns.get_loc("charging time")]
                * const.charging_efficiency
            )

            # charging start point
            start_point = round(
                newdata.iloc[i, newdata.columns.get_loc("End time (hour decimal)")]
                * 100
            )

            # charging end point
            end_point = start_point + round(
                newdata.iloc[i, newdata.columns.get_loc("charging time")] * 100
            )
            weekday_electricload[start_point:end_point] += newdata.iloc[
                i, newdata.columns.get_loc("charging power")
            ]

    weekday_output_electricload = np.zeros(48)
    for k in range(48):
        if k == 0:
            weekday_output_electricload[k] = sum(weekday_electricload[:100]) / 100
        elif k == 47:
            weekday_output_electricload[k] = sum(weekday_electricload[4700:]) / 100
        else:
            weekday_output_electricload[k] = (
                sum(weekday_electricload[(k + 1) * 100 - 150 : (k + 1) * 100 - 50])
                / 100
            )

    # weekend, reset vars
    trip_num = 1
    start_point = 0
    end_point = 0

    for i in range(l):
        if data_day[i] == 1:  # 1 is weekend
            if (
                i > 0
                and newdata.iloc[i, newdata.columns.get_loc("sample vehicle number")]
                == newdata.iloc[i - 1, newdata.columns.get_loc("sample vehicle number")]
            ):
                newdata.iloc[
                    i, newdata.columns.get_loc("trip start battery charge")
                ] = (
                    newdata.iloc[
                        i - 1, newdata.columns.get_loc("trip end battery charge")
                    ]
                    + newdata.iloc[
                        i - 1, newdata.columns.get_loc("charging consumption")
                    ]
                )
                trip_num += 1
                newdata.iloc[i, newdata.columns.get_loc("trip number")] = trip_num

            else:
                newdata.iloc[
                    i, newdata.columns.get_loc("trip start battery charge")
                ] = kwh
                trip_num = 1
                newdata.iloc[i, newdata.columns.get_loc("trip number")] = trip_num

            if (
                newdata.iloc[i, newdata.columns.get_loc("total vehicle miles traveled")]
                < veh_range * const.ER
            ):
                newdata.iloc[i, newdata.columns.get_loc("BEV could be used")] = 1
                newdata.iloc[i, newdata.columns.get_loc("trip end battery charge")] = (
                    newdata.iloc[
                        i, newdata.columns.get_loc("trip start battery charge")
                    ]
                    - newdata.iloc[i, newdata.columns.get_loc("Miles traveled")]
                    * kwhmi
                    * const.ER
                )

            else:
                newdata.iloc[i, newdata.columns.get_loc("BEV could be used")] = 0

            trip_data = newdata.iloc[i]

            newdata.iloc[
                i, newdata.columns.get_loc("charging power")
            ] = charging.get_charging_power(
                power,
                trip_strategy,
                location_strategy,
                kwh,
                trip_data,
            )

            newdata.iloc[
                i, newdata.columns.get_loc("charging time")
            ] = charging.get_charging_time(
                newdata.iloc[i, newdata.columns.get_loc("charging power")],
                kwh,
                newdata.iloc[i, newdata.columns.get_loc("trip end battery charge")],
                const.charging_efficiency,
                trip_data,
            )

            newdata.iloc[i, newdata.columns.get_loc("charging consumption")] = (
                newdata.iloc[i, newdata.columns.get_loc("charging power")]
                * newdata.iloc[i, newdata.columns.get_loc("charging time")]
                * const.charging_efficiency
            )

            start_point = round(
                newdata.iloc[i, newdata.columns.get_loc("End time (hour decimal)")]
                * 100
            )
            end_point = start_point + round(
                newdata.iloc[i, newdata.columns.get_loc("charging time")] * 100
            )
            weekend_electricload[start_point:end_point] += newdata.iloc[
                i, newdata.columns.get_loc("charging power")
            ]

    weekend_output_electricload = np.zeros(48)
    for k in range(48):
        if k == 0:
            weekend_output_electricload[k] = sum(weekend_electricload[:100]) / 100
        elif k == 47:
            weekend_output_electricload[k] = sum(weekend_electricload[4700:]) / 100
        else:
            weekend_output_electricload[k] = (
                sum(weekend_electricload[(k + 1) * 100 - 150 : (k + 1) * 100 - 50])
                / 100
            )

    outputs = [weekend_output_electricload, weekday_output_electricload]

    for day_iter in range(len(input_day)):
        # weekday = 1 if weekday, 0 if not weekday
        weekday = input_day[day_iter] - 1

        if day_iter == len(input_day) - 1:
            TRANS_charge[day_iter * 24 :] += outputs[weekday][:24].transpose()
            TRANS_charge[:24] += outputs[weekday][24:48].transpose()

        else:
            TRANS_charge[day_iter * 24 : day_iter * 24 + 48] += outputs[
                weekday
            ].transpose()

    TRANS_charge = TRANS_charge / sum(TRANS_charge)

    return TRANS_charge


def adjust_BEV(TRANS_charge, adjustment_values):
    """Adjusts the charging profiles by applying weighting factors based on
    seasonal/monthly values

    :param (*numpy.ndarray*) TRANS_charge: normalized charging profiles
    :param (*pandas.DataFrame*) adjustment_values: weighting factors for each
        day of the year loaded from month_info_nhts.mat.
    :return: (*numpy.ndarray*) -- the final adjusted charging profiles.
    """
    adj_vals = adjustment_values.transpose()
    profiles = TRANS_charge.reshape((24, 365), order="F")

    pr = profiles / sum(profiles)
    adjusted = pr * adj_vals

    return adjusted.T.flatten()

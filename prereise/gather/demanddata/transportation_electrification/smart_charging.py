import data_helper
import const
import dwelling
import numpy as np
import scipy


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
        "Electricity cost",
        "Battery discharge",
        "Battery charge",
        "Battery size"
    ]
    newdata = newdata.reindex(list(newdata.columns) + new_columns, axis=1, fill_value=0)

    input_day = data_helper.get_input_day(data_helper.get_model_year_dti(model_year))

    TRANS_charge = np.zeros(24 * len(input_day))
    data_day = data_helper.get_data_day(newdata)

    daily_vmt_total = data_helper.total_daily_vmt(census_region, comm_type, location_strategy, input_day)

    kwh = kwhmi * veh_range
    emfacvmt = 758118400

    LOAD = np.ones(24 * len(input_day))

    nd_len = len(newdata)

    for day_iter in range(len(input_day)):
  
        if day_iter == len(input_day) - 1:
            LOAD_adj = [LOAD[i] + TRANS_charge[i] for i in range(day_iter * 24, (day_iter+1) * 24)]
            LOAD_adj += [LOAD[i] + TRANS_charge[i] for i in range(24)]
        else:
            LOAD_adj = [LOAD[i] + TRANS_charge[i] for i in range(day_iter * 24, day_iter * 24 + 48)]
        
        cost = LOAD_adj

        G2Vload = np.zeros((100, 48))
        individualG2Vload = np.zeros(nd_len, 48)

        i = 0

        while i < nd_len:
            #zero individual block, this for each vehicle per day
            individual = 0

            #trip amount for each vehicle
            total_trips = newdata.iloc[i, newdata.columns.get_loc("total vehicle trips")]

            if data_day[i] == input_day[day_iter]:

                # only home based trips
                if newdata.iloc[i, newdata.columns.get_loc("why from")] * newdata.iloc[i+total_trips, newdata.columns.get_loc("why to")] == 1:
                    
                    # copy one vehicle information to the block
                    individual = newdata[i:i+total_trips-1]

                    # 'trip' is used to determine if the loop should end. 'trip' is to count the trip number
                    # e.g. 1.5-3.3 has 3 segment 1 2 3
                    trip_num = 0

                    # get the consumption and charging constraints for each trip(hour segment)
                    charging_consumption = []      # zero the consumption, this is a vector, the consumption for each trip
                    rates = []  # zero the rates of all segments, which will be used as cost function later
                    elimit = [] # zero the charging energy limits of all segments, which will be used as the upper bound
                    seg = []

                    # total_trips * 2 matrix, recording dwelling start and end time.
                    dwelling_times = []

                    while trip_num < total_trips:
                        #DC consumption
                        charging_consumption.append(individual.iloc[trip_num, individual.columns.get_loc("Miles traveled")] * kwhmi * -1)

                        # dwelling part, energylimit is the charging energy constraint
                        # get segment, t1, tn, s1, sn, energylimit, extracost from dwell function
                        dwelling_start_time = individual.iloc[trip_num, individual.columns.get_loc("End time (hour decimal)")]
                        dwelling_length = individual.iloc[trip_num, individual.columns.get_loc("Dwell time (hour decimal)")]
                        total_dwell_period = dwelling_start_time + dwelling_length

                        segment = dwelling.get_segment(dwelling_start_time, total_dwell_period)
                        power = dwelling.get_charging_power(power, trip_strategy, location_strategy, individual.iloc[trip_num])
                        energylimit = dwelling.get_energy_limit(power, segment, dwelling_start_time, dwelling_length, total_dwell_period)

                        # get the rates and the extra cost related to the infrasctructures; used as cost function
                        for _ in range(dwelling_start_time, dwelling_length + 1):
                            rates.append(cost[_])

                        # get the energy limit; used as constraint
                        for s in range(segment):
                            elimit.append(energylimit)

                        seg.append(segment)     # record the amount of the segments in the ith dwelling activity

                        dwelling_times.append([dwelling_start_time, total_dwell_period])

                        trip_num += 1
                    
                    segsum = sum(seg)
                    
                    # first cost function matrix, dimension 1 * segsum. representing the charging costs (rates * charging efficiency)
                    f = rates / const.charging_efficiency

                    # form all the constraints
                    Aeq = np.ones(1, segsum)                    # equality constraint
                    Beq = -sum(charging_consumption)            # equality constraint
                    ub = elimit * const.charging_efficiency     # G2V power upper bound in DC
                    lb = np.zeros((segsum, 1))                  # G2V power lower bound

                    # formulate the constraints matrix in Ax <= b, A can be divided into m
                    # generate the cumulative sum array of seg in segcum
                    segcum = np.cumsum(seg)
                    segsum = sum(seg)

                    m = total_trips                 # the amount of trips. submatrix dimension is m-1 * m
                    a = np.zeros((m-1, segsum))     # 'a' is a m-1 * segsum matrix
                    A_coeff = np.zeros(((m-1)*m, segsum))
                    b = np.tril(np.ones((m-1,m)), 1)
                    B_coeff = np.zeros((m*(m-1), 1))

                    for j in range(m):
                        # part of the A matrix
                        a = np.zeros((m-1, segsum))     

                        if j > 0:
                            # switch components in b matrix
                            bb = [b[:,m-j+1:m+1], b[:,:m-j+1]]
                        else:
                            # do not switch if j is 0
                            bb = b

                        # set the constraints in DC
                        B_coeff[(m-1)*j:(m-1)*(j+1),:] = kwh + bb * charging_consumption
                        
                        for i in range(m-1):
                            # indicate the number of the trips
                            k = j + i

                            if k <= m:
                                # ones part of the column
                                a[i-1:m, segcum[k]-seg[k]+1:segcum[k]] = 1
                            else:
                                k = k - m
                                # ones part of the column
                                a[i-1:m, segcum[k] - seg[k]+1:segcum[k]] = 1

                        A_coeff[(m-1)*j:(m-1)*j,:] = -a


                    # try to use linopy instead
                    linprog_result = scipy.optimize.linprog(f, A_coeff, B_coeff, Aeq, Beq, zip(lb, ub))
                    # fval is the value of the final cost, exitflag is the reason why the optimization terminates 
                    # 0-success, 1-limit reached, 2-problem infeasible, 3-problem unbounded, 4-numerical difficulties
                    x = np.array(linprog_result.x)
                    fval = linprog_result.fun
                    exitflag = linprog_result.status

                    SOC = np.zeros((total_trips, 2))
                    
                    #find the feasible points
                    if exitflag == 1:

                        #can be an EV
                        individual.iloc[:, newdata.columns.get_loc("BEV could be used")] = 1

                        for n in range(total_trips):
                            #SOC drop in kwh, from driving
                            individual.iloc[n, newdata.columns.get_loc("Battery discharge")] = charging_consumption[n]

                            #G2V results
                            #define the G2V load during a trip
                            tripG2Vload = np.zeros((1,48))
                            start, end = dwelling_times[n][0], dwelling_times[n][1]
                            why_to = individual.iloc[:, newdata.columns.get_loc("why to")]

                            tripG2Vload[start:end+1] = x[segcum[n]-seg[n]:segcum[n]] / const.charging_efficiency
                            G2Vload[why_to,:] += tripG2Vload
                            individualG2Vload[i+n][:] = tripG2Vload
                            tripG2Vcost = tripG2Vload * cost

                            # charging charge. in DC
                            charge = sum(x[segcum[n]-seg[n]:segcum[n]])

                            #V2G results
                            tripV2Gload = np.zeros((1,48))
                            tripV2Gcost = 0

                            electricitycost = tripG2Vcost + tripV2Gcost
                            tripload = tripV2Gload + tripG2Vload

                            #update the cost function and vonvert from KW to MW
                            cost += tripload/1000/daily_vmt_total[day_iter, 0] * emfacvmt

                            # SOC rise in kwh, from charging
                            individual.iloc[n, newdata.columns.get_loc("Battery charge")] = charge

                            if n == 1:
                                SOC[n][0] = charging_consumption[n]
                                SOC[n][1] = charging_consumption[n] + charge
                            else:
                                SOC[n][0] = SOC[n-1][1] + charging_consumption[n]
                                SOC[n][1] = SOC[n][0] + charge
                            
                            individual.iloc[n, newdata.columns.get_loc("Electricity cost")] = electricitycost

                        # copy SOC back
                        individual.iloc[:, newdata.columns.get_loc("trip start battery charge")] = SOC
                        individual.iloc[:, newdata.columns.get_loc("trip end battery charge")] = SOC

                        # find the acutal battery size, in DC
                        batterysize = max(SOC[:,1]) - min(SOC[:, 0])

                        # copy to individual
                        individual.iloc[n, newdata.columns.get_loc("Battery size")] = batterysize

                        # copy individual back to newdata if it can be an EV
                        newdata[i:i+total_trips-1, :] = individual

                    # no feasible points/other issue
                    else:
                        # cannot be an EV
                        individual.iloc[:, newdata.columns.get_loc("BEV could be used")] = 0

            # update the counter to the next vehicle
            i += total_trips

        outputelectricload = sum(G2Vload)

        if day_iter == len(input_day) - 1:
            # MW
            TRANS_charge[day_iter*24:day_iter*24+24] += (outputelectricload[:24] / (daily_vmt_total[day_iter][0] * 1000) * emfacvmt)
            TRANS_charge[:24] += (outputelectricload[24:48] / (daily_vmt_total[day_iter,0]*1000)*emfacvmt)

        else:
            #MW
            TRANS_charge[day_iter*24:day_iter*24+24] += (outputelectricload / (daily_vmt_total[day_iter,0]*1000)*emfacvmt)

    return TRANS_charge


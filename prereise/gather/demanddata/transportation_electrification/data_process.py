import pandas as pd

#Download CSV of NHTS 2017 from https://nhts.ornl.gov/

def data_filtering(census_division, filepath: str = "trippub.csv"):
    """Filter raw NHTS data to be used in mileage.py
    
    :param str filepath: filepath for the "trippub.csv" file in downloaded NHTS data
    :return: (*pd.DataFrame*) -- filtered and sorted trip data
    """

    nhts_raw = pd.read_csv(filepath)
    
    #filter to be only vehicle trips (TRPTRANS values 1-6)
    nhts = nhts_raw[nhts_raw.TRPTRANS.isin(range(1,7))]
    
    #filter out repeated trips (VMT = -1)
    nhts = nhts[nhts.TRPMILES != -1]
    
    #get correct census division
    nhts = nhts[nhts.CENSUS_D == census_division]

    #dataframe for use built here
    #columns taken directly from original csv:
    sorted_data = pd.DataFrame({"Household": nhts["HOUSEID"], 
                   "Vehicle ID": nhts["VEHID"], 
                   "Person ID": nhts["PERSONID"],
                   "Scaling Factor Applied": nhts["WTTRDFIN"],
                   "Trip Number": nhts["TDTRPNUM"],
                   "Date": nhts["TDAYDATE"], 
                   "Day of Week": nhts["TRAVDAY"],              
                   "If Weekend": nhts["TDWKND"],                
                   "Trip start time (HHMM)": nhts["STRTTIME"],
                   "Trip end time (HHMM)": nhts["ENDTIME"],
                   "Travel Minutes": nhts["TRVLCMIN"],
                   "Dwell time": nhts["DWELTIME"],
                   "Miles traveled": nhts["VMT_MILE"],          
                   "Vehicle miles travelled": nhts["TRPMILES"], 
                   "why from": nhts["WHYFROM"],
                   "why to": nhts["WHYTO"],
                   "Vehicle type": nhts["TRPTRANS"],            
                   "Household vehicle count": nhts["HHVEHCNT"],
                   "Household size": nhts["HHSIZE"]
                   })
    
    #columns that require calculations: 21-28
    sorted_data["Start time (hour decimal)"] = [row//100 + row % 100 / 60 for row in sorted_data["Trip start time (HHMM)"]]
    sorted_data["End time (hour decimal)"] = [row//100 + row % 100 / 60 for row in sorted_data["Trip end time (HHMM)"]]
    sorted_data['Dwell time (hour decimal)'] = ''
    sorted_data["Travel time (hour decimal)"]= sorted_data["End time (hour decimal)"] \
        - sorted_data["Start time (hour decimal)"]
    sorted_data["Vehicle speed (mi/hour)"] = sorted_data["Vehicle miles travelled"] \
        / sorted_data["Travel time (hour decimal)"]
    sorted_data['sample vehicle number'] = ''
    sorted_data['total vehicle trips'] = ''
    sorted_data['total vehicle miles travelled'] = ''


    i = 0
    l = len(sorted_data)
    curr_household = sorted_data.iloc[0, sorted_data.columns.get_loc('Household')]
    curr_vehicle_id = sorted_data.iloc[0, sorted_data.columns.get_loc('Vehicle ID')]
    sample_veh_num = 1
    total_trips = 0
    total_miles = 0

    while i < l:
        if curr_vehicle_id == sorted_data.iloc[i, sorted_data.columns.get_loc('Vehicle ID')] \
            and curr_household == sorted_data.iloc[i, sorted_data.columns.get_loc('Household')]:

            total_trips += 1
            total_miles += sorted_data.iloc[i, sorted_data.columns.get_loc('Vehicle miles travelled')]

            if total_trips > 1:
                sorted_data.iloc[i-1, sorted_data.columns.get_loc('Dwell time (hour decimal)')] = \
                    sorted_data.iloc[i, sorted_data.columns.get_loc('Start time (hour decimal)')] - sorted_data.iloc[i-1, sorted_data.columns.get_loc('End time (hour decimal)')]
        
            # if the last entry is == the prev few entries, this makes sure they get added in; 
            # otherwise, it would break out of loop w/o adding
            if i == (l-1):
                sorted_data.iloc[i-total_trips+1:, sorted_data.columns.get_loc('sample vehicle number')] = sample_veh_num
                sorted_data.iloc[i-total_trips+1:, sorted_data.columns.get_loc('total vehicle trips')] = total_trips
                sorted_data.iloc[i-total_trips+1:, sorted_data.columns.get_loc('total vehicle miles travelled')] = total_miles
                
                if total_trips == 1:
                    sorted_data.iloc[i, sorted_data.columns.get_loc('Dwell time (hour decimal)')] = 24 - \
                        (sorted_data.iloc[i-1, sorted_data.columns.get_loc('Start time (hour decimal)')] - sorted_data.iloc[i-1, sorted_data.columns.get_loc('End time (hour decimal)')])
                else:
                    sorted_data.iloc[i, sorted_data.columns.get_loc('Dwell time (hour decimal)')] = 24 - \
                        sorted_data.iloc[i-1, sorted_data.columns.get_loc('End time (hour decimal)')] + sorted_data.iloc[i-total_trips-1, sorted_data.columns.get_loc('Start time (hour decimal)')]
        
        else:
            sorted_data.iloc[i-total_trips:i, sorted_data.columns.get_loc('sample vehicle number')] = sample_veh_num
            sorted_data.iloc[i-total_trips:i, sorted_data.columns.get_loc('total vehicle trips')] = total_trips
            sorted_data.iloc[i-total_trips:i, sorted_data.columns.get_loc('total vehicle miles travelled')] = total_miles
            
            sample_veh_num += 1

            if total_trips == 1:
                sorted_data.iloc[i-1, sorted_data.columns.get_loc('Dwell time (hour decimal)')] = 24 - \
                    (sorted_data.iloc[i-1, sorted_data.columns.get_loc('Start time (hour decimal)')] - sorted_data.iloc[i-1, sorted_data.columns.get_loc('End time (hour decimal)')])
            else:
                sorted_data.iloc[i-1, sorted_data.columns.get_loc('Dwell time (hour decimal)')] = 24 - \
                    sorted_data.iloc[i-1, sorted_data.columns.get_loc('End time (hour decimal)')] + sorted_data.iloc[i-total_trips-1, sorted_data.columns.get_loc('Start time (hour decimal)')]
            
            total_trips = 1
            total_miles = sorted_data.iloc[i, sorted_data.columns.get_loc('Vehicle miles travelled')]
           
            curr_vehicle_id = sorted_data.iloc[i, sorted_data.columns.get_loc('Vehicle ID')]
            curr_household = sorted_data.iloc[i, sorted_data.columns.get_loc('Household')]

            # this makes sure the last entry gets included; 
            # otherwise, it would break out of loop w/o adding 
            if i == (l-1):
                sorted_data.iloc[i, sorted_data.columns.get_loc('total vehicle trips')] = total_trips
                sorted_data.iloc[i, sorted_data.columns.get_loc('total vehicle miles travelled')] = total_miles
                sorted_data.iloc[i, sorted_data.columns.get_loc('sample vehicle number')] = sample_veh_num

                if total_trips == 1:
                    sorted_data.iloc[i, sorted_data.columns.get_loc('Dwell time (hour decimal)')] = 24 - \
                        (sorted_data.iloc[i-1, sorted_data.columns.get_loc('Start time (hour decimal)')] - sorted_data.iloc[i-1, sorted_data.columns.get_loc('End time (hour decimal)')])
                else:
                    sorted_data.iloc[i, sorted_data.columns.get_loc('Dwell time (hour decimal)')] = 24 - \
                        sorted_data.iloc[i-1, sorted_data.columns.get_loc('End time (hour decimal)')] + sorted_data.iloc[i-total_trips-1, sorted_data.columns.get_loc('Start time (hour decimal)')]

        i += 1

    sorted_data.to_excel("output.xlsx")

    return sorted_data

# data_filtering(1)
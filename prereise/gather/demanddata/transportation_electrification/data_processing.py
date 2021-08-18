import pandas as pd


#Download CSV of NHTS 2017 from https://nhts.ornl.gov/

def data_filtering(filepath: str = "trippub.csv"):
    """Filter raw NHTS data to be used in mileage.py
    
    :param str filepath: filepath for the "trippub.csv" file in downloaded NHTS data
    :return: (*pd.DataFrame*) -- filtered and sorted trip data
    """
    nhts_raw = pd.read_csv(filepath)
    
    #filter to be only vehicle trips (TRPTRANS values 1-6)
    nhts = nhts_raw[nhts_raw.TRPTRANS.isin((1,6))]
    
    #fliter out repeated trips (VMT = -1)
    nhts = nhts[nhts.TRPMILES != -1]
    
    #sort by census divisions (col 80, CB)
    nhts = nhts.sort_values(by="CENSUS_D")
    
    #dataframe for use built here
    #columns taken directly from original csv:
    sorted_data = {"Household": nhts["HOUSEID"], 
                   "Vehicle ID": nhts["VEHID"], 
                   "Person ID": nhts["PERSONID"],
                   "Scaling Factor Applied": nhts["WTTRDFIN"],
                   "Trip Number": nhts["TDTRPNMUM"],
                   "Date": pd.to_datetime(nhts["TDAYDATE"],format="%Y%m"),
                   "Day of Week": nhts["TRAVDAY"],              #1-7
                   "If Weekend": nhts["TDWKND"],                #1 or 2
                   "Trip start time (HHMM)": 
                       pd.to_datetime(nhts["STRTTIME"],format="%H%M"),
                   "Trip end time (HHMM)": 
                       pd.to_datetime(nhts["ENDTIME"],format="%H%M"),
                   "Travel Minutes": nhts["TRVLCMIN"],
                   "Dwell time": nhts["DWELTIME"],
                   "Miles traveled": nhts["VMT_MILE"],
                   "Vehicle miles travelled": nhts["TRPMILES"],
                   "why from": nhts["WHYFROM"],
                   "why to": nhts["WHYTO"],
                   "Vehicle type": nhts["TRPTRANS"],            #1-4:LDV, 5+:LDT
                   "Household vehicle count": nhts["HHVEHCNT"],
                   "Household size": nhts["HHSIZE"]
                   }
    
    #columns that require calculations:
    
    #21: trip start time from HHMM to decimal hours
    hhmm_s = sorted_data["Trip start time (HHMM)"]
    sorted_data["Start time (hour decimal)"] = hhmm_s.hour + (hhmm_s.minute/60)
    
    
    #22: trip end time from HHMM to decimal hours
    hhmm_e = sorted_data["Trip end time (HHMM)"]
    sorted_data["End time (hour decimal)"] = hhmm_e.hour + (hhmm_e.minute/60)
    
    #23: calc dwell time and convert to decimal (last dwell time incorrect)
    #last trip dwell time = end of last trip to beginning of first trip
    #best approach?
    
    #24: travel time to decimal
    travel_time = sorted_data["End time (hour decimal)"] \
        - sorted_data["Start time (hour decimal)"]
    sorted_data["Travel time (hour decimal)"] = travel_time.hour \
        + (travel_time.minute/60)
    
    #25: vmt/travel time
    sorted_data["Vehicle speed (mi/hour)"] = sorted_data["Vehicle miles travelled"] \
        / sorted_data["Travel time (hour decimal)"]
    
    #26: renumber vehicles from 1
    #how to do this without a for loop?
    
    #27: for each unique vehicle, sum number of trips and put total in all 
    #lines for that vehicle
    #best approach?
    
    #28: for each unique vehicle, sum vehicle miles travelled and put total in 
    #all lines for that vehicle
    #best approach?
    
    return sorted_data
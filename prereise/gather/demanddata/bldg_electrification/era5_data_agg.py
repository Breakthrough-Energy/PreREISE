# This script contains functions to download ERA5 data and manipulate it to
# produce hourly time series of (dry bulb) temperature, dew point temperature
# and surface pressure. It is designed for the specific use case. For more 
# general information on accessing ERA5 data, see: 
# https://confluence.ecmwf.int/display/CKB/How+to+download+ERA5

import os
import pandas as pd
import numpy as np
import xarray as xr
from scipy.spatial import cKDTree

from prereise.gather.demanddata.bldg_electrification import const

def era5_download(years, directory, variable="temp"):
    """Download ERA5 data

    :param iterable integer: year(s) for which data to be downloaded given as single 
        value or iterable list
    :param string directory: path to root directory for ERA5 downloads
    :param string: variable to be downloaded, chosen from:
        temp {Default} -- dry bulb temperataure, corresponds to ERA5 variable "2m_temperature"
        dewpt -- dew point temperature, corresponds to ERA5 variable "2m_dewpoint_temperature"
        pres -- surface pressure, corresponds to ERA5 variable "surface_pressure"
    """

    # Check variable input and get associated ERA5 variable name
    if variable == "temp":
        variable_era5 = "2m_temperature"
    elif variable == "dewpt":
        variable_era5 = "2m_dewpoint_temperature"
    elif variable == "pres":
        variable_era5 = "surface_pressure"
    else:
        raise ValueError("Invalid variable name")

    # Make single year input iterable
    if not hasattr(years, "__iter__"):
        years=[years]

    # Error if 'years' includes any years prior to 1950
    if min(years) < 1950:
        raise ValueError("Input years must be 1950 or later")

    # Note if prior to 1979, preliminary version of reanalysis back extension
    if min(years) < 1979:
        print("Data for years 1950-1979 are a preliminary version of reanalysis back extension")

    import cdsapi
    """ Requires `cdsapi` to be installed per: 
        https://cds.climate.copernicus.eu/api-how-to
        """
    c = cdsapi.Client()

    # Create folder to store data for given variable if it doesn't yet exist
    if not os.path.isdir(os.path.join(directory,variable)):
        os.makedirs(os.path.join(directory,variable))

    for year in years:
        
        if year < 1979:
            dataset = "reanalysis-era5-single-levels-preliminary-back-extension"
        else:
            dataset = "reanalysis-era5-single-levels"
        
        print(f"Retrieving ERA5 {variable_era5} ({variable} input variable) dataset for {year}")
        c.retrieve(
            dataset,
            {
                "product_type" : "reanalysis",
                "format"       : "netcdf",
                "variable"     : variable_era5,
                "year"         : "{:04d}".format(year),
                "month"        : ["{:02d}".format(x) for x in range(1,13)],
                "day"          : ["{:02d}".format(x) for x in range(1,32)],
                "time"         : ["{:02d}:00".format(x) for x in range(0,24)],
                "area"         : [50,-128,24,-62],
            },
            os.path.join(directory,variable, f"{variable}s_era5_{year}.nc")
            )

def create_era5_pumas(
        years,tract_puma_mapping,tract_pop,tract_lat_lon,directory,variable="temp"
        ):
    """Create {variable}s_pumas_{state}_{year}.csv or dewpt_pumas_{state}_{year} for all
        CONUS states and input year(s)

    :param iterable integer: year(s) for which data files to be produced
    :param pandas.DataFrame tract_puma_mapping: tract to puma mapping.
    :param pandas.DataFrame tract_pop: population by tract
    :param pandas.DataFrame tract_lat_lon: latitutde and longitude of tract
    :param string directory: path to root directory for ERA5 downloads (not including variable name)
    :param string: variable to produce
        temp {Default} -- dry bulb temperataure, corresponds to ERA5 variable "2m_temperature"
        dewpt -- dew point temperature, corresponds to ERA5 variable "2m_dewpoint_temperature"
        pres -- surface pressure, corresponds to ERA5 variable "surface_pressure"
    """
    
    # Check variable input and get associated ERA5 variable name
    if variable == "temp":
        variable_era5 = "2m_temperature"
        variable_nc = "t2m"
    elif variable == "dewpt":
        variable_era5 = "2m_dewpoint_temperature"
        variable_nc = "d2m"
    elif variable == "pres":
        variable_era5 = "surface_pressure"
        variable_nc = "sp"
    else:
        raise ValueError("Variable name input is not supported")

    # Make single year input iterable
    if not hasattr(years, "__iter__"):
        years=[years]
    
    # Check if ERA5 files exist for all input years
    n_missing = 0
    for year in years:
        if not os.path.exists(os.path.join(directory,variable, f"{variable}s_era5_{year}.nc")):
            print(f"Missing file {variable_era5}_{year}.nc")
            n_missing = n_missing + 1
    if n_missing > 0:
        raise FileNotFoundError
    else:
        print("Confirmed: All required ERA5 input files present")
    
    # Create folder to store data for given variable if it doesn't yet exist
    if not os.path.isdir(os.path.join(directory,"pumas")):
        os.makedirs(os.path.join(directory,"pumas"))
        
    # Combine tract-level data into single data frame with only census tracts with building area data in included states
    tract_data = pd.concat(
        [tract_lat_lon, tract_pop], axis=1, join="inner"
    )
    tract_data = tract_data.loc[:, ~tract_data.columns.duplicated()]
    tract_data = tract_data[tract_data["state"].isin(const.state_list)]
    
    # Include tract_puma_mapping only for tracts in tract_data
    tract_puma_mapping = tract_puma_mapping[tract_puma_mapping["tract"].isin(tract_data["tract"])]
    
    # Loop through input years
    for year in years:
        print(f"Processing puma-level {variable} time series for {year}")
        # Load ERA5 dataset
        ds_era5 = xr.open_dataset(os.path.join(directory,variable, f"{variable}s_era5_{year}.nc"))
        
        # Get latitude and longitude from ERA5 dataset and make 2D arrays
        lats_era5 = ds_era5.variables["latitude"][:]
        lons_era5 = ds_era5.variables["longitude"][:]
        lons_era5_2d, lats_era5_2d = np.meshgrid(lons_era5, lats_era5)
        
        # Function to convert latitude and longitude to cartesian coordinates
        def lon_lat_to_cartesian(lon, lat):
            
            # WGS 84 reference coordinate system parameters
            A = 6378.137 # major axis [km]   
            E2 = 6.69437999014e-3 # eccentricity squared 
    
            lon_rad = np.radians(lon)
            lat_rad = np.radians(lat)
            # convert to cartesian coordinates
            r_n = A / (np.sqrt(1 - E2 * (np.sin(lat_rad) ** 2)))
            x = r_n * np.cos(lat_rad) * np.cos(lon_rad)
            y = r_n * np.cos(lat_rad) * np.sin(lon_rad)
            z = r_n * (1 - E2) * np.sin(lat_rad)
            return x,y,z
        
        x_era5, y_era5, z_era5 = lon_lat_to_cartesian(lons_era5_2d.flatten(), lats_era5_2d.flatten())
        x_tracts, y_tracts, z_tracts = lon_lat_to_cartesian(tract_data["lon"],tract_data["lat"])
        
        # Create KD-tree from ERA5 dataset coordinates
        tree_era5 = cKDTree(np.column_stack((x_era5, y_era5, z_era5)))
        
        # Create tracts values time series data frame with interpoltion using inverse distance-squared weighting for 4 nearest neighbors
        d, inds = tree_era5.query(np.column_stack((x_tracts, y_tracts, z_tracts)), k = 4)
        w = 1.0 / d**2
        vals_tracts_series = pd.Series(range(0,8760)).apply(lambda x: np.sum(w * ds_era5[variable_nc][x].values.flatten()[inds], axis=1) / np.sum(w, axis=1)) 
        vals_tracts = pd.DataFrame.from_dict(dict(zip(vals_tracts_series.index, vals_tracts_series.values))).T
        vals_tracts.columns = tract_data.tract
    
        #Loop through states
        for state in const.state_list:
            
            # Initiate vals_pumas data frame
            vals_pumas_it = pd.DataFrame(columns=const.puma_data.query("state == @state").index)
            # Loop through and compute population-weighted temperature time series
            for p in vals_pumas_it.columns:
                vals_tracts_p = vals_tracts[tract_puma_mapping["tract"][p == (tract_puma_mapping["puma"])]]
                pop_weights_p = tract_data["pop_2010"][tract_data["tract"].isin(tract_puma_mapping["tract"][p == (tract_puma_mapping["puma"])])]
                pop_weights_p.index = vals_tracts_p.columns
                vals_pumas_it[p] = vals_tracts_p.mul(pop_weights_p,axis=1).sum(axis=1) / pop_weights_p.sum()
            
            # Convert units if needed
            if variable == "temp":
                vals_pumas_it = vals_pumas_it - 273.15
            elif variable == "dewpt":
                vals_pumas_it = vals_pumas_it - 273.15

            # Save file for variable/state/year
            vals_pumas_it.to_csv(os.path.join(directory,"pumas",f"{variable}s",f"{variable}s_pumas_{state}_{year}.csv"),index=False)

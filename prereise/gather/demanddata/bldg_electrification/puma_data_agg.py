# This script develops puma-level data directly from census and aggregated from census tract data
import os

import pandas as pd
import geopandas as gpd

from prereise.gather.demanddata.bldg_electrification import const

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Load ACS fuel data for 2010
puma_fuel_2010 = pd.read_csv(
    os.path.join(data_dir, "puma_fuel_2010.csv"), index_col="puma"
)

# Load tract_puma_mapping
tract_puma_mapping = pd.read_csv(
    os.path.join(data_dir, "tract_puma_mapping.csv"), index_col="tract"
)

# Set up puma_data data frame
puma_data = puma_fuel_2010["state"].to_frame()

# Initialize columns that will be created via summing/averaging
sum_columns = [
    "pop_2010",
    "h_units_2010",
    "res_area_gbs_m2",
    "com_area_gbs_m2",
]
weighted_sum_columns = [
    "hdd65_normals_2010",
    "cdd65_normals_2010",
]

# Load RECS and CBECS area scales for res and com
resscales = pd.read_csv(os.path.join(data_dir, "area_scale_res.csv"))
comscales = pd.read_csv(os.path.join(data_dir, "area_scale_com.csv"))

# Interpolate a 2010 area to scale model area to corresponding RECS/CBECS area
resscales["2010_scalar"] = (
    resscales["RECS2009"] + (resscales["RECS2015"] - resscales["RECS2009"]) * ((const.target_year-const.recs_date_1) / (const.recs_date_2-const.recs_date_1))
) / resscales["Model2010"]
comscales["2010_scalar"] = (
    comscales["CBECS2003"] + (comscales["CBECS2012"] - comscales["CBECS2003"]) * ((const.target_year-const.cbecs_date_1) / (const.cbecs_date_2-const.cbecs_date_1))
) / comscales["Model2010"]

# Collect all state data into one data frame
tract_data = pd.concat(
    [
        pd.read_csv(os.path.join(data_dir, f"tract_data/tract_data_{state}.csv"))
        for state in const.state_list
    ]
)

# Rename tract IDs to match all dataframe naming conventions
tract_data["id"] = ["tract_" + str(i).rjust(11, "0") for i in tract_data["id"]]
tract_data["id"] = tract_data["id"].astype("str")
tract_data.set_index("id", inplace=True)

# Sum population, housing units, and areas
grouped_tracts = tract_data.groupby(tract_puma_mapping["puma"])
for col in sum_columns:
    col_to_sum = col.replace("_gbs", "").replace("_", ".")
    puma_data.loc[grouped_tracts.groups.keys(), col] = grouped_tracts[col_to_sum].sum()

# Population-weighted average hdd, cdd, and acpen
for col in weighted_sum_columns:
    col_to_sum = col.replace("_normals_2010", "").replace("_res_2010", ".res")
    weighted_elements = tract_data[col_to_sum] * tract_data["pop.2010"]
    puma_data[col] = (
        weighted_elements.groupby(tract_puma_mapping["puma"]).sum()
        / tract_data["pop.2010"].groupby(tract_puma_mapping["puma"]).sum()
    )

# Scale puma area from gbs to 2010 RECS/CBECS
for state in const.state_list:
    state_row_scale_res = resscales[resscales.eq(state).any(1)].reset_index()
    state_row_scale_com = comscales[comscales.eq(state).any(1)].reset_index()
    rscale = state_row_scale_res["2010_scalar"][0]
    cscale = state_row_scale_com["2010_scalar"][0]
    puma_data.loc[puma_data["state"] == state, "res_area_2010_m2"] = (
        puma_data[puma_data["state"] == state]["res_area_gbs_m2"] * rscale
    )
    puma_data.loc[puma_data["state"] == state, "com_area_2010_m2"] = (
        puma_data[puma_data["state"] == state]["com_area_gbs_m2"] * cscale
    )

# Calculate res fractions of fuel usage based off puma_fuel_2010 household data
puma_data["frac_sh_res_natgas"] = (
    puma_fuel_2010["hh_utilgas"] / puma_fuel_2010["hh_total"]
)
puma_data["frac_sh_res_fok"] = puma_fuel_2010["hh_fok"] / puma_fuel_2010["hh_total"]
puma_data["frac_sh_res_othergas"] = (
    puma_fuel_2010["hh_othergas"] / puma_fuel_2010["hh_total"]
)
puma_data["frac_sh_res_coal"] = puma_fuel_2010["hh_coal"] / puma_fuel_2010["hh_total"]
puma_data["frac_sh_res_wood"] = puma_fuel_2010["hh_wood"] / puma_fuel_2010["hh_total"]
puma_data["frac_sh_res_solar"] = puma_fuel_2010["hh_solar"] / puma_fuel_2010["hh_total"]
puma_data["frac_sh_res_elec"] = puma_fuel_2010["hh_elec"] / puma_fuel_2010["hh_total"]
puma_data["frac_sh_res_other"] = puma_fuel_2010["hh_other"] / puma_fuel_2010["hh_total"]
puma_data["frac_sh_res_none"] = puma_fuel_2010["hh_none"] / puma_fuel_2010["hh_total"]

regions = [const.us_northeast, const.us_midwest, const.us_south, const.us_west]
region_index = ['us_northeast', 'us_midwest', 'us_south', 'us_west']

region_series = pd.Series(regions, index=region_index)

for c in const.classes:
    if c == "res":
        uselist = ["dhw", "other"]
    else:
        uselist = ["sh", "dhw", "cook"]
    for u in uselist:
        frac_area = pd.DataFrame(columns=const.fuel)

        # Compute frac_area for each fuel type in each region
        for i in region_series:
            fuellist = []
            for j in const.fuel:
                region_df = puma_data[puma_data["state"].isin(i)].reset_index()
                fuellist.append(
                    sum(
                        region_df[f"frac_sh_res_{j}"]
                        * region_df[f"{c}_area_2010_m2"]
                    )
                    / sum(region_df[f"{c}_area_2010_m2"])
                )
            df_i = len(frac_area)
            frac_area.loc[df_i] = fuellist

        # Values calculated externally
        frac_scale = pd.read_csv(os.path.join(data_dir, f"frac_target_{u}_{c}.csv"))

        downscalar = frac_scale / frac_area

        upscalar = (frac_scale - frac_area) / (1 - frac_area)

        # Scale frac_hh_fuel to frac_com_fuel
        for f in const.fuel:
            scalar = 1
            fraccom = []
            for i in range(len(puma_data)):
                
                for j in range(len(regions)):
                    if puma_data["state"][i] in regions[j]:
                        region_index = j
                if downscalar[f][region_index] <= 1:
                    scalar = downscalar[f][region_index]
                    fraccom.append(puma_data[f"frac_sh_res_{f}"][i] * scalar)
                else:
                    scalar = upscalar[f][region_index]
                    fraccom.append(
                        (1 - puma_data[f"frac_sh_res_{f}"][i]) * scalar
                        + puma_data[f"frac_sh_res_{f}"][i]
                    )
            puma_data[f"frac_{u}_{c}_{f}"] = fraccom


# Sum coal, wood, solar and other fractions for frac_com_other
puma_data["frac_sh_com_other"] = puma_data[
    ["frac_sh_res_coal", "frac_sh_res_wood", "frac_sh_res_solar", "frac_sh_res_other"]
].sum(axis=1)

for c in const.classes:
    if c == "res":
        uselist = ["sh", "dhw", "other"]
    else:
        uselist = ["sh", "dhw", "cook"]
    for u in uselist:
        puma_data[f"frac_ff_{u}_{c}_2010"] = puma_data[
            [
                f"frac_{u}_{c}_natgas",
                f"frac_{u}_{c}_othergas",
                f"frac_{u}_{c}_fok",
            ]
        ].sum(axis=1)
        puma_data[f"frac_elec_{u}_{c}_2010"] = puma_data[
            f"frac_{u}_{c}_elec"
        ]


timezones = gpd.GeoDataFrame(gpd.read_file("data/tz_us.shp"))
pumas = gpd.GeoDataFrame(gpd.read_file("data/pumas.shp"))
puma_timezone = gpd.overlay(pumas, timezones.to_crs("EPSG:4269"))

puma_timezone["area"] = puma_timezone.area
puma_timezone.sort_values("area", ascending=False, inplace=True)
puma_timezone = puma_timezone.drop_duplicates(subset="GEOID10", keep="first")
puma_timezone.sort_values("GEOID10", ascending=True, inplace=True)
puma_timezone["puma"] = "puma_" + puma_timezone["GEOID10"]

puma_data["timezone"] = puma_timezone["TZID"]

puma_data.to_csv(os.path.join(data_dir, "puma_data.csv"), index=False)

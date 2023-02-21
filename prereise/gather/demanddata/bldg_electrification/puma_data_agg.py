# This script develops puma-level data directly from census and aggregated from census tract data
import os

import geopandas as gpd
import numpy as np
import pandas as pd

from prereise.gather.demanddata.bldg_electrification import const


def aggregate_puma_df(
    puma_states, tract_puma_mapping, tract_gbs_area, tract_degday_normals, tract_pop
):
    """Scale census tract data up to puma areas.

    :param pandas.DataFrame puma_states: mapping of puma to state.
    :param pandas.DataFrame tract_puma_mapping: tract to puma mapping.
    :param pandas.DataFrame tract_gbs_area: General Building Stock area for residential, commercial, industrial areas by tract
    :param pandas.DataFrame tract_degday_normals: heating and cooling degree day normals by tract
    :param pandas.DataFrame tract_pop: population by tract
    :return: (*pandas.DataFrame*) -- population; residential, commercial, industrial areas;
        heating degree days; cooling degree days; residential space heating household fuel
        fractions.
    """
    # Set up puma_df data frame
    puma_df = puma_states.to_frame()

    # Combine tract-level data into single data frame with only census tracts with building area data
    tract_data = pd.concat(
        [tract_gbs_area, tract_degday_normals, tract_pop], axis=1, join="inner"
    )
    tract_data = tract_data.loc[:, ~tract_data.columns.duplicated()]

    # Group tracts by PUMA for aggregration
    grouped_tracts = tract_data.groupby(tract_puma_mapping["puma"])
    # Sum population and GBS areas; store in data frame
    puma_df.loc[grouped_tracts.groups.keys(), "pop"] = grouped_tracts["pop"].sum()
    puma_df.loc[grouped_tracts.groups.keys(), "res_area_gbs_m2"] = grouped_tracts[
        "res_area_gbs_m2"
    ].sum()
    puma_df.loc[grouped_tracts.groups.keys(), "com_area_gbs_m2"] = grouped_tracts[
        "com_area_gbs_m2"
    ].sum()
    puma_df.loc[grouped_tracts.groups.keys(), "ind_area_gbs_m2"] = grouped_tracts[
        "ind_area_gbs_m2"
    ].sum()
    # Population-weighted average hdd, cdd, and acpen
    tract_data["pop_hdd65_normals"] = tract_data["pop"] * tract_data["hdd65_normals"]
    tract_data["pop_cdd65_normals"] = tract_data["pop"] * tract_data["cdd65_normals"]
    puma_df.loc[grouped_tracts.groups.keys(), "hdd65_normals"] = (
        grouped_tracts["pop_hdd65_normals"].sum() / grouped_tracts["pop"].sum()
    )
    puma_df.loc[grouped_tracts.groups.keys(), "cdd65_normals"] = (
        grouped_tracts["pop_cdd65_normals"].sum() / grouped_tracts["pop"].sum()
    )

    # Load RECS and CBECS area scales for res and com
    resscales = pd.read_csv(os.path.join(data_dir, "area_scale_res.csv"))
    comscales = pd.read_csv(os.path.join(data_dir, "area_scale_com.csv"))

    # Compute GBS areas for state groups in RECS and CBECS
    resscales["GBS"] = [
        puma_df.query("state in @s")["res_area_gbs_m2"].sum()
        * const.conv_m2_to_ft2
        * const.conv_ft2_to_bsf
        for s in resscales.fillna(0).values.tolist()
    ]
    comscales["GBS"] = [
        puma_df.query("state in @s")["com_area_gbs_m2"].sum()
        * const.conv_m2_to_ft2
        * const.conv_ft2_to_bsf
        for s in comscales.fillna(0).values.tolist()
    ]

    # Compute scalar for GBS area to base year area correspondingg to RECS/CBECS
    # and assuming a constant annual growth rate
    resscales["area_scalar"] = (
        resscales[f"RECS{const.recs_date_1}"]
        * (
            (
                resscales[f"RECS{const.recs_date_2}"]
                / resscales[f"RECS{const.recs_date_1}"]
            )
            ** (
                (const.base_year - const.recs_date_1)
                / (const.recs_date_2 - const.recs_date_1)
            )
        )
        / resscales["GBS"]
    )

    comscales["area_scalar"] = (
        comscales[f"CBECS{const.cbecs_date_1}"]
        * (
            (
                comscales[f"CBECS{const.cbecs_date_2}"]
                / comscales[f"CBECS{const.cbecs_date_1}"]
            )
            ** (
                (const.base_year - const.cbecs_date_1)
                / (const.cbecs_date_2 - const.cbecs_date_1)
            )
        )
        / comscales["GBS"]
    )

    # Scale puma area from gbs to base year
    for state in const.state_list:
        state_row_scale_res = resscales[resscales.eq(state).any(1)].reset_index()
        state_row_scale_com = comscales[comscales.eq(state).any(1)].reset_index()
        res_area_scalar = state_row_scale_res["area_scalar"][0]
        com_area_scalar = state_row_scale_com["area_scalar"][0]
        puma_df.loc[puma_df["state"] == state, f"res_area_{const.base_year}_m2"] = (
            puma_df[puma_df["state"] == state]["res_area_gbs_m2"] * res_area_scalar
        )
        puma_df.loc[puma_df["state"] == state, f"com_area_{const.base_year}_m2"] = (
            puma_df[puma_df["state"] == state]["com_area_gbs_m2"] * com_area_scalar
        )

    return puma_df


def scale_fuel_fractions(hh_fuels, puma_df, year=const.base_year):
    """Scale census tract data up to puma areas.

    :param pandas.DataFrame hh_fuels: household fuel type by puma.
    :param pandas.DataFrame puma_df: output of :func:`aggregate_puma_df`.
    :param int/str year: year to use within label when creating columns.
    :return: (*pandas.DataFrame*) -- fractions of natural gas, fuel oil and kerosone,
        propane, and electricity used for space heating, hot water, cooking, and other
        in residential and commercial buildings.
    """
    # Calculate res fractions of fuel usage based off ACS puma_fuel household data
    puma_df["frac_sh_res_natgas_acs"] = hh_fuels["hh_utilgas"] / hh_fuels["hh_total"]
    for f in ["fok", "othergas", "coal", "wood", "solar", "elec", "other", "none"]:
        puma_df[f"frac_sh_res_{f}_acs"] = hh_fuels[f"hh_{f}"] / hh_fuels["hh_total"]

    region_map = {state: r for r, states in const.regions.items() for state in states}
    puma_region_groups = puma_df.groupby(puma_df["state"].map(region_map))
    for c in const.classes:
        # Compute area fraction for each fuel type (column) in each region (index)
        area_fractions = puma_region_groups.apply(
            lambda x: pd.Series(
                {
                    f: (
                        (
                            x[f"frac_sh_res_{f}_acs"]
                            * x[f"{c}_area_{const.base_year}_m2"]
                        ).sum()
                        / x[f"{c}_area_{const.base_year}_m2"].sum()
                    )
                    for f in const.fuel
                }
            )
        )
        # Scale per-PUMA values to match target regional values (calculated externally)
        uselist = ["sh", "dhw", "other"] if c == "res" else ["sh", "dhw", "cook"]
        for u in uselist:
            area_fraction_targets = pd.read_csv(
                os.path.join(data_dir, f"frac_target_{u}_{c}.csv"),
                index_col=0,
            )
            down_scale = area_fraction_targets / area_fractions
            up_scale = (area_fraction_targets - area_fractions) / (1 - area_fractions)
            for r in const.regions:
                for f in const.fuel:
                    pre_scaling = puma_region_groups.get_group(r)[
                        f"frac_sh_res_{f}_acs"
                    ]
                    if down_scale.loc[r, f] <= 1:
                        scaled = pre_scaling * down_scale.loc[r, f]
                    else:
                        scaled = pre_scaling + up_scale.loc[r, f] * (1 - pre_scaling)
                    puma_df.loc[pre_scaling.index, f"frac_{f}_{u}_{c}_{year}"] = scaled

    # Sum coal, wood, solar and other fractions for frac_com_other
    named_sh_com_fuels = {"elec", "fok", "natgas", "othergas"}
    named_sh_com_cols = [f"frac_{f}_sh_com_{year}" for f in named_sh_com_fuels]
    puma_df[f"frac_other_sh_com_{year}"] = 1 - puma_df[named_sh_com_cols].sum(axis=1)

    # Copy residential space heating columns to match new column naming convention
    fossil_fuels = {"natgas", "othergas", "fok"}
    for c in const.classes:
        uselist = ["sh", "dhw", "other"] if c == "res" else ["sh", "dhw", "cook"]
        for u in uselist:
            fossil_cols = [f"frac_{f}_{u}_{c}_{year}" for f in fossil_fuels]
            puma_df[f"frac_ff_{u}_{c}_{year}"] = puma_df[fossil_cols].sum(axis=1)
    return puma_df


def puma_timezone_latlong(timezones, pumas):
    """Assign timezone and lat/long to each puma.

    :param geopandas.DataFrame timezones: US timezones.
    :param geopandas.DataFrame pumas: US pumas.

    :return: (*pandas.Series*) -- timezone for every puma.
    :return: (*pandas.DataFrame*) -- latitude and longitude for every puma.
    """
    puma_timezone = gpd.overlay(pumas, timezones.to_crs("EPSG:4269"))
    puma_timezone["area"] = puma_timezone.area
    puma_timezone.sort_values("area", ascending=False, inplace=True)
    puma_timezone = puma_timezone.drop_duplicates(subset="GEOID10", keep="first")
    puma_timezone.sort_values("GEOID10", ascending=True, inplace=True)

    puma_lat_long = pd.DataFrame(
        {
            "puma": "puma_" + pumas["GEOID10"],
            "latitude": [float(pumas["INTPTLAT10"][i]) for i in range(len(pumas))],
            "longitude": [float(pumas["INTPTLON10"][i]) for i in range(len(pumas))],
        }
    )
    puma_lat_long = puma_lat_long.set_index("puma")

    return puma_timezone["tzid"], puma_lat_long


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    # Load ACS fuel data
    puma_fuel = pd.read_csv(os.path.join(data_dir, "puma_fuel.csv"), index_col="puma")

    # Load tract_puma_mapping
    tract_puma_mapping = pd.read_csv(
        os.path.join(data_dir, "tract_puma_mapping.csv"), index_col="tract"
    )

    # Load tract-level data for General Building Stock area for residential, commercial and industral classes
    tract_gbs_area = pd.read_csv(
        os.path.join(data_dir, "tract_gbs_area.csv"), index_col="tract"
    )

    # Load tract-level data for heating and cooling degree day normals
    tract_degday_normals = pd.read_csv(
        os.path.join(data_dir, "tract_degday_normals.csv"), index_col="tract"
    )

    # Load tract-level data for population
    tract_pop = pd.read_csv(os.path.join(data_dir, "tract_pop.csv"), index_col="tract")

    puma_data_unscaled = aggregate_puma_df(
        puma_fuel["state"],
        tract_puma_mapping,
        tract_gbs_area,
        tract_degday_normals,
        tract_pop,
    )

    puma_data = scale_fuel_fractions(puma_fuel, puma_data_unscaled)

    # Add time zone information
    puma_timezones = pd.read_csv(
        os.path.join(data_dir, "puma_timezone.csv"), index_col="puma"
    )
    puma_data["timezone"] = puma_timezones["timezone"]

    # Add latitude and longitude information
    puma_lat_long = pd.read_csv(
        os.path.join(data_dir, "puma_lat_long.csv"), index_col="puma"
    )
    puma_data["latitude"], puma_data["longitude"] = (
        puma_lat_long["latitude"],
        puma_lat_long["longitude"],
    )

    # Add residential AC penetration
    acpen_b = 0.00117796
    acpen_n = 1.1243
    puma_data["AC_penetration"] = 1 - np.exp(
        -acpen_b * puma_data["cdd65_normals"] ** acpen_n
    )

    puma_data.to_csv(os.path.join(data_dir, "puma_data.csv"))

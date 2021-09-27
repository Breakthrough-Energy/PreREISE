# This script develops puma-level data directly from census and aggregated from census tract data
import os

import geopandas as gpd
import pandas as pd

from prereise.gather.demanddata.bldg_electrification import const


def aggregate_puma_df(
    puma_fuel_2010, tract_puma_mapping, tract_gbs_area, tract_degday_normals, tract_pop
):
    """Scale census tract data up to puma areas.

    :param pandas.DataFrame puma_fuel_2010: household fuel type by puma.
    :param pandas.DataFrame tract_puma_mapping: tract to puma mapping.
    :param pandas.DataFrame tract_gbs_area: General Building Stock area for residential, commercial, industrial areas by tract
    :param pandas.DataFrame tract_degday_normals: heating and cooling degree day normals by tract
    :param pandas.DataFrame tract_pop: population by tract
    :return: (*pandas.DataFrame*) -- population; residential, commercial, industrial areas;
        heating degree days; cooling degree days; residential space heating household fuel
        fractions.
    """
    # Set up puma_df data frame
    puma_df = puma_fuel_2010["state"].to_frame()

    # Combine tract-level data into single data frame with only census tracts with building area data
    tract_data = pd.concat(
        [tract_gbs_area, tract_degday_normals, tract_pop], axis=1, join="inner"
    )
    tract_data = tract_data.loc[:, ~tract_data.columns.duplicated()]

    # Group tracts by PUMA for aggregration
    grouped_tracts = tract_data.groupby(tract_puma_mapping["puma"])
    # Sum population and GBS areas; store in data frame
    puma_df.loc[grouped_tracts.groups.keys(), "pop_2010"] = grouped_tracts[
        "pop_2010"
    ].sum()
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
    tract_data["pop_hdd65_normals_2010"] = (
        tract_data["pop_2010"] * tract_data["hdd65_normals_2010"]
    )
    tract_data["pop_cdd65_normals_2010"] = (
        tract_data["pop_2010"] * tract_data["cdd65_normals_2010"]
    )
    puma_df.loc[grouped_tracts.groups.keys(), "hdd65_normals_2010"] = (
        grouped_tracts["pop_hdd65_normals_2010"].sum()
        / grouped_tracts["pop_2010"].sum()
    )
    puma_df.loc[grouped_tracts.groups.keys(), "cdd65_normals_2010"] = (
        grouped_tracts["pop_cdd65_normals_2010"].sum()
        / grouped_tracts["pop_2010"].sum()
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

    # Interpolate a 2010 area to scale model area to corresponding RECS/CBECS area
    resscales["2010_scalar"] = (
        resscales["RECS2009"]
        + (resscales["RECS2015"] - resscales["RECS2009"])
        * (
            (const.target_year - const.recs_date_1)
            / (const.recs_date_2 - const.recs_date_1)
        )
    ) / resscales["GBS"]
    comscales["2010_scalar"] = (
        comscales["CBECS2003"]
        + (comscales["CBECS2012"] - comscales["CBECS2003"])
        * (
            (const.target_year - const.cbecs_date_1)
            / (const.cbecs_date_2 - const.cbecs_date_1)
        )
    ) / comscales["GBS"]

    # Scale puma area from gbs to 2010 RECS/CBECS
    for state in const.state_list:
        state_row_scale_res = resscales[resscales.eq(state).any(1)].reset_index()
        state_row_scale_com = comscales[comscales.eq(state).any(1)].reset_index()
        res_scalar = state_row_scale_res["2010_scalar"][0]
        com_scalar = state_row_scale_com["2010_scalar"][0]
        puma_df.loc[puma_df["state"] == state, "res_area_2010_m2"] = (
            puma_df[puma_df["state"] == state]["res_area_gbs_m2"] * res_scalar
        )
        puma_df.loc[puma_df["state"] == state, "com_area_2010_m2"] = (
            puma_df[puma_df["state"] == state]["com_area_gbs_m2"] * com_scalar
        )

    # Calculate res fractions of fuel usage based off puma_fuel_2010 household data
    puma_df["frac_sh_res_natgas"] = (
        puma_fuel_2010["hh_utilgas"] / puma_fuel_2010["hh_total"]
    )
    puma_df["frac_sh_res_fok"] = puma_fuel_2010["hh_fok"] / puma_fuel_2010["hh_total"]
    puma_df["frac_sh_res_othergas"] = (
        puma_fuel_2010["hh_othergas"] / puma_fuel_2010["hh_total"]
    )
    puma_df["frac_sh_res_coal"] = puma_fuel_2010["hh_coal"] / puma_fuel_2010["hh_total"]
    puma_df["frac_sh_res_wood"] = puma_fuel_2010["hh_wood"] / puma_fuel_2010["hh_total"]
    puma_df["frac_sh_res_solar"] = (
        puma_fuel_2010["hh_solar"] / puma_fuel_2010["hh_total"]
    )
    puma_df["frac_sh_res_elec"] = puma_fuel_2010["hh_elec"] / puma_fuel_2010["hh_total"]
    puma_df["frac_sh_res_other"] = (
        puma_fuel_2010["hh_other"] / puma_fuel_2010["hh_total"]
    )
    puma_df["frac_sh_res_none"] = puma_fuel_2010["hh_none"] / puma_fuel_2010["hh_total"]

    return puma_df


def scale_fuel_fractions(puma_df, regions, fuel, year=2010):
    """Scale census tract data up to puma areas.

    :param pandas.DataFrame puma_df: output of :func:`aggregate_puma_df`.
    :param list of lists regions: state regions used to scale fuel fractions.
    :param list fuel: types of fuel.
    :param int/str year: year to use within label when creating columns.
    :return: (*pandas.DataFrame*) -- fractions of natural gas, fuel oil and kerosone,
        propane, and electricity used for space heating, hot water, cooking, and other
        in residential and commercial buildings.
    """
    region_map = {state: r for r, states in regions.items() for state in states}
    puma_region_groups = puma_df.groupby(puma_df["state"].map(region_map))
    for c in const.classes:
        # Compute area fraction for each fuel type (column) in each region (index)
        fuel_area_fractions = puma_region_groups.apply(
            lambda x: pd.Series(
                {
                    f: (
                        (x[f"frac_sh_res_{f}"] * x[f"{c}_area_2010_m2"]).sum()
                        / x[f"{c}_area_2010_m2"].sum()
                    )
                    for f in fuel
                }
            )
        )
        uselist = ["dhw", "other"] if c == "res" else ["sh", "dhw", "cook"]
        for u in uselist:

            # Values calculated externally
            frac_scale = pd.read_csv(os.path.join(data_dir, f"frac_target_{u}_{c}.csv"))

            downscalar = frac_scale / fuel_area_fractions

            upscalar = (frac_scale - fuel_area_fractions) / (1 - fuel_area_fractions)

            # Scale frac_hh_fuel to frac_com_fuel
            for f in fuel:
                scalar = 1
                fraccom = []
                for i in range(len(puma_df)):
                    for j in range(len(regions)):
                        if puma_df["state"][i] in regions[j]:
                            region_index = j
                    if downscalar[f][region_index] <= 1:
                        scalar = downscalar[f][region_index]
                        fraccom.append(puma_df[f"frac_sh_res_{f}"][i] * scalar)
                    else:
                        scalar = upscalar[f][region_index]
                        fraccom.append(
                            (1 - puma_df[f"frac_sh_res_{f}"][i]) * scalar
                            + puma_df[f"frac_sh_res_{f}"][i]
                        )
                puma_df[f"frac_{f}_{u}_{c}_{year}"] = fraccom

    # Sum coal, wood, solar and other fractions for frac_com_other
    named_sh_com_fuels = {"elec", "fok", "natgas", "othergas"}
    named_sh_com_cols = [f"frac_{f}_sh_com_{year}" for f in named_sh_com_fuels]
    puma_df[f"frac_other_sh_com_{year}"] = 1 - puma_df[named_sh_com_cols].sum(axis=1)

    # Copy residential space heating columns to match new column naming convention
    puma_df = puma_df.assign(
        **{f"frac_{f}_sh_res_{year}": puma_df[f"frac_sh_res_{f}"] for f in fuel}
    )
    fossil_fuels = {"natgas", "othergas", "fok"}
    for c in const.classes:
        uselist = ["sh", "dhw", "other"] if c == "res" else ["sh", "dhw", "cook"]
        for u in uselist:
            fossil_cols = [f"frac_{f}_{u}_{c}_{year}" for f in fossil_fuels]
            puma_df[f"frac_ff_{u}_{c}_{year}"] = puma_df[fossil_cols].sum(axis=1)
    return puma_df


def puma_timezone_join(timezones, pumas):
    """Assign timezone to each puma.

    :param geopandas.DataFrame timezones: US timezones.
    :param geopandas.DataFrame pumas: US pumas.
    :return: (*pandas.Series*) -- timezone for every puma.
    """
    puma_timezone = gpd.overlay(pumas, timezones.to_crs("EPSG:4269"))
    puma_timezone["area"] = puma_timezone.area
    puma_timezone.sort_values("area", ascending=False, inplace=True)
    puma_timezone = puma_timezone.drop_duplicates(subset="GEOID10", keep="first")
    puma_timezone.sort_values("GEOID10", ascending=True, inplace=True)

    return puma_timezone["tzid"]


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    # Load ACS fuel data for 2010
    puma_fuel_2010 = pd.read_csv(
        os.path.join(data_dir, "puma_fuel_2010.csv"), index_col="puma"
    )

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
        puma_fuel_2010,
        tract_puma_mapping,
        tract_gbs_area,
        tract_degday_normals,
        tract_pop,
    )

    puma_data = scale_fuel_fractions(puma_data_unscaled, const.regions, const.fuel)

    # Add time zone information
    puma_timezones = pd.read_csv(
        os.path.join(data_dir, "puma_timezone.csv"), index_col="puma"
    )
    puma_data["timezone"] = puma_timezones["timezone"]

    puma_data.to_csv(os.path.join(data_dir, "puma_data.csv"))

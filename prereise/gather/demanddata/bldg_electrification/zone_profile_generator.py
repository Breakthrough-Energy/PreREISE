import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar  # noqa: N813
from scipy.stats import linregress
from sklearn.linear_model import LinearRegression

from prereise.gather.demanddata.bldg_electrification import const


def bkpt_scale(df, num_points, bkpt, heat_cool):
    """Adjust heating or cooling breakpoint to ensure there are enough data points to fit.

    :param pandas.DataFrame df: load and temperature for a certain hour of the day, wk or wknd.
    :param int num_points: minimum number of points required in df to fit.
    :param float bkpt: starting temperature breakpoint value.
    :param str heat_cool: dictates if breakpoint is shifted warmer for heating or colder for cooling

    :return: (*pandas.DataFrame*) dft -- adjusted dataframe filtered by new breakpoint. Original input df if size of initial df >= num_points
    :return: (*float*) bkpt -- updated breakpoint. Original breakpoint if size of initial df >= num_points
    """

    dft = (
        df[df["temp_c"] <= bkpt].reset_index()
        if heat_cool == "heat"
        else df[df["temp_c"] >= bkpt].reset_index()
    )
    if len(dft) < num_points:
        dft = (
            df.sort_values(by=["temp_c"]).head(num_points).reset_index()
            if heat_cool == "heat"
            else df.sort_values(by=["temp_c"]).tail(num_points).reset_index()
        )
        bkpt = (
            dft["temp_c"][num_points - 1] if heat_cool == "heat" else dft["temp_c"][0]
        )

    return dft.sort_index(), bkpt


def zone_shp_overlay(zone_name_shp):
    """Select pumas within a zonal load area

    :param str zone_name_shp: name of zone in BA_map.shp

    :return: (*pandas.DataFrame*) puma_data_zone -- puma data of all pumas within zone, including fraction within zone
    """

    shapefile = gpd.GeoDataFrame(
        gpd.read_file(
            os.path.join(os.path.dirname(__file__), "shapefiles", "BA_map.shp")
        )
    )
    zone_shp = shapefile[shapefile["BA"] == zone_name_shp]
    pumas_shp = gpd.GeoDataFrame(
        gpd.read_file(
            os.path.join(os.path.dirname(__file__), "shapefiles", "pumas_overlay.shp")
        )
    )

    puma_zone = gpd.overlay(pumas_shp, zone_shp.to_crs("EPSG:4269"))
    puma_zone["area"] = puma_zone["geometry"].to_crs({"proj": "cea"}).area
    puma_zone["puma"] = "puma_" + puma_zone["GEOID10"]

    puma_zone["area_frac"] = [
        puma_zone["area"][i]
        / list(pumas_shp[pumas_shp["puma"] == puma_zone["puma"][i]]["area"])[0]
        for i in range(len(puma_zone))
    ]

    puma_data_zone = pd.DataFrame(
        {"puma": puma_zone["puma"], "frac_in_zone": puma_zone["area_frac"]}
    )

    puma_data = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "data", "puma_data.csv"),
        index_col="puma",
    )
    puma_data_zone = puma_data_zone.join(puma_data, on="puma")
    puma_data_zone = puma_data_zone.set_index("puma")

    return puma_data_zone


def zonal_data(puma_data, hours_utc):
    """Aggregate puma metrics to population weighted hourly zonal values

    :param pandas.DataFrame puma_data: puma data within zone, output of zone_shp_overlay()
    :param pandas.DatetimeIndex hours_utc: index of UTC hours.

    :return: (*pandas.DataFrame*) temp_df -- hourly zonal values of temperature, wetbulb temperature, and darkness fraction
    """
    puma_pop_weights = (puma_data["pop"] * puma_data["frac_in_zone"]) / sum(
        puma_data["pop"] * puma_data["frac_in_zone"]
    )
    zone_states = list(set(puma_data["state"]))
    timezone = max(
        set(list(puma_data["timezone"])), key=list(puma_data["timezone"]).count
    )

    base_year = const.base_year

    stats = pd.Series(
        data=[
            sum(puma_data["pop"]),
            sum(puma_data[f"res_area_{base_year}_m2"]),
            sum(puma_data[f"com_area_{base_year}_m2"]),
            sum(puma_data["ind_area_gbs_m2"]),
            sum(
                puma_data[f"res_area_{base_year}_m2"]
                * puma_data[f"frac_elec_sh_res_{base_year}"]
            )
            / sum(puma_data[f"res_area_{base_year}_m2"]),
            sum(puma_data[f"res_area_{base_year}_m2"] * puma_data["AC_penetration"])
            / sum(puma_data[f"res_area_{base_year}_m2"]),
            sum(
                puma_data[f"com_area_{base_year}_m2"]
                * puma_data[f"frac_elec_sh_com_{base_year}"]
            )
            / sum(puma_data[f"com_area_{base_year}_m2"]),
            sum(
                puma_data[f"res_area_{base_year}_m2"]
                * puma_data[f"frac_elec_dhw_res_{base_year}"]
            )
            / sum(puma_data[f"res_area_{base_year}_m2"]),
            sum(
                puma_data[f"com_area_{base_year}_m2"]
                * puma_data[f"frac_elec_dhw_com_{base_year}"]
            )
            / sum(puma_data[f"com_area_{base_year}_m2"]),
            sum(
                puma_data[f"res_area_{base_year}_m2"]
                * puma_data[f"frac_elec_other_res_{base_year}"]
            )
            / sum(puma_data[f"res_area_{base_year}_m2"]),
            sum(
                puma_data[f"com_area_{base_year}_m2"]
                * puma_data[f"frac_elec_cook_com_{base_year}"]
            )
            / sum(puma_data[f"com_area_{base_year}_m2"]),
            sum(puma_data["hdd65_normals"] * puma_data["pop"] / sum(puma_data["pop"])),
            sum(puma_data["cdd65_normals"] * puma_data["pop"] / sum(puma_data["pop"])),
        ],
        index=[
            "pop",
            "res_area_m2",
            "com_area_m2",
            "ind_area_m2_gbs",
            "frac_elec_res_heat",
            "frac_elec_res_cool",
            "frac_elec_com_heat",
            "frac_elec_dhw_res",
            "frac_elec_dhw_com",
            "frac_elec_other_res",
            "frac_elec_cook_com",
            "hdd65",
            "cdd65",
        ],
    )

    puma_hourly_temps = pd.concat(
        list(
            pd.Series(data=zone_states).apply(
                lambda x: pd.read_csv(
                    f"https://besciences.blob.core.windows.net/datasets/bldg_el/pumas/temps/temps_pumas_{x}_{year}.csv"
                ).T
            )
        )
    )
    puma_hourly_temps_wb = pd.concat(
        list(
            pd.Series(data=zone_states).apply(
                lambda x: pd.read_csv(
                    f"https://besciences.blob.core.windows.net/datasets/bldg_el/pumas/temps_wetbulb/temps_wetbulb_pumas_{x}_{year}.csv"
                ).T
            )
        )
    )
    puma_hourly_dark_frac = pd.concat(
        list(
            pd.Series(data=zone_states).apply(
                lambda x: pd.read_csv(
                    f"https://besciences.blob.core.windows.net/datasets/bldg_el/pumas/dark_frac/dark_frac_pumas_{x}_{year}.csv"
                ).T
            )
        )
    )

    hours_local = hours_utc.tz_convert(timezone)
    is_holiday = pd.Series(hours_local).dt.date.isin(
        list(
            pd.Series(
                calendar().holidays(start=hours_local.min(), end=hours_local.max())
            ).dt.date
        )
    )

    temp_df = pd.DataFrame(
        {
            "temp_c": puma_hourly_temps[puma_hourly_temps.index.isin(puma_data.index)]
            .mul(puma_pop_weights, axis=0)
            .sum(axis=0),
            "temp_c_wb": puma_hourly_temps_wb[
                puma_hourly_temps_wb.index.isin(puma_data.index)
            ]
            .mul(puma_pop_weights, axis=0)
            .sum(axis=0),
            "date_local": hours_local,
            "hour_local": hours_local.hour,
            "weekday": hours_local.weekday,
            "holiday": is_holiday,
            "hourly_dark_frac": puma_hourly_dark_frac[
                puma_hourly_dark_frac.index.isin(puma_data.index)
            ]
            .mul(puma_pop_weights, axis=0)
            .sum(axis=0),
        }
    )

    return temp_df, stats


def hourly_load_fit(load_temp_df, plot_boolean):
    """Fit hourly heating, cooling, and baseload functions to load data

    :param pandas.DataFrame load_temp_df: hourly load and temperature data
    :param boolean plot_boolean: whether or not create profile plots.

    :return: (*pandas.DataFrame*) hourly_fits_df -- hourly and week/weekend breakpoints and coefficients for electricity use equations
    :return: (*float*) s_wb_db, i_wb_db -- slope and intercept of fit between dry and wet bulb temperatures of zone
    """

    def make_hourly_series(load_temp_df, i):
        daily_points = 10
        result = {}
        for wk_wknd in ["wk", "wknd"]:
            if wk_wknd == "wk":
                load_temp_hr = load_temp_df[
                    (load_temp_df["hour_local"] == i)
                    & (load_temp_df["weekday"] < 5)
                    & ~load_temp_df["holiday"]  # boolean column
                ].reset_index()
                numpoints = daily_points * 5
            elif wk_wknd == "wknd":
                load_temp_hr = load_temp_df[
                    (load_temp_df["hour_local"] == i)
                    & (
                        (load_temp_df["weekday"] >= 5)
                        | load_temp_df["holiday"]  # boolean column
                    )
                ].reset_index()
                numpoints = daily_points * 2

            load_temp_hr_heat, t_bpc = bkpt_scale(
                load_temp_hr, numpoints, t_bpc_start, "heat"
            )

            load_temp_hr_cool, t_bph = bkpt_scale(
                load_temp_hr, numpoints, t_bph_start, "cool"
            )

            lm_heat = LinearRegression().fit(
                np.array(
                    [
                        [
                            load_temp_hr_heat["temp_c"][j],
                            load_temp_hr_heat["hourly_dark_frac"][j],
                        ]
                        for j in range(len(load_temp_hr_heat))
                    ]
                ),
                load_temp_hr_heat["load_mw"],
            )
            s_heat, s_dark, i_heat = (
                lm_heat.coef_[0],
                lm_heat.coef_[1],
                lm_heat.intercept_,
            )

            s_heat_only, i_heat_only, r_heat, pval_heat, stderr_heat = linregress(
                load_temp_hr_heat["temp_c"], load_temp_hr_heat["load_mw"]
            )

            lm_dark = LinearRegression().fit(
                np.expand_dims(load_temp_hr_heat["hourly_dark_frac"], 1),
                load_temp_hr_heat["load_mw"],
            )

            s_dark_only, i_heat_dark_only = (
                lm_dark.coef_[0],
                lm_dark.intercept_,
            )

            if s_heat > 0:
                s_heat, s_dark, i_heat = 0, s_dark_only, i_heat_dark_only

            if (
                s_dark < 0
                or (
                    max(load_temp_hr_heat["hourly_dark_frac"])
                    - min(load_temp_hr_heat["hourly_dark_frac"])
                )
                < 0.3
            ):
                s_dark, s_heat, i_heat = 0, s_heat_only, i_heat_only

                if s_heat > 0:
                    s_dark, s_heat, i_heat = 0, 0, np.mean(load_temp_hr_heat["load_mw"])

            load_temp_hr_cool["cool_load_mw"] = [
                load_temp_hr_cool["load_mw"][j]
                - (s_heat * t_bph + i_heat)
                - s_dark * load_temp_hr_cool["hourly_dark_frac"][j]
                for j in range(len(load_temp_hr_cool))
            ]

            load_temp_hr_cool["temp_c_wb_diff"] = load_temp_hr_cool["temp_c_wb"] - (
                db_wb_fit[0] * load_temp_hr_cool["temp_c"] ** 2
                + db_wb_fit[1] * load_temp_hr_cool["temp_c"]
                + db_wb_fit[2]
            )

            lm_cool = LinearRegression().fit(
                np.array(
                    [
                        [
                            load_temp_hr_cool["temp_c"][i],
                            load_temp_hr_cool["temp_c_wb_diff"][i],
                        ]
                        for i in range(len(load_temp_hr_cool))
                    ]
                ),
                load_temp_hr_cool["cool_load_mw"],
            )
            s_cool_db, s_cool_wb, i_cool = (
                lm_cool.coef_[0],
                lm_cool.coef_[1],
                lm_cool.intercept_,
            )

            t_bph = -i_cool / s_cool_db if -i_cool / s_cool_db > t_bph else t_bph

            #
            if wk_wknd == "wk":
                wk_graph = load_temp_df[
                    (load_temp_df["hour_local"] == i)
                    & (load_temp_df["weekday"] < 5)
                    & ~load_temp_df["holiday"]  # boolean column
                ]
            else:
                wk_graph = load_temp_df[
                    (load_temp_df["hour_local"] == i)
                    & (
                        (load_temp_df["weekday"] >= 5)
                        | load_temp_df["holiday"]  # boolean column
                    )
                ]

            load_temp_hr_cool_func = wk_graph[
                (wk_graph["temp_c"] < t_bph) & (wk_graph["temp_c"] > t_bpc)
            ].reset_index()

            heat_eqn = (
                load_temp_hr_heat["temp_c"] * s_heat
                + load_temp_hr_heat["hourly_dark_frac"] * s_dark
                + i_heat
            )
            cool_eqn = [
                max(
                    load_temp_hr_cool["temp_c"][i] * s_cool_db
                    + (
                        load_temp_hr_cool["temp_c_wb"][i]
                        - (
                            db_wb_fit[0] * load_temp_hr_cool["temp_c"][i] ** 2
                            + db_wb_fit[1] * load_temp_hr_cool["temp_c"][i]
                            + db_wb_fit[2]
                        )
                    )
                    * s_cool_wb
                    + i_cool,
                    0,
                )
                + t_bph * s_heat
                + load_temp_hr_cool["hourly_dark_frac"][i] * s_dark
                + i_heat
                for i in range(len(load_temp_hr_cool))
            ]
            cool_func_eqn = [
                max(
                    ((load_temp_hr_cool_func["temp_c"][i] - t_bpc) / (t_bph - t_bpc))
                    ** 2
                    * (
                        t_bph * s_cool_db
                        + (
                            load_temp_hr_cool_func["temp_c_wb"][i]
                            - (
                                db_wb_fit[0] * load_temp_hr_cool_func["temp_c"][i] ** 2
                                + db_wb_fit[1] * load_temp_hr_cool_func["temp_c"][i]
                                + db_wb_fit[2]
                            )
                        )
                        * s_cool_wb
                        + i_cool
                    ),
                    0,
                )
                + load_temp_hr_cool_func["temp_c"][i] * s_heat
                + load_temp_hr_cool_func["hourly_dark_frac"][i] * s_dark
                + i_heat
                for i in range(len(load_temp_hr_cool_func))
            ]

            # Generate hourly fit plot
            if plot_boolean:
                plt.rcParams.update({"font.size": 20})
                fig, ax = plt.subplots(figsize=(20, 10))

                plt.scatter(wk_graph["temp_c"], wk_graph["load_mw"], color="black")

                plt.scatter(load_temp_hr_heat["temp_c"], heat_eqn, color="red")
                plt.scatter(load_temp_hr_cool["temp_c"], cool_eqn, color="blue")
                plt.scatter(
                    load_temp_hr_cool_func["temp_c"], cool_func_eqn, color="green"
                )

                plt.title(
                    f"zone {zone_name}, hour {i}, {wk_wknd} \n t_bpc = "
                    + str(round(t_bpc, 2))
                    + "  t_bph = "
                    + str(round(t_bph, 2))
                )
                plt.xlabel("Temp (°C)")
                plt.ylabel("Load (MW)")
                os.makedirs(
                    os.path.join(
                        os.path.dirname(__file__), "dayhour_fits", "dayhour_fits_graphs"
                    ),
                    exist_ok=True,
                )
                plt.savefig(
                    os.path.join(
                        os.path.dirname(__file__),
                        "dayhour_fits",
                        "dayhour_fits_graphs",
                        f"{zone_name}_hour_{i}_{wk_wknd}_{base_year}.png",
                    )
                )

            mrae_heat = np.mean(
                [
                    np.abs(heat_eqn[i] - load_temp_hr_heat["load_mw"][i])
                    for i in range(len(load_temp_hr_heat))
                ]
            )
            mrae_cool = np.mean(
                [
                    np.abs(cool_eqn[i] - load_temp_hr_cool["load_mw"][i])
                    for i in range(len(load_temp_hr_cool))
                ]
            )
            mrae_cool_func = np.mean(
                [
                    np.abs(cool_func_eqn[i] - load_temp_hr_cool_func["load_mw"][i])
                    for i in range(len(load_temp_hr_cool_func))
                ]
            )

            result[wk_wknd] = {
                f"t.bpc.{wk_wknd}.c": t_bpc,
                f"t.bph.{wk_wknd}.c": t_bph,
                f"i.heat.{wk_wknd}": i_heat,
                f"s.heat.{wk_wknd}": s_heat,
                f"s.dark.{wk_wknd}": s_dark,
                f"i.cool.{wk_wknd}": i_cool,
                f"s.cool.{wk_wknd}.db": s_cool_db,
                f"s.cool.{wk_wknd}.wb": s_cool_wb,
                f"mrae.heat.{wk_wknd}.mw": mrae_heat,
                f"mrae.cool.{wk_wknd}.mw": mrae_cool,
                f"mrae.mid.{wk_wknd}.mw": mrae_cool_func,
            }

        return pd.Series({**result["wk"], **result["wknd"]})

    t_bpc_start = 10
    t_bph_start = 18.3

    db_wb_regr_df = load_temp_df[load_temp_df["temp_c"] >= t_bpc_start]

    db_wb_fit = np.polyfit(db_wb_regr_df["temp_c"], db_wb_regr_df["temp_c_wb"], 2)

    hourly_fits_df = pd.DataFrame(
        [make_hourly_series(load_temp_df, i) for i in range(24)]
    )

    return hourly_fits_df, db_wb_fit


def temp_to_energy(temp_series, hourly_fits_df, db_wb_fit):
    """Compute baseload, heating, and cooling electricity for a certain hour of year

    :param pandas.Series load_temp_series: data for the given hour.
    :param pandas.DataFrame hourly_fits_df: hourly and week/weekend breakpoints and
        coefficients for electricity use equations.
    :param float s_wb_db: slope of fit between dry and wet bulb temperatures of zone.
    :param float i_wb_db: intercept of fit between dry and wet bulb temperatures of zone.

    :return: (*list*) -- [baseload, heating, cooling]
    """
    temp = temp_series["temp_c"]
    temp_wb = temp_series["temp_c_wb"]
    dark_frac = temp_series["hourly_dark_frac"]
    zone_hour = temp_series["hour_local"]

    heat_eng = 0
    mid_cool_eng = 0
    cool_eng = 0

    wk_wknd = (
        "wk"
        if temp_series["weekday"] < 5 and ~temp_series["holiday"]  # boolean value
        else "wknd"
    )

    (t_bpc, t_bph, i_heat, s_heat, s_dark, i_cool, s_cool_db, s_cool_wb,) = (
        hourly_fits_df.at[zone_hour, f"t.bpc.{wk_wknd}.c"],
        hourly_fits_df.at[zone_hour, f"t.bph.{wk_wknd}.c"],
        hourly_fits_df.at[zone_hour, f"i.heat.{wk_wknd}"],
        hourly_fits_df.at[zone_hour, f"s.heat.{wk_wknd}"],
        hourly_fits_df.at[zone_hour, f"s.dark.{wk_wknd}"],
        hourly_fits_df.at[zone_hour, f"i.cool.{wk_wknd}"],
        hourly_fits_df.at[zone_hour, f"s.cool.{wk_wknd}.db"],
        hourly_fits_df.at[zone_hour, f"s.cool.{wk_wknd}.wb"],
    )

    base_eng = s_heat * t_bph + s_dark * dark_frac + i_heat

    if temp <= t_bph:
        heat_eng = -s_heat * (t_bph - temp)

    if temp >= t_bph:
        cool_eng = (
            s_cool_db * temp
            + s_cool_wb
            * (
                temp_wb
                - (db_wb_fit[0] * temp**2 + db_wb_fit[1] * temp + db_wb_fit[2])
            )
            + i_cool
        )

    if temp > t_bpc and temp < t_bph:

        mid_cool_eng = ((temp - t_bpc) / (t_bph - t_bpc)) ** 2 * (
            s_cool_db * t_bph
            + s_cool_wb
            * (
                temp_wb
                - (db_wb_fit[0] * temp**2 + db_wb_fit[1] * temp + db_wb_fit[2])
            )
            + i_cool
        )

    return [base_eng, heat_eng, max(cool_eng, 0) + max(mid_cool_eng, 0)]


def plot_profile(profile, actual, plot_boolean):
    """Plot profile vs. actual load

    :param pandas.Series profile: total profile hourly load
    :param pandas.Series actual: zonal hourly load data
    :param boolean plot_boolean: whether or not create profile plots.

    :return: (*plot*)
    """

    mrae = [np.abs(profile[i] - actual[i]) / actual[i] for i in range(len(profile))]

    rss = np.sqrt(
        np.mean([(actual[i] - profile[i]) ** 2 for i in range(len(profile))])
    ) / np.mean(actual)

    mrae_avg, mrae_max = np.mean(mrae), max(mrae)

    if plot_boolean:
        fig, ax = plt.subplots(figsize=(20, 10))
        plt.plot(list(profile.index), profile - actual)
        plt.legend(["Profile - Actual"])
        plt.xlabel("Hour")
        plt.ylabel("MW Difference")
        plt.title(
            "Zone "
            + zone_name
            + " Load Comparison \n"
            + "avg mrae = "
            + str(round(mrae_avg * 100, 2))
            + "% \n avg profile load = "
            + str(round(np.mean(profile), 2))
            + " MW"
        )
        os.makedirs(
            os.path.join(os.path.dirname(__file__), "Profiles", "Profiles_graphs"),
            exist_ok=True,
        )
        plt.savefig(
            os.path.join(
                os.path.dirname(__file__),
                "Profiles",
                "Profiles_graphs",
                f"{zone_name}_profile_{year}.png",
            )
        )

    return (
        mrae_avg,
        mrae_max,
        rss,
        np.mean(profile),
        np.mean(actual),
        max(profile),
        max(actual),
    )


def main(zone_name, zone_name_shp, base_year, year, plot_boolean=False):
    """Run profile generator for one zone for one year.

    :param str zone_name: name of load zone used to save profile.
    :param str zone_name_shp: name of load zone within shapefile.
    :param int base_year: data fitting year.
    :param int year: profile year to calculate.
    :param boolean plot_boolean: whether or not create profile plots.
    """
    zone_load = pd.read_csv(
        f"https://besciences.blob.core.windows.net/datasets/bldg_el/zone_loads_{year}/{zone_name}_demand_{year}_UTC.csv"
    )["demand.mw"]
    hours_utc_base_year = pd.date_range(
        start=f"{base_year}-01-01", end=f"{base_year+1}-01-01", freq="H", tz="UTC"
    )[:-1]

    hours_utc = pd.date_range(
        start=f"{year}-01-01", end=f"{year+1}-01-01", freq="H", tz="UTC"
    )[:-1]

    puma_data_zone = zone_shp_overlay(zone_name_shp)

    temp_df_base_year, stats_base_year = zonal_data(puma_data_zone, hours_utc_base_year)

    temp_df_base_year["load_mw"] = zone_load

    hourly_fits_df, db_wb_fit = hourly_load_fit(temp_df_base_year, plot_boolean)
    os.makedirs(os.path.join(os.path.dirname(__file__), "dayhour_fits"), exist_ok=True)
    hourly_fits_df.to_csv(
        os.path.join(
            os.path.dirname(__file__),
            "dayhour_fits",
            f"{zone_name}_dayhour_fits_{base_year}.csv",
        )
    )

    zone_profile_load_MWh = pd.DataFrame(  # noqa: N806
        {"hour_utc": list(range(len(hours_utc)))}
    )

    temp_df, stats = zonal_data(puma_data_zone, hours_utc)

    energy_list = zone_profile_load_MWh.hour_utc.apply(
        lambda x: temp_to_energy(temp_df.loc[x], hourly_fits_df, db_wb_fit)
    )
    (
        zone_profile_load_MWh["base_load_mw"],
        zone_profile_load_MWh["heat_load_mw"],
        zone_profile_load_MWh["cool_load_mw"],
        zone_profile_load_MWh["total_load_mw"],
    ) = (
        energy_list.apply(lambda x: x[0]),
        energy_list.apply(lambda x: x[1]),
        energy_list.apply(lambda x: x[2]),
        energy_list.apply(lambda x: sum(x)),
    )
    zone_profile_load_MWh.set_index("hour_utc", inplace=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "Profiles"), exist_ok=True)
    zone_profile_load_MWh.to_csv(
        os.path.join(
            os.path.dirname(__file__),
            "Profiles",
            f"{zone_name}_profile_load_mw_{year}.csv",
        )
    )

    (
        stats["mrae_avg_%"],
        stats["mrae_max_%"],
        stats["rss_avg_%"],
        stats["avg_profile_load_mw"],
        stats["avg_actual_load_mw"],
        stats["max_profile_load_mw"],
        stats["max_actual_load_mw"],
    ) = plot_profile(zone_profile_load_MWh["total_load_mw"], zone_load, plot_boolean)

    os.makedirs(
        os.path.join(os.path.dirname(__file__), "Profiles", "Profiles_stats"),
        exist_ok=True,
    )
    stats.to_csv(
        os.path.join(
            os.path.dirname(__file__),
            "Profiles",
            "Profiles_stats",
            f"{zone_name}_stats_{year}.csv",
        )
    )


if __name__ == "__main__":
    # Use base_year for model fitting
    base_year = const.base_year

    # Weather year to produce load profiles
    year = 2019

    # If produce profile plots
    plot_boolean = False

    zone_names = [
        "NYIS-ZONA",
        "NYIS-ZONB",
        "NYIS-ZONC",
        "NYIS-ZOND",
        "NYIS-ZONE",
        "NYIS-ZONF",
        "NYIS-ZONG",
        "NYIS-ZONH",
        "NYIS-ZONI",
        "NYIS-ZONJ",
        "NYIS-ZONK",
        "ERCO-C",
        "ERCO-E",
        "ERCO-FW",
        "ERCO-N",
        "ERCO-NC",
        "ERCO-S",
        "ERCO-SC",
        "ERCO-W",
        "CISO-PGAE",
        "CISO-SCE",
        "CISO-SDGE",
        "CISO-VEA",
        "IID",
        "WALC",
        "LDWP",
        "TIDC",
        "BANC",
    ]

    zone_name_shps = [
        "West",
        "Genesee",
        "Central",
        "North",
        "Mohawk Valley",
        "Capital",
        "Hudson Valley",
        "Millwood",
        "Dunwoodie",
        "N.Y.C.",
        "Long Island",
        "ERCO-C",
        "ERCO-E",
        "ERCO-FW",
        "ERCO-N",
        "ERCO-NC",
        "ERCO-S",
        "ERCO-SC",
        "ERCO-W",
        "CISO-PGAE",
        "CISO-SCE",
        "CISO-SDGE",
        "CISO-VEA",
        "IID",
        "WALC",
        "LADWP",
        "TID",
        "BANC",
    ]

    for i in range(len(zone_names)):
        zone_name, zone_name_shp = zone_names[i], zone_name_shps[i]
        main(zone_name, zone_name_shp, base_year, year, plot_boolean)

import os
from itertools import product

import numpy as np
import pandas as pd

from prereise.gather.demanddata.bldg_electrification import const
from prereise.gather.demanddata.bldg_electrification.ff2elec_profile_generator_cook import (
    generate_cook_profiles,
)
from prereise.gather.demanddata.bldg_electrification.ff2elec_profile_generator_dhw import (
    generate_dhw_profiles,
)
from prereise.gather.demanddata.bldg_electrification.ff2elec_profile_generator_htg import (
    generate_htg_profiles,
)
from prereise.gather.demanddata.bldg_electrification.helper import (
    read_shapefile,
    zone_shp_overlay,
)
from prereise.gather.demanddata.bldg_electrification.load_projection_scenario import (
    LoadProjectionScenario,
)
from prereise.gather.demanddata.bldg_electrification.zone_profile_generator import (
    zonal_data,
)


def temp_to_energy(temp_series, hourly_fits_df, db_wb_fit, base_scen, hp_heat_cop):
    """Compute baseload, heating, and cooling electricity for a certain hour of year
    under model base year scenario

    :param pandas.Series temp_series: data for the given hour.
    :param pandas.DataFrame hourly_fits_df: hourly and week/weekend breakpoints and
        coefficients for electricity use equations.
    :param pandas.DataFrame db_wb_fit: least-square estimators of the linear
        relationship between WBT and DBT
    :param load_projection_scenario.LoadProjectionScenario base_scen: reference
        scenario instance
    :param pandas.DataFrame hp_heat_cop: heat pump COP against DBT with
        a 0.1 degree C interval
    :return: (*list*) -- energy for baseload, heat pump heating, resistance heating,
        and cooling of certain hour
    """
    temp = temp_series["temp_c"]
    temp_wb = temp_series["temp_c_wb"]
    dark_frac = temp_series["hourly_dark_frac"]
    zone_hour = temp_series["hour_local"]

    heat_eng = 0
    mid_cool_eng = 0
    cool_eng = 0
    hp_eng = 0
    resist_eng = 0

    wk_wknd = (
        "wk"
        if temp_series["weekday"] < 5 and ~temp_series["holiday"]  # boolean value
        else "wknd"
    )

    (
        t_bpc,
        t_bph,
        i_heat,
        s_heat,
        s_dark,
        i_cool,
        s_cool_db,
        s_cool_wb,
    ) = (
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
        # Separate resistance heat and heat pump energy by COP.
        # HP assumed to be medium performance HP that's used in Mike's Joule paper
        # ! Since we now have our estimation of current heat pump adoption rate,
        # this function can be merged to the same one in zone_profile_generator.py
        cop_hp = hp_heat_cop.loc[round(temp, 1), "cop"]
        hp_eng = (
            heat_eng
            * (base_scen.hp_heat_frac / cop_hp)
            / (base_scen.resist_heat_frac + base_scen.hp_heat_frac / cop_hp)
        )
        resist_eng = (
            heat_eng
            * (base_scen.resist_heat_frac)
            / (base_scen.resist_heat_frac + base_scen.hp_heat_frac / cop_hp)
        )

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

    return [base_eng, hp_eng, resist_eng, max(cool_eng, 0) + max(mid_cool_eng, 0)]


def scale_energy(
    base_energy, temp_df, base_scen, new_scen, midperfhp_cop, advperfhp_cop
):
    """Project energy consumption for each projection scenarios from the base scenario

    :param pandas.DataFrame base_energy: dataframe of disaggregated
        electricity consumptions for all weather years
    :param pandas.DataFrame temp_df: weather records the given hours
    :param load_projection_scenario.LoadProjectionScenario base_scen:
        reference scenario instance
    :param load_projection_scenario.LoadProjectionScenario new_scen:
        projection scenario instance
    :param Pandas.DataFrame midperfhp_cop: average performance heat pump COP
        against DBT with a 0.1 degree C interval
    :param Pandas.DataFrame advperfhp_cop: advanced performance heat pump
        (90% percentile cold climate heat pump) COP against DBT with a 0.1
        degree C interval
    :return (*pandas.DataFrame*) -- hourly electricity consumption induced by heat pump
        heating, resistance heating, cooling, and baseload for a projection scenario
    """
    base_load_scaler = new_scen.floor_area_growth(base_scen)
    cool_load_scaler = new_scen.frac_cooling_eff_change(
        base_scen
    ) * new_scen.frac_cool_growth(base_scen)
    resist_load_scaler = new_scen.frac_resist_growth(base_scen)
    if new_scen.compare_hp_heat_type(base_scen):
        hp_load_scaler = new_scen.frac_hp_growth(base_scen)
    else:
        if base_scen.hp_type_heat == "midperfhp":
            base_hp_heat_cop = midperfhp_cop
        elif base_scen.hp_type_heat == "advperfhp":
            base_hp_heat_cop = advperfhp_cop
        if new_scen.hp_type_heat == "midperfhp":
            new_hp_heat_cop = midperfhp_cop
        elif new_scen.hp_type_heat == "advperfhp":
            new_hp_heat_cop = advperfhp_cop

        hp_cop_adv = base_hp_heat_cop / new_hp_heat_cop  # <1

        hp_cop_scaler = pd.Series(dtype="float64")
        for i in temp_df.index:
            hp_cop_scaler.loc[i] = hp_cop_adv.loc[
                round(temp_df.loc[i, "temp_c"], 1), "cop"
            ]
        hp_load_scaler = hp_cop_scaler * new_scen.frac_hp_growth(base_scen)

    scen_load_mwh = pd.DataFrame(index=base_energy.index)
    scen_load_mwh["base_load_mw"] = base_energy["base_load_mw"] * base_load_scaler
    if new_hp_profile == "elec":  # if user select to use the current electricity
        # heat pump consumption profiles for heating load projection
        scen_load_mwh["heat_hp_load_mw"] = (
            base_energy["heat_hp_load_mw"] * hp_load_scaler
        )
    else:
        scen_load_mwh["heat_existing_hp_load_mw"] = base_energy["heat_hp_load_mw"]
    scen_load_mwh["heat_resist_load_mw"] = (
        base_energy["heat_resist_load_mw"] * resist_load_scaler
    )
    scen_load_mwh["cool_load_mw"] = base_energy["cool_load_mw"] * cool_load_scaler

    return scen_load_mwh


def ff_electrify_profiles(weather_years, puma_data, base_scen, new_scen):
    """Calculate hourly electricity loads for a projection scenario from converting
    fossil fuel heating, dhw and cooking to electric ones

    :param list weather_years: user defined year(s) of weather profile for
        load projection
    :param pandas.DataFrame puma_data: puma data within zone,
        output of :func:`zone_shp_overlay`
    :param load_projection_scenario.LoadProjectionScenario base_scen:
        reference scenario instance
    :param load_projection_scenario.LoadProjectionScenario new_scen:
        projection scenario instance
    :return (*pandas.DataFrame*) -- hourly projection load from converting fossil fuel
        consumption to electricity for projection scenarios given weather conditions
        from selected weather years
    """

    def ff2hp_dhw_profiles(clas):
        ff2hp_dhw_pumas_yrs = pd.DataFrame()
        for weather_year, state in product(weather_years, zone_states):
            if not os.path.isfile(
                os.path.join(
                    os.path.dirname(__file__),
                    "Profiles",
                    f"elec_dhw_ff2hp_{clas}_{state}_{weather_year}_{hp_type_dhw}_mw.csv",
                )
            ):
                print(f"generating hot water profiles for {state}...")
                generate_dhw_profiles(weather_year, [state], clas, hp_type_dhw)

        for weather_year in weather_years:
            ff2hp_dhw_pumas = pd.concat(
                list(
                    pd.Series(data=zone_states).apply(
                        lambda x: pd.read_csv(
                            os.path.join(
                                os.path.dirname(__file__),
                                "Profiles",
                                f"elec_dhw_ff2hp_{clas}_{x}_{weather_year}_{hp_type_dhw}_mw.csv",
                            )
                        )
                    )
                ),
                axis=1,
            )
            ff2hp_dhw_pumas_yrs = pd.concat(
                [ff2hp_dhw_pumas_yrs, ff2hp_dhw_pumas], ignore_index=True
            )
        ff2hp_dhw_yrs = (
            ff2hp_dhw_pumas_yrs[puma_data.index]
            .mul(puma_data["frac_in_zone"])
            .sum(axis=1)
        )
        return ff2hp_dhw_yrs

    def ff2hp_htg_profiles(clas):
        ff2hp_htg_pumas_yrs = pd.DataFrame()
        for weather_year, state in product(weather_years, zone_states):
            if not os.path.isfile(
                os.path.join(
                    os.path.dirname(__file__),
                    "Profiles",
                    f"elec_htg_ff2hp_{clas}_{state}_{weather_year}_{hp_type_heat}_mw.csv",
                )
            ):
                print(f"generating ff heating profiles for {state}...")
                generate_htg_profiles(weather_year, [state], clas, hp_type_heat)

        for weather_year in weather_years:
            ff2hp_htg_pumas = pd.concat(
                list(
                    pd.Series(data=zone_states).apply(
                        lambda x: pd.read_csv(
                            os.path.join(
                                os.path.dirname(__file__),
                                "Profiles",
                                f"elec_htg_ff2hp_{clas}_{x}_{weather_year}_{hp_type_heat}_mw.csv",
                            )
                        )
                    )
                ),
                axis=1,
            )
            ff2hp_htg_pumas_yrs = pd.concat(
                [ff2hp_htg_pumas_yrs, ff2hp_htg_pumas], ignore_index=True
            )
        ff2hp_htg_yrs = (
            ff2hp_htg_pumas_yrs[puma_data.index]
            .mul(puma_data["frac_in_zone"])
            .sum(axis=1)
        )
        return ff2hp_htg_yrs

    def ff2hp_cook_profiles(clas):
        for state in zone_states:
            if not os.path.isfile(
                os.path.join(
                    os.path.dirname(__file__),
                    "Profiles",
                    f"elec_cook_ff2hp_{clas}_{state}_{base_year}_{cook_eff}_mw.csv",
                )
            ):
                print(f"generating ff cooking profiles for {state}...")
                generate_cook_profiles(base_year, [state], clas, cook_eff)

        ff2hp_cook_pumas = pd.concat(
            list(
                pd.Series(data=zone_states).apply(
                    lambda x: pd.read_csv(
                        os.path.join(
                            os.path.dirname(__file__),
                            "Profiles",
                            f"elec_cook_ff2hp_{clas}_{x}_{base_year}_{cook_eff}_mw.csv",
                        ),
                        index_col=0,
                    )
                )
            )
        ).iloc[:, 0]
        ff2hp_cook = (
            ff2hp_cook_pumas.loc[puma_data.index].mul(puma_data["frac_in_zone"]).sum()
        )
        return ff2hp_cook

    zone_states = list(set(puma_data["state"]))
    hours_utc_weather_years = pd.date_range(
        start=f"{weather_years[0]}-01-01",
        end=f"{weather_years[-1]+1}-01-01",
        freq="H",
        tz="UTC",
    )[:-1]
    hp_type_dhw = new_scen.hp_type_dhw
    hp_type_heat = new_scen.hp_type_heat
    cook_eff = new_scen.cook_efficiency
    ff2hp_load_mwh = pd.DataFrame(index=hours_utc_weather_years)
    for clas in const.classes:
        frac_dhw_ff2hp = new_scen.frac_dhw_ff2hp(base_scen, clas)
        if frac_dhw_ff2hp != 0:
            ff2hp_load_mwh[f"dhw_{clas}"] = ff2hp_dhw_profiles(clas).to_list()
            ff2hp_load_mwh[f"dhw_{clas}"] = (
                ff2hp_load_mwh[f"dhw_{clas}"]
                * new_scen.floor_area_growth_type(base_scen, clas)
                * frac_dhw_ff2hp
            )  # scale energy consumption by floor area information

        frac_htg_ff2hp = new_scen.frac_htg_ff2hp(base_scen, clas)
        if new_hp_profile == "ff" and frac_htg_ff2hp != 0:
            ff2hp_load_mwh[f"htg_{clas}"] = ff2hp_htg_profiles(clas).to_list()
            ff2hp_load_mwh[f"htg_{clas}"] = (
                ff2hp_load_mwh[f"htg_{clas}"]
                * new_scen.floor_area_growth_type(base_scen, clas)
                * frac_htg_ff2hp
            )

        frac_cook_ff2hp = new_scen.frac_cook_ff2hp(base_scen, clas)
        if frac_cook_ff2hp != 0:
            ff2hp_load_mwh[f"cook_{clas}"] = ff2hp_cook_profiles(clas)
            ff2hp_load_mwh[f"cook_{clas}"] = (
                ff2hp_load_mwh[f"cook_{clas}"]
                * new_scen.floor_area_growth_type(base_scen, clas)
                * new_scen.frac_cook_ff2hp(base_scen, clas)
            )
    return ff2hp_load_mwh


def predict_scenario(zone_name, zone_name_shp, base_scen, new_scens, weather_years):
    """Load projection for one zone in all selected weather years.

    :param str zone_name: name of load zone used to save profile.
    :param str zone_name_shp: name of load zone within shapefile.
    :param load_projection_scenario.LoadProjectionScenario base_scen:
        reference scenario instance
    :param load_projection_scenario.LoadProjectionScenario new_scen:
        projection scenario instance
    :param list weather_years: user defined year(s) of weather profile
        for load projection
    :return (*dict*) -- hourly projected load breakdowns for all scenarios, keys are
        scenario names, values are data frames of load breakdowns
    """
    hours_utc_weather_years = pd.date_range(
        start=f"{weather_years[0]}-01-01",
        end=f"{weather_years[-1]+1}-01-01",
        freq="H",
        tz="UTC",
    )[:-1]
    # prepare weather dataframe
    puma_data_zone = zone_shp_overlay(zone_name_shp, zone_shp, pumas_shp)
    temp_df = pd.DataFrame()
    for year in weather_years:
        hours_utc_year = pd.date_range(
            start=f"{year}-01-01", end=f"{year+1}-01-01", freq="H", tz="UTC"
        )[:-1]
        temp_df_yr, stats = zonal_data(puma_data_zone, hours_utc_year, year)
        temp_df = pd.concat([temp_df, temp_df_yr], ignore_index=True)
    temp_df.index = hours_utc_weather_years

    # compute least-square estimator for relation between WBT and DBT
    t_bpc_start = 10
    db_wb_regr_df = temp_df[
        (temp_df.index.year == base_year) & (temp_df["temp_c"] >= t_bpc_start)
    ]
    db_wb_fit = np.polyfit(db_wb_regr_df["temp_c"], db_wb_regr_df["temp_c_wb"], 2)

    hourly_fits_df = pd.read_csv(
        f"https://besciences.blob.core.windows.net/datasets/bldg_el/dayhour_fits/{zone_name}_dayhour_fits_{base_year}.csv",
        index_col=0,
    )

    midperfhp_cop = pd.read_csv("./data/cop_temp_htg_midperfhp.csv")
    advperfhp_cop = pd.read_csv("./data/cop_temp_htg_advperfhp.csv")
    midperfhp_cop.index = midperfhp_cop["temp"]
    advperfhp_cop.index = advperfhp_cop["temp"]

    if base_scen.hp_type_heat == "midperfhp":
        base_hp_heat_cop = midperfhp_cop
    elif base_scen.hp_type_heat == "advperfhp":
        base_hp_heat_cop = advperfhp_cop
    else:
        raise KeyError("hp type not defined. Choose from 'midperfhp' and 'advperfhp'")

    # run reference scenario
    zone_profile_refload_MWh = pd.DataFrame(  # noqa: N806
        {"hour_utc": hours_utc_weather_years}
    )

    energy_list = zone_profile_refload_MWh.hour_utc.apply(
        lambda x: temp_to_energy(
            temp_df.loc[x], hourly_fits_df, db_wb_fit, base_scen, base_hp_heat_cop
        )
    )

    (
        zone_profile_refload_MWh["base_load_mw"],
        zone_profile_refload_MWh["heat_hp_load_mw"],
        zone_profile_refload_MWh["heat_resist_load_mw"],
        zone_profile_refload_MWh["cool_load_mw"],
    ) = (
        energy_list.apply(lambda x: x[0]),
        energy_list.apply(lambda x: x[1]),
        energy_list.apply(lambda x: x[2]),
        energy_list.apply(lambda x: x[3]),
    )
    zone_profile_refload_MWh.set_index("hour_utc", inplace=True)

    # scale energy to each projection scenarios
    elec_profile_load_mwh = {}
    zone_profile_load_mwh = {}
    zone_profile_load_mwh["base"] = zone_profile_refload_MWh
    ff2hp_profile_load_mwh = {}
    for id, scenario in new_scens.items():
        elec_profile_load_mwh[id] = scale_energy(
            zone_profile_refload_MWh,
            temp_df,
            base_scen,
            scenario,
            midperfhp_cop,
            advperfhp_cop,
        )
        ff2hp_profile_load_mwh[id] = ff_electrify_profiles(
            weather_years, puma_data_zone, scenario, base_scen
        )
        zone_profile_load_mwh[id] = pd.concat(
            [elec_profile_load_mwh[id], ff2hp_profile_load_mwh[id]], axis=1
        )

    return zone_profile_load_mwh


if __name__ == "__main__":
    # Use base_year for model fitting
    base_year = const.base_year

    # Weather year to produce load profiles. If multiple years,
    # then time series result will show for more than one year
    weather_years = [2018, 2019]

    # new heat pump load profile assumption. User can select whether to use
    # electric profile or fossil fuel profile to estimate
    # electrified fossil fuel consumption for heating
    new_hp_profile = "elec"  # "elec" or "ff"

    # Reading Balancing Authority and Pumas shapefiles for overlaying
    zone_shp = read_shapefile(
        "https://besciences.blob.core.windows.net/shapefiles/USA/balancing-authorities/ba_area/ba_area.zip"
    )
    pumas_shp = read_shapefile(
        "https://besciences.blob.core.windows.net/shapefiles/USA/pumas-overlay/pumas_overlay.zip"
    )

    zone_names = [
        "NYIS-ZONA",
    ]

    zone_name_shps = [
        "NYISO-A",
    ]

    for i in range(len(zone_names)):
        zone_name, zone_name_shp = zone_names[i], zone_name_shps[i]

        scen_data = pd.read_csv(
            os.path.join(
                os.path.dirname(__file__),
                "projection",
                "scenario_inputs",
                f"{zone_name}_stats.csv",
            ),
            index_col=0,
        )

        base_scenarios = LoadProjectionScenario("base", scen_data.pop("yr2019"))
        print(f"base scenario: year {base_year}, weather year: {weather_years}")

        proj_scenarios = {}
        for name, values in scen_data.iteritems():
            proj_scenarios[name] = LoadProjectionScenario(name, values, base_scenarios)
            print(f"projection scenario {name}, year {proj_scenarios[name].year}")

        os.makedirs(
            os.path.join(os.path.dirname(__file__), "Profiles"),
            exist_ok=True,
        )
        zone_profile_load_mwh = predict_scenario(
            zone_name, zone_name_shp, base_scenarios, proj_scenarios, weather_years
        )

        os.makedirs(
            os.path.join(os.path.dirname(__file__), "projection", "results"),
            exist_ok=True,
        )

        for name, values in zone_profile_load_mwh.items():
            zone_profile_load_mwh[name].to_csv(
                os.path.join(
                    os.path.dirname(__file__),
                    "projection",
                    "results",
                    f"{zone_name}_{name}_mwh.csv",
                )
            )

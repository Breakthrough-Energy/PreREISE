import os
import shutil

import geopandas  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from prereise.gather.demanddata.bldg_electrification import const
from prereise.gather.demanddata.bldg_electrification.const import (
    iso_name,
    iso_zone_name_shps,
    iso_zone_names,
    state_list,
)
from prereise.gather.demanddata.bldg_electrification.helper import (
    read_shapefile,
    state_shp_overlay,
    zone_shp_overlay,
)


def get_zone_floor_area(iso, zone_shape, pumas_shp):
    """Computes the zone floor area for each ISO.

    :param str iso: abbrev. name of ISO.
    :param geopandas.GeoDataFrame zone_shape: geo data frame of zone(BA) shape file
    :param geopandas.GeoDataFrame pumas_shp: geo data frame of pumas shape file
    :return: (*pandas.DataFrame*) -- Floor area in square meters for all the zones
        with breakdowns of residential, commercial, total heated and total cooled

    .. note:: zone floor area in square meters saved as csv into Profiles/result_stats
    """
    zone_floor_area = pd.DataFrame()
    for zone in iso_zone_names[iso]:
        puma_data_zone = zone_shp_overlay(
            iso_zone_name_shps[iso][iso_zone_names[iso].index(zone)],
            zone_shape,
            pumas_shp,
        )
        puma_data_zone = puma_data_zone[~(puma_data_zone["frac_in_zone"] < 0.05)]

        total_area_zone_cool_res = (
            (
                puma_data_zone[f"res_area_{base_year}_m2"]
                * puma_data_zone["AC_penetration"]
            )
            * puma_data_zone["frac_in_zone"]
        ).sum()
        total_area_zone_cool_com = (
            (
                puma_data_zone[f"com_area_{base_year}_m2"]
                * puma_data_zone["AC_penetration"]
            )
            * puma_data_zone["frac_in_zone"]
        ).sum()
        total_area_zone_heat_res = (
            (
                puma_data_zone[f"res_area_{base_year}_m2"]
                * puma_data_zone[f"frac_elec_sh_res_{base_year}"]
            )
            * puma_data_zone["frac_in_zone"]
        ).sum()
        total_area_zone_heat_com = (
            (
                puma_data_zone[f"com_area_{base_year}_m2"]
                * puma_data_zone[f"frac_elec_sh_com_{base_year}"]
            )
            * puma_data_zone["frac_in_zone"]
        ).sum()
        total_area_res = (
            puma_data_zone[f"res_area_{base_year}_m2"] * puma_data_zone["frac_in_zone"]
        ).sum()
        total_area_com = (
            puma_data_zone[f"com_area_{base_year}_m2"] * puma_data_zone["frac_in_zone"]
        ).sum()
        zone_floor_area = pd.concat(
            [
                zone_floor_area,
                pd.DataFrame(
                    {
                        "total res": total_area_res,
                        "total com": total_area_com,
                        "heat": total_area_zone_heat_res + total_area_zone_heat_com,
                        "% Heated": (
                            (total_area_zone_heat_res + total_area_zone_heat_com)
                            / (total_area_res + total_area_com)
                        )
                        * 100,
                        "res heat": total_area_zone_heat_res,
                        "com heat": total_area_zone_heat_com,
                        "cool": total_area_zone_cool_res + total_area_zone_cool_com,
                        "res cool": total_area_zone_cool_res,
                        "com cool": total_area_zone_cool_com,
                    },
                    index=[zone],
                ),
            ]
        )

    zone_floor_area.to_csv(
        f"./Profiles/result_stats/{iso_name[iso]}_zone_floor_area_m2.csv"
    )
    return zone_floor_area


def main_plots(
    iso, zone_shape, pumas_shp, state_shp, country_shp, size, plot_show=True
):
    """Creats floor area avraged slopes for all zones within the ISO for one year.

    :param str iso: abbrev. name of ISO.
    :param geopandas.GeoDataFrame zone_shape: geo data frame of zone(BA) shape file
    :param geopandas.GeoDataFrame pumas_shp: geo data frame of pumas shape file
    :param geopandas.GeoDataFrame state_shp: geo data frame of state shape file
    :param geopandas.GeoDataFrame country_shp: geo data frame of nation shape file
    :param bool plot_show: show the plot or not, default to True.
    :param int size: defining the image size of plots in dpi.

    .. note:: Floor area avg. heating and cooling slope, error and map plots for all
        zones in each ISO saved as png and csv into Profiles/result_stats/hourly_plots
    """

    zone_floor_area = get_zone_floor_area(iso, zone_shape, pumas_shp)

    # Slope plots for all zones in each ISO in btu/m2/C

    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    for zone in iso_zone_names[iso]:
        dayhour_fits = pd.read_csv(
            f"https://besciences.blob.core.windows.net/datasets/bldg_el/dayhour_fits/{zone}_dayhour_fits_{base_year}.csv",
            index_col=0,
        )
        for wk_wknd in ["wk", "wknd"]:
            dayhour_fits[f"s.heat.{wk_wknd}"] = (
                abs(dayhour_fits[f"s.heat.{wk_wknd}"])
                / zone_floor_area.loc[zone, "heat"]
                * const.conv_mw_to_btu
            )
            dayhour_fits[f"s.heat.stderr.{wk_wknd}"] = (
                dayhour_fits[f"s.heat.stderr.{wk_wknd}"]
                / zone_floor_area.loc[zone, "heat"]
                * const.conv_mw_to_btu
            )
            dayhour_fits[f"s.cool.{wk_wknd}.db"] = (
                dayhour_fits[f"s.cool.{wk_wknd}.db"]
                / zone_floor_area.loc[zone, "cool"]
                * const.conv_mw_to_btu
            )
            dayhour_fits[f"s.cool.db.stderr.{wk_wknd}"] = (
                dayhour_fits[f"s.cool.db.stderr.{wk_wknd}"]
                / zone_floor_area.loc[zone, "cool"]
                * const.conv_mw_to_btu
            )

        zone_dayhour = pd.DataFrame()
        zone_dayhour["s.heat"] = (
            dayhour_fits["s.heat.wk"] * 5 + dayhour_fits["s.heat.wknd"] * 2
        ) / 7
        zone_dayhour["s.heat.stderr"] = (
            np.sqrt(
                dayhour_fits["s.heat.stderr.wk"] ** 2 * 5**2
                + dayhour_fits["s.heat.stderr.wknd"] ** 2 * 2**2
            )
            / 7
        )
        zone_dayhour["s.cool.db"] = (
            dayhour_fits["s.cool.wk.db"] * 5 + dayhour_fits["s.cool.wknd.db"] * 2
        ) / 7
        zone_dayhour["s.cool.db.stderr"] = (
            np.sqrt(
                dayhour_fits["s.cool.db.stderr.wk"] ** 2 * 5**2
                + dayhour_fits["s.cool.db.stderr.wknd"] ** 2 * 2**2
            )
            / 7
        )
        ax1.plot(zone_dayhour.index, zone_dayhour["s.heat"], label=zone)
        ax1.set_ylabel("$Btu_e/m^2/^oC$")
        ax1.set_xlabel("hour of day")
        ax1.set_title(f"heating slopes, {iso_name[iso]}")
        ax2.plot(zone_dayhour.index, zone_dayhour["s.cool.db"], label=zone)
        ax2.set_ylabel("$Btu_e/m^2/^oC$")
        ax2.set_xlabel("hour of day")
        ax2.set_title(f"cooling slopes, {iso_name[iso]}")
    ax1.legend()
    ax2.legend()
    if plot_show:
        fig1.savefig(
            f"./Profiles/result_stats/hourly_plots/zone_plots/{iso_name[iso]}_heating.png",
            dpi=size,
        )
        fig2.savefig(
            f"./Profiles/result_stats/hourly_plots/zone_plots/{iso_name[iso]}_cooling.png",
            dpi=size,
        )

    # Create hourly slope plots with error bars for each zone within each ISO

    iso_slope = pd.DataFrame()

    iso_dayhour_fits = pd.DataFrame(index=np.arange(0, 24))
    for wk_wknd in ["wk", "wknd"]:
        iso_floor_area = zone_floor_area.loc[iso_zone_names[iso]].sum()

        # read hourly slopes
        dayhour_fits = {
            i: pd.read_csv(
                f"https://besciences.blob.core.windows.net/datasets/bldg_el/dayhour_fits/{zone}_dayhour_fits_{base_year}.csv",
                index_col=0,
            )
            for i, zone in enumerate(iso_zone_names[iso])
        }

        iso_dayhour_fits[f"s.heat.{wk_wknd}"] = (
            np.sum(
                [
                    dayhour_fits[i][f"s.heat.{wk_wknd}"].to_list()
                    for i in range(len(iso_zone_names[iso]))
                ],
                axis=0,
            )
            / iso_floor_area["heat"]
            * const.conv_mw_to_btu
        )

        iso_dayhour_fits[f"s.cool.{wk_wknd}.db"] = (
            np.sum(
                [
                    dayhour_fits[i][f"s.cool.{wk_wknd}.db"].to_list()
                    for i in range(len(iso_zone_names[iso]))
                ],
                axis=0,
            )
            / iso_floor_area["cool"]
            * const.conv_mw_to_btu
        )

        iso_dayhour_fits[f"s.heat.stderr.{wk_wknd}"] = (
            np.sqrt(
                np.sum(
                    [
                        np.square(dayhour_fits[i][f"s.heat.stderr.{wk_wknd}"].to_list())
                        for i in range(len(iso_zone_names[iso]))
                    ],
                    axis=0,
                )
            )
            / iso_floor_area["heat"]
            * const.conv_mw_to_btu
        )

        iso_dayhour_fits[f"s.cool.db.stderr.{wk_wknd}"] = (
            np.sqrt(
                np.sum(
                    [
                        np.square(
                            dayhour_fits[i][f"s.cool.db.stderr.{wk_wknd}"].to_list()
                        )
                        for i in range(len(iso_zone_names[iso]))
                    ],
                    axis=0,
                )
            )
            / iso_floor_area["cool"]
            * const.conv_mw_to_btu
        )
        if plot_show:
            fig, ax1 = plt.subplots()
            ax1.errorbar(
                iso_dayhour_fits.index,
                np.abs(iso_dayhour_fits[f"s.heat.{wk_wknd}"]),
                yerr=iso_dayhour_fits[f"s.heat.stderr.{wk_wknd}"] * 1.96,
                fmt="x",
                capsize=3,
                label="Heating Slopes",
            )
            ax1.errorbar(
                iso_dayhour_fits.index + 0.3,
                np.abs(iso_dayhour_fits[f"s.cool.{wk_wknd}.db"]),
                yerr=iso_dayhour_fits[f"s.cool.db.stderr.{wk_wknd}"] * 1.96,
                fmt="x",
                capsize=3,
                color="tab:orange",
                label="Cooling Slopes",
            )
            ax1.set_ylabel("$Btu_e/h/m^2/^oC$", fontsize=14)
            ax1.set_xlabel("Hour of the Day", fontsize=14)
            ax1.legend(fontsize=14)
            text_wk_wknd = "Weekday" if wk_wknd == "wk" else "Weekend"
            plt.title(
                f"{text_wk_wknd} Hourly Profile of Heating and Cooling slopes, {iso_name[iso]}",
                fontsize=12,
            )
            plt.savefig(
                f"./Profiles/result_stats/hourly_plots/iso plot with error/{iso}_{wk_wknd}.png",
                dpi=size,
            )

    iso_dayhour = pd.DataFrame()
    iso_dayhour["s.heat"] = (
        iso_dayhour_fits["s.heat.wk"] * 5 + iso_dayhour_fits["s.heat.wknd"] * 2
    ) / 7
    iso_dayhour["s.heat.stderr"] = (
        np.sqrt(
            iso_dayhour_fits["s.heat.stderr.wk"] ** 2 * 5**2
            + iso_dayhour_fits["s.heat.stderr.wknd"] ** 2 * 2**2
        )
        / 7
    )
    iso_dayhour["s.cool.db"] = (
        iso_dayhour_fits["s.cool.wk.db"] * 5 + iso_dayhour_fits["s.cool.wknd.db"] * 2
    ) / 7
    iso_dayhour["s.cool.db.stderr"] = (
        np.sqrt(
            iso_dayhour_fits["s.cool.db.stderr.wk"] ** 2 * 5**2
            + iso_dayhour_fits["s.cool.db.stderr.wknd"] ** 2 * 2**2
        )
        / 7
    )

    if plot_show:
        fig, ax1 = plt.subplots()
        ax1.errorbar(
            iso_dayhour.index,
            np.abs(iso_dayhour["s.heat"]),
            yerr=iso_dayhour["s.heat.stderr"] * 1.96,
            fmt="x",
            capsize=3,
            label="Heating Slopes",
        )
        ax1.errorbar(
            iso_dayhour.index + 0.3,
            np.abs(iso_dayhour["s.cool.db"]),
            yerr=iso_dayhour["s.cool.db.stderr"] * 1.96,
            fmt="x",
            capsize=3,
            color="tab:orange",
            label="Cooling Slopes",
        )
        ax1.set_ylabel("$Btu_e/h/m^2/^oC$", fontsize=14)
        ax1.set_xlabel("Hour of the Day", fontsize=14)
        ax1.legend(fontsize=14)
        plt.title(
            f"Hourly Profile of Heating and Cooling slopes, {iso_name[iso]}",
            fontsize=14,
        )
        plt.savefig(
            f"./Profiles/result_stats/hourly_plots/iso plot with error/{iso}.png",
            dpi=size,
        )

    iso_slope.loc[iso, "s.heat"] = np.mean(iso_dayhour["s.heat"])
    iso_slope.loc[iso, "s.heat.stderr"] = (
        np.sqrt(np.sum(iso_dayhour["s.heat.stderr"] ** 2)) / 24
    )
    iso_slope.loc[iso, "s.cool.db"] = np.mean(iso_dayhour["s.cool.db"])
    iso_slope.loc[iso, "s.cool.db.stderr"] = (
        np.sqrt(np.sum(iso_dayhour["s.cool.db.stderr"] ** 2)) / 24
    )

    iso_slope.to_csv(
        f"./Profiles/result_stats/hourly_plots/iso plot with error/{iso_name[iso]}_iso_slope_with_error.csv"
    )

    # Creating the zone and iso level heating and cooling load in mw/C and btu/m2/C

    zone_slope_df = pd.DataFrame()
    for zone in iso_zone_names[iso]:
        hourly_data = pd.read_csv(
            f"https://besciences.blob.core.windows.net/datasets/bldg_el/dayhour_fits/{zone}_dayhour_fits_{base_year}.csv",
            index_col=0,
        )

        htg_mean = (
            np.mean(hourly_data.loc[:, "s.heat.wk"]) * 5
            + np.mean(hourly_data.loc[:, "s.heat.wknd"]) * 2
        ) / 7
        clg_mean = (
            np.mean(hourly_data.loc[:, "s.cool.wk.db"]) * 5
            + np.mean(hourly_data.loc[:, "s.cool.wknd.db"]) * 2
        ) / 7
        zone_slope_df = pd.concat(
            [
                zone_slope_df,
                pd.DataFrame({"Heating": htg_mean, "Cooling": clg_mean}, index=[zone]),
            ]
        )

    zone_slope_df.to_csv(f"./Profiles/result_stats/{iso_name[iso]}_zone_elec_mw_c.csv")
    zone_elec_btu_m2_c = pd.DataFrame()
    zone_elec_btu_m2_c["Heating"] = (
        zone_slope_df["Heating"] / zone_floor_area["heat"] * const.conv_mw_to_btu
    )
    zone_elec_btu_m2_c["Cooling"] = (
        zone_slope_df["Cooling"] / zone_floor_area["cool"] * const.conv_mw_to_btu
    )
    zone_elec_btu_m2_c.to_csv(
        f"./Profiles/result_stats/{iso_name[iso]}_zone_elec_btu_m2_c.csv"
    )

    # Creating ISO map plots containing load zones with the heating and cooling slope in btu/m2/C
    if iso in {"NY", "CA", "PJM", "SPP", "NW", "SE"}:
        zone_elec_btu_m2_c[
            (zone_elec_btu_m2_c >= 10) | (zone_elec_btu_m2_c <= -10)
        ] = np.nan
        for ba in {
            "NYIS-ZOND",
            "NYIS-ZONH",
            "WALC",
            "PJM-RECO",
            "SWPP-WFEC",
            "PSEI",
            "AECI",
        }:
            zone_elec_btu_m2_c.loc[ba] = np.nan

    zone_shp = pd.DataFrame()

    if iso in {"NE", "PJM", "SPP", "MISO", "SW", "NW", "SE"}:
        zone_shp = pd.concat([s for s in iso_state_overlay[iso]])

    elif iso == "USA" or iso == "Outliers":
        zone_shp = state_shp_overlay("United States", country_shp, zone_shape)

    else:
        zone_shp = state_shp_overlay(iso, state_shp, zone_shape)

    zone_shp.index = zone_shp["BA"]

    for i in range(len(iso_zone_name_shps[iso])):
        zone_shp.loc[iso_zone_name_shps[iso][i], "BA"] = iso_zone_names[iso][i]

    for use in ["Heating", "Cooling"]:
        if iso == "Outliers" and use == "Heating":
            vmax = 250
        elif iso == "Outliers" and use == "Cooling":
            vmax = 100
        else:
            vmax = 10
        zone_shp.index = zone_shp["BA"]
        zone_shp[use] = abs(zone_elec_btu_m2_c[use])
        if plot_show:
            fig, ax = plt.subplots(1, 1)
            zone_shp.plot(
                column=use,
                ax=ax,
                vmin=0,
                vmax=vmax,
                legend=True,
                cmap=plt.cm.hot_r,
                edgecolor="black",
                missing_kwds={"color": "lightgrey"},
                legend_kwds={
                    "label": "$Btu_e/m^2/^oC$",
                },
            )
            plt.title(f"Load Zone {use} slopes, {iso_name[iso]}")
            plt.tick_params(
                axis="both",
                which="both",
                bottom=False,
                top=False,
                right=False,
                left=False,
                labelbottom=False,
                labelleft=False,
            )

            plt.savefig(
                f"./Profiles/result_stats/hourly_plots/zone_plots/zone model/{iso}_{use}_zone_model.png",
                dpi=size,
            )


if __name__ == "__main__":
    os.makedirs(
        os.path.join(
            os.path.dirname(__file__),
            "Profiles/result_stats/hourly_plots/zone_plots/zone model",
        ),
        exist_ok=True,
    )

    os.makedirs(
        os.path.join(
            os.path.dirname(__file__),
            "Profiles/result_stats/hourly_plots/iso plot with error",
        ),
        exist_ok=True,
    )

    # Reading Balancing Authority, Pumas, state and country Boundary shapefiles for overlaying
    zone_shape = read_shapefile(
        "https://besciences.blob.core.windows.net/shapefiles/USA/balancing-authorities/ba_area/ba_area.zip"
    )
    pumas_shp = read_shapefile(
        "https://besciences.blob.core.windows.net/shapefiles/USA/pumas-overlay/pumas_overlay.zip"
    )
    state_shp = read_shapefile(
        "https://besciences.blob.core.windows.net/shapefiles/USA/state-outlines/cb_2018_us_state_20m.zip"
    )
    country_shp = read_shapefile(
        "https://besciences.blob.core.windows.net/shapefiles/USA/nation-outlines/cb_2018_us_nation_20m.zip"
    )

    # Executing the state overlay for all states in the US
    zone_shp_state = {
        s: state_shp_overlay(s, state_shp, zone_shape) for s in state_list
    }

    iso_state_overlay = {
        "NE": [
            zone_shp_state["MA"],
            zone_shp_state["ME"],
            zone_shp_state["NH"],
            zone_shp_state["VT"],
            zone_shp_state["CT"],
            zone_shp_state["RI"],
        ],
        "PJM": [
            zone_shp_state["DE"],
            zone_shp_state["IL"],
            zone_shp_state["IN"],
            zone_shp_state["KY"],
            zone_shp_state["MD"],
            zone_shp_state["NC"],
            zone_shp_state["MI"],
            zone_shp_state["NJ"],
            zone_shp_state["OH"],
            zone_shp_state["PA"],
            zone_shp_state["VA"],
            zone_shp_state["WV"],
            zone_shp_state["TN"],
            zone_shp_state["DC"],
        ],
        "SPP": [
            zone_shp_state["KS"],
            zone_shp_state["OK"],
            zone_shp_state["NM"],
            zone_shp_state["TX"],
            zone_shp_state["AR"],
            zone_shp_state["LA"],
            zone_shp_state["MO"],
            zone_shp_state["SD"],
            zone_shp_state["ND"],
            zone_shp_state["MT"],
            zone_shp_state["MN"],
            zone_shp_state["IA"],
            zone_shp_state["WY"],
            zone_shp_state["NE"],
        ],
        "MISO": [
            zone_shp_state["LA"],
            zone_shp_state["AR"],
            zone_shp_state["MS"],
            zone_shp_state["MI"],
            zone_shp_state["MO"],
            zone_shp_state["KY"],
            zone_shp_state["IN"],
            zone_shp_state["IL"],
            zone_shp_state["IA"],
            zone_shp_state["MN"],
            zone_shp_state["WI"],
            zone_shp_state["ND"],
            zone_shp_state["SD"],
            zone_shp_state["TX"],
            zone_shp_state["MT"],
        ],
        "SW": [
            zone_shp_state["AZ"],
            zone_shp_state["NM"],
            zone_shp_state["CO"],
            zone_shp_state["NV"],
            zone_shp_state["WY"],
            zone_shp_state["SD"],
            zone_shp_state["NE"],
        ],
        "NW": [
            zone_shp_state["CA"],
            zone_shp_state["WA"],
            zone_shp_state["OR"],
            zone_shp_state["ID"],
            zone_shp_state["NV"],
            zone_shp_state["UT"],
            zone_shp_state["WY"],
            zone_shp_state["MT"],
        ],
        "SE": [
            zone_shp_state["MO"],
            zone_shp_state["KY"],
            zone_shp_state["MS"],
            zone_shp_state["TN"],
            zone_shp_state["AL"],
            zone_shp_state["GA"],
            zone_shp_state["NC"],
            zone_shp_state["SC"],
            zone_shp_state["FL"],
            zone_shp_state["VA"],
        ],
    }

    # Use base_year for model results
    base_year = const.base_year

    # Plot size in dpi
    size = 700

    for iso in [
        "NY",
        "TX",
        "CA",
        "NE",
        "PJM",
        "SPP",
        "MISO",
        "SW",
        "NW",
        "SE",
        "USA",
        "Outliers",
    ]:
        main_plots(iso, zone_shape, pumas_shp, state_shp, country_shp, size)

    # Delete the tmp folder that holds the shapefiles localy after the script is run to completion
    shutil.rmtree(os.path.join("tmp"), ignore_errors=False, onerror=None)

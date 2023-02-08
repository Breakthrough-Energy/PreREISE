import os

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.api as sm

from prereise.gather.demanddata.bldg_electrification import const
from prereise.gather.demanddata.bldg_electrification.helper import read_shapefile


def puma_county_shp_overlay(pumas_shp, county_shp):
    """Align all counties that are within survey areas of AHS(American Housing Survey)
    to PUMAs geographically

    :param geopandas.GeoDataFrame pumas_shp: geo data frame of pumas shape file
    :param geopandas.GeoDataFrame county_shp: geo data frame of county shape file
    :return (*pandas.DataFrame*) -- puma data of all pumas within the survey areas of
        AHS, including fraction within the zone. Row indices are id's of puma that is
        covered by AHS survey data. Columns include household heat pump possession
        rate from AHS, fraction of geographical area each PUMA in each county,
        and other end-use energy information in "/data/puma_data.csv"
    """
    county_shp.index = county_shp["GEOID"]
    county_shp.sort_index(inplace=True)

    pumas_shp["area"] = pumas_shp["geometry"].to_crs({"proj": "cea"}).area

    # read AHS metropolitan data on HP
    hp_metro_ahs = pd.read_excel(
        os.path.join(os.path.dirname("__file__"), "data", "hp_ahs.xlsx"), dtype=str
    )
    hp_metro_ahs["counties"] = (
        hp_metro_ahs.filter(like="county").stack().groupby(level=0).apply(list).tolist()
    )

    for i in range(len(hp_metro_ahs)):
        county_shp.loc[
            county_shp.index.isin(hp_metro_ahs.loc[i, "counties"]), "metro_id"
        ] = i
        county_shp.loc[
            county_shp.index.isin(hp_metro_ahs.loc[i, "counties"]), "HP rate"
        ] = hp_metro_ahs.loc[i, "HP rate"]
    county_shp = county_shp[~county_shp["metro_id"].isna()]
    county_shp = county_shp.copy()
    county_shp["HP rate"] = county_shp["HP rate"].astype("float64")
    county_shp["metro_id"] = county_shp["metro_id"].astype("int64")
    county_shp = county_shp.dissolve(by="metro_id")
    county_shp["metro_id"] = county_shp.index

    puma_metro = gpd.overlay(pumas_shp, county_shp, keep_geom_type=True)
    puma_metro["area"] = puma_metro["geometry"].to_crs({"proj": "cea"}).area

    puma_metro["area_frac"] = [
        puma_metro["area"][i]
        / list(pumas_shp[pumas_shp["puma"] == puma_metro["puma"][i]]["area"])[0]
        for i in range(len(puma_metro))
    ]
    puma_metro = puma_metro.drop(puma_metro[puma_metro["area_frac"] <= 0.01].index)
    puma_data_metro = pd.DataFrame(
        {
            "puma": puma_metro["puma"],
            "frac_in_zone": puma_metro["area_frac"],
            "metro_id": puma_metro["metro_id"],
            "hp_penetration": puma_metro["HP rate"],
        }
    )
    puma_data = const.puma_data

    puma_data_metro = puma_data_metro.join(puma_data, on="puma")
    puma_data_metro = puma_data_metro.set_index("puma")

    ng_price = pd.read_csv(
        os.path.join(
            os.path.dirname(__file__), "data", "state_ng_residential_price_2019.csv"
        ),
        index_col=0,
    )
    puma_data_metro["ng_price"] = puma_data_metro.apply(
        lambda x: ng_price.loc[x.loc["state"], "$/kWh"], axis=1
    )
    return puma_data_metro


def metro_data(puma_data):
    """Aggregate puma metrics to the population weighted metropolitan area values of AHS
    survey

    :param pandas.DataFrame puma_data: puma data within metropolitan areas, output of
        :py:func: `puma_county_shp_overlay()`
    :return (*pandas.DataFrame*) stats -- metropolitan area data to be used for heat
        pump penetration linear regression model. The row indices includes all
        metropolitan areas with AHS heat pump data. Columns include data on the fraction
        of floor area that use electricity for space heating, average natural gas
        price for year 2019, normal year HDD, and AHS heat pump penetration rate.
    """
    puma_fuel = const.puma_fuel
    stats = pd.DataFrame()
    for id, puma_df in puma_data.groupby("metro_id"):
        puma_fuel_metro = puma_fuel[puma_fuel.index.isin(puma_df.index)]
        puma_pop_weights = (puma_df["pop"] * puma_df["frac_in_zone"]) / sum(
            puma_df["pop"] * puma_df["frac_in_zone"]
        )

        stats.loc[id, "frac_elec_htg"] = puma_fuel_metro["hh_elec"].mul(
            puma_pop_weights, axis=0
        ).sum(axis=0) / puma_fuel_metro["hh_total"].mul(puma_pop_weights, axis=0).sum(
            axis=0
        )
        stats.loc[id, "frac_elec_htg_sq"] = stats.loc[id, "frac_elec_htg"] ** 2
        stats.loc[id, "log_hdd"] = np.log(
            (puma_df["hdd65_normals"] * puma_pop_weights).sum()
        )
        stats.loc[id, "natgas_price"] = (
            puma_data["ng_price"].mul(puma_pop_weights, axis=0).sum(axis=0)
        )
        stats.loc[id, "hp_penetration"] = puma_df["hp_penetration"][0]
    return stats


def hp_penetration_fit(stats):
    """Fit current heat pump penetration rate on metropolitan area data

    :param pandas.DataFrame stats: metropolitan area data, output of
        :py:func: `metro_data()`
    :return: (*tuple*) -- hp_fit_df: slope and intercept of heat pump penetration
        regression model, fit_stats: fitting statistics of heat pump penetration
        regression model; hp_fit_df_low_elec: slope and intercept of a simpler heat
        pump penetration model fitted on data points with low electrification rate
        of buildings; fit_stats_low_elec: fitting statistics of a simpler heat pump
        penetration model fitted on data points with low electrification rate of
        buildings.
    """
    lm_hp = sm.OLS(
        stats["hp_penetration"],
        sm.add_constant(
            np.array(
                stats[
                    [
                        "frac_elec_htg",
                        "log_hdd",
                        "natgas_price",
                    ]
                ]
            )
        ),
    ).fit()
    print(
        "fitting statistics summary of heat pump penetration model:", lm_hp.summary()
    )  # check the fitting statistics
    hp_fit_df = pd.Series(
        data=[
            lm_hp.params[0],
            lm_hp.params[1],
            lm_hp.params[2],
            lm_hp.params[3],
        ],
        index=[
            "const",
            "s_frac_elec_htg",
            "s_log_hdd",
            "s_natgas_price",
        ],
    )
    fit_stats = pd.Series(
        data=[
            lm_hp.bse[0],
            lm_hp.bse[1],
            lm_hp.bse[2],
            lm_hp.bse[3],
            lm_hp.pvalues[1],
            lm_hp.pvalues[2],
            lm_hp.pvalues[3],
            lm_hp.rsquared,
        ],
        index=[
            "stderr_const",
            "stderr_frac_elec_htg",
            "stderr_log_hdd",
            "stderr_natgas_price",
            "pvalue_frac_elec_htg",
            "pvalue_log_hdd",
            "pvalue_natgas_price",
            "rsquared",
        ],
    )
    # It's observed that hp penetration has low variance when electric heating
    # rate is low, and high variance when electric heating rate is high. So fit a
    # simpler model with less variance for pumas with lower electric heating
    # penetration as follows
    lm_hp_low = sm.OLS(
        stats["hp_penetration"],
        sm.add_constant(
            np.array(
                stats[
                    [
                        "frac_elec_htg",
                        "frac_elec_htg_sq",
                    ]
                ]
            )
        ),
    ).fit()
    hp_fit_df_low_elec = pd.Series(
        data=[
            lm_hp_low.params[0],
            lm_hp_low.params[1],
            lm_hp_low.params[2],
        ],
        index=[
            "const",
            "s_frac_elec_htg",
            "s_frac_elec_htg_sq",
        ],
    )
    fit_stats_low_elec = pd.Series(
        data=[
            lm_hp_low.bse[0],
            lm_hp_low.bse[1],
            lm_hp_low.bse[2],
            lm_hp_low.pvalues[1],
            lm_hp_low.pvalues[2],
            lm_hp_low.rsquared,
        ],
        index=[
            "stderr_const",
            "stderr_frac_elec_htg",
            "stderr_frac_elec_htg_sq",
            "pvalue_frac_elec_htg",
            "pvalue_frac_elec_htg_sq",
            "rsquared",
        ],
    )

    return hp_fit_df, fit_stats, hp_fit_df_low_elec, fit_stats_low_elec


def estimate_puma_hp_penetration(hp_fit_df, hp_fit_df_low_elec, puma_data_metro):
    """Compute current heat pump penetration for PUMAs, and then scale the values to
    align with regional inputs from RECS and CBECS surveys. When compute heat pump
    penetration rate from the regression model, the simpler model with less variance
    is chosen when the fraction of electrified heating is less than 0.27 (by default)
    as observed from the relationship between current heat pump penetration rate and
    the fraction of electrified heating

    :param pandas.DataFrame hp_fit_df: slope and intercept of heat pump penetration
        regression model, output of :py:func:`hp_penetration_fit()`
    :param pandas.DataFrame hp_fit_df_low_elec: slope and intercept of heat pump
        penetration regression model for low electrified locations, output of
        :py:func: `hp_penetration_fit()`
    :param pandas.DataFrame puma_data_metro: puma data within metropolitan areas,
        output of :py:func: `puma_county_shp_overlay()`
    :return: (*pandas.DataFrame*) hp_puma_df: current heat pump penetration estimations
        for pumas that has been scaled based on RECS and CBECS surveys. The indices
        of this dataframe includes all PUMA id's in the CONUS. The columns include
        estimates of current heat pump penetration result for residential and commercial
        building stock
    """

    puma_fuel = const.puma_fuel
    puma_data = const.puma_data
    natgas_price = pd.read_csv(
        os.path.join(
            os.path.dirname(__file__), "data", "state_ng_residential_price_2019.csv"
        ),
        index_col=0,
    )
    puma_hp_df = pd.DataFrame(
        {
            "state": puma_fuel["state"],
            "frac_elec_htg": puma_fuel["hh_elec"] / puma_fuel["hh_total"],
            "log_hdd": np.log(puma_data["hdd65_normals"]),
            "natgas_price": puma_fuel.apply(
                lambda x: natgas_price.loc[x.loc["state"], "$/kWh"], axis=1
            ),
            "hh_total": puma_fuel["hh_total"],
        },
        index=puma_data.index,
    )
    puma_hp_df["frac_hp_fitted"] = puma_hp_df.apply(
        lambda x: (
            x["frac_elec_htg"] * hp_fit_df["s_frac_elec_htg"]
            + x["log_hdd"] * hp_fit_df["s_log_hdd"]
            + x["natgas_price"] * hp_fit_df["s_natgas_price"]
            + hp_fit_df["const"]
        )
        if x["frac_elec_htg"] > 0.27
        else (
            x["frac_elec_htg"] * hp_fit_df_low_elec["s_frac_elec_htg"]
            + x["frac_elec_htg"] ** 2 * hp_fit_df_low_elec["s_frac_elec_htg_sq"]
            + hp_fit_df_low_elec["const"]
        ),
        axis=1,
    )  # 0.27 is an empirical threshold
    puma_hp_df["frac_hp_fitted"].clip(lower=0, inplace=True)
    puma_hp_df["hh_hp"] = puma_hp_df["frac_hp_fitted"] * puma_hp_df["hh_total"]

    # scale hp penetration to align with AHS metropolitan area data
    puma_data_metro["frac_hp_fitted"] = puma_hp_df["frac_hp_fitted"]
    puma_data_metro["hh_total"] = puma_hp_df["hh_total"]
    puma_data_metro["hh_hp_fitted"] = (
        puma_data_metro["frac_hp_fitted"] * puma_data_metro["hh_total"]
    )
    puma_data_metro["hh_hp_target"] = (
        puma_data_metro["hp_penetration"] * puma_data_metro["hh_total"]
    )
    puma_metro = puma_data_metro.groupby("metro_id")[
        ["hh_hp_fitted", "hh_hp_target"]
    ].sum()
    scaler = puma_metro["hh_hp_target"] / puma_metro["hh_hp_fitted"]

    # if a puma is in two metropolitan area, then scale it by the metro area that
    # is larger overlaying with the puma
    puma_data_metro.sort_values("frac_in_zone", ascending=False, inplace=True)
    puma_data_metro = puma_data_metro[~puma_data_metro.index.duplicated(keep="first")]
    puma_data_metro = puma_data_metro.sort_index()

    puma_data_metro["frac_hp_scaled"] = puma_data_metro.apply(
        lambda x: x.loc["frac_hp_fitted"] * scaler[x.loc["metro_id"]], axis=1
    )
    puma_hp_df.loc[
        puma_hp_df.index.isin(puma_data_metro.index), "frac_hp_fitted"
    ] = puma_data_metro["frac_hp_scaled"]
    puma_hp_df["hh_hp"] = puma_hp_df["frac_hp_fitted"] * puma_hp_df["hh_total"]

    # scale hp penetration to align with RECS and CBECS survey
    for clas in const.classes:
        hp_target = pd.read_csv(
            os.path.join(
                os.path.dirname(__file__), "data", f"frac_target_hp_{clas}.csv"
            ),
            index_col=0,
        )

        puma_hp_df[f"census_region_{clas}"] = puma_hp_df.apply(
            lambda x: [
                i
                for i in const.census_region[clas]
                if x["state"] in const.census_region[clas][i]
            ][0],
            axis=1,
        )

        census_df = puma_hp_df.groupby(f"census_region_{clas}")[
            ["hh_hp", "hh_total"]
        ].sum()
        census_df["hh_hp_target"] = hp_target["hp_target"] * census_df["hh_total"]
        scaler = census_df["hh_hp_target"] / census_df["hh_hp"]
        puma_hp_df[f"frac_hp_{clas}"] = puma_hp_df.apply(
            lambda x: (x["frac_hp_fitted"] * scaler[x[f"census_region_{clas}"]]), axis=1
        )
        puma_hp_df[f"hh_hp_{clas}"] = (
            puma_hp_df[f"frac_hp_{clas}"] * puma_hp_df["hh_total"]
        )
        puma_hp_df[f"frac_hp_{clas}"].clip(
            upper=puma_hp_df["frac_elec_htg"], inplace=True
        )

    hp_puma_df = pd.DataFrame(
        {
            "state": puma_hp_df["state"],
            "frac_hp_res": puma_hp_df["frac_hp_res"],
            "frac_hp_com": puma_hp_df["frac_hp_com"],
        }
    )
    return hp_puma_df


if __name__ == "__main__":
    pumas_shp = read_shapefile(
        "https://besciences.blob.core.windows.net/shapefiles/USA/pumas-overlay/pumas_overlay.zip"
    )
    county_shp = read_shapefile(
        "https://besciences.blob.core.windows.net/shapefiles/USA/county-outlines/county_area.zip"
    )
    puma_data_metro = puma_county_shp_overlay(pumas_shp, county_shp)
    stats = metro_data(puma_data_metro)
    hp_fit_df, fit_stats, hp_fit_df_low_elec, fit_stats_low_elec = hp_penetration_fit(
        stats
    )
    hp_puma_df = estimate_puma_hp_penetration(
        hp_fit_df, hp_fit_df_low_elec, puma_data_metro
    )
    hp_puma_df.to_csv(
        os.path.join(os.path.dirname("__file__"), "data", "puma_hp_data.csv")
    )

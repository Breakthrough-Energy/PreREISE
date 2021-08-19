import os

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from prereise.gather.demanddata.bldg_electrification import const


def calculate_r2(endogenous, residuals):
    """Calculate r2 value of fit.

    :param iterable endogenous: vector of observations of endogenous variable.
    :param iterable residuals: vector of residuals between modeled fit and observations.
    :return: (*float*) -- r-squared value of fit.
    """
    sumres = np.square(np.array(residuals)).sum()
    sumtot = np.square(np.array(endogenous) - np.array(endogenous).mean()).sum()
    r2 = 1 - (sumres / sumtot)
    return r2


def calculate_state_slopes(puma_data, year):
    dti = pd.date_range(start=f"{year}-01-01", end=f"{year}-12-31 23:00:00", freq="H")
    hours_in_month = dti.month.value_counts()

    # Load in historical 2010 fossil fuel usage data
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    ng_usage_data = {
        clas: pd.read_csv(
            os.path.join(data_dir, f"ng_monthly_mmbtu_2010_{clas}.csv"), index_col=0
        )
        for clas in {"res", "com"}
    }
    fok_usage_data = pd.read_csv(
        os.path.join(data_dir, "fok_data_bystate_2010.csv"), index_col="state"
    )
    othergas_usage_data = pd.read_csv(
        os.path.join(data_dir, "propane_data_bystate_2010.csv"), index_col="state"
    )

    # Initialize dataframes to store state heating slopes
    state_slopes_res = pd.DataFrame(
        columns=(["state", "r2", "sh_slope", "dhw_const", "dhw_slope", "other_const"])
    )
    state_slopes_com = pd.DataFrame(
        columns=(
            [
                "state",
                "r2",
                "sh_slope",
                "dhw_const",
                "cook_const",
                "other_const",
                "other_slope",
            ]
        )
    )

    for state in const.state_list:
        # Load puma data
        puma_data_it = const.puma_data.query("state == @state")

        # Load puma temperatures
        temps_pumas = temps_pumas = pd.read_csv(
            f"https://besciences.blob.core.windows.net/datasets/pumas/temps_pumas_{state}_{year}.csv"
        )
        temps_pumas_transpose = temps_pumas.T

        for clas in const.classes:
            # puma area * percentage of puma area that uses fossil fuel
            areas_ff_sh_it = (
                puma_data_it[f"{clas}_area_2010_m2"]
                * puma_data_it[f"frac_ff_sh_{clas}_2010"]
            )
            areas_ff_dhw_it = (
                puma_data_it[f"{clas}_area_2010_m2"]
                * puma_data_it[f"frac_ff_dhw_{clas}_2010"]
            )
            areas_ff_cook_it = (
                puma_data_it[f"{clas}_area_2010_m2"]
                * puma_data_it["frac_ff_cook_com_2010"]
            )
            if clas == "res":
                areas_ff_other_it = (
                    puma_data_it[f"{clas}_area_2010_m2"]
                    * puma_data_it["frac_ff_other_res_2010"]
                )
            else:
                areas_ff_other_it = (
                    puma_data_it[f"{clas}_area_2010_m2"]
                    * puma_data_it["frac_ff_sh_com_2010"]
                )

            # sum of previous areas to be used in fitting
            sum_areaff_dhw = sum(areas_ff_dhw_it)
            sum_areaff_other = sum(areas_ff_other_it)
            sum_areaff_cook = sum(areas_ff_cook_it)

            # Load monthly natural gas usage for the state
            natgas = ng_usage_data[clas][state]
            # Load annual fuel oil/kerosene and other gas/propane usage for the state
            fok = fok_usage_data.loc[state, f"fok.{clas}.mmbtu"]
            other = othergas_usage_data.loc[state, f"propane.{clas}.mmbtu"]
            totfuel = fok + other + natgas.sum()
            # Scale total fossil fuel usage by monthly natural gas
            ff_usage_data_it = totfuel * natgas / natgas.sum()
            # Fossil fuel average monthly mmbtu, normalized by hours in month
            ff_monthly_it = ff_usage_data_it / hours_in_month

            # Hourly heating degrees for all pumas in a given state, multiplied by their corresponding area and percent fossil fuel, summed up to one hourly list
            hd_hourly_it_sh = (
                temps_pumas_transpose.applymap(
                    lambda x: max(const.temp_ref[clas] - x, 0)
                )
                .mul(areas_ff_sh_it, axis=0)
                .sum(axis=0)
            )
            hd_monthly_it_sh = hd_hourly_it_sh.groupby(dti.month).mean()

            if clas == "res":
                hd_hourly_it_dhw = (
                    temps_pumas_transpose.applymap(lambda x: const.temp_ref[clas] - x)
                    .mul(areas_ff_dhw_it, axis=0)
                    .sum(axis=0)
                )
                hd_monthly_it_dhw = hd_hourly_it_dhw.groupby(dti.month).mean()

                # Fitting function: Returns difference between fitted equation and actual fossil fuel usage for the least_squares function to minimize
                def func_r(par, sh, dhw, ff):
                    err = hours_in_month ** (1 / 2) * (
                        ff
                        - (
                            par[0] * sh
                            + par[1] * (sum_areaff_dhw + const.dhw_lin_scalar * dhw)
                            + par[2] * sum_areaff_other
                        )
                    )
                    return err

                # Least squares solver
                lm_it = least_squares(
                    func_r,
                    const.bounds_lower_res,
                    args=(hd_monthly_it_sh, hd_monthly_it_dhw, ff_monthly_it),
                    bounds=(const.bounds_lower_res, const.bounds_upper_res),
                )

                # Solved coefficients for slopes and constants
                par_sh_l = lm_it.x[0]
                par_dhw_c = lm_it.x[1]
                par_dhw_l = lm_it.x[1] * const.dhw_lin_scalar
                par_other_c = lm_it.x[2]

                corrected_residuals = np.array(lm_it.fun) / hours_in_month ** (1 / 2)
                r2 = calculate_r2(ff_monthly_it, corrected_residuals)

                # Add coefficients to output dataframe
                df_i = len(state_slopes_res)
                state_slopes_res.loc[df_i] = [
                    state,
                    r2,
                    par_sh_l,
                    par_dhw_c,
                    par_dhw_l,
                    par_other_c,
                ]
            else:
                hd_hourly_it_other = (
                    temps_pumas_transpose.applymap(
                        lambda x: max(x - const.temp_ref[clas], 0)
                    )
                    .mul(areas_ff_other_it, axis=0)
                    .sum(axis=0)
                )
                hd_monthly_it_other = hd_hourly_it_other.groupby(dti.month).mean()

                bound_lower_consts_par = (
                    const.dhw_low_bound_com * sum_areaff_dhw
                    + const.cook_c_scalar * const.dhw_low_bound_com * sum_areaff_cook
                ) / (sum_areaff_dhw + sum_areaff_cook + sum_areaff_other)
                bound_upper_consts_par = (
                    const.dhw_high_bound_com * sum_areaff_dhw
                    + const.cook_c_scalar * const.dhw_high_bound_com * sum_areaff_cook
                    + const.other_high_bound_com * sum_areaff_other
                ) / (sum_areaff_dhw + sum_areaff_cook + sum_areaff_other)

                bounds_lower_com = [0, bound_lower_consts_par, 0]
                bounds_upper_com = [np.inf, bound_upper_consts_par, np.inf]

                # Fitting function: Returns difference between fitted equation and actual fossil fuel usage for the least_squares function to minimize
                def func_c(par, sh, other, ff):
                    err = hours_in_month ** (1 / 2) * (
                        ff
                        - (
                            par[0] * sh
                            + par[1]
                            * (sum_areaff_dhw + sum_areaff_cook + sum_areaff_other)
                            + par[2] * other
                        )
                    )
                    return err

                # Least squares solver
                lm_it = least_squares(
                    func_c,
                    bounds_lower_com,
                    args=(hd_monthly_it_sh, hd_monthly_it_other, ff_monthly_it),
                    bounds=(bounds_lower_com, bounds_upper_com),
                )

                # Solved dhw/cook/other constants
                consts_par = lm_it.x[1]

                bound_decision_point = (
                    consts_par
                    * (sum_areaff_dhw + sum_areaff_cook + sum_areaff_other)
                    / (sum_areaff_dhw + const.cook_c_scalar * sum_areaff_cook)
                )
                if bound_decision_point <= const.dhw_high_bound_com:
                    par_dhw_c = bound_decision_point
                    par_other_c = 0
                else:
                    par_dhw_c = const.dhw_high_bound_com
                    par_other_c = (
                        consts_par
                        * (sum_areaff_dhw + sum_areaff_cook + sum_areaff_other)
                        - (
                            const.dhw_high_bound_com * sum_areaff_dhw
                            + const.cook_c_scalar
                            * const.dhw_high_bound_com
                            * sum_areaff_cook
                        )
                    ) / sum_areaff_other

                par_cook_c = const.cook_c_scalar * par_dhw_c

                # Solved coefficients for slopes
                par_sh_l = lm_it.x[0]
                par_other_l = lm_it.x[2]

                corrected_residuals = np.array(lm_it.fun) / hours_in_month ** (1 / 2)
                r2 = calculate_r2(ff_monthly_it, corrected_residuals)

                # Add coefficients to output dataframe
                df_i = len(state_slopes_com)
                state_slopes_com.loc[df_i] = [
                    state,
                    r2,
                    par_sh_l,
                    par_dhw_c,
                    par_cook_c,
                    par_other_c,
                    par_other_l,
                ]

    # Export heating/hot water/cooking coefficients for each state
    return state_slopes_res, state_slopes_com


if __name__ == "__main__":
    year = 2010
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    state_slopes_res, state_slopes_com = calculate_state_slopes(const.puma_data, year)
    state_slopes_res.to_csv(
        os.path.join(data_dir, "state_slopes_ff_res.csv"), index=False
    )
    state_slopes_com.to_csv(
        os.path.join(data_dir, "state_slopes_ff_com.csv"), index=False
    )
    ##############################################
    # Space heating slope adjustment for climate #
    ##############################################

    puma_data = const.puma_data

    state_slopes_res.set_index("state", inplace=True)
    state_slopes_com.set_index("state", inplace=True)

    # Create data frames for space heating fossil fuel usage slopes at each PUMA
    puma_slopes_res = pd.DataFrame({"state": puma_data["state"]})
    puma_slopes_com = pd.DataFrame({"state": puma_data["state"]})

    res_state_htg_slope = []
    com_state_htg_slope = []
    for state in puma_data["state"]:
        res_state_htg_slope.append(state_slopes_res.loc[state, "sh_slope"])
        com_state_htg_slope.append(state_slopes_com.loc[state, "sh_slope"])

    puma_slopes_res["htg_slope_res_mmbtu_m2_degC"] = res_state_htg_slope
    puma_slopes_com["htg_slope_com_mmbtu_m2_degC"] = com_state_htg_slope

    for state in const.state_list:

        # Load puma temperatures
        temps_pumas = pd.read_csv(
            f"https://besciences.blob.core.windows.net/datasets/pumas/temps_pumas_{state}_{year}.csv"
        )
        temps_pumas_transpose = temps_pumas.T

        # Hourly temperature difference below const.temp_ref_res/com for each puma
        temp_diff_res = temps_pumas_transpose.applymap(
            lambda x: max(const.temp_ref[("res")] - x, 0)
        ).T
        temp_diff_com = temps_pumas_transpose.applymap(
            lambda x: max(const.temp_ref[("com")] - x, 0)
        ).T

        puma_data.loc[temp_diff_res.columns, "hd_183C_2010"] = temp_diff_res.sum()
        puma_data.loc[temp_diff_com.columns, "hd_167C_2010"] = temp_diff_com.sum()

    # Load in state groups consistent with building area scale adjustments
    area_scale_res = pd.read_csv(
        os.path.join(data_dir, "area_scale_res.csv"), index_col=False
    )
    area_scale_com = pd.read_csv(
        os.path.join(data_dir, "area_scale_com.csv"), index_col=False
    )

    # Extract res state groups from area_scale_res
    res_state_rows = area_scale_res.values.tolist()
    res_state_groups = [
        [elem for elem in row if isinstance(elem, str)] for row in res_state_rows
    ]

    # Extract com state groups from area_scale_com
    com_state_rows = area_scale_com.values.tolist()
    com_state_groups = [
        [elem for elem in row if isinstance(elem, str)] for row in com_state_rows
    ]

    hdd65listres = []
    htgslppoplistres = []
    for res_state_group in res_state_groups:
        # res state group subset of data
        pumas_it = puma_data[puma_data["state"].isin(res_state_group)]
        puma_slopes_res_it = puma_slopes_res[
            puma_slopes_res["state"].isin(res_state_group)
        ]
        # Population weighted heating degree days
        hdd65listres.append(
            sum(pumas_it["hdd65_normals_2010"] * pumas_it["pop_2010"])
            / sum(pumas_it["pop_2010"])
        )
        # Population and heating degree day weighted heating slopes
        htgslppoplistres.append(
            sum(
                puma_slopes_res_it["htg_slope_res_mmbtu_m2_degC"]
                * pumas_it["hdd65_normals_2010"]
                * pumas_it["pop_2010"]
            )
            / sum(pumas_it["hdd65_normals_2010"] * pumas_it["pop_2010"])
        )

    area_scale_res["hdd_normals_2010_popwtd"] = hdd65listres
    area_scale_res["htg_slope_res_mmbtu_m2_degC_pophddwtd"] = htgslppoplistres

    hdd65listcom = []
    htgslppoplistcom = []
    for com_state_group in com_state_groups:
        # com state group subset of data
        pumas_it = puma_data[puma_data["state"].isin(com_state_group)]
        puma_slopes_com_it = puma_slopes_com[
            puma_slopes_com["state"].isin(com_state_group)
        ]
        # Population weighted heating degree days
        hdd65listcom.append(
            sum(pumas_it["hdd65_normals_2010"] * pumas_it["pop_2010"])
            / sum(pumas_it["pop_2010"])
        )
        # Population and heating degree day weighted heating slopes
        htgslppoplistcom.append(
            sum(
                puma_slopes_com_it["htg_slope_com_mmbtu_m2_degC"]
                * pumas_it["hdd65_normals_2010"]
                * pumas_it["pop_2010"]
            )
            / sum(pumas_it["hdd65_normals_2010"] * pumas_it["pop_2010"])
        )

    area_scale_com["hdd_normals_2010_popwtd"] = hdd65listcom
    area_scale_com["htg_slope_com_mmbtu_m2_degC_pophddwtd"] = htgslppoplistcom

    # Interpolating 2010 areas from the two survey years provided
    area_scale_res["2010_RECS"] = (
        area_scale_res["RECS2009"]
        + (area_scale_res["RECS2015"] - area_scale_res["RECS2009"]) / 6
    )
    area_scale_com["2010_CBECS"] = area_scale_com["CBECS2012"] - (
        area_scale_com["CBECS2012"] - area_scale_com["CBECS2003"]
    ) * (2 / 9)

    # Divide by 1000 for robust solver
    area_scale_res["hdd_normals_2010_popwtd_div1000"] = (
        area_scale_res["hdd_normals_2010_popwtd"] / 1000
    )
    area_scale_com["hdd_normals_2010_popwtd_div1000"] = (
        area_scale_com["hdd_normals_2010_popwtd"] / 1000
    )

    # Minimize error between actual slopes and fitted function
    # Note for fitting to converge, hdd must be divided by 1000 and slopes in btu
    def model(par, hdd_div1000, slope_btu):
        err = (
            slope_btu
            - (par[0] + par[1] * (1 - np.exp(-par[2] * hdd_div1000))) / hdd_div1000
        )
        return err

    # Least_squares residential model, to solve slope = (a + b*(1 - exp(-c*hdd)))/hdd
    ls_res = least_squares(
        model,
        [35, 35, 0.8],
        args=(
            np.array(area_scale_res["hdd_normals_2010_popwtd_div1000"]),
            np.array(area_scale_res["htg_slope_res_mmbtu_m2_degC_pophddwtd"]) * 10 ** 6,
        ),
        method="trf",
        loss="soft_l1",
        f_scale=0.1,
        bounds=(0, [100, 100, 1]),
    )
    # Residential coefficients output from least squares fit
    a_model_slope_res_exp = ls_res.x[0]
    b_model_slope_res_exp = ls_res.x[1]
    c_model_slope_res_exp = ls_res.x[2]

    # Least_squares commercial model, to solve slope = (a + b*(1 - exp(-c*hdd)))/hdd
    ls_com = least_squares(
        model,
        [35, 35, 0.8],
        args=(
            np.array(area_scale_com["hdd_normals_2010_popwtd_div1000"]),
            np.array(area_scale_com["htg_slope_com_mmbtu_m2_degC_pophddwtd"]) * 10 ** 6,
        ),
        method="trf",
        loss="soft_l1",
        f_scale=0.1,
        bounds=(0, [100, 100, 1]),
    )
    # Commercial coefficients output from least squares fit
    a_model_slope_com_exp = ls_com.x[0]
    b_model_slope_com_exp = ls_com.x[1]
    c_model_slope_com_exp = ls_com.x[2]

    # Functions with solved coefficients for res and com - produces slopes in btu/m2-C for inputs of HDD
    def func_slope_res_exp(x):
        return (
            (
                a_model_slope_res_exp
                + b_model_slope_res_exp
                * (1 - np.exp(-c_model_slope_res_exp * (x / 1000)))
            )
            / (x / 1000)
        ) * 10 ** (-6)

    def func_slope_com_exp(x):
        return (
            (
                a_model_slope_com_exp
                + b_model_slope_com_exp
                * (1 - np.exp(-c_model_slope_com_exp * (x / 1000)))
            )
            / (x / 1000)
        ) * 10 ** (-6)

    adj_slopes_res = pd.DataFrame({"state": puma_data["state"]})

    adj_slopes_com = pd.DataFrame({"state": puma_data["state"]})

    slope_scalar_res = state_slopes_res["sh_slope"] / (
        (
            puma_data["hdd65_normals_2010"].map(func_slope_res_exp)
            * puma_data["hd_183C_2010"]
            * puma_data["res_area_2010_m2"]
            * puma_data["frac_ff_sh_res_2010"]
        )
        .groupby(puma_data["state"])
        .sum()
        / (
            puma_data["hd_183C_2010"]
            * puma_data["res_area_2010_m2"]
            * puma_data["frac_ff_sh_res_2010"]
        )
        .groupby(puma_data["state"])
        .sum()
    )

    adj_slopes_res["htg_slope_res_mmbtu_m2_degC"] = puma_data["hdd65_normals_2010"].map(
        func_slope_res_exp
    ) * puma_data["state"].map(slope_scalar_res)

    slope_scalar_com = state_slopes_com["sh_slope"] / (
        (
            puma_data["hdd65_normals_2010"].map(func_slope_com_exp)
            * puma_data["hd_167C_2010"]
            * puma_data["com_area_2010_m2"]
            * puma_data["frac_ff_sh_com_2010"]
        )
        .groupby(puma_data["state"])
        .sum()
        / (
            puma_data["hd_167C_2010"]
            * puma_data["com_area_2010_m2"]
            * puma_data["frac_ff_sh_com_2010"]
        )
        .groupby(puma_data["state"])
        .sum()
    )

    adj_slopes_com["htg_slope_com_mmbtu_m2_degC"] = puma_data["hdd65_normals_2010"].map(
        func_slope_com_exp
    ) * puma_data["state"].map(slope_scalar_com)

    # Export climate adjusted space heating slopes of each puma
    adj_slopes_res.to_csv(os.path.join(data_dir, "puma_slopes_ff_res.csv"))
    adj_slopes_com.to_csv(os.path.join(data_dir, "puma_slopes_ff_com.csv"))

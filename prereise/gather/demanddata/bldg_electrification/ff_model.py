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


def calculate_state_slopes(puma_data, year=2010):
    """Estimate regression parameters per-state for residential and commercial fuel use.

    :param pandas.DataFrame puma_data: data frame of per-puma data.
    :param int/str year: year of data to use for analysis.
    :return: (*tuple*) -- a pair of pandas.DataFrame objects for per-state residential
        and commercial slopes, respectively.
    """
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


def adjust_puma_slopes(puma_data, state_slopes_res, state_slopes_com, year=2010):
    """Create per-puma slopes from per-state slopes.

    :param pandas.DataFrame puma_data: puma data.
    :param pandas.DataFrame state_slopes_res: residential state slopes.
    :param pandas.DataFrame state_slopes_com: commercial state slopes.
    :param int year: year of temperatures to download.
    :return: (*tuple*) -- a pair of pandas.DataFrame objects for per-puma residential
        and commercial slopes, respectively.
    """
    # Minimize error between actual slopes and fitted function
    # Note for fitting to converge, hdd must be divided by 1000 and slopes in btu
    def model(par, hdd_div1000, slope_btu):
        err = (
            slope_btu
            - (par[0] + par[1] * (1 - np.exp(-par[2] * hdd_div1000))) / hdd_div1000
        )
        return err

    # Functions with solved coefficients for res and com - produces slopes in btu/m2-C for inputs of HDD
    def func_slope_exp(x, a, b, c):
        return (a + b * (1 - np.exp(-c * (x / 1000))) / (x / 1000)) * 1e-6

    classes = ["res", "com"]
    hd_col_names = {"res": "hd_183C_2010", "com": "hd_167C_2010"}
    state_slopes = {
        "res": state_slopes_res.set_index("state"),
        "com": state_slopes_com.set_index("state"),
    }
    puma_slopes = {clas: puma_data["state"].to_frame() for clas in classes}
    # Create data frames to hold output
    adj_slopes = {clas: puma_data["state"].to_frame() for clas in classes}

    for state in const.state_list:
        # Load puma temperatures
        temps_pumas = pd.read_csv(
            f"https://besciences.blob.core.windows.net/datasets/pumas/temps_pumas_{state}_{year}.csv"
        )
        # Hourly temperature difference below const.temp_ref_res/com for each puma
        for clas in classes:
            temp_diff = temps_pumas.applymap(lambda x: max(const.temp_ref[clas] - x, 0))
            puma_data.loc[temp_diff.columns, hd_col_names[clas]] = temp_diff.sum()

    # Load in state groups consistent with building area scale adjustments
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    area_scale = {
        clas: pd.read_csv(
            os.path.join(data_dir, f"area_scale_{clas}.csv"), index_col=False
        )
        for clas in classes
    }

    # Interpolating 2010 areas from the two survey years provided
    area_scale["res"]["2010"] = (
        area_scale["res"]["RECS2009"]
        + (area_scale["res"]["RECS2015"] - area_scale["res"]["RECS2009"]) / 6
    )
    area_scale["com"]["2010"] = area_scale["com"]["CBECS2012"] - (
        area_scale["com"]["CBECS2012"] - area_scale["com"]["CBECS2003"]
    ) * (2 / 9)

    for clas in classes:
        puma_slopes[clas]["htg_slope_mmbtu_m2_degC"] = puma_data["state"].map(
            state_slopes[clas]["sh_slope"]
        )

        # Extract state groups from area_scale
        state_to_group = {
            elem: i
            for i, row in area_scale[clas].iterrows()
            for elem in row
            if isinstance(elem, str)
        }

        # Calculate population-weighted HDD and slopes
        state_puma_groupby = puma_data.groupby(puma_data["state"].map(state_to_group))
        state_puma_slope_groupby = puma_slopes[clas].groupby(
            puma_data["state"].map(state_to_group)
        )
        area_scale[clas]["hdd_normals_2010_popwtd"] = [
            (
                sum(data["hdd65_normals_2010"] * data["pop_2010"])
                / data["pop_2010"].sum()
            )
            for group, data in state_puma_groupby
        ]
        area_scale[clas]["htg_slope_mmbtu_m2_degC_pophddwtd"] = [
            sum(
                state_puma_slope_groupby.get_group(group)["htg_slope_mmbtu_m2_degC"]
                * data["hdd65_normals_2010"]
                * data["pop_2010"]
            )
            / sum(data["hdd65_normals_2010"] * data["pop_2010"])
            for group, data in state_puma_groupby
        ]

        ls_args = (
            # Divide by 1000 for robust solver
            np.array(area_scale[clas]["hdd_normals_2010_popwtd"]) / 1000,
            np.array(area_scale[clas]["htg_slope_mmbtu_m2_degC_pophddwtd"]) * 10 ** 6,
        )
        ls = least_squares(
            model,
            [35, 35, 0.8],
            args=ls_args,
            method="trf",
            loss="soft_l1",
            f_scale=0.1,
            bounds=(0, [100, 100, 1]),
        )

        slope_scalar = state_slopes[clas]["sh_slope"] / (
            (
                puma_data["hdd65_normals_2010"].apply(
                    func_slope_exp, args=(ls.x[0], ls.x[1], ls.x[2])
                )
                * puma_data[hd_col_names[clas]]
                * puma_data[f"{clas}_area_2010_m2"]
                * puma_data[f"frac_ff_sh_{clas}_2010"]
            )
            .groupby(puma_data["state"])
            .sum()
            / (
                puma_data[hd_col_names[clas]]
                * puma_data[f"{clas}_area_2010_m2"]
                * puma_data[f"frac_ff_sh_{clas}_2010"]
            )
            .groupby(puma_data["state"])
            .sum()
        )

        adj_slopes[clas][f"htg_slope_{clas}_mmbtu_m2_degC"] = puma_data["state"].map(
            slope_scalar
        ) * puma_data["hdd65_normals_2010"].apply(
            func_slope_exp, args=(ls.x[0], ls.x[1], ls.x[2])
        )

    return adj_slopes["res"], adj_slopes["com"]


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    # Calculate and save state slopes
    state_slopes_res, state_slopes_com = calculate_state_slopes(const.puma_data)
    state_slopes_res.to_csv(
        os.path.join(data_dir, "state_slopes_ff_res.csv"), index=False
    )
    state_slopes_com.to_csv(
        os.path.join(data_dir, "state_slopes_ff_com.csv"), index=False
    )

    # Calculate and save puma slopes
    adj_slopes_res, adj_slopes_com = adjust_puma_slopes(
        const.puma_data, state_slopes_res, state_slopes_com
    )
    adj_slopes_res.to_csv(os.path.join(data_dir, "puma_slopes_ff_res.csv"))
    adj_slopes_com.to_csv(os.path.join(data_dir, "puma_slopes_ff_com.csv"))

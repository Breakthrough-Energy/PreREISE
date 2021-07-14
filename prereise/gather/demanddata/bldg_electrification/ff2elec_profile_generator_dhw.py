import os

import numpy as np
import pandas as pd

from prereise.gather.demanddata.bldg_electrification import const


def func_dhw_cop(temp_c, model):
    """Generate COPs for input hourly temperatures with a given heat pump model
    :param list temp_c: hourly temperatures
    :param str model : type of heat pump
    :return list cop: Coefficient of performance list
    """
    cop_base = [0] * len(temp_c)

    model_params = const.hp_param_dhw.set_index("model").loc[model]
    t_low = model_params.loc["t_low"]
    t_cp = model_params.loc["t_cp"]
    t_high = model_params.loc["t_high"]
    cop_er = model_params.loc["cop_er"]
    cop_low = model_params.loc["cop_low"]
    cop_cp = model_params.loc["cop_cp"]
    cop_high = model_params.loc["cop_high"]

    for i in range(len(temp_c)):
        if temp_c[i] <= t_cp:
            cop_base[i] = ((temp_c[i] - t_low) / (t_cp - t_low)) * (
                cop_cp - cop_low
            ) + cop_low
        else:
            cop_base[i] = ((temp_c[i] - t_cp) / (t_high - t_cp)) * (
                cop_high - cop_cp
            ) + cop_cp

    cop = [max(c, cop_er) for c in cop_base]

    return cop


# Create folder for output profiles
os.makedirs("Profiles", exist_ok=True)


def generate_profiles(yr_temps=2016, bldg_class="res", hp_model="advperfhp"):
    """Create time series for electricity loads from converting fossil fuel
    water heating to heat pump water heaters

    :param int yr_temps: year for temperature. Default is 2016.
    :param str bldg_class: type of building. Default is residential.
    :param str hp_model: type of heat pump. Default is advanced performance cold
        climate heat pump.
    :raises TypeError:
        if ``yr_temps`` is not an int.
        if ``bldg_class`` and ``hp_model`` are not str.
    :raises ValueError:
        if ``bldg_class`` is not 'res' or 'com'
        if ``hp_model`` is not 'advperfhp', 'midperfhp' or 'futurehp'
    """
    if not isinstance(yr_temps, int):
        raise TypeError("yr_temps must be an int")
    if not isinstance(bldg_class, str):
        raise TypeError("bldg_class must be a str")
    if not isinstance(hp_model, str):
        raise TypeError("hp_model must be a str")

    if yr_temps not in const.yr_temps_all:
        raise ValueError(
            "yr_temps must be among available temperature years: {const.yr_temps_first}-{const.yr_temps_last}"
        )
    if bldg_class not in ["res", "com"]:
        raise ValueError(
            "bldg_class must be one of: \n", "res: residential \n", "com: commercial"
        )
    if hp_model not in ["advperfhp", "midperfhp", "futurehp"]:
        raise ValueError(
            "hp_model must be one of: \n",
            "midperfhp: mid-performance cold climate heat pump \n",
            "advperfhp: advanced performance cold climate heat pump \n",
            "futurehp: future performance heat pump",
        )

    # parse user data
    temp_ref_it = const.temp_ref_com if bldg_class == "com" else const.temp_ref_res
    dhw_mult = const.dhw_com_mult if bldg_class == "com" else const.dhw_res_mult

    dir_path = os.path.dirname(os.path.abspath(__file__))

    state_slopes = pd.read_csv(
        os.path.join(dir_path, "data", f"state_slopes_ff_{bldg_class}.csv"),
        index_col="state",
    )

    # Loop through states to create profile outputs
    for state in const.state_list:

        # Load and subset relevant data for the state
        puma_data_it = const.puma_data.query("state == @state")

        temps_pumas_it = pd.read_csv(
            f"https://besciences.blob.core.windows.net/datasets/pumas/temps_pumas_{state}_{yr_temps}.csv"
        )

        hours = pd.date_range(
            f"{yr_temps}-01-01", periods=len(temps_pumas_it), freq="H", tz="UTC"
        )

        # Load DHW constant and slope for state_it
        dhw_const_mmbtu_m2 = state_slopes.loc[state, "dhw_const"]

        dhw_slope_mmbtu_m2_degC = (  # noqa: N806
            state_slopes.loc[state, "dhw_slope"] if bldg_class == "res" else 0
        )

        # Based on the timezone for each PUMA, the dhw multiplier list is arranged to match local time
        dhw_mult_df = puma_data_it.apply(
            lambda x: pd.Series(
                hours.tz_convert(x.timezone).hour.map(lambda y: dhw_mult[y])
            ),
            axis=1,
        )

        temps_pumas_transpose_it = temps_pumas_it.T

        temp_dev_from_ref_degC = temps_pumas_transpose_it.applymap(  # noqa: N806
            lambda x: temp_ref_it - x
        )
        cop_inverse = temps_pumas_transpose_it.apply(
            lambda x: np.reciprocal(func_dhw_cop(x, hp_model)), 1
        )

        cop_list_df = pd.DataFrame(
            cop_inverse.to_list(), list(temp_dev_from_ref_degC.index)
        )

        temp_dev_from_ref_degC_slope = (  # noqa: N806
            temp_dev_from_ref_degC * dhw_slope_mmbtu_m2_degC
            + dhw_const_mmbtu_m2  # noqa: N806
        )

        temp_dev_cop = (
            temp_dev_from_ref_degC_slope.multiply(cop_list_df) * const.eff_dhw_ff_base
        )  # mmbtu-heat pump electricity load per m2 for 100% of puma floor area

        temp_dev_cop *= dhw_mult_df

        ff_area_scalars = list(
            puma_data_it["{}_area_2010_m2".format(bldg_class)]
            * puma_data_it["frac_ff_dhw_{}_2010".format(bldg_class)]
            * (const.conv_mmbtu_to_kwh * const.conv_kw_to_mw)
        )

        elec_dhw_ff2hp_puma_mw_it = temp_dev_cop.mul(ff_area_scalars, axis=0).T
        elec_dhw_ff2hp_puma_mw_it.columns = temps_pumas_it.columns

        # Export profile file as CSV
        elec_dhw_ff2hp_puma_mw_it.to_csv(
            os.path.join(
                "Profiles",
                f"elec_dhw_ff2hp_{bldg_class}_{state}_{yr_temps}_{hp_model}_mw.csv",
            ),
            index=False,
        )

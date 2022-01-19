# Import libraries
import os

import pandas as pd

from prereise.gather.demanddata.bldg_electrification import const


def generate_profiles(yr_temps=2016, bldg_class="res", efficiency="high"):
    """This script returns hourly electricity loads from converting
    fossil fuel cooking to electric cooking

    :param int yr_temps: year for temperature. Default is 2016.
    :param str bldg_class: type of building. Default is residential.
    :param str efficiency: efficiency of cooking. Default is high.
    :raises TypeError:
        if ``yr_temps`` is not an int.
        if ``bldg_class`` and ``efficiency`` are not str.
    :raises ValueError:
        if ``bldg_class`` is not 'res' or 'com'
        if ``efficiency`` is not 'high' or 'low'
    """
    if not isinstance(yr_temps, int):
        raise TypeError("yr_temps must be an int")
    if not isinstance(bldg_class, str):
        raise TypeError("bldg_class must be a str")
    if not isinstance(efficiency, str):
        raise TypeError("efficiency must be a str")

    if yr_temps not in const.yr_temps_all:
        raise ValueError(
            "yr_temps must be among available temperature years: {const.yr_temps_first}-{const.yr_temps_last}"
        )
    if bldg_class not in ["res", "com"]:
        raise ValueError(
            "bldg_class must be one of: \n", "res: residential \n", "com: commercial"
        )
    if efficiency not in ["high", "low"]:
        raise ValueError(
            "efficiency must be one of: \n",
            "high: High cooking efficiency \n",
            "low: Low cooking efficiency \n",
        )

    dir_path = os.path.dirname(os.path.abspath(__file__))
    state_slopes = pd.read_csv(
        os.path.join(dir_path, "data", f"state_slopes_ff_{bldg_class}.csv"),
        index_col="state",
    )

    cook_other = "cook" if bldg_class == "com" else "other"

    # Make directory for output profiles
    os.makedirs("Profiles", exist_ok=True)

    # Loop through states to create profile outputs
    for state in const.state_list:

        # Load and subset relevant data for the state
        puma_data_it = const.puma_data[const.puma_data["state"] == state]

        # Load cook constant for state_it
        cook_const_mmbtu_m2 = state_slopes.loc[state, f"{cook_other}_const"]

        # Area * frac_ff * efficiency * cook_const * unit conv
        cook_elec = (
            puma_data_it[f"{bldg_class}_area_{const.base_year}_m2"]
            * puma_data_it[f"frac_ff_{cook_other}_{bldg_class}_{const.base_year}"]
            * (const.conv_mmbtu_to_kwh / 1000)
            * cook_const_mmbtu_m2
            * const.cooking_multiplier[(bldg_class, efficiency)]
        )

        # Export profile file as CSV
        cook_elec.to_csv(
            os.path.join(
                "Profiles",
                f"elec_cook_ff2hp_{bldg_class}_{state}_{yr_temps}_{efficiency}_mw.csv",
            )
        )

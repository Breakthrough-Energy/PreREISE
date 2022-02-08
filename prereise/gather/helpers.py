import os

import numpy as np
import pandas as pd

from prereise.gather.const import abv2state


def trim_eia_form_923(filename):
    """Remove columns in EIA form 923 that are unnecessary to calculate the
    monthly generation per resource as performed by
    :py:func:`get_monthly_net_generation`.

    :param str filename: name of the reference file.
    :return: (*pandas.DataFrame*) -- EIA form 923 with only relevant columns.
    """
    filedir = os.path.join(os.path.dirname(__file__), "data")
    eia_form_923 = pd.read_excel(
        io=os.path.join(filedir, filename),
        header=0,
        usecols="A,D,G,I,P,CB:CM",
        skiprows=range(5),
    )
    return eia_form_923


def get_monthly_net_generation(state, eia_form_923, resource, hps=True):
    """Return monthly total net generation for a given resource and state from
    EIA form 923.

    :param str state: state abbreviation.
    :param pandas.DataFrame eia_form_923: EIA form 923. The reduced form as
        returned by :py:func:`trim_eia_form_923` can be used.
    :param str resource: type of generator.
    :param bool hps: determine whether pumped hydro storage is included in
        the result if resource is *'hydro'*.
    :return: (*list*) -- monthly net generation of the query fuel type
        in state.
    :raises TypeError: if eia_form_923 is not a data frame
        or resource is not a str.
    :raises ValueError: if state or resource is invalid.
    """
    if not isinstance(state, str):
        raise TypeError("state must be a str")
    if not isinstance(eia_form_923, pd.DataFrame):
        raise TypeError("eia_form_923 must be a pandas.DataFrame")
    if not isinstance(resource, str):
        raise TypeError("resource must be a str")

    if state not in abv2state:
        raise ValueError(
            "Invalid state. Possible states are %s" % " | ".join(set(abv2state))
        )

    all_resource = {
        "solar": {"SUN"},
        "coal": {"COL"},
        "dfo": {"DFO"},
        "geothermal": {"GEO"},
        "hydro": {
            "HYC",
            "HPS",
        },  # Hydroelectric Conventional, Hydroelectric Pumped Storage
        "ng": {"NG"},
        "nuclear": {"NUC"},
        "wind": {"WND"},
    }

    if resource not in all_resource.keys():
        raise ValueError(
            "Invalid resource. Possible resources are %s"
            % " | ".join(all_resource.keys())
        )

    if resource == "hydro" and not hps:
        all_resource["hydro"].remove("HPS")

    # Filter by state and fuel type
    net_generation_by_plant = eia_form_923[
        (eia_form_923["Plant State"] == state)
        & (eia_form_923["AER\nFuel Type Code"].isin(all_resource[resource]))
    ].copy()

    # Drop unnecessary columns, plant ID, etc..
    net_generation = net_generation_by_plant.drop(
        net_generation_by_plant.columns[[0, 1, 2, 3, 4]], axis=1
    )
    net_generation = net_generation.replace(".", 0)

    # Get monthly total net generation by summing up across plants
    # with all positive values. Note that negative ones are included in
    # actual demand.
    eia_net_generation = list(net_generation.apply(lambda x: x[x > 0].sum()).values)

    # If there is no such generator in the state, the function will return
    # a list of 0 instead of NaN.
    eia_net_generation = list(np.nan_to_num(eia_net_generation))

    return eia_net_generation

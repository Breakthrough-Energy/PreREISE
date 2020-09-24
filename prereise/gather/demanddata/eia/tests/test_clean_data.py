from random import random

import numpy as np
import pandas as pd

from prereise.gather.demanddata.eia.clean_data import slope_interpolate


def test_slope_interpolate():
    # Create a list of data that approximates a sin curve with some randomness
    # then manually change two numbers to be outliers
    demand_list = [5 + random() * np.sin(np.pi * i / 8) for i in range(1000)]
    demand_list[4] = 40
    demand_list[100] = 120
    ba_dict = {i: {"ba": demand} for i, demand in enumerate(demand_list)}

    ba = pd.DataFrame(ba_dict).T
    result = slope_interpolate(ba)
    r_dict = result["ba"].T.to_dict()

    assert r_dict[4] == (r_dict[3] + r_dict[5]) / 2
    assert r_dict[100] == (r_dict[99] + r_dict[101]) / 2

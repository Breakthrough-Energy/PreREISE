import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from prereise.gather.demanddata.eia import find_fix_outliers 


def test_slope_interpolate():
    """
    Test outlier detection and replacement method.
    Test checks that there are 4 changed outliers
    for the input test set and threshold.
    """

    dir1 = os.path.join(os.path.dirname(__file__), 'data')
    BA = pd.read_csv(dir1 + "/" + 'BA_2016.csv', index_col='UTC Time',
            parse_dates=True )
    orig_fall = BA['PSCO'].to_frame().copy()

    threshold = 3
    fixed = find_fix_outliers.slope_interpolate(orig_fall, threshold)
    fixed.rename(columns ={'PSCO':'PSCO3'}, inplace = True)
    
    combine = pd.concat([orig_fall, fixed], axis =1)
    assert (len(combine.loc[combine['PSCO'] != combine['PSCO3']]) == 4)

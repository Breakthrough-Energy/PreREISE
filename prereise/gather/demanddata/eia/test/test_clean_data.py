import os

import pandas as pd

from prereise.gather.demanddata.eia.clean_data import slope_interpolate


def test_slope_interpolate():
    """Test outlier detection and replacement method. Check that there are four
        changed outliers for the input test set and threshold.
    """

    dir1 = os.path.join(os.path.dirname(__file__), 'data')
    ba = pd.read_csv(dir1 + "/" + 'BA_2016.csv', index_col='UTC Time',
                     parse_dates=True)
    orig_fall = ba['PSCO'].to_frame().copy()

    fixed = slope_interpolate(orig_fall)
    fixed.rename(columns={'PSCO': 'PSCO3'}, inplace=True)

    combine = pd.concat([orig_fall, fixed], axis=1)
    assert (len(combine.loc[combine['PSCO'] != combine['PSCO3']]) == 4)

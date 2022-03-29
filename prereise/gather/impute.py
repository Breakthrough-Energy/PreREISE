import pandas as pd


def linear(data, inplace=True):
    """Given a 2D array, linearly interpolate any missing values column-wise.

    :param numpy.array/pandas.DataFrame data: data to interpolate.
    :param bool inplace: whether to modify the data inplace or return a modified copy.
    :return: (*None/pandas.DataFrame*) -- if ``inplace`` is False, data frame with
        missing entries imputed.
    """
    data_impute = data if inplace else data.copy()
    data_impute[:] = pd.DataFrame(data_impute).interpolate()
    if not inplace:
        return data_impute

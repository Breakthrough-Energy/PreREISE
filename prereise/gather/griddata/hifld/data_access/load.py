import pandas as pd


def load_csv(csv_filename, dtypes=None):
    if dtypes:
        data = pd.read_csv(csv_filename, dtype=dtypes)
    else:
        data = pd.read_csv(csv_filename)

    return data

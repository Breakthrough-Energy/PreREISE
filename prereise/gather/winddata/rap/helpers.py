import pandas as pd


def to_reise(data):
    """Format data for REISE.

    :param pandas.DataFrame data: data frame as returned by
        :func:`prereise.gather.winddata.rap.rap.retrieve_data`.
    :return: (*pandas.DataFrame*) -- data frame formatted for REISE.
    """
    ts = data["ts"].unique()
    plant_id = data[data.ts_id == 1].plant_id.values

    profile = None
    for i in range(1, max(data.ts_id) + 1):
        data_tmp = pd.DataFrame(
            {"Pout": data[data.ts_id == i].Pout.values}, index=plant_id
        )
        if i == 1:
            profile = data_tmp.T
        else:
            profile = profile.append(data_tmp.T, sort=False, ignore_index=True)

    profile.set_index(ts, inplace=True)
    profile.index.name = "UTC"

    return profile

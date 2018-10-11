import pandas as pd


def to_reise(data):
    """Format data for REISE.

    :param data: pandas DataFrame as returned by py:method:`rap.retrieve_data`.
    :return: pandas DataFrame formated for REISE.
    """
    ts = data['ts'].unique()
    plantID = data[data.tsID == 1].plantID.values

    for i in range(1, max(data.tsID)+1):
        data_tmp = pd.DataFrame({'Pout': data[data.tsID == i].Pout.values},
                                index=plantID)
        if i == 1:
            dataT = data_tmp.T
        else:
            dataT = dataT.append(data_tmp.T, sort=False, ignore_index=True)

    dataT.set_index(ts, inplace=True)
    dataT.index.name = 'UTC'

    return dataT

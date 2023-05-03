import os
import tarfile
import urllib.request
import zipfile

import numpy as np
import pandas as pd


def cleanup_directory(root):
    """Recursively cleanup a folder by deleting meaningless or empty files

    :param str root: the root directory containing raw de-compressed DOE flexibility data
    """

    all_files = os.listdir(root)
    for i in all_files:
        fp = os.path.join(root, i)
        if i[0] == "." or (i[-3:] == "csv" and os.path.getsize(fp) < 0.01):
            os.remove(fp)

    all_folders = os.listdir(root)
    for i in all_folders:
        if os.path.isdir(os.path.join(root, i)):
            cleanup_directory(os.path.join(root, i))


def download_doe(download_path="data"):
    """Download demand flexibility filters from OEDI, extract and cleanup

    :param str download_path: the directory where the original DOE data will be stored
    """

    # create data directory
    os.makedirs(download_path, exist_ok=True)

    # download zip data
    oedi_filter_link = (
        "https://data.openei.org/files/180/2006weatherentireusdrfilters.tar.zip"
    )
    urllib.request.urlretrieve(
        oedi_filter_link, os.path.join(download_path, "filter.zip")
    )

    # extract
    with zipfile.ZipFile(os.path.join(download_path, "filter.zip"), "r") as fh:
        fh.extractall(download_path)

    # delete and further extract
    os.remove(os.path.join(download_path, "filter.zip"))

    for f in os.listdir(download_path):
        with tarfile.open(os.path.join(download_path, f), "r:gz") as fh:
            fh.extractall(download_path)
        os.remove(os.path.join(download_path, f))

    # cleanup
    cleanup_directory(download_path)


def aggregate_doe(root, out_path):
    """Aggregate sector flexibilties by summing up the percentage flexibility from all sectors
    and store to output csv file

    :param str root: the root directory containing raw de-compressed DOE flexibility data
    :param str out_path: the output file where the aggregated data will be stored
    """

    all_folders = os.listdir(root)

    # initialize output container
    eia_flex = pd.DataFrame(np.zeros((8808, len(all_folders))), columns=all_folders)

    for i in all_folders:
        all_csvs = os.listdir(os.path.join(root, i))

        # new column for total flexibility
        file_flex = pd.read_csv(os.path.join(root, i, all_csvs[0]), index_col=0)

        # assign index to the output df
        if "time" not in eia_flex.keys():
            eia_flex["time"] = pd.to_datetime(file_flex.index.copy())
            eia_flex.set_index("time", inplace=True)

        eia_flex[i] = eia_flex[i] + file_flex["Flexibility"].values

        for c in all_csvs[1:]:
            fn = os.path.join(root, i, c)
            file_flex = pd.read_csv(fn, index_col=0)

            if file_flex.shape[0] == eia_flex.shape[0]:
                eia_flex[i] = eia_flex[i] + file_flex["Flexibility"].values
            else:
                eia_flex[i] = eia_flex[i].add(file_flex["Flexibility"], fill_value=0)

    eia_flex = eia_flex.round(4)
    eia_flex.to_csv(out_path)

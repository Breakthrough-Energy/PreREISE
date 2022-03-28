import os
import pickle as pkl
import urllib.request

import numpy as np
import pandas as pd


def get_census_data(download_path):
    """Download county population data from USA Census website

    :param str download_path: folder to store the downloaded file
    """

    os.makedirs(download_path, exist_ok=True)
    census_file_link = "https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/co-est2020-alldata.csv"
    urllib.request.urlretrieve(
        census_file_link, os.path.join(download_path, "county_population.csv")
    )


def get_crosswalk_data(download_path):
    """Download FIPS-ZIP crosswalk data from USPS and convert to csv

    :param str download_path: folder to store the downloaded file
    """

    # download
    os.makedirs(download_path, exist_ok=True)
    usps_file_link = (
        "https://www.huduser.gov/portal/datasets/usps/COUNTY_ZIP_122021.xlsx"
    )
    urllib.request.urlretrieve(
        usps_file_link, os.path.join(download_path, "county_to_zip.xlsx")
    )

    # convert to csv
    usps_df = pd.read_excel(os.path.join(download_path, "county_to_zip.xlsx"))
    usps_df = usps_df.sort_values(by=["county", "zip"])
    usps_df.to_csv(os.path.join(download_path, "county_to_zip.csv"), index=False)
    os.remove(os.path.join(download_path, "county_to_zip.xlsx"))


def get_lse_region_data(download_path):
    """Download LSE service region data

    :param str download_path: folder to store the downloaded file
    """

    os.makedirs(download_path, exist_ok=True)
    iou_file_link = "https://data.openei.org/files/4042/iou_zipcodes_2019.csv"
    niou_file_link = "https://data.openei.org/files/4042/non_iou_zipcodes_2019.csv"

    urllib.request.urlretrieve(
        iou_file_link, os.path.join(download_path, "iou_zipcodes_2019.csv")
    )
    urllib.request.urlretrieve(
        niou_file_link, os.path.join(download_path, "non_iou_zipcodes_2019.csv")
    )


def get_county_fips_data(download_path):
    """Download county FIPS data

    :param str download_path: folder to store the downloaded file
    """

    os.makedirs(download_path, exist_ok=True)
    county_fips_link = (
        "https://github.com/kjhealy/fips-codes/raw/master/county_fips_master.csv"
    )
    urllib.request.urlretrieve(
        county_fips_link, os.path.join(download_path, "county_fips_master.csv")
    )


def zip_to_eiaid(raw_data_path, cache_path):
    """Find the LSE of all zip codes listed in the EIA LSE service regoin data

    :param str raw_data_path: folder that contains downloaded raw data
    :param str cache_path: folder to store processed cache files
    """

    assert os.path.isfile(
        os.path.join(raw_data_path, "iou_zipcodes_2019.csv")
    ), "Input file iou_zipcodes_2019.csv does not exist."
    assert os.path.isfile(
        os.path.join(raw_data_path, "non_iou_zipcodes_2019.csv")
    ), "Input file non_iou_zipcodes_2019.csv does not exist."

    iou_df = pd.read_csv(os.path.join(raw_data_path, "iou_zipcodes_2019.csv"))
    niou_df = pd.read_csv(os.path.join(raw_data_path, "non_iou_zipcodes_2019.csv"))

    all_zips = set(iou_df["zip"].to_list() + niou_df["zip"].to_list())

    zip2id = {}

    for i in all_zips:
        ioulses = iou_df.loc[iou_df["zip"] == i]["eiaid"].to_list()
        nioulses = niou_df.loc[niou_df["zip"] == i]["eiaid"].to_list()
        alllses = set(ioulses + nioulses)
        zip2id[i] = alllses

    with open(os.path.join(cache_path, "zip2eiaid.pkl"), "wb") as fh:
        pkl.dump(zip2id, fh)


def fips_to_eiaid(raw_data_path, cache_path):
    """Find the corresponding LSE for all counties identified by their FIPS number

    :param str raw_data_path: folder that contains downloaded raw data
    :param str cache_path: folder to store processed cache files
    """

    assert os.path.isfile(
        os.path.join(cache_path, "zip2eiaid.pkl")
    ), "Cached file eiaid2zip.pkl does not exist."
    assert os.path.isfile(
        os.path.join(cache_path, "zip2fips.pkl")
    ), "Cached file zip2fips.pkl does not exist."
    assert os.path.isfile(
        os.path.join(cache_path, "fips_population.pkl")
    ), "Cached file fips_population.pkl does not exist."

    # load cached data
    with open(os.path.join(cache_path, "zip2eiaid.pkl"), "rb") as fh:
        zip2eiaid = pkl.load(fh)

    with open(os.path.join(cache_path, "zip2fips.pkl"), "rb") as fh:
        zip2fips = pkl.load(fh)

    zip_keys = list(zip2eiaid.keys())
    zip_num = len(zip_keys)

    fips2eiaid = {}
    for i in range(zip_num):
        key = zip_keys[i]
        lses = zip2eiaid[key]

        # all fips for this zip
        try:
            fipss, weights = zip2fips[key]
        except Exception:
            continue

        # map to eiaid
        fips_num = len(fipss)

        for j in range(fips_num):
            # append to dictionary
            if fipss[j] in fips2eiaid.keys():
                fips2eiaid[fipss[j]].update(lses)
            else:
                fips2eiaid[fipss[j]] = lses

    with open(os.path.join(cache_path, "fips2eiaid.pkl"), "wb") as fh:
        pkl.dump(fips2eiaid, fh)


def eiaid_to_zip(raw_data_path, cache_path):
    """Find the service region (list of ZIP codes) for every LSE identified by their EIA ID
    Create a dictionary with EIA ID as keys for list of zip codes in the cache folder

    :param str raw_data_path: folder that contains downloaded raw data
    :param str cache_path: folder to store processed cache files
    """

    assert os.path.isfile(
        os.path.join(raw_data_path, "iou_zipcodes_2019.csv")
    ), "Input file iou_zipcodes_2019.csv does not exist."
    assert os.path.isfile(
        os.path.join(raw_data_path, "non_iou_zipcodes_2019.csv")
    ), "Input file non_iou_zipcodes_2019.csv does not exist."

    iou_df = pd.read_csv(os.path.join(raw_data_path, "iou_zipcodes_2019.csv"))
    niou_df = pd.read_csv(os.path.join(raw_data_path, "non_iou_zipcodes_2019.csv"))

    all_ids = set(iou_df["eiaid"].to_list() + niou_df["eiaid"].to_list())

    id2zip = {}

    for i in all_ids:
        iouzips = iou_df.loc[iou_df["eiaid"] == i]["zip"].to_list()
        niouzips = niou_df.loc[niou_df["eiaid"] == i]["zip"].to_list()
        allzips = set(iouzips + niouzips)
        id2zip[i] = allzips

    with open(os.path.join(cache_path, "eiaid2zip.pkl"), "wb") as fh:
        pkl.dump(id2zip, fh)


def eiaid_to_fips(raw_data_path, cache_path):
    """Find the service region (list of FIPS codes) for every LSE identified by their EIA ID
    Create a dictionary with EIA ID as keys for list of FIPS codes in the cache folder

    :param str raw_data_path: folder that contains downloaded raw data
    :param str cache_path: folder to store processed cache files
    """

    assert os.path.isfile(
        os.path.join(cache_path, "eiaid2zip.pkl")
    ), "Cached file eiaid2zip.pkl does not exist."
    assert os.path.isfile(
        os.path.join(cache_path, "zip2fips.pkl")
    ), "Cached file zip2fips.pkl does not exist."
    assert os.path.isfile(
        os.path.join(cache_path, "fips_population.pkl")
    ), "Cached file fips_population.pkl does not exist."

    # load cached data
    with open(os.path.join(cache_path, "eiaid2zip.pkl"), "rb") as fh:
        eiaid2zip = pkl.load(fh)

    with open(os.path.join(cache_path, "zip2fips.pkl"), "rb") as fh:
        zip2fips = pkl.load(fh)

    with open(os.path.join(cache_path, "fips_population.pkl"), "rb") as fh:
        fips_pop_df = pkl.load(fh)

    eia_keys = list(eiaid2zip.keys())
    eia_num = len(eia_keys)

    eiaid2fips = {}
    for i in range(eia_num):
        key = eia_keys[i]
        zips = eiaid2zip[key]
        all_fips = []
        all_pops = []

        # aggregate all zip codes
        for j in zips:
            try:
                fipss, weights = zip2fips[j]
            except Exception:
                continue
            fips_num = len(fipss)

            for k in range(fips_num):
                # total population in this fips
                total_pops = fips_pop_df.loc[
                    fips_pop_df["fips"] == fipss[k], "population"
                ].to_list()[0]
                if fipss[k] in all_fips:
                    all_pops[all_fips.index(fipss[k])] += weights[k]
                else:
                    all_fips.append(fipss[k])
                    all_pops.append(weights[k] * total_pops)

        eiaid2fips.update({key: [all_fips, all_pops]})

    with open(os.path.join(cache_path, "eiaid2fips.pkl"), "wb") as fh:
        pkl.dump(eiaid2fips, fh)


def fips_zip_conversion(raw_data_path, cache_path):
    """Create a two-way mapping for all ZIP and FIPS in the crosswalk data
    save to dictionary files for future use

    :param str raw_data_path: folder that contains downloaded raw data
    :param str cache_path: folder to store processed cache files
    """
    assert os.path.isfile(
        os.path.join(raw_data_path, "county_to_zip.csv")
    ), "Input file county_to_zip.csv does not exist."

    df_raw = pd.read_csv(os.path.join(raw_data_path, "county_to_zip.csv"))

    all_fips = df_raw["county"].astype("int32")
    all_zip = df_raw["zip"].astype("int32")
    all_weights = df_raw["tot_ratio"]

    # create zip -> counties mapping
    zip2fips = {}

    for i in pd.unique(all_zip):
        idx = all_zip.index[all_zip == i]

        cty = all_fips[idx].tolist()
        wgt = all_weights[idx].tolist()

        zip2fips.update({i: (cty, wgt)})

    with open(os.path.join(cache_path, "zip2fips.pkl"), "wb") as fh:
        pkl.dump(zip2fips, fh)

    # create county -> zips mapping
    fips2zip = {}

    for i in pd.unique(all_fips):
        idx = all_fips.index[all_fips == i]

        zips = all_zip[idx].tolist()
        wgt = all_weights[idx].tolist()

        fips2zip.update({i: (zips, wgt)})

    with open(os.path.join(cache_path, "fips2zip.pkl"), "wb") as fh:
        pkl.dump(fips2zip, fh)


def get_fips_population(raw_data_path, cache_path):
    """Match county population and county FIPS data to produce concise FIPS population
    save to a dictonary in cache folder with key being 5-digit FIPS codes.

    :param str raw_data_path: folder that contains downloaded raw data
    :param str cache_path: folder to store processed cache files
    """

    assert os.path.isfile(
        os.path.join(raw_data_path, "county_population.csv")
    ), "Input file county_population.csv does not exist."
    assert os.path.isfile(
        os.path.join(raw_data_path, "county_fips_master.csv")
    ), "Input file county_fips_master.csv does not exist."

    cty_pop_df = pd.read_csv(
        os.path.join(raw_data_path, "county_population.csv"), encoding="cp1252"
    )
    cty_name_df = pd.read_csv(
        os.path.join(raw_data_path, "county_fips_master.csv"), encoding="cp1252"
    )

    pops = np.zeros(len(cty_name_df.index))
    for cty in cty_name_df.index:
        name = cty_name_df["county_name"][cty]
        state = cty_name_df["state_name"][cty]

        tmp = cty_pop_df.loc[
            (cty_pop_df["CTYNAME"] == name) & (cty_pop_df["STNAME"] == state),
            "POPESTIMATE2019",
        ]
        # if no data
        if len(tmp) == 0:
            pops[cty] = 0
        elif len(tmp) == 1:
            pops[cty] = tmp
        else:
            pops[cty] = tmp.to_list()[0]

    cty_name_df["population"] = pops

    new_df = cty_name_df.loc[:, ["fips", "county_name", "population"]]

    with open(os.path.join(cache_path, "fips_population.pkl"), "wb") as fh:
        pkl.dump(new_df, fh)


def get_zip_population(raw_data_path, cache_path):
    """Compute population of each ZIP code using percentage share and FIPS population
    save to a dictonary in cache folder with key being zip codes.

    :param str raw_data_path: folder that contains downloaded raw data
    :param str cache_path: folder to store processed cache files
    """

    assert os.path.isfile(
        os.path.join(cache_path, "fips_population.pkl")
    ), "Cached fips_population.pkl does not exist."
    assert os.path.isfile(
        os.path.join(cache_path, "zip2fips.pkl")
    ), "Cached file zip2fips.pkl does not exist."

    with open(os.path.join(cache_path, "fips_population.pkl"), "rb") as fh:
        fips_pop_df = pkl.load(fh)

    with open(os.path.join(cache_path, "zip2fips.pkl"), "rb") as fh:
        zip2fips = pkl.load(fh)

    zips = sorted(list(zip2fips.keys()))

    zip_num = len(zips)
    zip_pops = {}

    for i in range(zip_num):
        z = zips[i]

        fipss = zip2fips[z][0]
        pcts = zip2fips[z][1]
        zip_pops[z] = 0
        for f in range(len(fipss)):
            tmp = fips_pop_df.loc[fips_pop_df["fips"] == fipss[f], "population"].values
            if len(tmp) > 0:
                zip_pops[z] += tmp[0] * pcts[f]

    with open(os.path.join(cache_path, "zip_population.pkl"), "wb") as fh:
        pkl.dump(zip_pops, fh)

import errno
import os
import pickle as pkl
import re
import time

import numpy as np
import pandas as pd
import requests
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from powersimdata.utility.distance import find_closest_neighbor
from tqdm import tqdm


def get_bus_pos(network_path):
    """Read raw files of synthetic grid and extract the lat/lon coordinate of all buses

    :param str network_path: path to folder of raw data of a power network
    :return: (*pandas.DataFrame*) -- (n x 3) dataframe containing bus coordinates
    """

    try:
        sub_df = pd.read_csv(os.path.join(network_path, "sub.csv"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Can't find sub.csv file in {network_path} folder")
    try:
        bus2sub_df = pd.read_csv(os.path.join(network_path, "bus2sub.csv"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Can't find bus2sub.csv file in {network_path} folder")

    bus_pos = pd.DataFrame()

    bus_pos["bus_id"] = bus2sub_df["bus_id"]

    bus_pos["lat"] = [
        sub_df.loc[sub_df["sub_id"] == i, "lat"].values[0] for i in bus2sub_df["sub_id"]
    ]
    bus_pos["lon"] = [
        sub_df.loc[sub_df["sub_id"] == i, "lon"].values[0] for i in bus2sub_df["sub_id"]
    ]

    return bus_pos


def get_bus_fips(bus_pos, cache_path, start_idx=0):
    """Try to get FIPS of each bus in a case mat using FCC AREA API
    Can take hours to run, save to cache file for future use

    :param pandas.DataFrame bus_pos: a dataframe of (bus, lat, lon)
    :param str cache_path: folder to store processed cache files
    :param int start_idx: pointer to the index of a bus to start query from
    """
    bus_num = len(bus_pos)
    bus_fips_dict = {
        "busid": bus_pos["bus_id"].values,
        "latitude": bus_pos["lat"].values,
        "longitude": bus_pos["lon"].values,
        "fips": [0] * bus_num,
    }

    url = "https://geo.fcc.gov/api/census/area"

    for i in tqdm(range(start_idx, bus_num)):
        if i % 1000 == 0:
            with open(os.path.join(cache_path, "bus_fips.pkl"), "wb") as fh:
                pkl.dump(bus_fips_dict, fh)

        params = {
            "latitude": bus_pos.loc[i, "lat"],
            "longitude": bus_pos.loc[i, "lon"],
            "format": "json",
        }

        try:
            r = requests.get(url, params=params)
            bus_fips_dict["fips"][i] = int(r.json()["County"]["FIPS"])
            time.sleep(0.02)
        except TypeError:
            bus_fips_dict["fips"][i] = -1
        finally:
            if r.status_code != 200:
                print(f"Request failed with return code {r.status_code}!")
                break

    with open(os.path.join(cache_path, "bus_fips.pkl"), "wb") as fh:
        pkl.dump(bus_fips_dict, fh)


def cleanup_zip(zipdict):
    """Try to cleanup a zip dictionary obtained using online query by converting
    to 5-digit integers. Several possible mis-format are considered

    :param dict zipdict: a dictionary containing raw zip-code of buses
    :return: (*dict*) -- a dictionary containing 5-digit zip codes
    """
    for i in range(len(zipdict["zip"])):
        if isinstance(zipdict["zip"][i], int):
            continue
        try:
            zipdict["zip"][i] = int(
                re.search(r"(?<!\d)\d{5}(?!\d)", zipdict["zip"][i]).group(0)
            )
        except Exception:
            zipdict["zip"][i] = -1

    return zipdict


def get_bus_zip(bus_pos, cache_path, start_idx=0):
    """Try to get ZIP of each bus in a case mat using geopy
    Can take hours to run, save to cache file for future use

    :param pandas.DataFrame bus_pos: a dataframe of (bus, lat, lon)
    :param str cache_path: folder to store processed cache files
    :param int start_idx: pointer to the index of a bus to start query from
    """
    bus_num = len(bus_pos)
    bus_zip_dict = {
        "busid": bus_pos["bus_id"].values,
        "latitude": bus_pos["lat"].values,
        "longitude": bus_pos["lon"].values,
        "zip": [0] * bus_num,
    }

    geocoder = Nominatim(user_agent="BES")
    reverse = RateLimiter(
        geocoder.reverse, min_delay_seconds=0.05, return_value_on_exception=None
    )

    def get_zip_code(lat, lon):
        location = reverse("{}, {}".format(lat, lon))
        if location is not None:
            address = location.raw["address"]
        else:
            return -1

        if "postcode" in address.keys():
            return address["postcode"]
        else:
            return -1

    for i in tqdm(range(start_idx, bus_num)):
        bus_zip_dict["zip"][i] = int(
            get_zip_code(bus_zip_dict["latitude"][i], bus_zip_dict["longitude"][i])
        )

    bus_zip_dict = cleanup_zip(bus_zip_dict)

    with open(os.path.join(cache_path, "bus_zip.pkl"), "wb") as fh:
        pkl.dump(bus_zip_dict, fh)


def get_all_bus_eiaid(bus_csv_path, doe_csv_path, cache_path, bus_pos, out_path):
    """Compute the EIA ID of each bus in bus.csv from powersimdata using cached files

    :param str bus_csv_path: bus.csv in a powersimdata network model
    :param str doe_csv_path: aggregated .csv DOE flexibility data
    :param str cache_path: folder to store processed cache files
    :param pandas.DataFrame bus_pos: (n x 3) dataframe containing bus coordinates
    :param str out_path: output path to store the bus.csv with EIA ID
    :raises FileNotFoundError: when any required cache file is not present
    """

    # check all required files
    if not os.path.isfile(bus_csv_path):
        raise OSError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            "Incorrect path for network data files bus.csv.",
        )
    if not os.path.isfile(os.path.join(cache_path, "bus_fips.pkl")):
        raise OSError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            "Cached file bus_fips.pkl does not exist.",
        )
    if not os.path.isfile(os.path.join(cache_path, "bus_zip.pkl")):
        raise OSError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            "Cached file bus_zip.pkl does not exist.",
        )
    if not os.path.isfile(os.path.join(cache_path, "zip2eiaid.pkl")):
        raise OSError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            "Cached file fips2eiaid.pkl does not exist.",
        )
    if not os.path.isfile(os.path.join(cache_path, "fips2eiaid.pkl")):
        raise OSError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            "Cached file zip2eiaid.pkl does not exist.",
        )
    if not os.path.isfile(doe_csv_path):
        raise OSError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            "DOE flexibility .csv data does not exist.",
        )

    bus_df = pd.read_csv(bus_csv_path)
    doe_df = pd.read_csv(doe_csv_path)

    with open(os.path.join(cache_path, "bus_fips.pkl"), "rb") as fh:
        bus_fips = pkl.load(fh)

    with open(os.path.join(cache_path, "bus_zip.pkl"), "rb") as fh:
        bus_zip = pkl.load(fh)

    with open(os.path.join(cache_path, "fips2eiaid.pkl"), "rb") as fh:
        fips2eiaid = pkl.load(fh)

    with open(os.path.join(cache_path, "zip2eiaid.pkl"), "rb") as fh:
        zip2eiaid = pkl.load(fh)

    bus_num = bus_df["bus_id"].shape[0]
    bus_eiaid = np.zeros(bus_num, dtype=int)
    all_eias = doe_df.columns.values[1:].astype("int32").tolist()

    # match with bus number
    for i in range(bus_num):
        # match zip
        if bus_zip["zip"][i] in zip2eiaid.keys():
            for j in zip2eiaid[bus_zip["zip"][i]]:
                if j in all_eias:
                    bus_eiaid[i] = j

        # match fips
        if bus_fips["fips"][i] in fips2eiaid.keys() and bus_eiaid[i] == 0:
            for j in fips2eiaid[bus_fips["fips"][i]]:
                if j in all_eias:
                    bus_eiaid[i] = j

    bus_df["eia_id"] = bus_eiaid

    # buses that cannot be identified with LSE
    bus_pos_ids = bus_pos["bus_id"].tolist()
    bus_without_lse = bus_df.loc[bus_df["eia_id"] == 0, "bus_id"]

    for i in bus_without_lse:
        # position of target bus
        lat, lon = bus_pos.loc[bus_pos_ids.index(i), ["lat", "lon"]].values

        # find all buses in the same load zone as the target bus
        bus_zone = bus_df.loc[bus_df["bus_id"] == i, "zone_id"].values[0]
        buses_same_zone = bus_df.loc[
            (bus_df["zone_id"] == bus_zone) & (bus_df["eia_id"] > 0), "bus_id"
        ]
        same_zone_bus_idx = [bus_pos_ids.index(j) for j in buses_same_zone]
        same_zone_bus_pos = bus_pos.loc[same_zone_bus_idx, ["lat", "lon"]].values

        # find nearest neighbor and assign the same eia id
        nearest_neighbor_id = bus_pos_ids[
            same_zone_bus_idx[find_closest_neighbor((lat, lon), same_zone_bus_pos)]
        ]
        nearest_neighbor_eiaid = bus_df.loc[
            bus_df["bus_id"] == nearest_neighbor_id, "eia_id"
        ].values[0]
        bus_df.loc[bus_df["bus_id"] == i, "eia_id"] = nearest_neighbor_eiaid

    bus_df.to_csv(out_path, index=False)

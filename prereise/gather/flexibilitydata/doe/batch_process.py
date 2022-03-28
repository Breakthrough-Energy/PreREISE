import os
import urllib.request

from prereise.gather.flexibilitydata.doe.geo_data import (
    eiaid_to_fips,
    eiaid_to_zip,
    fips_zip_conversion,
    get_census_data,
    get_county_fips_data,
    get_crosswalk_data,
    get_fips_population,
    get_lse_region_data,
    get_zip_population,
)


def get_cache_from_blob(cache_path):
    """Download previously uploaded cached files from BLOB storage

    :param str cache_path: folder to store downloaded cache files
    """

    cache_names = [
        "eiaid2fips.pkl",
        "eiaid2zip.pkl",
        "fips_population.pkl",
        "fips2zip.pkl",
        "zip_population.pkl",
        "zip2fips.pkl",
        "bus_fips.pkl",
        "bus_zip.pkl",
    ]

    blob_path = (
        "https://besciences.blob.core.windows.net/datasets/demand_flexibility_doe/"
    )
    for f in cache_names:
        urllib.request.urlretrieve(blob_path + f, os.path.join(cache_path, f))


def collect_all_raw_data(download_path):
    """Download all required raw data needed for producing cached files

    :param str download_path: folder to store the downloaded file
    """

    get_census_data(download_path)
    get_crosswalk_data(download_path)
    get_lse_region_data(download_path)
    get_county_fips_data(download_path)


def create_geo_cache_files(raw_path, cache_path):
    """Process downloaded raw files and create cached intermediate files

    :param str raw_path: folder that contains downloaded raw data
    :param str cache_path: folder to store processed cache files
    """

    os.makedirs(cache_path, exist_ok=True)
    fips_zip_conversion(raw_path, cache_path)
    get_fips_population(raw_path, cache_path)
    get_zip_population(raw_path, cache_path)
    eiaid_to_zip(raw_path, cache_path)
    eiaid_to_fips(raw_path, cache_path)

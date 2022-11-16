import os

import pytest

from prereise.gather.flexibilitydata.doe.batch_process import (
    collect_all_raw_data,
    create_geo_cache_files,
)


@pytest.mark.integration
def test_batch_download():
    """Test the downloader from all raw data sources, check if file exist"""

    abs_download_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "..", "raw"
    )
    collect_all_raw_data(abs_download_path)

    # check downloaded files
    assert os.path.isfile(os.path.join(abs_download_path, "county_fips_master.csv"))
    assert os.path.isfile(os.path.join(abs_download_path, "county_population.csv"))
    assert os.path.isfile(os.path.join(abs_download_path, "county_to_zip.csv"))
    assert os.path.isfile(os.path.join(abs_download_path, "iou_zipcodes_2019.csv"))
    assert os.path.isfile(os.path.join(abs_download_path, "non_iou_zipcodes_2019.csv"))

    # delete downloaded files
    os.remove(os.path.join(abs_download_path, "county_fips_master.csv"))
    os.remove(os.path.join(abs_download_path, "county_population.csv"))
    os.remove(os.path.join(abs_download_path, "county_to_zip.csv"))
    os.remove(os.path.join(abs_download_path, "iou_zipcodes_2019.csv"))
    os.remove(os.path.join(abs_download_path, "non_iou_zipcodes_2019.csv"))


@pytest.mark.integration
def test_cache_production():
    """Test the functions that produce cached files"""

    abs_raw_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "raw")
    abs_cache_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "..", "cache"
    )
    abs_download_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "..", "raw"
    )

    collect_all_raw_data(abs_download_path)
    create_geo_cache_files(abs_raw_path, abs_cache_path)

    # check cache files
    assert os.path.isfile(os.path.join(abs_cache_path, "eiaid2fips.pkl"))
    assert os.path.isfile(os.path.join(abs_cache_path, "eiaid2zip.pkl"))
    assert os.path.isfile(os.path.join(abs_cache_path, "fips2zip.pkl"))
    assert os.path.isfile(os.path.join(abs_cache_path, "fips_population.pkl"))
    assert os.path.isfile(os.path.join(abs_cache_path, "zip_population.pkl"))
    assert os.path.isfile(os.path.join(abs_cache_path, "zip2fips.pkl"))

    # delete downloaded files
    os.remove(os.path.join(abs_download_path, "county_fips_master.csv"))
    os.remove(os.path.join(abs_download_path, "county_population.csv"))
    os.remove(os.path.join(abs_download_path, "county_to_zip.csv"))
    os.remove(os.path.join(abs_download_path, "iou_zipcodes_2019.csv"))
    os.remove(os.path.join(abs_download_path, "non_iou_zipcodes_2019.csv"))

    # delete cache files
    os.remove(os.path.join(abs_cache_path, "eiaid2fips.pkl"))
    os.remove(os.path.join(abs_cache_path, "eiaid2zip.pkl"))
    os.remove(os.path.join(abs_cache_path, "fips2zip.pkl"))
    os.remove(os.path.join(abs_cache_path, "fips_population.pkl"))
    os.remove(os.path.join(abs_cache_path, "zip_population.pkl"))
    os.remove(os.path.join(abs_cache_path, "zip2fips.pkl"))

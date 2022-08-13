import os

from prereise.gather.flexibilitydata.doe.batch_process import (
    collect_all_raw_data,
    create_geo_cache_files,
    get_cache_from_blob,
)

download_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), os.pardir, "raw"
)
cache_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), os.pardir, "cache"
)

# download raw data from sources
collect_all_raw_data(download_path)

# create cache files after downloading raw data
create_geo_cache_files(download_path, cache_path)

# download cache files directly from BLOB storage
get_cache_from_blob(cache_path)

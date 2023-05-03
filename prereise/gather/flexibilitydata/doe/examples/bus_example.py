import os

from prereise.gather.flexibilitydata.doe.bus_data import (
    get_all_bus_eiaid,
    get_bus_fips,
    get_bus_pos,
    get_bus_zip,
)

cache_path = os.path.join(os.path.dirname(__file__), os.pardir, "cache")

# find coordinates of buses in a .mat case
bus_pos = get_bus_pos(cache_path)

# find the FIPS of all buses and store to cache
get_bus_fips(bus_pos, cache_path)

# find the ZIP of all buses and store to cache
get_bus_zip(bus_pos, cache_path)

# use the cached file to identify EIA ID of buses and add to bus.csv
bus_csv_path = "bus.csv"
doe_csv_path = "doe_flexibility_2016.csv"
bus_csv_out_path = "bus_with_lse.csv"
get_all_bus_eiaid(bus_csv_path, doe_csv_path, cache_path, bus_pos, bus_csv_out_path)

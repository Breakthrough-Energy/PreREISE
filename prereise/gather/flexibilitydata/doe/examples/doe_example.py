from prereise.gather.flexibilitydata.doe.doe_data import aggregate_doe, download_doe

download_path = "doe"
aggregated_path = "aggregated_doe_flexibility.csv"

download_doe(download_path)
aggregate_doe(download_path, aggregated_path)

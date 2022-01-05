# additional sources of data can be found at https://rapidrefresh.noaa.gov/hrrr/
# as well as https://github.com/blaylockbk/Herbie/blob/a20d1017ea4c73916cb4436ad797804854109db3/herbie/models/hrrr.py#L58-L63
HRRR_S3_BASE_URL = "https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.{dt:%Y%m%d}/conus/hrrr.t{dt:%H}z.wrf{product}f{hours_forecasted:02d}.grib2"
HRRR_GOOGLE_BASE_URL = "https://storage.googleapis.com/high-resolution-rapid-refresh/hrrr.{dt:%Y%m%d}/conus/hrrr.t{dt:%Y%m%d}z.wrf{product}f{hours_forecasted:02d}.grib2"
HRRR_AZURE_BASE_URL = "https://noaahrrr.blob.core.windows.net/hrrr/hrrr.{dt:%Y%m%d}/conus/hrrr.t{dt:%H}z.wrf{product}f{hours_forecasted:02d}.grib2"
HRRR_NOMADS_BASE_URL = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{dt:%Y%m%d}/conus/hrrr.t{dt:%H}z.wrf{product}f{hours_forecasted:02d}.grib2"

DEFAULT_PRODUCT = "sfc"
DEFAULT_HOURS_FORECASTED = "0"

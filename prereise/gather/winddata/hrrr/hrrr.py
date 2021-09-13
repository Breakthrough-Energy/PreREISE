from prereise.gather.winddata.hrrr.constants import HRRR_S3_BASE_URL
from prereise.gather.winddata.hrrr.downloader import Downloader
from prereise.gather.winddata.hrrr.hrrr_api import HrrrApi


def retrieve_data(start_dt, end_dt, directory):
    """Retrieves all HRRR wind data for all hours between start_dt and
    end_dt. (In a future PR) will convert all that wind data to
    Pout in order to be compatible with REISE.

    Sample usage:
    from datetime import datetime, timedelta
    retrieve_data(start_dt=datetime.fromisoformat("2016-01-01"), end_dt=datetime.fromisoformat("2016-01-01") + timedelta(hours=2), directory="./")

    :param datetime.datetime start_dt: datetime to start at
    :param datetime.datetime end_dt: datetime to end at
    :param str directory: file directory to download data into
    """
    api = HrrrApi(Downloader, HRRR_S3_BASE_URL)
    api.download_wind_data(start_dt, end_dt, directory)

import requests
from pandas import date_range
from tqdm import tqdm

from prereise.gather.winddata.hrrr.constants import DEFAULT_PRODUCT
from prereise.gather.winddata.hrrr.grib import GribRecordInfo
from prereise.gather.winddata.hrrr.helpers import (
    formatted_filename,
    get_indices_that_contain_selector,
)


class HrrrApi:
    """Class to interact with to get and download HRRR data. More information
    about HRRR data can be found at
    `this link <https://registry.opendata.aws/noaa-hrrr-pds/>`_
    and
    `this link <https://www.nco.ncep.noaa.gov/pmb/products/hrrr/>`_

    :param prereise.gather.winddata.hrrr.downloader.Downloader downloader: class
        that holds helper functions for downloading
    :param str base_url: url to download data from. Should take "dt", "product"
        and "hours_forecasted" as format variables. See
        :mod:`prereise.gather.winddata.hrrr.constants` for more detail
    """

    U_COMPONENT_FILTER = "UGRD:80 m above ground"
    V_COMPONENT_FILTER = "VGRD:80 m above ground"

    def __init__(self, downloader, base_url):
        self.downloader = downloader
        self.base_url = base_url

    def _filename_url_iter(self, start_dt, end_dt, product):
        """Iterates from a start datetime (inclusive) to a end datetime (inclusive)
        at 1 hour steps, returning a filename as well as a url based
        on each intermediary datetime

        :param datetime.datetime start_dt: datetime to start at
        :param datetime.datetime end_dt: datetime to end at
        :param str product: info at `this link <https://www.nco.ncep.noaa.gov/pmb/products/hrrr/>`_

        :return: (*generator*) -- generator that yields filename and url
        """
        for dt in date_range(start=start_dt, end=end_dt, freq="H").to_pydatetime():
            url = self.base_url.format(dt=dt, product=product, hours_forecasted=0)
            yield formatted_filename(dt, product), url

    def download_meteorological_data(
        self, start_dt, end_dt, directory, product, selectors=None
    ):
        """Iterates from a start datetime (inclusive) to a end datetime (inclusive)
        at 1 hour steps, downloading data for each intermediary datetime into
        the directory provided. product and selectors variables are used
        to control what specific type of data to download. See
        `this link <https://www.nco.ncep.noaa.gov/pmb/products/hrrr/>`_ to understand
        more about product and
        `this link <https://github.com/blaylockbk/Herbie/blob/18945e4c5103386c98d08dcb2de590e2ac14c3d5/docs/user_guide/grib2.rst#how-grib-subsetting-works-in-herbie>`_
        to understand more about what kind of strings can be passed into selectors

        :param datetime.datetime start_dt: datetime to start at
        :param datetime.datetime end_dt: datetime to end at
        :param str directory: file directory to download data into
        :param str product: info at `this link <https://www.nco.ncep.noaa.gov/pmb/products/hrrr/>`_
        :param list selectors: list of strings that can be used to narrow down
            the amount of data downloaded from a specific GRIB file.
        """
        for filename, url in tqdm(self._filename_url_iter(start_dt, end_dt, product)):
            grib_record_information_list = [GribRecordInfo.full_file()]
            # first grab index file and figure out which bytes to download
            if selectors:
                index_url = f"{url}.idx"
                response = requests.get(
                    index_url
                )  # index files are typically a few kb, so safe to hold in memory
                raw_record_information_list = response.text.split("\n")
                index_list = get_indices_that_contain_selector(
                    raw_record_information_list, selectors
                )
                grib_record_information_list = (
                    GribRecordInfo.generate_grib_record_information_list(
                        raw_record_information_list, index_list
                    )
                )

            with open(directory + filename, "ab") as f:
                for grib_record_information in grib_record_information_list:
                    try:
                        self.downloader.download(
                            url,
                            f,
                            headers={
                                "Range": f"bytes={grib_record_information.byte_range_header_string()}"
                            },
                        )
                    except Exception:
                        print(
                            f"Failed to download data from {url} with byte range {grib_record_information.byte_range_header_string()}"
                        )

    def download_wind_data(self, start_dt, end_dt, directory):
        """See :meth:`download_meteorological_data`
        for more information. Default product used is "sfc" which represents
        2D Surface Levels, and the selectors used filter specifically for
        U component and V component of wind at 80 meters above ground.

        :param datetime.datetime start_dt: datetime to start at
        :param datetime.datetime end_dt: datetime to end at
        :param str directory: file directory to download data into
        """
        self.download_meteorological_data(
            start_dt,
            end_dt,
            directory,
            product=DEFAULT_PRODUCT,
            selectors=[self.U_COMPONENT_FILTER, self.V_COMPONENT_FILTER],
        )

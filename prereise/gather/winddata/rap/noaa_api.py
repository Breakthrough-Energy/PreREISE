import datetime
from dataclasses import dataclass

import requests


class NoaaApi:
    """API client for downloading rap-130 data from NOAA.

    :param dict box: geographic area
    """

    base_url = "https://www.ncdc.noaa.gov/thredds/ncss/model-rap130/"
    fallback_url = "https://www.ncdc.noaa.gov/thredds/ncss/model-rap130-old/"
    var_u = "u-component_of_wind_height_above_ground"
    var_v = "v-component_of_wind_height_above_ground"

    def __init__(self, box):
        self.box = box
        self._set_params()

    def _set_params(self):
        """Set default query parameters that will be sent with each request"""
        extension = "accept=netCDF"
        self.params = [
            ("accept", "netCDF"),
            ("var", NoaaApi.var_u),
            ("var", NoaaApi.var_v),
            ("disableProjSubset", "on"),
            ("horizStride", "1"),
            ("addLatLon", "true"),
        ] + [(k, v) for k, v in self.box.items()]

    def get_url_list(self, start, end):
        """Enable calculating the final result size prior to download. Used for
        initializing data frames to the correct size.

        :param datetime start: the start date
        :param datetime end: the end date
        :return: (*list*) -- a list of urls that span the date range
        """
        result = []
        for time_slice in self.iter_hours(start, end):
            result.append(self.build_url(time_slice))
        return result

    def iter_hours(self, start, end):
        """Iterate over the hours in the given range, yielding a path segment
        matching the structure of NOAA's server

        :param datetime start: the start date
        :param datetime end: the end date
        :return: (*Generator[str]*) -- path part of the url pertaining to time range
        """
        step = datetime.timedelta(days=1)
        while start <= end:
            ts = start.strftime("%Y%m%d")
            path = ts[:6] + "/" + ts + "/rap_130_" + ts
            for h in range(10000, 12400, 100):
                yield "_".join([path, str(h)[1:], "000.grb2?"])
            start += step

    def build_url(self, time_slice, fallback=False):
        """Build the url for the given time slice

        :param str time_slice: url path segment specifying the time range
        :param bool fallback: whether to use the fallback url for older data
        :return: (*str*) -- the url to download
        """
        url = NoaaApi.fallback_url if fallback else NoaaApi.base_url
        return url + time_slice

    def get_hourly_data(self, start, end):
        """Iterate responses over the given time range

        :param datetime start: the start date
        :param datetime end: the end date
        :return: (*Generator[requests.Response]*) -- yield the next http response
        """

        def download(time_slice, fallback=False):
            url = self.build_url(time_slice, fallback)
            return requests.get(url, stream=True, params=self.params)

        for time_slice in self.iter_hours(start, end):
            response = download(time_slice)
            if response.status_code == 404:
                print(f"Got 404 response, trying fallback url. Original={url}")
                download(time_slice, fallback=True)
                if response.status_code == 404:
                    print(
                        "Content not found for the given range - it may be"
                        + "available via tape archive, please contact NOAA for"
                        + "support"
                    )
            yield response

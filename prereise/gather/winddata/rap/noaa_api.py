import datetime

import requests

from prereise.gather.request_util import TransientError, retry


class NoaaApi:
    """API client for downloading rap-130 data from NOAA.

    :param dict box: geographic area
    :raises TypeError: if box None or not a dict
    :raises ValueError: if box is missing keys or contains unknown keys
    """

    base_url = "https://www.ncei.noaa.gov/thredds/ncss/model-rap130/"
    fallback_url = "https://www.ncei.noaa.gov/thredds/ncss/model-rap130-old/"
    var_u = "u-component_of_wind_height_above_ground"
    var_v = "v-component_of_wind_height_above_ground"

    def __init__(self, box):
        self.box = box
        self._check_box()
        self._set_params()

    def _check_box(self):
        if self.box is None or not isinstance(self.box, dict):
            raise TypeError("box must be a non-empty dict")
        valid_keys = {"north", "south", "east", "west"}
        if set(self.box.keys()) != valid_keys:
            raise ValueError(f"Keys must be one of: {','.join(valid_keys)}")

    def _set_params(self):
        """Set default query parameters that will be sent with each request"""
        self.params = [
            ("var", NoaaApi.var_u),
            ("var", NoaaApi.var_v),
            ("disableProjSubset", "on"),
            ("horizStride", "1"),
            ("addLatLon", "true"),
            ("accept", "netCDF"),
        ] + [(k, v) for k, v in self.box.items()]

    def get_path_list(self, start, end):
        """Enable calculating the final result size prior to download. Used for
        initializing data frames to the correct size.

        :param datetime start: the start date
        :param datetime end: the end date
        :return: (*list*) -- a list of url paths that span the date range
        """
        result = []
        for time_slice in self.iter_hours(start, end):
            result.append(time_slice)
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
                yield "_".join([path, str(h)[1:], "000.grb2"])
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

        retry_limit = 3

        @retry(max_attempts=retry_limit, allowed_exceptions=(TransientError))
        def download(time_slice, fallback=False):
            url = self.build_url(time_slice, fallback)
            resp = requests.get(url, params=self.params)
            if resp.status_code == 500 and download.retry_count < retry_limit:
                msg = f"Server error for url={resp.url}, retry_count={download.retry_count}"
                raise TransientError(msg)
            return resp

        for time_slice in self.iter_hours(start, end):
            response = download(time_slice)
            if response.status_code == 404:
                print("Got 404 response, trying fallback url.")
                response = download(time_slice, fallback=True)
                if response.status_code == 404:
                    print(
                        "Content not found for the given range - it may be"
                        + " available via tape archive, please contact NOAA for"
                        + " support"
                    )
            yield response

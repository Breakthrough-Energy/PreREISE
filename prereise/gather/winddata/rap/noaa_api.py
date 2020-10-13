import datetime
from dataclasses import dataclass

import requests


@dataclass
class CoordBox:
    north: float
    south: float
    west: float
    east: float

    def to_query(self):
        return "&".join(
            [
                f"north={self.north}",
                f"west={self.west}",
                f"east={self.east}",
                f"south={self.south}",
            ]
        )


class NoaaApi:
    """API client for downloading rap-130 data from NOAA.

    :param prereise.gather.winddata.rap.noaa_api.CoordBox box: geographic area
    """

    base_url = "https://www.ncdc.noaa.gov/thredds/ncss/model-rap130/"
    fallback_url = "https://www.ncdc.noaa.gov/thredds/ncss/model-rap130-old/"

    def __init__(self, box):
        self.box = box
        self._set_params()

    def _set_params(self):
        """Set default query parameters that will be sent with each request"""
        extension = "accept=netCDF"
        self.var_u = "u-component_of_wind_height_above_ground"
        self.var_v = "v-component_of_wind_height_above_ground"
        self.params = [
            extension,
            self.box.to_query(),
            f"var={self.var_u}",
            f"var={self.var_v}",
            "disableProjSubset=on",
            "horizStride=1",
            "addLatLon=true",
        ]

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
        return url + time_slice + "&".join(self.params)

    def get_hourly_data(self, start, end, check=False):
        """
        Return netCDF4 Dataset generator for the given query
        """
        for time_slice in self.iter_hours(start, end):
            url = self.build_url(time_slice)
            httpfunc = lambda url: requests.head(url) if check else requests.get(url)
            response = httpfunc(url)
            if response.status_code == 404:
                url = self.build_url(time_slice, fallback=True)
                response = httpfunc(url)

            yield response

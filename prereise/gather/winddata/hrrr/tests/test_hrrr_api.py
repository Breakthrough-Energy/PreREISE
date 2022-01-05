from unittest.mock import MagicMock, mock_open, patch

import pytest

from prereise.gather.winddata.hrrr.hrrr_api import HrrrApi

CSNOW_SELECTOR = "CSNOW:surface"
CICEP_SELECTOR = "CICEP:surface"
UGRD_SELECTOR = "UGRD:80 m above ground"
VGRD_SELECTOR = "VGRD:80 m above ground"

UGRD_BYTE_START = "43816635"
VGRD_BYTE_START = "44816635"
CICEP_BYTE_START = "42816635"
CSNOW_BYTE_START = "42783532"

DIRECTORY = "./"
FILENAME = "somefile"
URL = "someurl"
FLAGS = "ab"


def filename_url_iter_mock(filename, url):
    def _filename_url_iter(start_dt, end_dt, product):
        yield filename, url

    return _filename_url_iter


@pytest.fixture
def requests_mock():
    with patch("prereise.gather.winddata.hrrr.hrrr_api.requests") as r:
        r.get.return_value.text = (
            f"60:{CSNOW_BYTE_START}:d=2016010100:{CSNOW_SELECTOR}:anl:\n"
            f"61:{CICEP_BYTE_START}:d=2016010100:{CICEP_SELECTOR}:anl:\n"
            f"62:{UGRD_BYTE_START}:d=2016010100:{UGRD_SELECTOR}:anl:\n"
            f"63:{VGRD_BYTE_START}:d=2016010100:{VGRD_SELECTOR}:anl:"
        )
        yield r


@pytest.fixture
def open_mock():
    m = mock_open()
    with patch("builtins.open", m):
        yield m


@pytest.fixture
def hrrr_api(requests_mock, open_mock):
    h = HrrrApi(MagicMock(), "")
    h._filename_url_iter = filename_url_iter_mock(FILENAME, URL)
    return h


def test_download_wind_data(open_mock, hrrr_api):
    hrrr_api.download_wind_data(None, None, DIRECTORY)

    open_mock.assert_called_once_with(DIRECTORY + FILENAME, FLAGS)
    hrrr_api.downloader.download.assert_any_call(
        URL,
        open_mock(),
        headers={"Range": f"bytes={UGRD_BYTE_START}-{int(VGRD_BYTE_START)-1}"},
    )
    hrrr_api.downloader.download.assert_any_call(
        URL, open_mock(), headers={"Range": f"bytes={VGRD_BYTE_START}-"}
    )


def test_download_meteorological_data_no_selectors(open_mock, hrrr_api):
    hrrr_api.download_meteorological_data(None, None, DIRECTORY, None)

    open_mock.assert_called_once_with(DIRECTORY + FILENAME, FLAGS)
    hrrr_api.downloader.download.assert_any_call(
        URL, open_mock(), headers={"Range": "bytes=0-"}
    )


def test_download_meteorological_data_with_selectors(open_mock, hrrr_api):
    hrrr_api.download_meteorological_data(
        None, None, DIRECTORY, None, selectors=[CICEP_SELECTOR, CSNOW_SELECTOR]
    )

    open_mock.assert_called_once_with(DIRECTORY + FILENAME, FLAGS)
    hrrr_api.downloader.download.assert_any_call(
        URL,
        open_mock(),
        headers={"Range": f"bytes={CSNOW_BYTE_START}-{int(CICEP_BYTE_START)-1}"},
    )
    hrrr_api.downloader.download.assert_any_call(
        URL,
        open_mock(),
        headers={"Range": f"bytes={CICEP_BYTE_START}-{int(UGRD_BYTE_START)-1}"},
    )

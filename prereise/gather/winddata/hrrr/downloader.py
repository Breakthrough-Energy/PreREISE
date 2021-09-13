import shutil

import requests


class Downloader:
    """Class that holds downloading functionality"""

    @staticmethod
    def download(url, file, headers):
        """Downloads file from a url and stores contents into file.

        :param str url: url to download from
        :param io.BufferedIOBase file: file to write to, opened in
            binary mode
        :param dict headers: dictionary holding headers to be sent
            to url when attempting to download
        """
        with requests.get(url, stream=True, headers=headers) as r:
            shutil.copyfileobj(r.raw, file)

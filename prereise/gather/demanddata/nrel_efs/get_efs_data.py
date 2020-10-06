import io
import os
import platform
import zipfile

import requests


def download_data(es={"all"}, ta={"all"}, path=""):
    """Downloads the NREL EFS data for the specified electrification scenarios and
    technology advancements.

    :param set/list es: The electrification scenarios that will be downloaded. Can
        choose any of: *'Reference'*, *'Medium'*, *'High'*, or *'All'*. Defaults to
        *'All'*.
    :param set/list ta: The technology advancements that will be downloaded. Can
        choose any of: *'Slow'*, *'Moderate'*, *'Rapid'*, or *'All'*. Defaults to
        *'All'*.
    :param str path: The file path to which the NREL EFS data will be downloaded.
    """

    # Check that the inputs are of an appropriate type
    if not isinstance(es, (set, list)):
        raise TypeError("Electrification scenarios must be input as a set or list.")
    if not isinstance(ta, (set, list)):
        raise TypeError("Technology advancements must be input as a set or list.")
    if not isinstance(path, str):
        raise TypeError("The file path must be input as a str.")

    # Check that the components of es and ta are str
    if not all(isinstance(x, str) for x in es):
        raise TypeError("Individual electrification scenarios must be input as a str.")
    if not all(isinstance(x, str) for x in ta):
        raise TypeError("Individual technology advancements must be input as a str.")

    # Reformat components of es and ta
    es = {x.capitalize() for x in es}
    if "All" in es:
        es = {"Reference", "Medium", "High"}
    ta = {x.capitalize() for x in ta}
    if "All" in ta:
        ta = {"Slow", "Moderate", "Rapid"}

    # Check that the components of es and ta are valid
    if not es.issubset({"Reference", "Medium", "High"}):
        invalid_es = es - {"Reference", "Medium", "High"}
        raise ValueError(f'Invalid electrification scenarios: {", ".join(invalid_es)}')
    if not ta.issubset({"Slow", "Moderate", "Rapid"}):
        invalid_ta = ta - {"Slow", "Moderate", "Rapid"}
        raise ValueError(f'Invalid electrification scenarios: {", ".join(invalid_ta)}')

    # Access the actual path if not already provided
    if len(path) == 0:
        path = os.getcwd()
        path = path.replace("\\", "/")

    # Download each of the specified load profiles
    for i in es:
        for j in ta:
            try:
                # Assign path and file names
                zip_name = "EFSLoadProfile_" + i + "_" + j + ".zip"
                url = "https://data.nrel.gov/system/files/126/" + zip_name
                if path.endswith("/"):
                    zip_path = path + zip_name
                else:
                    zip_path = path + "/" + zip_name

                # Try Python's zipfile module first
                r = requests.get(url, stream=True)
                if r.status_code != requests.codes.ok:
                    r.raise_for_status()
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(path)
            except NotImplementedError:
                print("This compression is not supported by the zipfile module.")

                # Save a local copy of the .zip file for extraction
                open(zip_name, "wb").write(r.content)
                if platform.system() == "Windows":
                    try:
                        # Try using 7zip, if it is installed
                        sz_path = "C:/Program Files/7-Zip/7z.exe"
                        if not os.path.isfile(sz_path):
                            raise OSError(
                                "7zip is not in this directory or is not installed."
                            )
                        os.system(
                            'cmd /c powershell -c & "'
                            + sz_path
                            + '" x "'
                            + zip_path
                            + '" -o"'
                            + path
                            + '"'
                        )
                        os.remove(zip_path)
                    except NotImplementedError:
                        print("This compression is not supported by 7zip.")
                elif platform.system() == "Darwin":
                    raise OSError("Other extraction methods not implemented in MacOS.")
                elif platform.system() == "Linux":
                    raise OSError("Other extraction methods not implemented in Linux.")
                else:
                    raise OSError("Not a valid operating system.")

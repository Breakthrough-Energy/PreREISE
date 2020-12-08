import io
import os
import platform
import subprocess
import zipfile

import pandas as pd
import requests
from powersimdata.network.usa_tamu.constants.zones import abv2state


def download_data(es=None, ta=None, fpath=""):
    """Downloads the NREL EFS data for the specified electrification scenarios and
    technology advancements.

    :param set/list es: The electrification scenarios that will be downloaded. Can
        choose any of: *'Reference'*, *'Medium'*, *'High'*, or *'All'*. Defaults to
        None.
    :param set/list ta: The technology advancements that will be downloaded. Can
        choose any of: *'Slow'*, *'Moderate'*, *'Rapid'*, or *'All'*. Defaults to
        None.
    :param str fpath: The file path to which the NREL EFS data will be downloaded.
    :raises TypeError: if es and ta are not input as a set or list, if fpath is not
        input as a str, or if the components of es and ta are not input as str.
    :raises ValueError: if the components of es and ta are not valid.
    :raises NotImplementedError: if the method for uncompressing a file that has been
        compressed a certain way is not implemented.
    :raises OSError: if the specified 7zip directory cannot be found (on Windows
        machines) or if compression outside of Python's zipfile module is attempted on
        non-Windows machines.
    """

    # Account for the immutable default parameters
    if es is None:
        es = {"All"}
    if ta is None:
        ta = {"All"}

    # Check that the inputs are of an appropriate type
    if not isinstance(es, (set, list)):
        raise TypeError("Electrification scenarios must be input as a set or list.")
    if not isinstance(ta, (set, list)):
        raise TypeError("Technology advancements must be input as a set or list.")
    if not isinstance(fpath, str):
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
    if len(fpath) == 0:
        fpath = os.getcwd()

    # Download each of the specified load profiles
    z = {}
    for i in es:
        z[i] = {}
        for j in ta:
            # Assign path and file names
            zip_name = "EFSLoadProfile_" + i + "_" + j + ".zip"
            url = "https://data.nrel.gov/system/files/126/" + zip_name
            zip_path = os.path.join(fpath, zip_name)

            # Save a local copy of the .zip file for extraction
            r = requests.get(url, stream=True)
            if r.status_code != requests.codes.ok:
                r.raise_for_status()
            open(zip_name, "wb").write(r.content)
            print(zip_name + " successfully downloaded!")

            # Store the data in memory to try extracting with Python's zipfile module
            z[i][j] = zipfile.ZipFile(io.BytesIO(r.content))

    # Try to extract the .csv file from the .zip file
    zf_works = True
    for i in es:
        for j in ta:
            # Assign path and file names
            zip_name = "EFSLoadProfile_" + i + "_" + j + ".zip"
            csv_name = "EFSLoadProfile_" + i + "_" + j + ".csv"
            zip_path = os.path.join(fpath, zip_name)

            try:
                if zf_works:
                    # Try the zipfile module first
                    z[i][j].extractall(fpath)
                    print(csv_name + " successfully extracted!")
                else:
                    # Bypass the zipfile module if it does not work on the first file
                    raise NotImplementedError
            except NotImplementedError:
                if zf_works:
                    print(
                        zip_name
                        + " is compressed using a method that is not supported by the"
                        + " zipfile module."
                    )
                    print("Trying other extraction methods supported by your OS.")
                    zf_works = False

                # Try other extraction methods depending on operating system
                if platform.system() == "Windows":
                    try:
                        # Windows Command Line does not support this type of compression
                        # Try using 7zip, if it is installed in the default location
                        sz_path = "C:/Program Files/7-Zip/7z.exe"
                        if not os.path.isfile(sz_path):
                            print(
                                "7zip is not in this directory or is not installed. "
                                + "Extract all data manually (refer to documentation)."
                            )
                            return
                        subprocess.check_call(
                            'cmd /c powershell -c & "'
                            + sz_path
                            + '" x "'
                            + zip_path
                            + '" -o"'
                            + fpath
                            + '" -y'
                        )
                        os.remove(zip_path)
                        print(csv_name + " successfully extracted!")
                    except subprocess.CalledProcessError:
                        print(csv_name + " could not be extracted using 7zip.")
                        print("Extract all data manually (refer to documentation).")
                        return
                elif platform.system() in {"Darwin", "Linux"}:
                    try:
                        # Try unzipping using the Terminal
                        subprocess.check_call(["unzip", "-o", zip_path, "-d", fpath])
                        os.remove(zip_path)
                        print(csv_name + " successfully extracted!")
                    except subprocess.CalledProcessError:
                        print(csv_name + " could not be extracted using the Terminal.")
                        print("Extract all data manually (refer to documentation).")
                        return
                else:
                    raise OSError("This operating system is not supported.")


def partition_by_sector(es, ta, year, sect=None, fpath="", save=True):
    """Creates .csv files for each of the specified sectors given a specified
    electrification scenario and technology advancement.

    :param str es: An electrification scenario. Can choose one of: *'Reference'*,
        *'Medium'*, or *'High'*.
    :param str ta: A technology advancement. Can choose one of: *'Slow'*, *'Moderate'*,
        or *'Rapid'*.
    :param int year: The selected year's worth of demand data. Can choose one of: 2018,
        2020, 2024, 2030, 2040, or 2050.
    :param set/list sect: The sectors for which .csv files are to be created. Can
        choose any of: *'Transportation'*, *'Residential'*, *'Commercial'*,
        *'Industrial'*, or *'All'*. Defaults to None.
    :param str fpath: The file path where the demand data might be saved and to where
        the sectoral data will be saved.
    :param bool save: Determines whether or not the .csv file is saved. Defaults to
        True. If the file is saved, it is saved to the same location as fpath.
    :return: (*dict*) -- A dict of pandas.DataFrame objects that contain demand data
        for each state and time step in the specified sectors.
    :raises TypeError: if es and ta are not input as str, if year is not input as an
        int, if sect is not input as a set or list, if fpath is not input as a str, or
        if the components of sect are not input as str.
    :raises ValueError: if es, ta, year, or the components of sect are not valid.
    """

    # Account for the immutable default parameters
    if sect is None:
        sect = {"All"}

    # Check that the inputs are of an appropriate type
    if not isinstance(es, str):
        raise TypeError("Electrification scenario must be input as a str.")
    if not isinstance(ta, str):
        raise TypeError("Technology advancement must be input as a str.")
    if not isinstance(year, int):
        raise TypeError("The year must be input as an int.")
    if not isinstance(sect, (set, list)):
        raise TypeError("Sector inputs must be input as a set or list.")
    if not isinstance(fpath, str):
        raise TypeError("The file path must be input as a str.")

    # Check that the components of sect are str
    if not all(isinstance(x, str) for x in sect):
        raise TypeError("Each individual sector must be input as a str.")

    # Reformat components of es, ta, and sect
    es = es.capitalize()
    ta = ta.capitalize()
    sect = {x.capitalize() for x in sect}
    if "All" in sect:
        sect = {"Transportation", "Residential", "Commercial", "Industrial"}

    # Check that the components of es, ta, year, and sect are valid
    if es not in {"Reference", "Medium", "High"}:
        raise ValueError(f"{es} is not a valid electrification scenario.")
    if ta not in {"Slow", "Moderate", "Rapid"}:
        raise ValueError(f"{ta} is not a valid technology advancement.")
    if year not in {2018, 2020, 2024, 2030, 2040, 2050}:
        raise ValueError(f"{year} is not a valid year.")
    if not sect.issubset({"Transportation", "Residential", "Commercial", "Industrial"}):
        invalid_sect = sect - {
            "Transportation",
            "Residential",
            "Commercial",
            "Industrial",
        }
        raise ValueError(f'Invalid sectors: {", ".join(invalid_sect)}')

    # Access the actual path if not already provided
    if len(fpath) == 0:
        fpath = os.getcwd()

    # Specify the file name and path
    csv_name = "EFSLoadProfile_" + es + "_" + ta + ".csv"
    csv_path = os.path.join(fpath, csv_name)

    # Download the specified NREL EFS dataset if it is not already downloaded
    if not os.path.isfile(csv_path):
        download_data({es}, {ta}, fpath)

    # Load the data from the downloaded .csv file as a DataFrame
    df = pd.read_csv(csv_path)

    # Trim the DataFrame for only the specified year
    df = df.loc[df["Year"] == year]

    # Drop unnecessary "Year", "Electrification", and "TechnologyAdvancement" columns
    df.drop(columns=["Year", "Electrification", "TechnologyAdvancement"], inplace=True)

    # Sum by sector and state
    df = df.groupby(["LocalHourID", "State", "Sector"], as_index=False).sum()

    # Split the demand DataFrame by sector
    sect_dem = {
        i: df[df["Sector"] == i]
        .drop(columns=["Sector"])
        .groupby(["LocalHourID", "State"])
        .sum()
        .unstack()
        for i in sect
    }
    sect_dem = {
        i: sect_dem[i].set_axis(sorted(set(abv2state) - {"AK", "HI"}), axis="columns")
        for i in sect
    }

    # Add extra day's worth of demand to account for leap year
    sect_dem = {i: account_for_leap_year(sect_dem[i]) for i in sect}

    # Include the appropriate time stamps for the local time (with year=2016)
    sect_dem = {
        i: sect_dem[i].set_axis(
            pd.date_range("2016-01-01", "2017-01-01", freq="H", closed="left"),
            axis="index",
        )
        for i in sect
    }
    sect_dem = {i: sect_dem[i].rename_axis("Local Time", axis="index") for i in sect}

    # Save the sectoral DataFrames to .csv files, if desired
    if save:
        for i in sect:
            new_csv_name = i + "_Demand_" + es + "_" + ta + "_" + str(year) + ".csv"
            new_csv_path = os.path.join(fpath, new_csv_name)
            sect_dem[i].to_csv(new_csv_path)

    # Return the dictionary containing the formatted sectoral demand data
    return sect_dem


def account_for_leap_year(df):
    """Creates an additional day's worth of demand data to account for the additional
    day that occurs during leap years. This function takes an 8760-hour DataFrame as
    input and returns an 8784-hour DataFrame. To prevent the weekly structure of the
    input DataFrame from being disrupted, the additional 24 hours of demand are merely
    added to the end of the input 8760-hour DataFrame for each state. The additional 24
    hours of demand are set equal to the demand profile for January 2nd because January
    2nd and December 31st occur on the same day of the week during a leap year.

    :param pandas.DataFrame df: DataFrame of sectoral demand data. Rows are each hour
        of the 8760 hours and Columns are the abbreviations of each state of the
        contiguous U.S.
    :return: (*pandas.DataFrame*) -- Sectoral demand data with 8784 hours and of a
        similar form to the input DataFrame.
    :raises ValueError: if the dimensions of the input DataFrame do not reflect 8760
        hours or 48 states.
    """

    # Check the elements of the input DataFrame
    if df.index.size != 8760:
        raise ValueError("The input DataFrame does not have 8760 hours.")
    if list(df.columns.values) != sorted(set(abv2state) - {"AK", "HI"}):
        raise ValueError("The input DataFrame does not include all 48 states.")

    # Get the demand for each state and each hour on January 2nd
    jan2_dem = df.iloc[24:48]

    # Append to the input DataFrame to create an 8784-hour profile
    new_df = df.append(jan2_dem, ignore_index=True)

    # Return the 8784-hour profile
    return new_df

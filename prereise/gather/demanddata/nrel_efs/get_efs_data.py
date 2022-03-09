import io
import os
import platform
import subprocess
import zipfile

import pandas as pd
import requests

from prereise.gather.const import abv2state


def download_demand_data(
    es=None, ta=None, fpath="", sz_path="C:/Program Files/7-Zip/7z.exe"
):
    """Downloads the NREL EFS base demand data for the specified electrification
    scenarios and technology advancements.

    :param set/list es: The electrification scenarios that will be downloaded. Can
        choose any of: *'Reference'*, *'Medium'*, *'High'*, or *'All'*. Defaults to
        None.
    :param set/list ta: The technology advancements that will be downloaded. Can
        choose any of: *'Slow'*, *'Moderate'*, *'Rapid'*, or *'All'*. Defaults to
        None.
    :param str fpath: The file path to which the NREL EFS data will be downloaded.
    :param str sz_path: The file path on Windows machines that points to the 7-Zip tool.
        Defaults to *'C:/Program Files/7-Zip/7z.exe'*.
    :raises TypeError: if sz_path is not input as a str.
    """

    # Account for the immutable default parameters
    if es is None:
        es = {"All"}
    if ta is None:
        ta = {"All"}

    # Check the inputs
    es = _check_electrification_scenarios_for_download(es)
    ta = _check_technology_advancements_for_download(ta)
    fpath = _check_path(fpath)
    if not isinstance(sz_path, str):
        raise TypeError("The 7-Zip path must be input as a str.")

    # Download each of the specified load profiles
    z = {}
    for i in es:
        z[i] = {}
        for j in ta:
            # Assign path and file names
            zip_name = f"EFSLoadProfile_{i}_{j}.zip"
            url = f"https://data.nrel.gov/system/files/126/{zip_name}"

            # Store the data in memory to try extracting with Python's zipfile module
            z[i][j] = _download_data(zip_name, url, fpath)

    # Try to extract the .csv file from the .zip file
    zf_works = True
    for i in es:
        for j in ta:
            # Assign path and file names
            zip_name = f"EFSLoadProfile_{i}_{j}.zip"
            csv_name = f"EFSLoadProfile_{i}_{j}.csv"

            # Try to extract the .csv file from the .zip file
            zf_works = _extract_data(
                z[i][j], zf_works, zip_name, csv_name, fpath, sz_path
            )


def download_flexibility_data(
    es=None, fpath="", sz_path="C:/Program Files/7-Zip/7z.exe"
):
    """Downloads the NREL EFS flexibility data for the specified electrification
    scenarios.

    :param set/list es: The electrification scenarios that will be downloaded. Can
        choose any of: *'Reference'*, *'Medium'*, *'High'*, or *'All'*. Defaults to
        None.
    :param str fpath: The file path to which the NREL EFS data will be downloaded.
    :param str sz_path: The file path on Windows machines that points to the 7-Zip tool.
        Defaults to *'C:/Program Files/7-Zip/7z.exe'*.
    :raises TypeError: if sz_path is not input as a str.
    """

    # Account for the immutable default parameter
    if es is None:
        es = {"All"}

    # Check the inputs
    es = _check_electrification_scenarios_for_download(es)
    fpath = _check_path(fpath)
    if not isinstance(sz_path, str):
        raise TypeError("The 7-Zip path must be input as a str.")

    # Download each of the specified load profiles
    z = {}
    for i in es:
        # Assign path and file names
        zip_name = f"EFS Flexible Load Profiles - {i} Electrification.zip"
        url = f"https://data.nrel.gov/system/files/127/{zip_name}"

        # Store the data in memory to try extracting with Python's zipfile module
        z[i] = _download_data(zip_name, url, fpath)

    # Try to extract the .csv file from the .zip file
    zf_works = True
    for i in es:
        # Assign path and file names
        zip_name = f"EFS Flexible Load Profiles - {i} Electrification.zip"
        csv_name = f"EFSFlexLoadProfiles_{i}.csv"

        # Try to extract the .csv file from the .zip file
        zf_works = _extract_data(z[i], zf_works, zip_name, csv_name, fpath, sz_path)


def _check_electrification_scenarios_for_download(es):
    """Checks the electrification scenarios input to :py:func:`download_demand_data`
    and :py:func:`download_flexibility_data`.

    :param set/list es: The input electrification scenarios that will be checked. Can
        be any of: *'Reference'*, *'Medium'*, *'High'*, or *'All'*.
    :return: (*set*) -- The formatted set of electrification scenarios.
    :raises TypeError: if es is not input as a set or list, or if the components of es
        are not input as str.
    :raises ValueError: if the components of es are not valid.
    """

    # Check that the input is of an appropriate type
    if not isinstance(es, (set, list)):
        raise TypeError("Electrification scenarios must be input as a set or list.")

    # Check that the components of es are str
    if not all(isinstance(x, str) for x in es):
        raise TypeError("Individual electrification scenarios must be input as a str.")

    # Reformat components of es
    es = {x.capitalize() for x in es}
    if "All" in es:
        es = {"Reference", "Medium", "High"}

    # Check that the components of es are valid
    if not es.issubset({"Reference", "Medium", "High"}):
        invalid_es = es - {"Reference", "Medium", "High"}
        raise ValueError(f'Invalid electrification scenarios: {", ".join(invalid_es)}')

    # Return the reformatted es
    return es


def _check_technology_advancements_for_download(ta):
    """Checks the technology advancements input to :py:func:`download_demand_data` and
    :py:func:`download_flexibility_data`.

    :param set/list ta: The input technology advancements that will be checked. Can be
        any of: *'Slow'*, *'Moderate'*, *'Rapid'*, or *'All'*.
    :return: (*set*) -- The formatted set of technology advancements.
    :raises TypeError: if ta is not input as a set or list, or if the components of ta
        are not input as str.
    :raises ValueError: if the components of ta are not valid.
    """

    # Check that the input is of an appropriate type
    if not isinstance(ta, (set, list)):
        raise TypeError("Technology advancements must be input as a set or list.")

    # Check that the components of ta are str
    if not all(isinstance(x, str) for x in ta):
        raise TypeError("Individual technology advancements must be input as a str.")

    # Reformat components of ta
    ta = {x.capitalize() for x in ta}
    if "All" in ta:
        ta = {"Slow", "Moderate", "Rapid"}

    # Check that the components of ta are valid
    if not ta.issubset({"Slow", "Moderate", "Rapid"}):
        invalid_ta = ta - {"Slow", "Moderate", "Rapid"}
        raise ValueError(f'Invalid electrification scenarios: {", ".join(invalid_ta)}')

    # Return the reformatted ta
    return ta


def _check_path(fpath):
    """Checks the file path input to :py:func:`download_demand_data`,
    :py:func:`download_flexibility_data`, :py:func:`partition_demand_by_sector`, and
    :py:func:`partition_flexibility_by_sector`.

    :param str fpath: The input file path.
    :return: (*str*) -- The necessary file path in case it needed to be accessed.
    :raises TypeError: if fpath is not input as a str.
    """

    # Check that the input is of an appropriate type
    if not isinstance(fpath, str):
        raise TypeError("The file path must be input as a str.")

    # Access the actual path if not already provided
    if len(fpath) == 0:
        fpath = os.getcwd()

    # Return fpath in case it had to be accessed
    return fpath


def _download_data(zip_name, url, fpath):
    """Downloads the specified NREL EFS data for :py:func:`download_demand_data` and
    :py:func:`download_flexibility_data`.

    :param str zip_name: The name of the specified .zip file.
    :param str url: The specified URL to access the desired .zip file.
    :param str fpath: The input file path.
    :return: (*zipfile.ZipFile*) -- The .zip file stored in memory for attempted
        extraction using Python's zipfile module.
    """

    # Save a local copy of the .zip file for extraction
    r = requests.get(url, stream=True)
    if r.status_code != requests.codes.ok:
        r.raise_for_status()
    with open(zip_name, "wb") as f:
        f.write(r.content)
    print(f"{zip_name} successfully downloaded!")

    # Return the data to try extracting with Python's zipfile module
    return zipfile.ZipFile(io.BytesIO(r.content))


def _extract_data(z, zf_works, zip_name, csv_name, fpath, sz_path):
    """Extracts the .csv file containing NREL EFS data from the downloaded .zip file.
    First attempts extraction using Python's zipfile module, then attempts other
    OS-dependent methods, as needed.

    :param zipfile.ZipFile z: The .zip file stored in memory for attempted extraction
        using Python's zipfile module.
    :param bool zf_works: An indicator flag that states whether or not Python's zipfile
        module works for extraction. True if Python's zipfile module works, else False.
    :param str zip_name: The name of the specified .zip file.
    :param str csv_name: The name of the .csv file contained within the .zip file.
    :param str fpath: The input file path.
    :param str sz_path: The file path on Windows machines that points to the 7-Zip tool.
    :return: (*bool*) -- The indicator flag that states whether or not Python's zipfile
        module works for extraction. This is returned to prevent checking Python's
        zipfile module if it does not work the first time (in the event multiple .zip
        files require extraction).
    :raises NotImplementedError: if Python's zipfile module cannot extract the .csv
        file.
    :raises OSError: if an OS other than Windows, macOS, or Linux is identified.
    """

    # Assign the path name of the .zip file
    zip_path = os.path.join(fpath, zip_name)

    try:
        if zf_works:
            # Try the zipfile module first
            z.extractall(fpath)
            print(f"{csv_name} successfully extracted!")
        else:
            # Bypass the zipfile module if it does not work on the first file
            raise NotImplementedError
    except NotImplementedError:
        if zf_works:
            print(
                f"{zip_name} is compressed using a method that is not supported by the "
                + "zipfile module."
            )
            print("Trying other extraction methods supported by your OS.")
            zf_works = False

        # Try other extraction methods depending on operating system
        if platform.system() == "Windows":
            try:
                # Windows Command Line does not support this type of compression
                # Try using 7-Zip, if it is installed in the specified location
                if not os.path.isfile(sz_path):
                    print(
                        "7-Zip is not in this directory or is not installed. "
                        + "Extract all data manually (refer to documentation)."
                    )
                    return
                subprocess.check_call(
                    f'cmd /c powershell -c & "{sz_path}" x "{zip_path}" -o"{fpath}" -y'
                )
                os.remove(zip_path)
                print(f"{csv_name} successfully extracted!")
            except subprocess.CalledProcessError:
                print(f"{csv_name} could not be extracted using 7-Zip.")
                print("Extract all data manually (refer to documentation).")
                return
        elif platform.system() in {"Darwin", "Linux"}:
            try:
                # Try unzipping using the Terminal
                subprocess.check_call(["unzip", "-o", zip_path, "-d", fpath])
                os.remove(zip_path)
                print(f"{csv_name} successfully extracted!")
            except subprocess.CalledProcessError:
                print(f"{csv_name} could not be extracted using the Terminal.")
                print("Extract all data manually (refer to documentation).")
                return
        else:
            raise OSError("This operating system is not supported.")

    # Return the flag that indicates whether or not Python's zipfile module works
    return zf_works


def partition_demand_by_sector(es, ta, year, sect=None, fpath="", save=False):
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
        False. If the file is saved, it is saved to the same location as fpath.
    :return: (*dict*) -- A dict of pandas.DataFrame objects that contain demand data
        for each state and time step in the specified sectors.
    :raises TypeError: if save is not input as a bool.
    """

    # Account for the immutable default parameters
    if sect is None:
        sect = {"All"}

    # Check the inputs
    es = _check_electrification_scenarios_for_partition(es)
    ta = _check_technology_advancements_for_partition(ta)
    _check_year(year)
    sect = _check_sectors(sect)
    fpath = _check_path(fpath)
    if not isinstance(save, bool):
        raise TypeError("save must be input as a bool.")

    # Specify the file name and path
    csv_name = f"EFSLoadProfile_{es}_{ta}.csv"
    csv_path = os.path.join(fpath, csv_name)

    # Download the specified NREL EFS dataset if it is not already downloaded
    if not os.path.isfile(csv_path):
        download_demand_data({es}, {ta}, fpath)

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
        .groupby(["LocalHourID", "State"], sort=True)
        .sum()
        .unstack()
        for i in sect
    }
    sect_dem = {
        i: sect_dem[i].set_axis(
            sect_dem[i].columns.get_level_values("State"), axis="columns"
        )
        for i in sect
    }

    # Add extra day's worth of demand to account for leap year
    sect_dem = {i: account_for_leap_year(sect_dem[i]) for i in sect}

    # Include the appropriate timestamps for the local time (with year=2016)
    sect_dem = {
        i: sect_dem[i].set_axis(
            pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
            axis="index",
        )
        for i in sect
    }
    sect_dem = {i: sect_dem[i].rename_axis("Local Time", axis="index") for i in sect}

    # Save the sectoral DataFrames to .csv files, if desired
    if save:
        for i in sect:
            new_csv_name = f"{i}_Demand_{es}_{ta}_{year}.csv"
            new_csv_path = os.path.join(fpath, new_csv_name)
            sect_dem[i].to_csv(new_csv_path)

    # Return the dictionary containing the formatted sectoral demand data
    return sect_dem


def partition_flexibility_by_sector(
    es, ta, flex, year, sect=None, fpath="", save=False
):
    """Creates .csv files for each of the specified sectors given a specified
    electrification scenario and technology advancement.

    :param str es: An electrification scenario. Can choose one of: *'Reference'*,
        *'Medium'*, or *'High'*.
    :param str ta: A technology advancement. Can choose one of: *'Slow'*, *'Moderate'*,
        or *'Rapid'*.
    :param str flex: A flexibility scenario. Can choose one of: *'Base'* or
        *'Enhanced'*.
    :param int year: The selected year's worth of demand data. Can choose one of: 2018,
        2020, 2024, 2030, 2040, or 2050.
    :param set/list sect: The sectors for which .csv files are to be created. Can
        choose any of: *'Transportation'*, *'Residential'*, *'Commercial'*,
        *'Industrial'*, or *'All'*. Defaults to None.
    :param str fpath: The file path where the demand data might be saved and to where
        the sectoral data will be saved.
    :param bool save: Determines whether or not the .csv file is saved. Defaults to
        False. If the file is saved, it is saved to the same location as fpath.
    :return: (*dict*) -- A dict of pandas.DataFrame objects that contain flexibility
        data for each state and time step in the specified sectors.
    :raises TypeError: if save is not input as a bool.
    """

    # Account for the immutable default parameters
    if sect is None:
        sect = {"All"}

    # Check the inputs
    es = _check_electrification_scenarios_for_partition(es)
    ta = _check_technology_advancements_for_partition(ta)
    flex = _check_flexibility_scenario(flex)
    _check_year(year)
    sect = _check_sectors(sect)
    fpath = _check_path(fpath)
    if not isinstance(save, bool):
        raise TypeError("save must be input as a bool.")

    # Specify the file name and path
    csv_name = f"EFSFlexLoadProfiles_{es}.csv"
    csv_path = os.path.join(fpath, csv_name)

    # Download the specified NREL EFS dataset if it is not already downloaded
    if not os.path.isfile(csv_path):
        download_flexibility_data({es}, fpath)

    # Load the data from the downloaded .csv file as a DataFrame
    df = pd.read_csv(csv_path)

    # Trim the DataFrame for only the specified year
    df = df.loc[df["Year"] == year]

    # Trim the DataFrame for only the specified technology advancement
    df = df.loc[df["TechnologyAdvancement"] == ta]

    # Trim the DataFrame for only the specified flexibility scenario
    df = df.loc[df["Flexibility"] == flex]

    # Drop unnecessary "Year", "Electrification", and "TechnologyAdvancement" columns
    df.drop(
        columns=["Year", "Electrification", "TechnologyAdvancement", "Flexibility"],
        inplace=True,
    )

    # Split the flexibility DataFrame by sector
    sect_flex = {
        i: df[df["Sector"] == i]
        .drop(columns=["Sector"])
        .groupby(["LocalHourID", "State"], sort=True)
        .sum()
        .unstack()
        for i in sect
    }
    sect_flex = {
        i: sect_flex[i].set_axis(
            sect_flex[i].columns.get_level_values("State"), axis="columns"
        )
        for i in sect
    }

    # Add extra day's worth of flexibility to account for leap year
    sect_flex = {i: account_for_leap_year(sect_flex[i]) for i in sect}

    # Include the appropriate timestamps for the local time (with year=2016)
    sect_flex = {
        i: sect_flex[i].set_axis(
            pd.date_range("2016-01-01", "2017-01-01", freq="H", inclusive="left"),
            axis="index",
        )
        for i in sect
    }
    sect_flex = {i: sect_flex[i].rename_axis("Local Time", axis="index") for i in sect}

    # Save the sectoral DataFrames to .csv files, if desired
    if save:
        for i in sect:
            new_csv_name = f"{i}_{flex}_Flexibility_{es}_{ta}_{year}.csv"
            new_csv_path = os.path.join(fpath, new_csv_name)
            sect_flex[i].to_csv(new_csv_path)

    # Return the dictionary containing the formatted sectoral flexibility data
    return sect_flex


def _check_electrification_scenarios_for_partition(es):
    """Checks the electrification scenario input to
    :py:func:`partition_demand_by_sector` and
    :py:func:`partition_flexibility_by_sector`.

    :param str es: The input electrification scenario that will be checked. Can be any
        of: *'Reference'*, *'Medium'*, or *'High'*.
    :return: (*str*) -- The formatted electrification scenario.
    :raises TypeError: if es is not input as a str.
    :raises ValueError: if es is not valid.
    """

    # Check that the input is of an appropriate type
    if not isinstance(es, str):
        raise TypeError("Electrification scenario must be input as a str.")

    # Reformat es
    es = es.capitalize()

    # Check that es is valid
    if es not in {"Reference", "Medium", "High"}:
        raise ValueError(f"{es} is not a valid electrification scenario.")

    # Return the reformatted es
    return es


def _check_technology_advancements_for_partition(ta):
    """Checks the technology advancment input to :py:func:`partition_demand_by_sector`
    and :py:func:`partition_flexibility_by_sector`.

    :param str ta: The input technology advancement that will be checked. Can be any of:
        *'Slow'*, *'Moderate'*, or *'Rapid'*.
    :return: (*str*) -- The formatted technology advancement.
    :raises TypeError: if ta is not input as a str.
    :raises ValueError: if ta is not valid.
    """

    # Check that the input is of an appropriate type
    if not isinstance(ta, str):
        raise TypeError("Technology advancement must be input as a str.")

    # Reformat ta
    ta = ta.capitalize()

    # Check that ta is valid
    if ta not in {"Slow", "Moderate", "Rapid"}:
        raise ValueError(f"{ta} is not a valid technology advancement.")

    # Return the reformatted ta
    return ta


def _check_flexibility_scenario(flex):
    """Checks the flexibility scenario input to
    :py:func:`partition_flexibility_by_sector`.

    :param str flex: The input flexibility scenario that will be checked. Can be any of:
        *'Base'* or *'Enhanced'*.
    :return: (*set*) -- The formatted set of flexibility scenarios.
    :raises TypeError: if flex is not input as a set or list, or if the components of
        flex are not input as str.
    :raises ValueError: if the components of flex are not valid.
    """

    # Check that the input is of an appropriate type
    if not isinstance(flex, str):
        raise TypeError("Flexibility scenario must be input as a str.")

    # Reformat flex
    flex = flex.capitalize()

    # Check that flex is valid
    if flex not in {"Base", "Enhanced"}:
        raise ValueError(f"{flex} is not a valid flexibility scenario.")

    # Return the reformatted flex
    return flex


def _check_year(year):
    """Checks the year input to :py:func:`partition_demand_by_sector` and
    :py:func:`partition_flexibility_by_sector`.

    :param int year: The selected year's worth of demand data. Can be any of: 2018,
        2020, 2024, 2030, 2040, or 2050.
    :raises TypeError: if year is not input as an int.
    :raises ValueError: if year is not valid.
    """

    # Check that the input is of an appropriate type
    if not isinstance(year, int):
        raise TypeError("The year must be input as an int.")

    # Check that year is valid
    if year not in {2018, 2020, 2024, 2030, 2040, 2050}:
        raise ValueError(f"{year} is not a valid year.")


def _check_sectors(sect):
    """Checks the sectors input to :py:func:`partition_demand_by_sector` and
    :py:func:`partition_flexibility_by_sector`.

    :param set/list sect: The input sectors. Can be any of: *'Transportation'*,
        *'Residential'*, *'Commercial'*, *'Industrial'*, or *'All'*.
    :return: (*set*) -- The formatted set of sectors.
    :raises TypeError: if sect is not input as a set or list, or if the components of
        sect are not input as str.
    :raises ValueError: if the components of sect are not valid.
    """

    # Check that the input is of an appropriate type
    if not isinstance(sect, (set, list)):
        raise TypeError("Sector inputs must be input as a set or list.")

    # Check that the components of sect are str
    if not all(isinstance(x, str) for x in sect):
        raise TypeError("Each individual sector must be input as a str.")

    # Reformat components of sect
    sect = {x.capitalize() for x in sect}
    if "All" in sect:
        sect = {"Transportation", "Residential", "Commercial", "Industrial"}

    # Check that the components of sect are valid
    if not sect.issubset({"Transportation", "Residential", "Commercial", "Industrial"}):
        invalid_sect = sect - {
            "Transportation",
            "Residential",
            "Commercial",
            "Industrial",
        }
        raise ValueError(f'Invalid sectors: {", ".join(invalid_sect)}')

    # Return the reformatted sect
    return sect


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
    new_df = pd.concat([df, jan2_dem], ignore_index=True)

    # Return the 8784-hour profile
    return new_df

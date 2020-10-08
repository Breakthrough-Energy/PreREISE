import io
import os
import platform
import zipfile

import pandas as pd
import requests
from powersimdata.network.usa_tamu.constants.zones import abv2state


def download_data(es={"All"}, ta={"All"}, path=""):
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
                        print("Extract the data manually.")
                elif platform.system() == "Darwin":
                    # TODO: Create the means to extract through the terminal
                    raise OSError("Other extraction methods not implemented in MacOS.")
                elif platform.system() == "Linux":
                    # TODO: Create the means to extract through the terminal
                    raise OSError("Other extraction methods not implemented in Linux.")
                else:
                    raise OSError("Not a valid operating system.")


def partition_by_sector(es, ta, year, sect={"all"}, path=""):
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
        *'Industrial'*, or *'All'*. Defaults to *'All'*.
    :param str path: The file path to which the sectoral data will be saved.
    """

    # Check that the inputs are of an appropriate type
    if not isinstance(es, str):
        raise TypeError("Electrification scenario must be input as a str.")
    if not isinstance(ta, str):
        raise TypeError("Technology advancement must be input as a str.")
    if not isinstance(year, int):
        raise TypeError("The year must be input as an int.")
    if not isinstance(sect, (set, list)):
        raise TypeError("Sector inputs must be input as a set or list.")
    if not isinstance(path, str):
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
    if len(path) == 0:
        path = os.getcwd()
        path = path.replace("\\", "/")

    # Specify the file name and path
    csv_name = "EFSLoadProfile_" + es + "_" + ta + ".csv"
    if path.endswith("/"):
        csv_path = path + csv_name
    else:
        csv_path = path + "/" + csv_name

    # Download the specified NREL EFS dataset if it is not already downloaded
    if not os.path.isfile(csv_path):
        download_data({es}, {ta}, path)

    # Load the data from the downloaded .csv file as a DataFrame
    df = pd.read_csv(csv_path)

    # Trim the DataFrame for only the specified year
    df = df.loc[df["Year"] == year]

    # Drop unnecessary "Year", "Electrification", and "TechnologyAdvancement" columns
    df.drop(columns=["Year", "Electrification", "TechnologyAdvancement"], inplace=True)

    # Sum by sector and state
    df = df.groupby(["LocalHourID", "State", "Sector"], as_index=False).sum()

    # Access the specified sectors
    sect_ref = {}
    sect_dem = {}
    for i in sect:
        sect_ref[i] = df.loc[df["Sector"] == i]

        # Create new DataFrame, where indices and columns are from hours and states
        sect_dem[i] = pd.DataFrame()
        for j in sorted(list(set(abv2state) - {"AK", "HI"})):
            sect_dem[i][j] = sect_ref[i].loc[sect_ref[i]["State"] == j, "LoadMW"].values

        # Add extra day for leap year and include time stamps
        sect_dem[i] = account_for_leap_year(sect_dem[i])
        sect_dem[i].set_index(
            pd.date_range("2016-01-01", "2017-01-01", freq="H", closed="left"),
            inplace=True,
        )
        sect_dem[i].index.name = "UTC Time"

        # Save the sectoral DataFrames to .csv files
        new_csv_name = i + "_Demand_" + es + "_" + ta + "_" + str(year) + ".csv"
        if path.endswith("/"):
            new_csv_path = path + new_csv_name
        else:
            new_csv_path = path + "/" + new_csv_name
        sect_dem[i].to_csv(new_csv_path)

    # Delete the original .csv file
    os.remove(csv_path)


def account_for_leap_year(df):
    """Creates an additional day's worth of demand data to account for the additional
    day that occurs during leap years. This function takes an 8760-hour DataFrame as
    input and returns an 8784-hour DataFrame. To prevent the weekly structure of the
    input DataFrame from being disrupted, the additional 24 hours of demand are merely
    added to the end of hte input 8760-hour DataFrame for each state. The additional 24
    hours of demand are set equal to the demand profile for January 2nd because January
    2nd and December 31st occur on the same day of the week during a leap year.

    :param pandas.DataFrame df: DataFrame of sectoral demand data. Rows are each hour
        of the 8760 hours and Columns are the abbreviations of each state of the
        contiguous U.S.
    :return: (*pandas.DataFrame*) -- Sectoral demand data with 8784 hours and of a
        similar form to the input DataFrame.
    """

    # Check the elements of the input DataFrame
    if df.index.size != 8760:
        raise ValueError("The input DataFrame does not have 8760 hours.")
    if list(df.columns.values) != sorted(list(set(abv2state) - {"AK", "HI"})):
        raise ValueError("The input DataFrame does not include all 48 states.")

    # Get the demand for each state and each hour on January 2nd
    jan2_dem = df.iloc[24:48]

    # Append to the input DataFrame to create an 8784-hour profile
    new_df = df.append(jan2_dem, ignore_index=True)

    # Return the 8784-hour profile
    return new_df

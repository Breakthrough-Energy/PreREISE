import os
import shutil

from powersimdata.input import const as psd_const

from prereise.gather.griddata.hifld.const import powersimdata_column_defaults
from prereise.gather.griddata.hifld.data_process.demand import assign_demand_to_buses
from prereise.gather.griddata.hifld.data_process.generators import build_plant
from prereise.gather.griddata.hifld.data_process.profiles import build_solar
from prereise.gather.griddata.hifld.data_process.transmission import build_transmission


def create_csvs(output_folder, nrel_email, nrel_api_key, solar_kwargs={}):
    """Process HIFLD source data to CSVs compatible with PowerSimData.

    :param str output_folder: directory to write CSVs to.
    :param str nrel_email: email used to`sign up <https://developer.nrel.gov/signup/>`_.
    :param str nrel_api_key: API key.
    :param dict solar_kwargs: keyword arguments to pass to
        :func:`prereise.gather.solardata.nsrdb.sam.retrieve_data_individual`.
    """
    full_tables = create_grid(output_folder)
    create_profiles(
        full_tables["plant"], nrel_email, nrel_api_key, output_folder, solar_kwargs
    )


def create_grid(output_folder=None):
    """Process a table of plant data to produce grid CSVs compatible with PowerSimData.

    :param str output_folder: directory to write CSVs to. If None, CSVs will not be
        written (just returned).
    :return: (*dict*) -- keys are strings for table names, values are dataframes that
        correspond to those tables. These dataframes have all available columns for
        each table, even though the CSV files which are written are limited to only the
        columns expected by powersimdata.
    """
    # Process grid data from original sources
    branch, bus, substation, dcline = build_transmission()
    plant = build_plant(bus, substation)
    assign_demand_to_buses(substation, branch, plant, bus)

    full_tables = {}
    full_tables["branch"] = branch
    full_tables["dcline"] = dcline
    full_tables["sub"] = substation
    # Separate tables as necessary to match PowerSimData format
    # bus goes to bus and bus2sub
    full_tables["bus2sub"] = bus[["sub_id", "interconnect"]]
    full_tables["bus"] = bus.drop(["sub_id"], axis=1)
    # plant goes to plant and gencost
    full_tables["gencost"] = plant[["c0", "c1", "c2", "interconnect"]].copy()
    full_tables["plant"] = plant.drop(["c0", "c1", "c2"], axis=1)

    # Fill in missing column values
    for name, defaults in powersimdata_column_defaults.items():
        full_tables[name] = full_tables[name].assign(**defaults)

    if output_folder is not None:
        os.makedirs(output_folder, exist_ok=True)
        # Filter to only the columns expected by PowerSimData, in the expected order
        powersimdata_outputs = {}
        for name, df in full_tables.items():
            col_names = getattr(psd_const, f"col_name_{name}")
            if name == "bus":
                # The bus column names in PowerSimData include the index
                col_names = col_names[1:]
            if name == "branch":
                col_names += ["branch_device_type"]
            if name == "plant":
                col_names += ["type", "GenFuelCost", "GenIOB", "GenIOC", "GenIOD"]
            if name == "dcline":
                col_names += ["from_interconnect", "to_interconnect"]
            else:
                col_names += ["interconnect"]
            powersimdata_outputs[name] = full_tables[name][col_names]

        # Save files
        for name, df in powersimdata_outputs.items():
            df.to_csv(os.path.join(output_folder, f"{name}.csv"))
        # The zone file gets copied directly
        zone_path = os.path.join(os.path.dirname(__file__), "data", "zone.csv")
        shutil.copyfile(zone_path, os.path.join(output_folder, "zone.csv"))

    return full_tables


def create_profiles(
    plants, nrel_email, nrel_api_key, output_folder=None, solar_kwargs={}
):
    """Process a table of plant data to produce profile CSVs compatible with
        PowerSimData.

    :param pandas.DataFrame plants: table of plant data.
    :param str nrel_email: email used to`sign up <https://developer.nrel.gov/signup/>`_.
    :param str nrel_api_key: API key.
    :param str output_folder: directory to write CSVs to. If None, CSVs will not be
        written (just returned).
    :param dict solar_kwargs: keyword arguments to pass to
        :func:`prereise.gather.solardata.nsrdb.sam.retrieve_data_individual`.
    :return: (*dict*) -- keys are strings for profile names, values are dataframes,
        indexed by timestamp, with plant IDs as columns.
    """
    # Use plant data to build profiles
    profiles = {
        "solar": build_solar(
            nrel_email,
            nrel_api_key,
            plants.query("type == 'solar'"),
            **solar_kwargs,
        ),
    }
    if output_folder is not None:
        os.makedirs(output_folder, exist_ok=True)
        # Write profiles
        for name, df in profiles.items():
            df.to_csv(os.path.join(output_folder, f"{name}.csv"))

    return profiles

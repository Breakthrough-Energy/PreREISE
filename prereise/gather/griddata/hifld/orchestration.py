import os
import shutil

from powersimdata.input import const as psd_const

from prereise.gather.griddata.hifld.const import powersimdata_column_defaults
from prereise.gather.griddata.hifld.data_process.demand import assign_demand_to_buses
from prereise.gather.griddata.hifld.data_process.generators import build_plant
from prereise.gather.griddata.hifld.data_process.transmission import build_transmission


def create_csvs(output_folder):
    """Process HIFLD source data to CSVs compatible with PowerSimData.

    :param str output_folder: directory to write CSVs to.
    """
    # Process grid data from original sources
    branch, bus, substation, dcline = build_transmission()
    plant = build_plant(bus, substation)
    assign_demand_to_buses(substation, branch, plant, bus)

    outputs = {}
    outputs["branch"] = branch
    outputs["dcline"] = dcline
    outputs["sub"] = substation
    # Separate tables as necessary to match PowerSimData format
    # bus goes to bus and bus2sub
    outputs["bus2sub"] = bus[["sub_id", "interconnect"]]
    outputs["bus"] = bus.drop(["sub_id"], axis=1)
    # plant goes to plant and gencost
    outputs["gencost"] = plant[["c0", "c1", "c2", "interconnect"]].copy()
    outputs["plant"] = plant.drop(["c0", "c1", "c2"], axis=1)

    # Fill in missing column values
    for name, defaults in powersimdata_column_defaults.items():
        outputs[name] = outputs[name].assign(**defaults)

    # Filter to only the columns expected by PowerSimData, in the expected order
    for name, df in outputs.items():
        col_names = getattr(psd_const, f"col_name_{name}")
        if name == "bus":
            # The bus column names in PowerSimData include the index for legacy reasons
            col_names = col_names[1:]
        if name == "branch":
            col_names += ["branch_device_type"]
        if name == "plant":
            col_names += ["type", "GenFuelCost", "GenIOB", "GenIOC", "GenIOD"]
        if name == "dcline":
            col_names += ["from_interconnect", "to_interconnect"]
        else:
            col_names += ["interconnect"]
        outputs[name] = outputs[name][col_names]

    # Save files
    os.makedirs(output_folder, exist_ok=True)
    for name, df in outputs.items():
        df.to_csv(os.path.join(output_folder, f"{name}.csv"))
    # The zone file gets copied directly
    zone_path = os.path.join(os.path.dirname(__file__), "data", "zone.csv")
    shutil.copyfile(zone_path, os.path.join(output_folder, "zone.csv"))

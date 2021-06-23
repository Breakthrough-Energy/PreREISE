import csv

import pandas as pd

if __name__ == "__main__":
    branches = pd.read_csv("output/branch.csv")
    plants = pd.read_csv("output/plant.csv")
    buses = pd.read_csv("output/bus.csv")
    demands = pd.read_csv("data/demand.csv")
    demands = demands.drop("UTC Time", axis=1)

    bus_line_total_capa = {}
    # bus_load = buses.set_index('bus_id')['Pd'].to_dict()

    grouped = buses["Pd"].groupby(buses["zone_id"])
    sum_pd = grouped.sum().to_dict()

    max_demand = demands.max().to_dict()

    scaling_factor = {}
    for i in range(1, 53):
        scaling_factor[i] = max_demand[str(i)] / sum_pd[i]

    bus_load = {}

    buses["true_load"] = ""

    for index in range(len(buses)):
        buses["true_load"][index] = (
            buses["Pd"][index] * scaling_factor[buses["zone_id"][index]]
        )
        bus_load[buses["bus_id"][index]] = buses["true_load"][index]

    for br in branches.iloc:
        if br["from_bus_id"] not in bus_line_total_capa:
            bus_line_total_capa[br["from_bus_id"]] = br["rateA"]
        else:
            bus_line_total_capa[br["from_bus_id"]] = (
                bus_line_total_capa[br["from_bus_id"]] + br["rateA"]
            )
        if br["to_bus_id"] not in bus_line_total_capa:
            bus_line_total_capa[br["to_bus_id"]] = br["rateA"]
        else:
            bus_line_total_capa[br["to_bus_id"]] = (
                bus_line_total_capa[br["to_bus_id"]] + br["rateA"]
            )

    buses.to_csv("output/check_plant/bus.csv", index=False)

    ill_plant = open("output/check_plant/ill_plant.csv", "w", newline="")
    csv_writer1 = csv.writer(ill_plant)
    csv_writer1.writerow(
        ["plant_id", "bus_id", "distance", "plant_Pmax", "bus_capacity", "true_load"]
    )
    with open(
        "output/check_plant/plant_bus_distance_capacity.csv", "w", newline=""
    ) as plant_bus:
        csv_writer = csv.writer(plant_bus)
        csv_writer.writerow(
            [
                "plant_id",
                "bus_id",
                "distance",
                "plant_Pmax",
                "bus_capacity",
                "true_load",
            ]
        )
        for plant in plants.iloc:
            bus_capacity = bus_line_total_capa[plant["bus_id"]]
            true_load = bus_load[plant["bus_id"]]
            if bus_capacity < 1.2 * abs(plant["Pmax"] - true_load):
                csv_writer1.writerow(
                    [
                        plant["plant_id"],
                        plant["bus_id"],
                        plant["distance"],
                        plant["Pmax"],
                        bus_capacity,
                        true_load,
                    ]
                )
                # print(plant['plant_id'],plant['bus_id'],plant['distance'],plant['Pmax'],bus_capacity)
            csv_writer.writerow(
                [
                    plant["plant_id"],
                    plant["bus_id"],
                    plant["distance"],
                    plant["Pmax"],
                    bus_capacity,
                    true_load,
                ]
            )
    ill_plant.close()

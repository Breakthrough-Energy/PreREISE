import pandas as pd
import csv


if __name__ == "__main__":
    branches = pd.read_csv('output/branch.csv')
    plants = pd.read_csv('output/plant.csv')
    bus_line_total_capa = {}
    for br in branches.iloc:
        if br['from_bus_id'] not in bus_line_total_capa:
            bus_line_total_capa[br['from_bus_id']] = br['rateA']
        else:
            bus_line_total_capa[br['from_bus_id']] = bus_line_total_capa[br['from_bus_id']] + br['rateA']
        if br['to_bus_id'] not in bus_line_total_capa:
            bus_line_total_capa[br['to_bus_id']] = br['rateA']
        else:
            bus_line_total_capa[br['to_bus_id']] = bus_line_total_capa[br['to_bus_id']] + br['rateA']
        
    ill_plant = open('output/ill_plant.csv','w',newline="")
    csv_writer1 = csv.writer(ill_plant)
    csv_writer1.writerow(['plant_id','bus_id', 'distance','plant_Pmax','bus_capacity'])
    with open("output/plant_bus_distance_capacity.csv", "w", newline="") as plant_bus:
        csv_writer = csv.writer(plant_bus)
        csv_writer.writerow(['plant_id','bus_id', 'distance','plant_Pmax','bus_capacity'])
        for plant in plants.iloc:
            bus_capacity = bus_line_total_capa[plant['bus_id']]
            if(bus_capacity < 1.2*plant['Pmax']):
                csv_writer1.writerow([plant['plant_id'],plant['bus_id'],plant['distance'],plant['Pmax'],bus_capacity])
                print(plant['plant_id'],plant['bus_id'],plant['distance'],plant['Pmax'],bus_capacity)
            csv_writer.writerow([plant['plant_id'],plant['bus_id'],plant['distance'],plant['Pmax'],bus_capacity])
    ill_plant.close()

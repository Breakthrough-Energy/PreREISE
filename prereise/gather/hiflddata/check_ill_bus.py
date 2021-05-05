import pandas as pd
import csv


if __name__ == "__main__":
    branches = pd.read_csv('output/branch.csv')
    plants = pd.read_csv('output/plant.csv')
    buses = pd.read_csv('output/bus.csv')
    demands = pd.read_csv('data/demand.csv')
    demands = demands.drop('UTC Time', axis=1)
    
    bus_line_total_capa = {}
    #bus_load = buses.set_index('bus_id')['Pd'].to_dict()

    grouped = buses['Pd'].groupby(buses['zone_id']) 
    sum_pd = grouped.sum().to_dict()

    max_demand = demands.max().to_dict()

    scaling_factor = {}
    for i in range(1,53):
        scaling_factor[i] = max_demand[str(i)]/sum_pd[i]

    bus_pmax = plants['Pmax'].groupby(plants['bus_id']).sum().to_dict()

    buses['true_load'] = ''

    for index in range(len(buses)):
        buses['true_load'][index] = buses['Pd'][index]*scaling_factor[buses['zone_id'][index]]

    
    for br in branches.iloc:
        if br['from_bus_id'] not in bus_line_total_capa:
            bus_line_total_capa[br['from_bus_id']] = br['rateA']
        else:
            bus_line_total_capa[br['from_bus_id']] = bus_line_total_capa[br['from_bus_id']] + br['rateA']
        if br['to_bus_id'] not in bus_line_total_capa:
            bus_line_total_capa[br['to_bus_id']] = br['rateA']
        else:
            bus_line_total_capa[br['to_bus_id']] = bus_line_total_capa[br['to_bus_id']] + br['rateA']

    buses.to_csv('output/check_plant/bus.csv', index=False)    
        
    ill_bus = open('output/check_plant/ill_bus.csv','w',newline="")
    csv_writer1 = csv.writer(ill_bus)
    csv_writer1.writerow(['bus_id','Pmax','bus_capacity','true_load'])
    with open("output/check_plant/bus_load_capacity.csv", "w", newline="") as plant_bus:
        csv_writer = csv.writer(plant_bus)
        csv_writer.writerow(['bus_id','Pmax','bus_capacity','true_load'])
        for bus in buses.iloc:
            bus_id = bus['bus_id']
            bus_capacity = bus_line_total_capa[bus_id]
            true_load = bus['true_load']
            if(bus_id in bus_pmax):
                pmax = bus_pmax[bus_id]
            else:
                pmax = 0.0
            if(bus_capacity < 1.2*abs(pmax - true_load)):
                csv_writer1.writerow([bus_id,pmax,bus_capacity,true_load])
                #print(plant['plant_id'],plant['bus_id'],plant['distance'],plant['Pmax'],bus_capacity)
            csv_writer.writerow([bus_id,pmax,bus_capacity,true_load])
    ill_bus.close()

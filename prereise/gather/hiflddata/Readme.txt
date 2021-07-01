
Step1: Get hiflddata:

1.Enter the workspace "\hiflddata"


2.Run command "python data_trans.py".

This program will create branch.csv, dcline.csv, bus.csv, sub.csv, bus2sub.csv.


3.Run command "python topology_validation.py".

This program will update the branches which across 2 different interconnects. It returns branch.csv, bus.csv, sub.csv, bus2sub.csv.


3.Run command "python bus_island_remove.py".

This program will remove the islands in each interconnects. It returns branch.csv, bus.csv, sub.csv, bus2sub.csv.


4.Run command "python plant_agg.py".

This program will create plant.csv, gencost.csv.


5.




# HIFLDParser

### Data Source
- Transmission Line:
https://hifld-geoplatform.opendata.arcgis.com/datasets/electric-power-transmission-lines
- Substation:
https://hifld-geoplatform.opendata.arcgis.com/datasets/electric-substations
- PowerPlant:
https://hifld-geoplatform.opendata.arcgis.com/datasets/power-plants


### Sample Output Data
- https://zenodo.org/record/3530898


### What it does
Move the code from private GitHub proj to PreREISE. 
To give more context, this new HIFLD module has two python scripts to output the transmission topology and power generation data.

- data_trans.py is the one to parse the substation, transmission csv and json raw data downloaded from HIFLD. 
  - `DataTransform(E_csv, T_csv, Z_csv)` is the main entry point in this script to all the other methods, i.e., parse, calcualte and approximate the topology information.
  - The most important internal analysis functions 
    - `def Neighbors(sub_by_coord_dict, sub_name_dict, raw_lines)`, which figures out the topology with geo coordinate information for all the transmission lines
    - `calculate_reactance_and_rateA(bus_id_to_kv, lines, raw_lines)`, which is using pre-defined line parameters and rules
    - `GetMaxIsland(G)`, which detects the connectivity of the network topology; we leverage the networkx as the Graph computing library - some of the topology calculation is done easily.

- topology_validation.py is the one to revise the ill buses and tranmission lines.
  - `get_across_branch(branch, bus_dict)` is to -- identify all ill branch and all normal bus
    - a branch is ill when its two ends are in two different U.S. interconnect region
    - The lable for normal bus cannot be changed once it is assigned.
  - The most important internal analysis functions is `get_update_branch_bus(branch_need_update, bus_acc, zone_map, bus_state)`
    - In ill branch set, find the branch whose two ends are both normal bus. 
     - Delete the branch. 
     - In this situtation, the branch is ill and across two different interconnect regions. 
     - However, the two end buses are unchangable due each bus is connected with the large network in each region.
    - In ill branch set, find the branch whose two ends are one normal bus and one unlable bus.
     - Assgin the unlable bus' interconnect region as the normal bus' interconnect region. 
     - Assgin this branch's interconnnect region as the normal bus' interconnect region.
     - In this sitution, one end of the branch is connected with the network of the region. The other end is a island. 
    - In ill brnach set, find the branch whose two ends are both unlable buses.
     - Delete the branch and both unlable buses.
     - In this situtation, this branch is a island. 

- bus_island_remove.py is the one to remove islands in each U.S. interconnect region
  - `graph_of_net(branch, bus, interconnect)` is to create the graph for the HIFLD transmission network.

- plant_agg.py is the one to parse the generation raw data from HIFLD and EIA
  - `Plant(E_csv, U_csv, G2019_csv)` is the main entry point in this script to all other methods, i.e., cleanup, aggregate the power plant generation information.
  - The most important internal analysis function is `Plant_agg(clean_data,ZipOfsub_dict,loc_of_plant,LocOfsub_dict,Pmin)`, which aggregate the power generation based on zip code grouping 

- create_virtual_plant is the one to find all ill plants and divide them into smaller plants
  - The most important internal analysis functions 
    - `avai_load(buses, bus_pmax, bus_line_total_capa)`, which calculate the avaiable extra load for each bus.
    - `find_near_sub(lat, lon, pmax, re, plant_zip, ziplist, zip_of_sub_dict, avaiable_load)`, which find 5 near avaiable buses for an ill plant.

- create_virtual_line is the one to find all ill buses and add lines to satisfy its load
  - The most important internal analysis functions 
    - `find_neigh(bus, depth, load, re)`, which find the neighbor buses in a default depth.
    - `new_branch(buses, bus_load, add_branch, new_branch_id, depth)`, which calculate the number and size of branches need to be added.

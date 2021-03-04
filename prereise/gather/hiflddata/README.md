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

- plant_agg.py is the one to parse the generation raw data from HIFLD and EIA
  - `Plant(E_csv, U_csv, G2019_csv)` is the main entry point in this script to all other methods, i.e., cleanup, aggregate the power plant generation information.
  - The most important internal analysis function is `Plant_agg(clean_data,ZipOfsub_dict,loc_of_plant,LocOfsub_dict,Pmin)`, which aggregate the power generation based on zip code grouping 
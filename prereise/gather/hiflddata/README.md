# HIFLDData

### Data Source
- Transmission Line:
https://hifld-geoplatform.opendata.arcgis.com/datasets/electric-power-transmission-lines
- Substation:
https://hifld-geoplatform.opendata.arcgis.com/datasets/electric-substations
- PowerPlant:
https://hifld-geoplatform.opendata.arcgis.com/datasets/power-plants
- U.S Population:
https://simplemaps.com/data/us-counties https://simplemaps.com/data/us-zips

### Sample Output Data
- https://zenodo.org/record/3530898


### What it does
This new HIFLD module will output the transmission topology and power generation data.

- data_trans.py is the one to parse the substation, transmission csv and json raw data downloaded from HIFLD. 
  - `DataTransform(E_csv, T_csv, Z_csv)` is the main entry point in this script to all the other methods, i.e., parse, calcualte and approximate the topology information.
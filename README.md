# PreREISE
This package defines the scenario and calls the Matlab simulation engine.
The name stands for pre Renewable Energy Integration Study Engine.
After setting up the scenario in REISE you create an entry in `ScenarioList.csv`.
This file contains all scenraios. The location of the list on the server is `/home/EGM/`.


## 1. Creating a Scenario
A scenario can be defined by adding an entry to the scenario list `ScenarioList.csv`.
Fill in all the required information. The following fields are required:

name | folder_location | input_data_location | output_data_location | start_index | end_index | extract | description
------------ | ------------- | ------------ | ------------- | ------------ | ------------- | ------------ | -------------
`scenario_name` | Folder location of Matlab files | Input data location | Output data location | Start index | End index | True/False to convert data into csv | Description

Make sure you choose an unique name in the scenario_name column . Since this list is temporary
and will be replaced by a database there is no check of uniqueness.
Make sure you have stored the `scenario_name.m` file, the related simulation and
data files in the defined locations.
The convention is that we use the scenario name as the output folder name.
Make sure your simulation m-file has the same name as the unique scenario name.


## 2. Call (Start the simulation)
After setting up the scenario, the simulation engine can be called.
You launch the simulation the following way:
```python
import prereise

prereise.launch_scenario_performance('scenario_name')
```

### A. Setup/Install
This package requires Matlab, Gurobi, and Matpower. Make sure to put the paths
from Gurobi and Matpower into the `add_path.m` file.
Before installing this package install Matlab, Gurobi and Matpower.

### B. For Matlab the following setup is required:
On Windows systems —
```
cd "matlabroot\extern\engines\python"
python setup.py install
```
On Mac or Linux systems —
```
cd "matlabroot/extern/engines/python"
python setup.py install
```

### C. Install Gurobi and add path
Install Gurobi and add Matlab path to 'add_path.m'
```
<GUROBI>/<os>/matlab
```

### D. For Matpower the following setup is required:
Download Matpower and add the following directories to the `add_path.m`:
```
<MATPOWER>        — core MATPOWER functions
<MATPOWER>/most   — core MOST functions
```

### E. Install this package
In the folder with the setup.py file type:
`pip3 install .`


## 3. Gather
This module allows you to gather data for the simulation.

### A. Wind data

####  &alpha;. Rapid Refresh
[RAP](https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/rapid-refresh-rap) (Rapid Refresh) is the continental-scale NOAA hourly-updated assimilation/modeling system operational at the National Centers for Environmental Prediction (NCEP). RAP covers North America and is comprised primarily of a numerical weather model and an analysis system to initialize that model. RAP provides, every hour ranging from May 2012 to date, the U and V components of the wind speed at 80 meter above ground on a 13x13 square kilometer resolution grid every hour. Data can be retrieved using the NetCDF Subset Service. Information on this interface is described [here](https://www.unidata.ucar.edu/software/thredds/current/tds/reference/NetcdfSubsetServiceReference.html).

Usage in general:
```
from prereise.gather.winddata import rap

rap.retrieve_data(wind_farm)
```
Check out the demo jupyter notebook in
`prereise/gather/winddata/rap/demo/`

#### &beta;. Techno-Economic Wind Integration National Dataset Toolkit
The [Techno-Economic WIND (Wind Integration National Dataset) Toolkit](https://www.nrel.gov/grid/wind-toolkit.html) provides 5-min resolution data for 7 years, ranging from 2007 to 2013, at 120,000 points within the continental U.S. selected for their wind resource. This set contains power estimates and forecasts along with a subset of atmospheric variables. Data can be accessed via an [API](https://developer.nrel.gov/docs/wind/wind-toolkit/).

Check out the demo jupyter notebook in
`prereise/gather/winddata/te_wind/demo/`

Usage in general:
```
from prereise.gather.winddata.te_wind import te_wind

te_wind.get_all_NREL_siteID_for_states(['WA','CA'])
```
To run a test:
```
from prereise.gather.winddata.te_wind.test import te_wind_test
te_wind_test.test()
```


### B. Solar data

####  &alpha;. The Gridded Atmospheric Wind Integration National Dataset Toolkit
The [Gridded Atmospheric WIND (Wind Integration National Dataset) Toolkit](https://www.nrel.gov/grid/wind-toolkit.html) provides 1-hour resolution irradiance data for 7 years, ranging from 2007 to 2013, on a uniform 2x2 square kilometer grid that covers the continental U.S., the Baja Peninsula, and parts of the Pacific and Atlantic oceans. Data can be accessed using the Highly Scalable Data Service. NREL wrote [example notebooks](https://github.com/NREL/hsds-examples) that demonstrate how to access the data.

####  &beta;. The National Solar Radiation database
[NSRDB (National Solar Radiation Database)](https://nsrdb.nrel.gov/) provides 1-hour resolution solar radiation data, ranging from 1998 to 2016, for the entire U.S. and a growing list of international locations on a 4x4 square kilometer grid. Data can be accessed via an [API](https://developer.nrel.gov/docs/solar/nsrdb/). Note that the Physical Solar Model v3 is used.

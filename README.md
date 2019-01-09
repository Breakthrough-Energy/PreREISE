# PreREISE
This package defines the scenario and calls the MATLAB simulation engine. The name stands for pre Renewable Energy Integration Study Engine. After setting up the scenario in REISE you create an entry in ***ScenarioList.csv***. This file contains all scenarios. The location of the list on the server is `/home/EGM/`.



## 1. Setup/Install
This package requires MATLAB, Gurobi, MATPOWER and WesternInterconnect.


### A. MATLAB
Install MATLAB and proceed as follows:  
```
cd "matlabroot\extern\engines\python"
python setup.py install
```
for Windows systems.

```
cd "matlabroot/extern/engines/python"
python setup.py install
```
for Mac or Linux systems.


### B. Gurobi
Install Gurobi and add MATLAB path to ***add_path.m***:
```
<GUROBI>/<os>/matlab
```


### C. MATPOWER
Download MATPOWER and add the following directories in ***add_path.m***:
```
<MATPOWER>        — core MATPOWER functions
<MATPOWER>/most   — core MOST functions
```


### D. WesternInterconnectNetwork
In the WesternInterconnect package, locate the ***setup.py*** file and type: `pip3 install .` Do not forget to update your PYTHONPATH environment variable.


### E. PreREISE
In the PreREISE package, locate the ***setup.py*** file and type: `pip3 install .` Do not forget to update your PYTHONPATH environment variable.



## 2. Create Scenario
A scenario can be defined by adding an entry to the scenario list ***ScenarioList.csv*** table. Fill in all the required information. There are 8 columns in the scenario list table. These are:
* **name**: `scenario_name`;
* **folder_location**: path to folder where MATLAB files are located;
* **input_data_location**: path to folder where input data are located;
* **output_data_location**: path to folder where input will be saved;
* **start_index**: start index;
* **end_index**: end index;
* **extract**: True/False. Should output data be converted to csv and;
* **description**: description, problem encountered, ...

Make sure you choose an unique name in the `scenario_name` column. Since this list is temporary and will be replaced by a database there is no check of uniqueness. Make sure you have stored the ***scenario_name.m*** file, the related simulation and data files in the defined locations. The convention is that we use the scenario name as the output folder name. Make sure your simulation m-file has the same name as the unique scenario name.



## 3. Gather Data for Simulation 
This module aims at gathering the required data for the simulation.

### A. Wind data

#### i. Rapid Refresh
[RAP](https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/rapid-refresh-rap) (Rapid Refresh) is the continental-scale NOAA hourly-updated assimilation/modeling system operational at the National Centers for Environmental Prediction (NCEP). RAP covers North America and is comprised primarily of a numerical weather model and an analysis system to initialize that model. RAP provides, every hour ranging from May 2012 to date, the U and V components of the wind speed at 80 meter above ground on a 13x13 square kilometer resolution grid every hour. Data can be retrieved using the NetCDF Subset Service. Information on this interface is described [here](https://www.unidata.ucar.edu/software/thredds/current/tds/reference/NetcdfSubsetServiceReference.html).

Note that the dataset is incomplete (33 hours are missing in 2016) and, consequently, missing entries need to be imputed. Afterwards, wind speed is converted to power for all the wind farms in the network using the *IEC class 2* power curve provided by NREL in the [WIND Toolkit documentation](https://www.nrel.gov/docs/fy14osti/61714.pdf).

Check out the ***[rap_demo.ipynb](https://github.com/intvenlab/PreREISE/blob/sam/prereise/gather/winddata/rap/demo/rap_demo.ipynb)*** notebook for demo.

#### ii. Techno-Economic Wind Integration National Dataset Toolkit
The [Techno-Economic WIND (Wind Integration National Dataset) Toolkit](https://www.nrel.gov/grid/wind-toolkit.html) provides 5-min resolution data for 7 years, ranging from 2007 to 2013, at 120,000 points within the continental U.S. selected for their wind resource. This set contains power estimates and forecasts along with a subset of atmospheric variables. Data can be accessed via an [API](https://developer.nrel.gov/docs/wind/wind-toolkit/).

The closest site to the wind farm in the network is found in the NREL dataset and the associated power estimate is simply scaled to the plant capacity to obtain a wind power output profile. The procedure is illustrated in the ***[te_wind_demo.ipynb](https://github.com/intvenlab/PreREISE/blob/sam/prereise/gather/winddata/te_wind/demo/te_wind_demo.ipynb)*** notebook.

Also, a test can be run as follows:
```python
from prereise.gather.winddata.te_wind.test import te_wind_test

te_wind_test.test()
```


### B. Solar data

#### i. The Gridded Atmospheric Wind Integration National Dataset Toolkit
The [Gridded Atmospheric WIND (Wind Integration National Dataset) Toolkit](https://www.nrel.gov/grid/wind-toolkit.html) provides 1-hour resolution irradiance data for 7 years, ranging from 2007 to 2013, on a uniform 2x2 square kilometer grid that covers the continental U.S., the Baja Peninsula, and parts of the Pacific and Atlantic oceans. Data can be accessed using the Highly Scalable Data Service. NREL wrote [example notebooks](https://github.com/NREL/hsds-examples) that demonstrate how to access the data.

Power output is estimated using a simple normalization procedure. For each solar plant location the hourly Global Horizontal Irradiance (GHI) is divided by the maximum GHI over the period considered and multiplied by the capacity of the plant. This procedure is referred to as naïve since it only accounts for the plant capacity. Note that other factors can possibly affect the conversion from solar radiation at ground to power such as the temperature at the site as well as many system configuration including tracking technology.

Check out the ***[ga_wind_demo.ipynb](https://github.com/intvenlab/PreREISE/blob/sam/prereise/gather/solardata/ga_wind/demo/ga_wind_demo.ipynb)*** notebook for demo.

#### ii. The National Solar Radiation Database
[NSRDB (National Solar Radiation Database)](https://nsrdb.nrel.gov/) provides 1-hour resolution solar radiation data, ranging from 1998 to 2016, for the entire U.S. and a growing list of international locations on a 4x4 square kilometer grid. Data can be accessed via an [API](https://developer.nrel.gov/docs/solar/nsrdb/). Note that the Physical Solar Model v3 is used.

An API key is required to access and use the above databases. Get your own API key [here](https://developer.nrel.gov/signup/).

Here, the power output can be estimated using the previously presented naïve method or a more sophisticated one. The latter uses the System Advisor Model ([SAM](https://sam.nrel.gov/)) developed by NREL. The developer tools for creating renewable energy system models can be downloaded [here](https://sam.nrel.gov/sdk). Irradiance data along with other meteorological parameters must first be retrieved from NSRDB for each site. This information are then fed to the SAM Simulation Core (SCC) and the power output is retrieved. The SSC reflect the technology used: photovoltaic (PV), solar water heating and concentrating solar power (CSP). The *[PVWatts v5](https://www.nrel.gov/docs/fy14osti/62641.pdf)* model is used for all the solar plants in the grid. The default values of the parameters of the *PVWatts* model are untouched. Only the system size and the array type (fixed open rack, backtracked, 1-axis and 2-axis) is set for each solar plant.

The naïve and the SAM method are used in the ***[nsrdb_naive_demo.ipynb](https://github.com/intvenlab/PreREISE/blob/sam/prereise/gather/solardata/nsrdb/demo/nsrdb_naive_demo.ipynb)*** and ***[nsrdb_sam_demo.ipynb](https://github.com/intvenlab/PreREISE/blob/sam/prereise/gather/solardata/nsrdb/demo/nsrdb_sam_demo.ipynb)*** demo notebook, respectively.


### C. Hydro Data
EIA (Energy Information Administration) published monthly capacity factors for hydro plants across the country. This dataset (available [here](https://www.eia.gov/electricity/annual/html/epa_04_08_b.html)) is used to produce a profile for each hydro plant in the grid. Note that we are using the same set of capacity factor independently of the geographical location of the plant. As a result, the profile of all the hydro plants in the grid will have the same shape. Only the power output will differ (the scale of the profile).

Check out the ***[eia_demo.ipynb](https://github.com/intvenlab/PreREISE/blob/hydro/prereise/gather/hydrodata/eia/demo/eia_demo.ipynb)*** notebook for demo.


### D. Demand Data
Demand data are obtained from EIA, to whom Balancing Authorities have submitted their data. The data can be obtained either by direct download from their database using an API or by download of Excel spreadsheets. A API key is required for the API download and this key can be obtained by a user by registering at https://www.eia.gov/opendata/.

The direct download currently contains only published demand data. The Excel spreadsheets include original and imputed demand data, as well as results of various data quality checks done by EIA. Documentation about the datasets can be found [here](https://www.eia.gov/realtime_grid/docs/userguide-knownissues.pdf). Excel spreadsheets can be downloaded by clicking on the links in page 9 (Table of all US and foreign connected balancing authorities).

Module `get_eia_data` contains functions that converts the data into data frames for further processing.

To use, 
```python
from prereise.gather.demanddata.eia import get_eia_data

data = get_eia_data.from_excel(dir, BA_list, startdate, enddate)

```
To test EIA download (This requires an EIA API key):
```python
from prereise.gather.demanddata.eia.test import test_eia_download

test_eia_download.test_eia_download()
```
To test EIA download from Excel:
```python
from prereise.gather.demanddata.eia.test import test_from_excel

test_from_excel.test_from_excel()
```

The notebook [AssembleBAfromExcel_demo.ipynb](https://github.com/intvenlab/PreREISE/blob/sam/prereise/gather/demanddata/EIA/demo/AssembleBAfromExcel_demo.ipynb) illustrates usage.

To output the demand profile, cleaning steps were applied to the EIA data:  
1) missing data imputation - the EIA method was used, i.e., EIA published data was used; beyond this, NA's were converted to float zeros;  
2) missing hours were added.

The BA counts were then distributed across each region where the BA operates, using the region populations as weights. For example, if a BA operates in both WA and OR, the counts for WA are weighted by the fraction of the total counts in WA relative to the total population of WA and OR.



## 4. Start simulation
Simulation can only be launched on server. After setting up the scenario, the simulation engine can be called and the simulation can be started as follows:
```python
import prereise

prereise.launch_scenario_performance('scenario_name')
```
To test, run:
```python
from prereise.call.test import test_call

test_call.test()
```

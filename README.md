# PreREISE
This package defines the scenario and calls the Matlab simulation engine.
The name stands for pre Renewable Energy Integration Study Engine.
After setting up the scenario in REISE you create an entry in `ScenarioList.csv`.
This file contains all scenraios. The location of the list on the server is `/home/EGM/`.
## Creating a Scenario
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

## Start the simulation.
After setting up the scenario, the simulation engine can be called.
You launch the simulation the following way:
```python
import prereise

prereise.launch_scenario_performance('scenario_name')
```
## Setup/Install
This package requires Matlab, Gurobi, and Matpower. Make sure to put the paths
from Gurobi and Matpower into the `add_path.m` file.
Before installing this package install Matlab, Gurobi and Matpower.
### For Matlab the following setup is required:
On Windows systems —
'''
cd "matlabroot\extern\engines\python"
python setup.py install
'''
On Mac or Linux systems —
'''
cd "matlabroot/extern/engines/python"
python setup.py install
'''
### Install Gurobi and add path
Install Gurobi and add Matlab path to 'add_path.m'
```
<GUROBI>/<os>/matlab
```
### For Matpower the following setup is required:
Download Matpower and add the following directories to the `add_path.m`:
```
<MATPOWER>        — core MATPOWER functions
<MATPOWER>/most   — core MOST functions
```
### Install this package
In the folder with the setup.py file type:
`pip3 install .`

## Collecting Demand Data
Demand data are obtained from EIA, to whom Balancing Authorities have submitted their data.
The data can be obtained either by direct download from their database or
by download of Excel spreadsheets. The direct download currently contains only published 
demand data. The Excel spreadsheets include original and imputed demand data, as well as
results of various data quality checks done by EIA. Documentation about the datasets are in https://github.com/intvenlab/PreREISE/blob/mlh/doc/EIA-930_userguide-knownissues.pdf. 
Excel spreadsheets can be downloaded by clicking on the links in page 9 (Table of all US and
foreign connected balancing authorities).

Module getEIAdata contains functions that converts the data into pandas dataframes for
further processing.

To use, 
```python
import getEIAdata
...
data = getEIAdata.from_excel(dir, BA_list, startdate, enddate)

```

The notebook https://github.com/intvenlab/PreREISE/blob/mlh/prereise/gather/demanddata/EIA/demo/AssembleBAfromExcel_demo.ipynb 
illustrates usage.

## Outputting Demand Profile
The notebook https://github.com/intvenlab/PreREISE/blob/mlh/prereise/gather/demanddata/EIA/demo/OutputDemandProfiles.ipynb 
shows the steps done to convert the raw demand data into the input demand profile data. Cleaning steps included
1) missing data imputation - the EIA method was used, i.e., EIA published data was used; beyond this, NA's were converted to float zeros
2) missing hours were added 
3) the BA counts were distributed across each region where the BA operates, using the region populations as weights. For example, if a BA operates in both WA and OR, the counts for WA are weighted by the fraction of the total counts in WA relative to the total population of WA and OR.
The demand profile is finally converted to Matlab input using Matlab. Another copy with headers is saved in L:\Renewable Energy\EnergyGridModeling\Data\Western\demand_data\processed.

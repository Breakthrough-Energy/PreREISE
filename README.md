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
Simulation can only be launched on server. 
After setting up the scenario, the simulation engine can be called.
You launch the simulation the following way:
```python
import prereise

prereise.launch_scenario_performance('scenario_name')
```
### Test
To test run:
```python
from prereise.call.test import test_call

test_call.test()
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

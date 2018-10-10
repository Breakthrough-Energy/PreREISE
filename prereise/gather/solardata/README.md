# Introduction
REISE takes as input the power produced every UTC hour by each solar plant in the network. Solar irradiance data need first to be collected and then converted to power. The procedure used to achieve these goals is explained below.

# Data
1-hour resolution solar irradiance data are needed. In addition these data should be available for all the solar plants location in the network, i.e., the data must have a good a spatial resolution.

The National Renewable Energy Laboratory (NREL) provides two sets of data that achieve these goals. These are the WIND (Wind Integration National Dataset) Toolkit and the National Solar Radiation Database (NSRDB).
* The [WIND Toolkit](https://www.nrel.gov/grid/wind-toolkit.html) provides 1-hour resolution irradiance data for 7 years, **ranging from 2007 to 2013**, on a uniform 2-km square grid that covers the continental U.S., the Baja Peninsula, and parts of the Pacific and Atlantic oceans.
* The [NSRDB](https://nsrdb.nrel.gov/) provides 1-hour resolution solar radiation data, **ranging from 1998 to 2016**, for the entire U.S. and a growing list of international locations on a 4-km square grid.

# Solar Power Output Calculation
The solar irradiance data then need to be converted to power output. Two methods have been used.

## Naïve Method
This estimation method uses a simple normalization procedure to convert the Global Horizontal Irradiance (GHI) to power output. For each plant location the hourly GHI is divided by the maximum GHI over the period considered and multiplied by the capacity of the plant. In other words, each plant reaches its maximal capacity only once over the period considered. This procedure is referred to as **naive** since it only takes into account the plant capacity. Other factors can possibly affect the conversion from solar radiation at ground to power such as the temperature at the site as well as many system configuration including DC/AC ratio or eventual tilt system.


## System Advisor Model (SAM)
Power output can be estimated using SAM. A collection of developer tools ([SDK](https://sam.nrel.gov/sdk)) can be used to create a renewable energy system model. The solar and meteorological data collected from NSRDB as well as some variables characterizing the plant can be used to construct a SAM Simulation Core (SSC) object and generate solar power output. A technical report of the SAM Photovoltaic model can be consulted in this [document](https://www.nrel.gov/docs/fy18osti/67399.pdf). Also a notebook   whose goal is to present the SDK can be found [here](NSRDB/sam.ipynb).

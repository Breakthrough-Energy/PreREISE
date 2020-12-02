## Third Party Data
This package contains a variety of materials, including data sets and related materials. The third party data sets and related materials are provided by their respective publishers, and may be subject to separate and additional terms and conditions. The following summarizes the sources of the applicable data, and details regarding the applicable provider. Additional terms and conditions, including certain restrictions on commercial use, redistribution, or other similar restrictions, may apply to the applicable data sets. If you cannot comply with the terms of the applicable data collection, you may not use that data, and your ability to make use of this software package, and/or the results or output you are able to generate through its use may be impacted. Please review the information provided below, and the terms and conditions provided by the publisher at the original source for more information.


### Geographical Information
#### BA to County Mapping
#### Source
* Name: Counties in the United States
* Author: mapchart.net
* Description: An interactive map contains all the counties in the United
 States
* Source: https://mapchart.net
* Exact source location: https://mapchart.net/usa-counties.html

#### Destination
* Modifications to source file(s): None
* Location: ***prereise/gather/data/ba_to_county.txt***


---
### Generation
#### Energy Information Administration (EIA)
##### Source
* Name: Form EIA-923
* Author: EIA
* Description: Electric power data -- monthly and annually -- on electricity generation, fuel consumption, fossil fuel stocks, and receipts at the power plant and prime mover level for 2016
* Source: https://www.eia.gov
* Exact source location: https://www.eia.gov/electricity/data/eia923/

##### Destination
* Modifications to source files(s): None
* Location: ***prereise/gather/data/EIA923_Schedules_2_3_4_5_M_12_2016_Final_Revision.xlsx***

##### General Purpose
The dataset is used to generate hydro profiles.


---
### Demand
#### Southwest Power Pool (SPP)
##### Source
* Name: Historical load
* Author: SPP
* Description: Historical load data rolled up at an hourly level and grouped by sub-area for 2015 and 2016
* Source: https://spp.org/
* Exact source location: https://marketplace.spp.org/pages/hourly-load

##### Destination
* Modifications to source file(s): None
* Location: ***prereise/gather/demanddata/eia/demo/eastern_demand_v6_demo/spp/load/****

##### General Purpose
The dataset is used to generate demand profiles for the Eastern interconnection.

##### Note
Data from this source may be freely copied and distributed except in connection with a commercial publication.

##### Source
* Name: Legacy BAs geographical coverage
* Author: SPP
* Description: link each county covered by SPP to its sub-area
* Source: https://spp.org/
* Exact source location: file obtained open request through SPP internal request management system (https://spprms.issuetrak.com/Login.asp)

##### Destination
* Modifications to source file(s): None
* Location: ***prereise/gather/demanddata/eia/demo/eastern_demand_v6_demo/spp/spp_counties_owners.xlsx***

##### General Purpose
The dataset is used to generate demand profiles for the Eastern interconnection.

##### Note
Legal review pending


#### Midcontinent Independent System Operator (MISO)
##### Source
* Name: Historical forecasted and actual load
* Author: MISO
* Description: Historical forecasted and actual load data rolled up at an hourly level and grouped by sub-area for 2015 and 2016
* Source: https://www.misoenergy.org/
* Exact source location: https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports

##### Destination
* Modifications to source file(s): None
* Location:
  * ***prereise/gather/demanddata/eia/demo/eastern_demand_v6_demo/miso/20151231_dfal_hist.xls***
  * ***prereise/gather/demanddata/eia/demo/eastern_demand_v6_demo/miso/20161231_dfal_hist.xls***

##### General Purpose
The dataset is used to generate demand profiles for the Eastern interconnection.

##### Note
When using this dataset, provide a copy of the final product to MISO.


#### National Renewable Energy Laboratory (NREL)
##### Source
* Name: Electrification Futures Study Load Profiles
* Authors: Trieu Mai, Paige Jadun, Jeffrey Logan, Colin McMillan, Matteo Muratori, Daniel Steinberg, Laura Vimmerstedt, Ryan Jones, Ben Haley, Brent Nelson, Caitlin Murphy, Yinong Sun
* Description: Projected state-level demand profiles for different electrification scenarios, levels of technology advancement, and years.
* Source: https://data.nrel.gov/submissions/126
* Exact source location: There are nine different .zip files containing demand data for the nine combinations of three electrification scenarios and three technology advancements. They can be accessed via: "https://data.nrel.gov/system/files/126/EFSLoadProfile_" + es + "_" + ta + ".zip", where es is in {"Reference", "Medium", "High"} and ta is in {"Slow", "Moderate", "Rapid"}

##### Destination
* Modifications to source file(s):
  * Sectoral demand is aggregated so that there is only one value for each time and location.
  * State-level demand is mapped to the load zones defined by Breakthrough Energy Sciences.
  * Of the six years' worth of data provided in each dataset, only one user-specified year is kept.
* Location: These datasets are not included in this package. Rather, users are able to access and modify the datasets using modules included in this package.

##### General Purpose
These datasets are used as the basis for demand profiles of the contiguous U.S. These resulting demand profiles are different from other demand profiles discussed in this package in that these demand profiles account for projected widespread electrification.

##### Note
These datasets are generously provided by NREL, which is operated for the U.S. Department of Energy by the Alliance for Sustainable Energy, LLC. Before using these datasets, please read [this disclaimer][nrel_disclaimer] first.


---
### Hydro
#### Energy Information Administration (EIA)
##### Source
* Name: Electric power annual
* Author: EIA
* Description: Capacity factors for utility scale generators not primarily using fossil fuel, January 2013-December 2017 (Table 4.8.B)
* Source: https://www.eia.gov
* Exact source location: https://www.eia.gov/electricity/annual/archive/pdf/03482017.pdf

##### Destination
* Modifications to source file(s): extract 2015, 2016 and 2017 monthly capacity factors for conventional hydropower
* Location: ***prereise/gather/hydrodata/data/usa_hydro_capacity_factors.csv***

##### General Purpose
The dataset is used to generate hydro profiles.


#### Electric Reliability Council of Texas (ERCOT)
##### Source
* Name: Fuel mix report
* Author: ERCOT
* Description: Actual generation by fuel type for each 15-minute settlement interval, as well as totals by month and year-to-date.
* Source: http://www.ercot.com/
* Exact source location: http://www.ercot.com/gridinfo/generation/

##### Destination
* Modifications to source file(s): monthly files have been concatenated and timestamps have been converted to UTC.
* Location: ***prereise/gather/hydrodata/data/ercot_hydro_2016.csv***

##### General Purpose
The dataset is used to generate hydro profiles for the Texas interconnection.

##### Note
Disclose modifications when redistributing this dataset in modified form.


#### U.S. Army Corps of Engineers (USACE)
##### Source
* Name: Dataquery 2.0
* Author: USACE
* Description: historical hourly data from the largest twenty hydroelectric dams in the USACE's Northwestern hydro system.
* Source: https://www.nwd.usace.army.mil/CRWM/Hydro-Engineering-Power/
* Exact source location: https://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/

##### Destination
* Modifications to source file(s): power output on 4/26/2019 16:00 UTC for two dams (WAN and PRD) exceeds their respective capacity. These outliers were replaced with an average of the hour before and after the outlier hour, for each of the two dams.
* Location: ***prereise/gather/hydrodata/data/usace_hydro_2019.csv***

##### General Purpose
The dataset is used to generate hydro profiles for the Western interconnection.


#### ISO New England (ISONE)
##### Source
* Name: Real-Time Maps and Charts
* Author: ISONE
* Description: real-time generation data by fuel type for ISONE in UTC.
Temporal resolution is adjustable from 2 min to 20 min per sample.
* Source: https://www.iso-ne.com/
* Exact source location: https://www.iso-ne.com/isoexpress/

##### Destination
* Modifications to source file(s): Average of all samples during each hour was
used. Data from all two-day files was concatenated into one csv file for the
entire year of 2016. Data for 121 missing hours were imputed.
* Location: ***prereise/gather/hydrodata/data/neiso_hydro_2016.csv***

##### General Purpose
The dataset is used to generate hydro profiles for the Eastern interconnection.

#### Southwest Power Pool (SPP)
##### Source
* Name: SPP Integrated Marketplace
* Author: SPP
* Description: publicly available generation fuel mix data for SPP
* Source: https://marketplace.spp.org
* Exact source location: https://marketplace.spp.org/pages/generation-mix-historical

##### Destination
* Modifications to source file(s): Raw data is provided at 5 min interval and
was averaged for the hour to create an hourly profile.
* Location: ***prereise/gather/hydrodata/data/spp_hydro_2016.csv***

##### General Purpose
The dataset is used to generate hydro profiles for the Eastern interconnection.

##### Note
Data from this source may be freely copied and distributed except in
connection with a commercial publication.

#### New York Independent System Operator (NYISO)
##### Source
* Name: Open Access Same-Time Information System (OASIS)
* Author: NYISO
* Description: historical fuel mix generation data in various temporal
resolution
* Source: http://mis.nyiso.com/
* Exact source location: http://mis.nyiso.com/public/P-63list.htm

##### Destination
* Modifications to source file(s): Data was reformatted into one excel file
and averaged among the intervals within one hour. Data for missing hours was
computed by averaging the non-blank hour before and after the missing hour.  
* Location: ***prereise/gather/hydrodata/data/nyiso_hydro_2016.csv***

##### General Purpose
The dataset is used to generate hydro profiles for the Eastern interconnection.

####  PJM Interconnection LLC (PJM)
##### Source
* Name: Data Miner 2
* Author: PJM
* Description: historical hourly hydro generation data for PJM in 2016
* Source: http://dataminer2.pjm.com/
* Exact source location: http://dataminer2.pjm.com/feed/gen_by_fuel

##### Destination
* Modifications to source file(s): Data for 2015 is not available from the
tool and the time series data for 2016 is recorded in local time. The last 5
hours of 2016 EST were used to represent the first 5 hours of the year to
fill in that missing data.
* Location: ***prereise/gather/hydrodata/data/pjm_hydro_2016.csv***

##### General Purpose
The dataset is used to generate hydro profiles for the Eastern interconnection.

---
### Solar
#### Energy Information Administration (EIA)
##### Source
* Name: Form EIA-860
* Author: EIA
* Description: 2016 solar technology data for operable units (Schedule 3)
* Source: https://www.eia.gov
* Exact source location: https://www.eia.gov/electricity/data/eia860/

##### Destination
* Modifications to source file(s): convert to `csv`
* Location: ***prereise/gather/solardata/data/3_3_Solar_Y2016.csv***

##### General Purpose
The dataset is used to generate solar profiles.


---
### Wind
#### Energy Information Administration (EIA)
##### Source
* Name: Form EIA-860
* Author: EIA
* Description: 2016 wind technology data for operable units (Schedule 3)
* Source: https://www.eia.gov
* Exact source location: https://www.eia.gov/electricity/data/eia860/

##### Destination
* Modifications to source file(s): convert to `csv`
* Location: ***prereise/gather/winddata/data/3_2_Wind_Y2016.csv***

##### General Purpose
The dataset is used to generate wind profiles.


---


[nrel_disclaimer]: https://www.nrel.gov/disclaimer.html

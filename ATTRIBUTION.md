## Third Party Data
This package contains a variety of materials, including data sets and related materials. The third party data sets and related materials are provided by their respective publishers, and may be subject to separate and additional terms and conditions. The following summarizes the sources of the applicable data, and details regarding the applicable provider. Additional terms and conditions, including certain restrictions on commercial use, redistribution, or other similar restrictions, may apply to the applicable data sets. If you cannot comply with the terms of the applicable data collection, you may not use that data, and your ability to make use of this software package, and/or the results or output you are able to generate through its use may be impacted. Please review the information provided below, and the terms and conditions provided by the publisher at the original source for more information.


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
* Location: ***prereise/gather/data/demanddata/eia/demo/eastern_demand_v6_demo/spp/load/****

##### Note
* Data from this source may be freely copied and distributed except in connection with a commercial publication.


##### Source
* Name: Legacy BAs geographical coverage
* Author: SPP
* Description: link each county covered by SPP to its sub-area
* Source: https://spp.org/
* Exact source location: file obtained open request through SPP internal request management system (https://spprms.issuetrak.com/Login.asp)

##### Destination
* Modifications to source file(s): None
* Location: ***prereise/gather/data/demanddata/eia/demo/eastern_demand_v6_demo/spp/spp_counties_owners.xlsx***

##### Note
* Legal review pending


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
  * ***prereise/gather/data/demanddata/eia/demo/eastern_demand_v6_demo/miso/20151231_dfal_hist.xls***
  * ***prereise/gather/data/demanddata/eia/demo/eastern_demand_v6_demo/miso/20161231_dfal_hist.xls***

##### Note
* Requesting attribution
* Provide a copy of the final product to MISO


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
* Location: ***prereise/gather/data/hydrodata/data/usa_hydro_capacity_factors.csv***


#### Electric Reliability Council of Texas (ERCOT)
##### Source
* Name: Fuel mix report
* Author: ERCOT
* Description: Actual generation by fuel type for each 15-minute settlement interval, as well as totals by month and year-to-date.
* Source: http://www.ercot.com/
* Exact source location: http://www.ercot.com/gridinfo/generation/

##### Destination
* Modifications to source file(s): monthly files have been concatenated and timestamps have been converted to UTC.
* Location: ***prereise/gather/data/hydrodata/data/texas_hydro_generation.csv***

#### Note
* Disclose modifications


#### U.S. Army Corps of Engineers (USACE)
##### Source
* Name: Dataquery 2.0
* Author: USACE
* Description: historical hourly data from the largest twenty hydroelectric dams in the USACE's Northwestern hydro system.
* Source: https://www.nwd.usace.army.mil/CRWM/Hydro-Engineering-Power/
* Exact source location: https://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/

##### Destination
* Modifications to source file(s): power output on 4/26/2019 16:00 UTC for two dams (WAN and PRD) exceeds their respective capacity. These outliers were replaced with an average of the hour before and after the outlier hour, for each of the two dams.
* Location: ***prereise/gather/data/hydrodata/data/western_hydro_generation.csv***

#### Note
* Public data


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
* Location: ***prereise/gather/data/solardata/data/3_3_Solar_Y2016.csv***


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
* Location: ***prereise/gather/data/winddata/data/3_2_Wind_Y2016.csv***


---

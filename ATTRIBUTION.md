## Third Party Data
This package contains a variety of materials, including data sets and related materials. The third party data sets and related materials are provided by their respective publishers, and may be subject to separate and additional terms and conditions. The following summarizes the sources of the applicable data, and details regarding the applicable provider. Additional terms and conditions, including certain restrictions on commercial use, redistribution, or other similar restrictions, may apply to the applicable data sets. If you cannot comply with the terms of the applicable data collection, you may not use that data, and your ability to make use of this software package, and/or the results or output you are able to generate through its use may be impacted. Please review the information provided below, and the terms and conditions provided by the publisher at the original source for more information.


### Geographical Information
#### BA to County Mapping
##### Source
* Name: Counties in the United States
* Author: mapchart.net
* Description: An interactive map contains all the counties in the United
 States
* Source: https://mapchart.net
* Exact source location: https://mapchart.net/usa-counties.html

##### Destination
* Modifications to source file(s): None
* Location: ***prereise/gather/data/ba_to_county.txt***

#### PUMA Shape File
##### Source
* Name: TIGER/Line Shapefiles, PUMA, 2010
* Author: U.S. Census Bureau
* Description: Shapefiles for Public Use Microdata Areas (PUMAs), Year 2010
* Source: https://www.census.gov/
* Exact source location: https://www2.census.gov/geo/tiger/TIGER2010/PUMA5/2010/

##### Destination
* Modifications to source file(s): Shapefiles for 48 contiguous U.S states and DC are merged into one shapefile covering entire geography.
* Location: 
  * ***prereise/gather/demanddata/bldg_electrification/data/pumas.dbf***
  * ***prereise/gather/demanddata/bldg_electrification/data/pumas.prj***
  * ***prereise/gather/demanddata/bldg_electrification/data/pumas.shp***
  * ***prereise/gather/demanddata/bldg_electrification/data/pumas.shx***

##### General Purpose
The data are used to assign a time zone to each PUMA.

#### Timezone Shape File
##### Source
* Name: Timezone Boundary Shapefiles
* Author: Evan Siroky
* Description: Shapefiles for Public Use Microdata Areas (PUMAs), Year 2010
* Source: https://github.com/evansiroky/timezone-boundary-builder
* Exact source location: https://github.com/evansiroky/timezone-boundary-builder/releases/download/2020d/timezones.shapefile.zip

##### Destination
* Modifications to source file(s): Rename files from combined shapefiles to timezones shapefiles.
* Location: 
  * ***prereise/gather/demanddata/bldg_electrification/data/tz_us.dbf***
  * ***prereise/gather/demanddata/bldg_electrification/data/tz_us.prj***
  * ***prereise/gather/demanddata/bldg_electrification/data/tz_us.shp***
  * ***prereise/gather/demanddata/bldg_electrification/data/tz_us.shx***

##### General Purpose
The data are used to assign a time zone to each PUMA.

##### Note
The data is licensed under the [Open Data Commons Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/)

#### US County Map Shape Files
#### Source
* Name: US County map
* Author: US Census Bureau
* Description: US county map
* Source: https://www.census.gov/
* Exact source location: https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html
#### Destination
* Modifications to source files(s): None
* Location: ***prereise/gather/data/cb_2020_us_county_500k.zip***


#### Retail Service Territory 
#### Source
* Name: Electric Retail Service Territory 
* Author: Homeland Infrastructure Foundation-Level Data (HIFLD)
* Description: electric retail service territory
* Source: https://hifld-geoplatform.opendata.arcgis.com/
* Exact source location: https://hifld-geoplatform.opendata.arcgis.com/datasets/geoplatform::electric-retail-service-territories-2/explore
#### Destination
* Modifications to source files(s): none
* Location: ***prereise/gather/data/Electric_Retail_Service_Territories.zip***


#### Upstate Subregions of NYISO
#### Source
* Name: upstate subregions of NYISO
* Author: ArcGIS
* Description: upstate subregions of NYISO
* Source: https://www.arcgis.com/
* Exact source location: https://www.arcgis.com/home/item.html?id=6fd1de467b134f47a607721f23a69f0c
#### Destination
* Modifications to source files(s): None for the upstate subregions A-F, they are directly downloaded by the program 
* Location: ***prereise/gather/data/remap_ba_area/nyiso/***

#### Downstate Subregions of NYISO
#### Source
* Name: downstate subregions of NYISO
* Author: Self created
* Description: downstate subregions of NYISO
* Source: N/A
* Exact source location: N/A
#### Destination
* Modifications to source files(s): Subregions H and I are made by splitting the Westchester County of New York State; Subregion K is by grouping the five counties of the New York City, Kings, Queens, Richmond, Bronx and New York County; Subregion K is made by combining the Nassau county and the Suffolk county. The NYISO zonal map is referenced here https://www.nyiso.com/documents/20142/1397960/nyca_zonemaps.pdf/8c3807e1-5bab-ab44-3c71-2c8e61b5748b?msclkid=01dfacc4b7a411ec99d260fa17bfa652.
* Location: ***prereise/gather/data/remap_ba_area/nyiso/NYISO_downstate.geojson***

#### CAISO
#### Source
* Name: subregions of CAISO
* Author: CAISO
* Description: the subregions of CAISO
* Source: https://www.caiso.com/
* Exact source location: https://cecgis-caenergy.opendata.arcgis.com/datasets/CAEnergy::california-electric-balancing-authority-areas
#### Destination
* Modifications to source files(s): None
* Location: ***prereise/gather/data/remap_ba_area/CA_balancing_authorities/***

#### PJM
#### Source
* Name: subregions of PJM
* Author: PJM
* Description: the subregions of PJM
* Source: PJM
* Exact source location:  https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/2018/2018-som-pjm-volume2-appendix.pdf
#### Destination
* Modifications to source files(s): The shape files are made from the image.
* Location: ***prereise/gather/data/remap_ba_area/pjm.zip***

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
* Exact source location: There are nine different .zip files containing demand data for the nine combinations of three electrification scenarios and three technology advancements. They can be accessed via: "https://data.nrel.gov/system/files/126/EFSLoadProfile_" + es + "_" + ta + ".zip", where es is in {"Reference", "Medium", "High"} and ta is in {"Slow", "Moderate", "Rapid"}.

##### Destination
* Modifications to source file(s):
  * Sectoral demand is aggregated so that there is only one value for each time and location.
  * State-level demand is mapped to the load zones defined by Breakthrough Energy Sciences.
  * Of the six years' worth of data provided in each dataset, only one user-specified year is kept.
* Location: These datasets are not included in this package. Rather, users are able to access and modify the datasets using modules included in this package.

##### General Purpose
These datasets are used to generate demand profiles that account for projected widespread electrification in the contiguous U.S.

##### Note
These datasets are generously provided by NREL, which is operated for the U.S. Department of Energy by the Alliance for Sustainable Energy, LLC. Before using these datasets, please read [this disclaimer](https://www.nrel.gov/disclaimer.html) first.

##### Source
* Name: Electrification Futures Study Flexible Load Profiles
* Authors: Paige Jadun, Trieu Mai, Caitlin Murphy, Yinong Sun, Matteo Muratori, Brent Nelson, Ryan Jones, Jeffrey Logan
* Description: Projected state-level flexible demand profiles for different electrification scenarios, levels of technology advancement, flexibility scenarios, and years.
* Source: https://data.nrel.gov/submissions/127
* Exact source location: There are three different .zip files containing flexibility data for each of the three electrification scenarios. They can be accessed via: "https://data.nrel.gov/system/files/127/EFS Flexible Load Profiles - " + es + " Electrification.zip", where es is in {"Reference", "Medium", "High"}.

##### Destination
* Modifications to source file(s):
  * State-level demand is mapped to the load zones defined by Breakthrough Energy Sciences.
  * Of the six years' worth of data provided in each dataset, only one user-specified year is kept.
  * Of the three different technology advancements, data for only one user-specified technology advancement is kept.
  * Of the two different flexibility scenarios, data for only one user-specified flexibility scenario is kept.
* Location: These datasets are not included in this package. Rather, users are able to access and modify the datasets using modules included in this package.

##### General Purpose
These datasets are used to generate flexibility profiles that are realized through the projected widespread electrification in the contiguous U.S.

##### Note
These datasets are generously provided by NREL, which is operated for the U.S. Department of Energy by the Alliance for Sustainable Energy, LLC. Before using these datasets, please read [this disclaimer](https://www.nrel.gov/disclaimer.html) first.


#### U.S. Environmental Protection Agency
##### Source
* Name: MOVES2010 Highway Vehicle Population and Activity Data
* Author: U.S. Environmental Protection Agency
* Description: Vehicle Miles Travelled disribution by month and by weekday/weekend
* Source: https://www.epa.gov/moves/moves-onroad-technical-reports
* Exact Source Location: https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=P100ABRO.pdf

##### Destination
* Modifications to source file(s): None
* Location:
  * ***prereise/gather/demanddata/transportation_electrification/moves_daily.csv***
  * ***prereise/gather/demanddata/transportation_electrification/moves_monthly.csv***

##### General Purpose
The dataset is used to distribute the annual vehicle miles traveled (VMT) using seasonal weight factors for the final charging profiles.

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
The dataset is used to generate wind profiles from wind speed profiles.

### The Wind Power
##### Source
* Name: Power curves database
* Author: The Wind Power
* Description: power curves for 802 different turbines
* Source: https://www.thewindpower.net
* Exact source location: https://www.thewindpower.net/store_manufacturer_turbine_en.php?id_type=7

##### Destination
* Modifications to source file(s): 82 power curves are selected and gathered in a `csv` file.
* Location: ***prereise/gather/winddata/data/PowerCurves.csv***

##### General Purpose
The dataset is used to generate wind profiles from wind speed profiles.

### NREL
##### Source 
* Name: Wind Integration National Data set (WIND) toolkit
* Author: NREL
* Description: report dedicated to the validation of power output for the NREL WIND toolkit
* Source: https://www.nrel.gov/docs/fy14osti/61714.pdf
* Exact source location: Table 2 of report.

##### Destination
* Modifications to source file(s): the 4 normalized power curves were added to the list of power curves used to produce the wind profiles
* Location: ***prereise/gather/winddata/data/PowerCurves.csv***

##### General Purpose
The dataset is used to generate wind profiles from wind speed profiles.

##### Note
Recommended citation: J. King, A. Clifton and B.-M. Hodge. 2014. Validation of Power Output for the WIND Toolkit, Golden, CO: National Renewable Energy Laboratory. NREL/TP-6A20-74110. https://www.nrel.gov/docs/fy14osti/61714.pdf

---


### Building Electrification
#### Quadracci Sustainable Engineering Lab (QSEL)
##### Source
* Name: Space Heating Heat Pump Parameters
* Author: QSEL
* Description: space heating heat pump coefficient of performance and capacity rating at standard temperatures for 3 models: "midperfhp", "advperfhp" and "futurehp"
* Source:
  * "midperfhp" and "advperfhp": https://neep.org/ 
  * "futurehp": https://www.energy.gov/eere/office-energy-efficiency-renewable-energy/
* Exact source location: 
  * "midperfhp" and "advperfhp": [ccASHP 2019]
  * "futurehp": [Bouza, A 2016]

##### Destination
* Modifications to source file(s): The development of hp_parameters is described in detail in [Waite M, Modi V 2020], including: three models for temperature-dependent HP coefficient of performance, are developed based on the 90th percentile performance of HPs in [ccASHP 2019] ("advperfhp"), the median performance of cold climate HPs in [ccASHP 2019] ("midperfhp"), and the midpoint between residential and commercial electric HP performance targets set by the U.S. Department of Energy in [Bouza, A 2016].

[ccASHP 2019]: https://neep.org/heating-electrification/ccashp-specification-product-list
[Bouza, A 2016]: https://energy.gov/sites/prod/files/2016/04/f30/Bouza%2C%20Tony_HVAC%2C%20WH%20and%20Appliance.pdf
[Waite M, Modi V 2020]: https://engrxiv.org/mh4py/download
* Location: ***prereise/gather/demanddata/bldg_electrification/data/hp_parameters.csv***

##### General Purpose
The data is used to compute temperature-dependent coefficient of performance for each of the three model space heating heat pumps in `ff2elec_profile_generator_htg.py`. Pre-computed COP values against ambient temperature is stored in `data/cop_temp_htg_advperfhp.csv` and `data/cop_temp_htg_midperfhp.csv`

##### Source
* Name: Domestic Hot Water Heat Pump Parameters
* Author: QSEL
* Description: domestic hot water (DHW) heat pump coefficient of performance and capacity rating at standard temperatures for 3 models: "midperfhp," "advperfhp," and "futurehp"
* Source:
  * Base product: https://www.eco2waterheater.com/
  * Performance data: https://www.smallplanetsupply.com/
* Exact source location: page 13 of [Sanden SanCO2 performance data]

##### Destination
* Modifications to source file(s): "advperfhp" parameters directly from [Sanden SanCO2 performance data] for outlet water temperature of 140 deg. F. "midperfhp" scales "advperfhp" parameters to match HP performance in [Shapiro C, Puttagunta S 2016]. "futurehp" scales "advperfhp" parameters to match improvement target in [Goetzler W, et al. 2014].

[Sanden SanCO2 performance data]: https://static1.squarespace.com/static/5c1a79ca96d455dcbffdc742/t/5c474cee562fa759dd733b04/1548176625850/Sanden_sanc02_technical-info_10-2017_4.pdf
[Shapiro C, Puttagunta S 2016]: https://www.nrel.gov/docs/fy16osti/64904.pdf
[Goetzler W, et al. 2014]: https://www.energy.gov/sites/prod/files/2014/09/f18/WH_Roadmap_Report_Final_2014-09-22.pdf
* Location: ***prereise/gather/demanddata/bldg_electrification/data/hp_parameters_dhw.csv***

##### General Purpose
The data are used to compute temperature-dependent coefficient of performance for each of the three model domestic hot water heating heat pumps in `ff2elec_profile_generator_dhw.py`.


#### Energy Information Administration (EIA)
##### Source
* Name: CBECS Floor Areas
* Author: EIA
* Description: Floor areas of state groups from CBECS data
* Source: https://www.eia.gov
* Exact source location: 
  * CBECS2003 Table A4: https://www.eia.gov/consumption/commercial/archive/cbecs/cbecs2003/detailed_tables_2003/2003set2/2003html/a4.html
  * CBECS2003 Table B5: https://www.eia.gov/consumption/commercial/data/2012/bc/pdf/b1-b46.pdf

##### Destination
* Modifications to source file(s): Data from CBECS2003 Table A4 and CBECS2012 Table B5 are combined. Columns corresponding to states in each Census Division are added.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/area_scale_com.csv***

##### General Purpose
The data are used to compute 2010 commercial floor areas for state groupings in order to scale General Building Stock data.

##### Source
* Name: RECS Floor Areas
* Author: EIA
* Description: Floor areas of state groups from RECS data
* Source: https://www.eia.gov
* Exact source location:
  * RECS2009: https://www.eia.gov/consumption/residential/data/2009/
  * RECS2015: https://www.eia.gov/consumption/residential/data/2015/

##### Destination
* Modifications to source file(s): Data from RECS2009 Tables HC10.2-10.5 and RECS2015 Tables HC10.2-10.5 are combined. Columns corresponding to states in each Census Division and subgroups reported in RECS are added.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/area_scale_res.csv***

##### General Purpose
The data are used to compute 2010 commercial floor areas for state groupings in order to scale General Building Stock data.

##### Source
* Name: Natural Gas Consumption by End Use, Volumes Delivered to Commercial
* Author: EIA
* Description: Monthly natural gas usage by commercial customers by state 2010
* Source: https://www.eia.gov
* Exact source location: https://www.eia.gov/dnav/ng/ng_cons_sum_a_EPG0_vcs_mmcf_m.htm

##### Destination
* Modifications to source file(s): The data are organized and labeled for use in fossil fuel fitting and electrification models.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/ng_monthly_mmbtu_2010_com.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: Natural Gas Consumption by End Use, Volumes Delivered to Residential
* Author: EIA
* Description: Monthly natural gas usage by residential customers by state 2010
* Source: https://www.eia.gov
* Exact source location: https://www.eia.gov/dnav/ng/ng_cons_sum_a_EPG0_vrs_mmcf_m.htm

##### Destination
* Modifications to source file(s): The data are organized and labeled for use in fossil fuel fitting and electrification models.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/ng_monthly_mmbtu_2010_res.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: Adjusted Fuel Oil and Kerosene Sales by End Use, Revised
* Author: EIA
* Description: Annual fuel oil and kerosense usage by consumer class (residential/commercial) year and state
* Source: https://www.eia.gov
* Exact source location: http://www.eia.gov/dnav/pet/xls/eia_821_data_difference.xls

##### Destination
* Modifications to source file(s): The data are organized and labeled for use in fossil fuel fitting and electrification models.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/fok_data_bystate_2010.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: 2010 Propane Sales by State
* Author: EIA
* Description: Annual propane usage, by consumer class (residential/commercial) year and state
* Source: https://www.eia.gov
* Exact source location: https://www.eia.gov/state/seds/seds-data-complete.php?sid=US

##### Destination
* Modifications to source file(s): Annual propane usage data for residential and commercial buildings are extracted. The data are organized and labeled for use in fossil fuel fitting and electrification models.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/propane_data_bystate_2010.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: Fraction Target for Main Commercial Cooking Fuel
* Author: EIA
* Description: Fraction of commercial floor space using electricity, natural gas, propane for cooking in 2010 for each of 4 Census Regions
* Source: https://www.eia.gov
* Exact source location:
  * CBECS2003: https://www.eia.gov/consumption/commercial/data/2003/
  * CBECS2012: https://www.eia.gov/consumption/commercial/data/2012/

##### Destination
* Modifications to source file(s): Interpolate 2010 values based on CBECS 2003 Table B33 and estimate values for 2012 main cooking fuel computed from any use of each fuel for cooking (CBECS 2012 Table B3) and total commercial floor area with cooking in each region (CBECS 2012 Table B25).
* Location: ***prereise/gather/demanddata/bldg_electrification/data/frac_target_cook_com.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: Fraction Target for Main Commercial Domestic Hot Water Fuel
* Author: EIA
* Description: Fraction of commercial floor space using electricity, natural gas, propane, fuel oil for domestic hot water in 2010 for each of 4 Census Regions
* Source: https://www.eia.gov
* Exact source location:
  * CBECS2003: https://www.eia.gov/consumption/commercial/data/2003/
  * CBECS2012: https://www.eia.gov/consumption/commercial/data/2012/

##### Destination
* Modifications to source file(s): Interpolate 2010 values based on CBECS 2003 Table B32 and estimate values for 2012 main domestic hot water fuel computed from any use of each fuel for DHW (CBECS 2012 Table B3) and total commercial floor area with DHW in each region (CBECS 2012 Table B25).
* Location: ***prereise/gather/demanddata/bldg_electrification/data/frac_target_dhw_com.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: Fraction Target for Main Residential Domestic Hot Water Fuel
* Author: EIA
* Description: Fraction of households using electricity, natural gas, propane, fuel oil for domestic hot water in 2010 for each of 4 Census Regions
* Source: https://www.eia.gov
* Exact source location:
  * RECS2009: https://www.eia.gov/consumption/residential/data/2009/
  * RECS2015: https://www.eia.gov/consumption/residential/data/2015/

##### Destination
* Modifications to source file(s): Interpolate 2010 values based on RECS2009 Tables 8.8-8.11 and RECS2015 Tables 8.7 and 8.8.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/frac_target_dhw_res.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: Fraction Target for Main Residential Cooking Fuel
* Author: EIA
* Description: Fraction of households using electricity, natural gas, propane for cooking in 2010 for each of 4 Census Regions
* Source: https://www.eia.gov
* Exact source location:
  * RECS2009: https://www.eia.gov/consumption/residential/data/2009/
  * RECS2015: https://www.eia.gov/consumption/residential/data/2015/

##### Destination
* Modifications to source file(s): Interpolate 2010 values based on RECS2009 Tables 3.8-3.11 and RECS2015 Tables 3.7 and 3.8.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/frac_target_other_res.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: Fraction Target for Main Commercial Space Heating Fuel
* Author: EIA
* Description: Fraction of commercial floor space using electricity, natural gas, propane, fuel oil for space heating in 2010 for each of 4 Census Regions
* Source: https://www.eia.gov
* Exact source location:
  * CBECS2003: https://www.eia.gov/consumption/commercial/data/2003/
  * CBECS2012: https://www.eia.gov/consumption/commercial/data/2012/

##### Destination
* Modifications to source file(s): Interpolate 2010 values based on CBECS2003 Table B29 and CBECS2012 Table B3.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/frac_target_sh_com.csv***

##### General Purpose
The data are used to fit model for temperature-dependent fossil fuel usage.

##### Source
* Name: Fraction Target for Residential and Commercial Heat Pump Possession as Main Heating Device
* Author: EIA
* Description: Fraction of residential or commercial floor space using heat pump as main heating device for Census Regions
* Source: https://www.eia.gov
* Exact source location:
  * RECS2015: https://www.eia.gov/consumption/residential/data/2015/
  * RECS2020: https://www.eia.gov/consumption/residential/data/2020/
  * CBECS2012: https://www.eia.gov/consumption/commercial/data/2012/
  * CBECS2018: https://www.eia.gov/consumption/commercial/data/2018/

##### Destination
* Modifications to source file(s): Interpolate 2019 values based on RECS2015 and RECS2020, and extrapolate 2019 values based on CBECS2012 and CBECS 2018.
* Location: 
  * ***prereise/gather/demanddata/bldg_electrification/data/frac_target_hp_res.csv***
  * ***prereise/gather/demanddata/bldg_electrification/data/frac_target_hp_com.csv***

##### General Purpose
The data are used to fit model for current heat pump penetration rate.

##### Source
* Name: Natural Gas Prices
* Author: EIA
* Description: Annual average natural gas price (residential) of states
* Source: https://www.eia.gov
* Exact source location: https://www.eia.gov/dnav/ng/ng_pri_sum_dcu_nus_a.htm
##### Destination
* Location: ***prereise/gather/demanddata/bldg_electrification/data/state_ng_residential_price_2019.csv***

##### General Purpose
The data are used in the linear regression model for estimating current heat pump penetration rate. 


#### U.S. Census Bureau
##### Source
* Name: House Heating Fuel
* Author: U.S. Census Bureau
* Description: Estimated primary heating fuel by number of households in each Public Use Microdata Area (PUMA) based on American Community Survey (ACS), Table B25040, 2012: ACS 5-Year Estimates Detailed Tables
* Source: https://www.census.gov/
* Exact source location: https://data.census.gov/cedsci/table?q=B25040&tid=ACSDT1Y2019.B25040

##### Destination
* Modifications to source file(s): Column headers are modified. State ID is added as another column.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/puma_fuel_2010.csv***

##### General Purpose
The data are used as basis for PUMA-level adjustments for other residential end uses (DHW and cooking) and commercial fossil fuel uses (space heating, DHW and cooking).

##### Source
* Name: 2010 Census Tract to 2010 PUMA Mapping File
* Author: U.S. Census Bureau
* Description: File with Census Tract ID and corresponding PUMA for each Census Tract
* Source: https://www.census.gov/
* Exact source location: https://www2.census.gov/geo/docs/maps-data/data/rel/2010_Census_Tract_to_2010_PUMA.txt

##### Destination
* Modifications to source file(s): Census Tract and PUMA identification numbers are extracted from source data. Text strings for consistency with other elements of  code are appended. File format is changed to CSV.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/tract_puma_mapping.csv***

##### General Purpose
The data are used to aggregate to the PUMA level data available only at the Census Tracts level or previously assigned to Census Tracts.

##### Source
* Name: 2010 Decennial Census Population by Census Tract
* Author: U.S. Census Bureau
* Description: Census Tract level population for Year 2010
* Source: https://www.census.gov/
* Exact source location: https://data.census.gov/cedsci/table?t=Populations%20and%20People&g=0100000US%241400000&y=2010&d=DEC%20Summary%20File%201&tid=DECENNIALSF12010.P1

##### Destination
* Modifications to source file(s): None
* Location: ***prereise/gather/demanddata/bldg_electrification/data/tract_pop.csv***

##### General Purpose
The data are used to compute population-weighted average values for PUMAs based on the Census Tract data.

##### Source
* Name: American Housing Survey (AHS)
* Author: U.S. Census Bureau
* Description: Number of household use heat pumps as main heating equipment for metropolitan areas, Table "Heating, Air Conditioning, and Appliances", year 2017 and 2019
* Source: https://www.census.gov/
* Exact source location: https://www.census.gov/programs-surveys/ahs/data/interactive/ahstablecreator.html?s_areas=00000&s_year=2019&s_tablename=TABLE3&s_bygroup1=1&s_bygroup2=1&s_filtergroup1=1&s_filtergroup2=1

##### Destination
* Modifications to source file(s): the household number that possess heat pumps are converted to fractions of household within the survey area by dividing it to the total household number provided in the same tables. 
* Location: ***prereise/gather/demanddata/bldg_electrification/data/hp_ahs.xlsx***

##### General Purpose
The data are used as basis for estimating current heat pump penetration rate. 


#### U.S. Federal Emergency Management Agency (FEMA)
##### Source
* Name: General Building Stock Floor Areas by Building Class
* Author: FEMA
* Description: General Building Stock database available as part of FEMA's Hazus application, which includes building square footage estimates by occupancy at the Cenus Tract level for 2010.
* Source: https://www.fema.gov
* Exact source location: https://msc.fema.gov/portal/resources/download#HazusDownloadAnchor

##### Destination
* Modifications to source file(s): Details of the modifcations are in [Waite M, et al. 2020].

[Waite M, et al. 2020]: https://www.sciencedirect.com/science/article/pii/S2542435119305781
* Location: ***prereise/gather/demanddata/bldg_electrification/data/tract_gbs_area.csv***

##### General Purpose
The data are used to assign building areas by class at the Census Tract level. These areas are then scaled based on other data sources to estimate 2010 floor areas of each class in `puma_data_agg.py`.

##### Note
The source data is at times not available and may requires the installation of the Hazus Application.


#### U.S. National Oceanic and Atmospheric Administration (NOAA)
##### Source
* Name: 1981-2010 Climate Normals
* Author: NOAA
* Description: Heating Degree Day and Cooling Degree Day Normals (65 deg. F basis)
* Source: https://www.noaa.gov
* Exact source location:
  * Heating degree day normals: https://www.ncei.noaa.gov/pub/data/normals/1981-2010/products/temperature/ann-htdd-normal.txt
  * Cooling degree day normals: https://www.ncei.noaa.gov/pub/data/normals/1981-2010/products/temperature/ann-cldd-normal.txt

##### Destination
* Modifications to source file(s): Heating Degree Day normals (HDD65) and Cooling Degree Day normals (CDD65) are assigned to each Census Tract based on the nearest weather station in the NOAA data.
* Location: ***prereise/gather/demanddata/bldg_electrification/data/tract_degday_normals.csv***

##### General Purpose
The data are aggregated at the PUMA level and used for various modules that estimate technology adoption (e.g. residential air conditioning) and climate-adjusted heating and cooling behavior.

---

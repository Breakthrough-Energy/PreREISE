## Demand Profiles

| Demand Profiles  | Methodology   | Dimension     | Notes
| ------------- |:-------------:|:-------------:|:------------:|
| western_demand_v4 | BA County mapping + population proportion | 8784*16 | [EIA 930] and [EIA 860]
| texas_demand_ercot | historical load data | 8784*8 | ERCOT
| texaswestern_demand_v4 | western_demand_v4 + texas_demand_ercot | 8784*24 | existing profiles concatenation
| eastern_demand_v5 | Bus BA mapping + PD proportion | 8784*52 | [EIA 930]
| eastern_demand_v6 | Bus BA/BA subarea mapping + PD proportion | 8784*52 | [EIA 930] and MISO/SPP contacts
| usa_demand_v6 | texaswestern_demand_v4 + eastern_demand_v6 | 8784*76 | existing profiles concatenation

<!--Profiles no longer in use:
 western_demand_v3
 western_demand_ca2020
 western_demand_ca2030
 -->

[EIA 860]: https://www.eia.gov/electricity/data/eia860/
[EIA 930]: https://www.eia.gov/opendata/


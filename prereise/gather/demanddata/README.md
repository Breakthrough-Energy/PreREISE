## Demand Profiles

| Name            | Grid Model | Methodology  | Dimension    | Notes
|:----------------|:-----------|:-------------|:-------------|:------------|
| demand_vJan2021 | usa_tamu   | <li>Texas: historical load data</li><li>Western: BA to county mapping + population weighting (v4)</li><li>Eastern: bus BA to BA subarea mapping + `Pd` weighting (v6)</li> | 8784*76 | <li>Texas: ERCOT</li><li>Western: [EIA 930] + [EIA 860]</li><li>Eastern: [EIA 930] + MISO/SPP contacts</li> |

---
**Definition**
* BA: Balancing Authority
* ERCOT: Electricity Reliability Council of Texas
* EIA: U.S. Energy Information Administration
* MISO: Midcontinent Independent System Operator
* SPP: Southwest Power Pool
* `Pd`: Real Power demand (MW). The value is given for each bus in the ***bus.csv***
file of a grid model, see e.g., ***powersimdata/network/usa_tamu/data/bus.csv***

---

[EIA 860]: https://www.eia.gov/electricity/data/eia860/
[EIA 930]: https://www.eia.gov/opendata/

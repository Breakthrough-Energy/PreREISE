## Solar Profiles

| Name            | Grid Model | Methodology  | Dimension    | Notes
|:----------------|:-----------|:-------------|:-------------|:------------|
| solar_vJan2021  | usa_tamu   | [NSRDB][NSRDB_web] + [SAM][SAM_web] with [PVWatts v5][SAM_pvwatts] model:<li>DC/AC=1.25</li><li>inverter efficiency: 0.94</li><li>tilt angle: 30deg</li><li>array type: [0, 2, 4] in proportion to technology used in State | 8784*1139 | [EIA 860] |

---
**Definition**
* NSRDB: National Solar Radiation DataBase
* SAM: System Advisor Model

---


[NSRDB_web]: https://nsrdb.nrel.gov/
[SAM_web]: https://sam.nrel.gov/
[SAM_pvwatts]: https://www.nrel.gov/docs/fy14osti/62641.pdf
[EIA 860]: https://www.eia.gov/electricity/data/eia860/

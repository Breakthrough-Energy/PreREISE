## Wind Profiles

| Name          | Grid Model | Methodology  | Dimension    | Notes
|:--------------|:-----------|:-------------|:-------------|:------------|
| wind_vJan2021 | usa_tamu   | [RAP]:<li>wind speed at 80m</li><li>power curve per state for onshore and unique power curve for offshore<li>gaussian with std=0.4 (onshore) and 0.25 (offshore) for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*1084 | [EIA 860] |

---
**Definition**
* RAP: Rapid Refresh

---

[RAP]: https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/rapid-refresh-rap
[WIND_doc]: https://www.nrel.gov/docs/fy14osti/61714.pdf
[issue #71]: https://github.com/intvenlab/PreREISE/issues/71
[EIA 860]: https://www.eia.gov/electricity/data/eia860/

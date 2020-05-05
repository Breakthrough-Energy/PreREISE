## Wind Profiles

| Wind Profiles        | Methodology   | Dimension     | Notes
| -------------------- |:--------------|:-------------:|:------------|
| texas_wind_v2        | [RAP]:<li>wind speed at 80m</li><li>[NREL IEC-2][WIND_doc] power curve</li><li>10% loss factor</li><li>random distributions for imputation</li> | 8784*87| [bug][issue #71]
| western_wind_v2      | [RAP]:<li>wind speed at 80m</li><li>[NREL IEC-2][WIND_doc] power curve</li><li>10% loss factor</li><li>random distributions for imputation</li> | 8784*243 |
| texaswestern_wind_v2 | texas_wind_v2 + western_wind_v2 | 8784*330 | <li>existing profiles concatenation</li><li>[bug][issue #71]</li>
| eastern_wind_v2      | [RAP]:<li>wind speed at 80m</li><li>[NREL IEC-2][WIND_doc] power curve</li><li>10% loss factor</li><li>random distributions for imputation</li> | 8784*576 | [bug][issue #71]
| eastern_wind_v4.1    | [RAP]:<li>wind speed at 80m</li><li>power curve per state<li>gaussian with std=0.4 for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*598 | <li>[EIA 860]</li><li>[bug][issue #71]
| usa_wind_v4.1        | [RAP]:<li>wind speed at 80m</li><li>power curve per state<li>gaussian with std=0.4 for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*928 | <li>[EIA 860]</li><li>[bug][issue #71]</li>
| eastern_wind_v5      | [RAP]:<li>wind speed at 80m</li><li>power curve per state<li>gaussian with std=0.4 for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*598 | <li>[EIA 860]</li><li>[bug][issue #71]</li><li>new Pmax in Eastern</li>
| eastern_wind_v5.2.1  | [RAP]:<li>wind speed at 80m</li><li>power curve per state <li>gaussian with std=0.4 for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*640 | <li>[EIA 860]</li><li>new Pmax in Eastern</li>
| usa_wind_v5.2.1  | [RAP]:<li>wind speed at 80m</li><li>power curve per state <li>gaussian with std=0.4 for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*970 | [EIA 860]</li><li>new Pmax in Eastern</li>
| texas_wind_v5 | [RAP]:<li>wind speed at 80m</li><li>unique power curve<li>gaussian with std=0.4 for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*87 | [EIA 860]
| western_wind_v5.1 | [RAP]:<li>wind speed at 80m</li><li>power curve per state for onshore and unique power curve for offshore<li>gaussian with std=0.4 (onshore) and 0.25 (offshore) for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*267 | [EIA 860]
| texaswestern_wind_v5.1 | texas_wind_v5 + western_wind_v5.1 | 8784*354 | existing profiles concatenation
| eastern_wind_v5.3 | [RAP]:<li>wind speed at 80m</li><li>power curve per state for onshore and unique power curve for offshore<li>gaussian with std=0.4 (onshore) and 0.25 (offshore) for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li> | 8784*687 | [EIA 860]
| usa_wind_v5.3 | eastern_wind_v5.3 + texas_wind_v5 + western_wind_v5.1 | 8784*1041 | existing profiles concatenation
| western_wind_v5.2 | [RAP]:<li>wind speed at 80m</li><li>power curve per state for onshore and unique power curve for offshore<li>gaussian with std=0.4 (onshore) and 0.25 (offshore) for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li><li>newly introduced locations have been assigned the profile of the closest neighbor</li> | 8784*280 | [EIA 860]
| texas_wind_v5.1 | [RAP]:<li>wind speed at 80m</li><li>power curve per state<li>gaussian with std=0.4 for smoothing</li><li>10% loss factor</li><li>gaussian distributions for imputation</li><li>newly introduced locations have been assigned the profile of the closest neighbor</li> | 8784*117 | [EIA 860]
| texaswestern_wind_v5.2 | texas_wind_v5.1 + western_wind_v5.2 | 8784*397 | existing profiles concatenation
| usa_wind_v5.4 | eastern_wind_v5.3 + texas_wind_v5.1 + western_wind_v5.2| 8784*1084 | existing profiles concatenation


<!--Profiles no longer in use:
western_wind_v1
texas_wind_v1
texaswestern_wind_v1
eastern_wind_v1
eastern_wind_v3
eastern_wind_v3.1
-->

[RAP]: https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/rapid-refresh-rap
[WIND_doc]: https://www.nrel.gov/docs/fy14osti/61714.pdf
[issue #71]: https://github.com/intvenlab/PreREISE/issues/71
[EIA 860]: https://www.eia.gov/electricity/data/eia860/

## Solar Profiles

| Solar Profiles        | Methodology  | Dimension     | Notes
| --------------------- |:-------------|:-------------:|:------------|
| western_solar_v2      | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.1</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in interconnect</li> | 8784*391 | [EIA 860]
| texas_solar_v2        | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.1</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in interconnect</li> | 8784*22| [EIA 860]
| eastern_solar_v2      | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.1</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in interconnect</li> | 8784*571 | [EIA 860]
| texaswestern_solar_v2 | texas_solar_v2 + western_solar_v2 | 8784*413 | existing profiles concatenation
| eastern_solar_v3.1    | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.25</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in State</li> | 8784*612 | [EIA 860]
| usa_solar_v3.1        | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.25</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in State</li>| 8784*1025 | [EIA 860]
| eastern_solar_v4      | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.25</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in State </li> | 8784*612 | <li>[EIA 860]</li><li>new Pmax in Eastern</li>
| eastern_solar_v4.2    | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.25</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in State | 8784*670| <li>[EIA 860]</li><li>new Pmax in Eastern</li>
| usa_solar_v4.2    | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.25</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in State | 8784*1083| <li>[EIA 860]</li><li>new Pmax in Eastern</li>
| western_solar_v4.1    | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.25</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in State | 8784*433 | <li>[EIA 860]</li>
| texas_solar_v4.1    | [NSRDB][NSRDB_web] + [SAM][SAM_web] + [PVWatts v5][SAM_pvwatts]:<li>DC/AC=1.25</li><li>inverter efficiency=0.94</li><li>tilt angle=30deg</li><li>array type: [0, 2, 4] in proportion to technology used in State | 8784*36 | <li>[EIA 860]</li>
| texaswestern_solar_v4.1    | texas_solar_v4.1 + western_solar_v4.1 | 8784*469 | existing profiles concatenation
| usa_solar_v4.3    | texaswestern_solar_v4.1 + eastern_solar_v4.2 | 8784*1139 | existing profiles concatenation

[NSRDB_web]: https://nsrdb.nrel.gov/
[SAM_web]: https://sam.nrel.gov/
[SAM_pvwatts]: https://www.nrel.gov/docs/fy14osti/62641.pdf
[EIA 860]: https://www.eia.gov/electricity/data/eia860/

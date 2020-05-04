## Hydro Profiles

| Hydro Profiles  | Methodology   | Dimension     | Notes
| ------------- |:-------------:|:-------------:|:------------:|
| western_hydro_v2 | dams/net demand shape + historical total profile | 8784*715 | [US Army Corps][USACE_dataquery] and [EIA 923]
| texas_hydro_v2 | historical total profile decomposition | 8784*22 | [ERCOT][ERCOT_generation]
| texaswestern_hydro_v2 | western_hydro_v2 + texas_hydro_v2 | 8784*737 | existing profiles concatenation
| eastern_hydro_v1 | monthly capacity factors in the U.S. | 8784*2306 | [EIA Table 4.08.B][hydro_cf]
| usa_hydro_v3 | texaswestern_hydro_v2 + eastern_hydro_v3 | 8784*3043 | existing profiles concatenation
| eastern_hydro_v3 | net demand shape + historical BA/total profiles | 8784*2306 | [EIA 923] and BA websites
| eastern_hydro_v4 | scale eastern_hydro_v3 for rebased grid | 8784*2306 | existing profile scaling

<!--Profiles no longer in use:
western_hydro_v1
texas_hydro_v1
texaswestern_hydro_v1
-->

[ERCOT_generation]: http://www.ercot.com/gridinfo/generation/
[hydro_cf]: https://www.eia.gov/electricity/annual/html/epa_04_08_b.html
[USACE_dataquery]: http://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/
[EIA 923]: https://www.eia.gov/electricity/data/eia923/


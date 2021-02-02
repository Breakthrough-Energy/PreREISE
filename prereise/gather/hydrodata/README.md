## Hydro Profiles

| Name            | Grid Model | Methodology  | Dimension    | Notes
|:----------------|:-----------|:-------------|:-------------|:------------|
| hydro_vJan2021  | usa_tamu   | <li>Texas: historical total profile decomposition</li><li>Western: net demand shape + historical total profile (v2)</li><li>Eastern: net demand shape + historical total profile decomposition in BA/ISO (v3)</li> | 8784*3043 | <li>Texas: ERCOT</li><li>Western: [EIA 923] + [US Army Corps][USACE_dataquery]</li><li>Eastern: [EIA 923] + ISONE/NYISO/PJM/SPP websites</li> |

---
**Definition**
* BA: Balancing Authority
* ISO:Independent System Operator
* ISONE: ISO New England
* NYISO: New York ISO
* PJM: Pennsylvania-New Jersey-Maryland Interconnection
* SPP: Southwest Power Pool

---

[ERCOT_generation]: http://www.ercot.com/gridinfo/generation/
[hydro_cf]: https://www.eia.gov/electricity/annual/html/epa_04_08_b.html
[USACE_dataquery]: http://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/
[EIA 923]: https://www.eia.gov/electricity/data/eia923/
[ISO New England]: https://www.iso-ne.com/isoexpress/
[NY ISO]: http://mis.nyiso.com/public/P-63list.htm
[PJM]: http://dataminer2.pjm.com/feed/gen_by_fuel
[Southwest Power Pool]: https://marketplace.spp.org/pages/generation-mix-historical

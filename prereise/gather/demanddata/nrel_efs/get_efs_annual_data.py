import pandas as pd

nrel_annual_efs_url = "https://data.nrel.gov/system/files/92/service_demand.csv.gzip"


def get_efs_annual_data(path, sector):
    """Download the electric technology service demand file from the NREL
    Electrification Future Study (EFS) and return the electrification projection in
    each state for a given sector

    :param str path: path to electric technology service demand file from NREL EFS
        (local or url)
    :param str sector: sector to query in the file. Can be one of *'RESIDENTIAL'*,
        *'COMMERCIAL'*, *'PRODUCTIVE'* (industrial) and *'TRANSPORTATION'*.
    :return: (*pandas.DataFrame*) -- Columns are *'SCENARIO'* (range of electrification
        futures, e.g. *'MEDIUM ELECTRIFICATION - MODERATE TECHNOLOGY ADVANCEMENT'*,
        *'DEMAND_TECHNOLOGY'* (technologies for a given sector, e.g. *'ELECTRIC LIGHT-
        DUTY AUTO - 100 MILE RANGE'* for transportation sector), *'STATE'* (50 United
        States and District of Columbia), *'SUBSECTOR'* (a sub category of technology
        for any sector, e.g. *'AVIATION'* of the transportation sector), *'YEAR'* (year
        of projection), *'FINAL_ENERGY'* (type of energy, e.g. *'RESIDUAL FUEL
        OIL'*), *'UNIT'* (unit of *'VALUE'*, e.g. *'MILE'*), *'VALUE'* (projected annual value).
    :raises ValueError: if ``sector`` is invalid.
    """
    possible = ["RESIDENTIAL", "COMMERCIAL", "PRODUCTIVE", "TRANSPORTATION"]
    if sector not in possible:
        raise ValueError(f"invalid sector. Choose from {' | '.join(possible)}")

    df = pd.read_csv(path, compression="gzip")

    return df.query("SECTOR==@sector")[
        [
            "SCENARIO",
            "SECTOR",
            "DEMAND_TECHNOLOGY",
            "STATE",
            "SUBSECTOR",
            "YEAR",
            "FINAL_ENERGY",
            "UNIT",
            "VALUE",
        ]
    ]

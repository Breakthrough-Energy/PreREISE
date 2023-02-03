import os
import warnings

import pandas as pd
from powersimdata.network.constants.region.geography import USA

warnings.simplefilter(action="ignore", category=UserWarning)

census_ua_url = "https://www2.census.gov/geo/docs/reference/ua/ua_st_list_all.xls"
census_state_url = "https://www2.census.gov/programs-surveys/popest/tables/2010-2019/state/totals/nst-est2019-01.xlsx"
tht_data_url = "https://www7.transportation.gov/file/51021/download?token=2nJBkBSM"

state2abv = USA().state2abv | {"District of Columbia": "DC"}
id2state = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
}


def load_census_ua(path):
    """Load census data for urban population

    :param str path: path to census file (local or url)
    :return: (*dict*) -- keys are state abbreviation and values are data frames giving
        population by urban area in the state.
    """
    df = pd.read_excel(
        path,
        index_col=0,
        keep_default_na=False,
        usecols=[1, 2, 4],
        skiprows=2,
    )
    state2ua = {}
    for n, s in id2state.items():
        state2ua[s] = df.query("STATE==@n")["POP"]

    return state2ua


def load_census_state(path, year=None):
    """Load census data for state population

    :param str path: path to census file (local or url)
    :param str year: year to query for state population.
    :return: (*pandas.Series*) -- indices are state abbreviations and values are
        population in state
    """
    if year is None:
        year = 2015

    df = pd.read_excel(path, skiprows=3, index_col=0, skipfooter=7)
    df.index = df.index.map(lambda x: str(x)[1:])

    return df.loc[state2abv.keys()][year].rename(index=state2abv)


def load_dot_vmt_per_capita(path):
    """Load Vehicle Miles Traveled (VMT) per capita in urban areas

    :param str path: path to Department of Transportation's Transportation Health Tools
        (local or url)
    :return: (*tuple*) -- series. Indices are state abbreviations and values are
        VMT per capita in urban area (first element) or state (second element)
    """
    df_ua = pd.read_excel(
        path,
        sheet_name="Urbanized Area",
        index_col=0,
        usecols=[0, 3],
        names=["UA", "VMT per Capita (daily)"],
    )

    df_state = pd.read_excel(
        path,
        sheet_name="State",
        index_col=0,
        usecols=[0, 39],
        names=["State", "VMT per Capita (annual)"],
    )

    return (
        df_ua.squeeze().loc[~df_ua.index.str.contains("\[no data\]")],  # noqa: W605
        df_state.rename(index=state2abv).squeeze(),
    )


def calculate_vmt_for_ua(census_ua, tht_ua, tht_state):
    """Calculate the total annual Vehicle Miles Traveled (VMT) in urban areas

    :param dict census_ua: dictionary as returned by :func:`load_census_ua`
    :param pandas.Series tht_ua: daily vmt per capita in urban areas as returned by
        :func:`load_dot_vmt_per_capita`
    :param pandas.Series tht_state: annual vmt per capita in state as returned by
        :func:`load_dot_vmt_per_capita`
    :return: (*dict*) -- keys are state abbreviations and values are data frame giving
        annual vmt by urban areas.
    """

    tht_ua_format = tht_ua.copy()
    vmt_for_ua = {}

    tht_ua_format.index = tht_ua_format.index.str.replace(r"[, -.]", "", regex=True)
    format2original = dict(zip(tht_ua_format.index, tht_ua.index))

    for s in census_ua:
        census_ua_format = census_ua[s].copy()
        census_ua_format.index = census_ua_format.index.str.replace(
            r"[, -.]", "", regex=True
        )
        common = set(tht_ua_format.index).intersection(set(census_ua_format.index))
        vmt_for_ua[s] = pd.DataFrame(
            {
                "Annual VMT": [
                    365 * tht_ua_format.loc[i] * census_ua_format.loc[i]
                    if tht_ua_format.loc[i] != "[no data]"
                    else tht_state.loc[s] * census_ua_format.loc[i]
                    for i in common
                ]
            },
            index=list(common),
        ).rename(index=format2original)

    return vmt_for_ua


def calculate_vmt_for_state(census_state, tht_state):
    """Calculate the total annual Vehicle Miles Traveled (VMT) in states

    :param dict census_state: dictionary as returned by :func:`load_census_state`
    :param pandas.Series tht_state: vmt per capita in states as returned by
        :func:`load_dot_vmt_per_capita`
    :return: (*pandas.Series*) -- indices are state abbreviations and values are annual
        VMT in state.
    """
    common = list(set(tht_state.index).intersection(set(census_state.index)))
    vmt_for_state = tht_state.loc[common] * census_state.loc[common]

    return vmt_for_state


def calculate_urban_rural_fraction(vmt_for_ua, vmt_for_state):
    """Calculate the percentage of Vehicle Miles Traveled (VMT) in urban and rural areas

    :param dict vmt_for_ua: dictionary as returned by :func:`calculate_vmt_for_ua`.
    :param pandas.Series vmt_for_state: series as returned by
        :func:`calculate_vmt_for_state`
    :return: (*tuple*) -- keys are state abbreviations and values are either series of
        percentage vmt in urban areas (first element) or percentage in rural area
        (second element)
    """
    vmt_for_ua_perc = vmt_for_ua.copy()
    vmt_for_ra_perc = {}
    for s in vmt_for_ua:
        if s in vmt_for_state.index:
            vmt_for_ua_perc[s] = vmt_for_ua[s] / vmt_for_state.loc[s]
            vmt_for_ra_perc[s] = 1 - vmt_for_ua_perc[s].sum()
        # Handle District of Columbia
        else:
            vmt_for_ua_perc[s] = pd.Series({"Washington, DC-VA-MD": 1})
            vmt_for_ra_perc[s] = pd.Series(0.0, index=["Annual VMT"])

    return vmt_for_ua_perc, vmt_for_ra_perc


def get_efs_vmt_projection_for_state(efs_annual_data, electrification_scenario=None):
    """Retrieve the projected annual Vehicle Miles Traveled (VMT) for various
    technolgies for a chosen scenario.

    :param pandas.DataFrame efs_annual_data: electrification projection in
        each state for the transportation sector as returned by the
        :func:`prereise.gather.demanddata.nrel_efs.get_efs_annual_data.get_efs_annual_data` function
    :param str electrification_scenario: range of electrification futures. Default to
        *'HIGH ELECTRIFICATION - MODERATE TECHNOLOGY ADVANCEMENT'* if not specified.
    :return: (*dict*) -- keys are state abbreviations and values are data frames
        giving projected VMT values for different years and vehicle types.
    :raises ValueError: if ``electrification_scenario`` is invalid.
    """
    if electrification_scenario is None:
        electrification_scenario = (
            "HIGH ELECTRIFICATION - MODERATE TECHNOLOGY ADVANCEMENT"
        )

    possible = [
        "HIGH ELECTRIFICATION - MODERATE TECHNOLOGY ADVANCEMENT",
        "MEDIUM ELECTRIFICATION - MODERATE TECHNOLOGY ADVANCEMENT",
        "REFERENCE ELECTRIFICATION - MODERATE TECHNOLOGY ADVANCEMENT",
        "LOW ELECTRICITY GROWTH - MODERATE TECHNOLOGY ADVANCEMENT",
        "ELECTRIFICATION TECHNICAL POTENTIAL - MODERATE TECHNOLOGY ADVANCEMENT",
    ]
    if electrification_scenario not in possible:
        raise ValueError(f"invalid scenario. Choose from {' | '.join(possible)}")

    tech = [  # noqa: F841
        "ELECTRIC LIGHT-DUTY AUTO - 100 MILE RANGE",
        "ELECTRIC LIGHT-DUTY AUTO - 200 MILE RANGE",
        "ELECTRIC LIGHT-DUTY AUTO - 300 MILE RANGE",
        "ELECTRIC LIGHT-DUTY TRUCK - 100 MILE RANGE",
        "ELECTRIC LIGHT-DUTY TRUCK - 200 MILE RANGE",
        "ELECTRIC LIGHT-DUTY TRUCK - 300 MILE RANGE",
        "BATTERY ELECTRIC MEDIUM-DUTY VEHICLE",
        "ELECTRIC HEAVY DUTY VEHICLE",
    ]

    efs_annual_data = efs_annual_data.query(
        "SCENARIO==@electrification_scenario & FINAL_ENERGY=='ELECTRICITY' & DEMAND_TECHNOLOGY==@tech"
    )[["STATE", "DEMAND_TECHNOLOGY", "YEAR", "UNIT", "VALUE"]].dropna(
        subset=["DEMAND_TECHNOLOGY"]
    )

    efs_annual_data["VALUE"] = efs_annual_data.apply(
        lambda x: x["VALUE"] * pow(10, 9) if x["UNIT"] == "GIGAMILE" else x["VALUE"],
        axis=1,
    )

    efs_annual_data.drop("UNIT", axis=1, inplace=True)
    efs_annual_data["STATE"] = efs_annual_data["STATE"].map(
        lambda x: state2abv.get(x.title(), "DC")
    )
    efs_for_state = {
        s: efs_annual_data.query("STATE==@s")
        .drop("STATE", axis=1)
        .reset_index(drop=True)
        for s in state2abv.values()
    }

    return efs_for_state


def generate_scaling_factor(efs_vmt_for_state, vmt_for_ua_perc, vmt_for_ra_perc):
    """Calculate for each year the scaling factors by vehicle technology in urban and
    rural areas.

    :param dict efs_vmt_for_state: keys are state abbreviations and values are data
        frames enclosing the projected annual VMT by vehicle technology and year
        as returned by :func:`get_efs_vmt_projection_for_state`.
    :param dict vmt_for_ua_perc: keys are state abbreviations and values are series
        giving VMT fractions for urban areas in state. This is returned by
        :func:`calculate_urban_rural_fraction`
    :param dict vmt_for_ra_perc: same as ``vmt_for_ua_perc`` but for rural areas.
    :return: (*tuple*) -- dictionary for urban and rural area. Keys are years, values
        are data frames enclosing scaling factors for each vehicle type.
    """
    rural_scaling_factor = {}
    urban_scaling_factor = {}
    for s in state2abv.values():
        efs_value = (
            efs_vmt_for_state[s]
            .pivot(index="YEAR", columns="DEMAND_TECHNOLOGY", values="VALUE")
            .rename(
                columns={
                    "ELECTRIC LIGHT-DUTY AUTO - 100 MILE RANGE": "LDV Car - 100 mi",
                    "ELECTRIC LIGHT-DUTY AUTO - 200 MILE RANGE": "LDV Car - 200 mi",
                    "ELECTRIC LIGHT-DUTY AUTO - 300 MILE RANGE": "LDV Car - 300 mi",
                    "ELECTRIC LIGHT-DUTY TRUCK - 100 MILE RANGE": "LDV Truck - 100 mi",
                    "ELECTRIC LIGHT-DUTY TRUCK - 200 MILE RANGE": "LDV Truck - 200 mi",
                    "ELECTRIC LIGHT-DUTY TRUCK - 300 MILE RANGE": "LDV Truck - 300 mi",
                    "BATTERY ELECTRIC MEDIUM-DUTY VEHICLE": "MDV Truck",
                    "ELECTRIC HEAVY DUTY VEHICLE": "HDV Truck",
                }
            )
            .rename_axis(columns=None, index=None)
        )
        rural_scaling_factor_state = efs_value.multiply(vmt_for_ra_perc[s].squeeze())
        for y in efs_value.index:
            rural_scaling_factor[y] = pd.concat(
                [
                    rural_scaling_factor.get(y, pd.DataFrame()),
                    rural_scaling_factor_state.loc[y]
                    .to_frame(name=s)
                    .T.rename_axis("State"),
                ]
            )
            urban_scaling_factor[y] = pd.concat(
                [
                    urban_scaling_factor.get(y, pd.DataFrame()),
                    pd.concat(
                        [
                            pd.DataFrame(
                                {
                                    "State": s,
                                    "UA": vmt_for_ua_perc[s]
                                    .index.str.split(",")
                                    .str[0],
                                },
                                index=vmt_for_ua_perc[s].index,
                            ),
                            pd.DataFrame(
                                efs_value.loc[y].to_dict(),
                                index=vmt_for_ua_perc[s].index,
                            ).multiply(vmt_for_ua_perc[s].values, axis=0),
                        ],
                        axis=1,
                    ).rename_axis("Area Name"),
                ]
            )

    return urban_scaling_factor, rural_scaling_factor


def write_scaling_factor_files(
    urban_scaling_factor, rural_scaling_factor, dir_path=None
):
    """Create files for each year enclosing scaling factors by vehicle technology in
    urban and rural areas.

    :param dict urban_scaling_factor: keys are years, values are data frames enclosing
        scaling factors for each vehicle type in urban area.
    :param dict rural_scaling_factor: keys are years, values are data frames enclosing
        scaling factors for each vehicle type in each rural area.
    :param str dir_path: path to folder wher files will be written. Default to *'data/
        regional_scaling_factors'* in current directory.
    """
    if dir_path is None:
        dir_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data",
            "regional_scaling_factors",
        )
    os.makedirs(dir_path, exist_ok=True)
    for y in urban_scaling_factor:
        rural_scaling_factor[y].to_csv(
            os.path.join(dir_path, f"regional_scaling_factors_RA_{y}.csv")
        )
        urban_scaling_factor[y].to_csv(
            os.path.join(dir_path, f"regional_scaling_factors_UA_{y}.csv")
        )

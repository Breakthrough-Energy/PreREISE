s_base = 100  # MVA

mile_to_meter = 1609.34
meter_to_mile = 1.0 / mile_to_meter

# contiguous state
abv2state = {
    "AL": "Alabama",
    "AR": "Arkansas",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
}

abv_state_neighbor = {
    "AL": ["FL", "GA", "MS", "TN"],
    "AZ": ["CA", "CO", "NV", "NM", "UT"],
    "AR": ["LA", "MS", "MO", "OK", "TN", "TX"],
    "CA": ["AZ", "NV", "OR"],
    "CO": ["AZ", "KS", "NE", "NM", "OK", "UT", "WY"],
    "CT": ["MA", "NY", "RI"],
    "DE": ["MD", "NJ", "PA"],
    "FL": ["AL", "GA"],
    "GA": ["AL", "FL", "NC", "SC", "TN"],
    "ID": ["MT", "NV", "OR", "UT", "WA", "WY"],
    "IL": ["IN", "IA", "MI", "KY", "MO", "WI"],
    "IN": ["IL", "KY", "MI", "OH"],
    "IA": ["IL", "MN", "MO", "NE", "SD", "WI"],
    "KS": ["CO", "MO", "NE", "OK"],
    "KY": ["IL", "IN", "MO", "OH", "TN", "VA", "WV"],
    "LA": ["AR", "MS", "TX"],
    "ME": ["NH"],
    "MD": ["DE", "PA", "VA", "WV"],
    "MA": ["CT", "NH", "NY", "RI", "VT"],
    "MI": ["IL", "IN", "MN", "OH", "WI"],
    "MN": ["IA", "MI", "ND", "SD", "WI"],
    "MS": ["AL", "AR", "LA", "TN"],
    "MO": ["AR", "IL", "IA", "KS", "KY", "NE", "OK", "TN"],
    "MT": ["ID", "ND", "SD", "WY"],
    "NE": ["CO", "IA", "KS", "MO", "SD", "WY"],
    "NV": ["AZ", "CA", "ID", "OR", "UT"],
    "NH": ["ME", "MA", "VT"],
    "NJ": ["DE", "NY", "PA"],
    "NM": ["AZ", "CO", "OK", "TX", "UT"],
    "NY": ["CT", "MA", "NJ", "PA", "RI", "VT"],
    "NC": ["GA", "SC", "TN", "VA"],
    "ND": ["MN", "MT", "SD"],
    "OH": ["IN", "KY", "MI", "PA", "WV"],
    "OK": ["AR", "CO", "KS", "MO", "NM", "TX"],
    "OR": ["CA", "ID", "NV", "WA"],
    "PA": ["DE", "MD", "NJ", "NY", "OH", "WV"],
    "RI": ["CT", "MA", "NY"],
    "SC": ["GA", "NC"],
    "SD": ["IA", "MN", "MT", "NE", "ND", "WY"],
    "TN": ["AL", "AR", "GA", "KY", "MS", "MO", "NC", "VA"],
    "TX": ["AR", "LA", "NM", "OK"],
    "UT": ["AZ", "CO", "ID", "NV", "NM", "WY"],
    "VT": ["MA", "NH", "NY"],
    "VA": ["KY", "MD", "NC", "TN", "WV"],
    "WA": ["ID", "OR"],
    "WV": ["KY", "MD", "OH", "PA", "VA"],
    "WI": ["IL", "IA", "MI", "MN"],
    "WY": ["CO", "ID", "MT", "NE", "SD", "UT"],
}

blob_paths = {
    "eia_form860_2019_generator": "https://besciences.blob.core.windows.net/datasets/EIA_Form860/3_1_Generator_Y2019_Operable.csv",
    "eia_form860_2019_plant": "https://besciences.blob.core.windows.net/datasets/EIA_Form860/2___Plant_Y2019.csv",
    "eia_form860_2019_solar": "https://besciences.blob.core.windows.net/datasets/EIA_Form860/3_3_Solar_Y2019_Operable.csv",
    "eia_form860_2019_wind": "https://besciences.blob.core.windows.net/datasets/EIA_Form860/3_2_Wind_Y2019_Operable.csv",
    "epa_ampd": "https://besciences.blob.core.windows.net/datasets/EPA_AMPD/",
    "epa_needs": "https://besciences.blob.core.windows.net/datasets/EPA_NEEDS/needs-v620_06-30-21-2_active.csv",
    "substations": "https://besciences.blob.core.windows.net/datasets/hifld/Electric_Substations_Jul2020.csv",
    "transmission_lines": "https://besciences.blob.core.windows.net/datasets/hifld/Electric_Power_Transmission_Lines_Jul2020.geojson.zip",
    "us_counties": "https://besciences.blob.core.windows.net/datasets/geo_data/uscounties.csv",
    "us_zips": "https://besciences.blob.core.windows.net/datasets/geo_data/uszips.csv",
}
eia_epa_crosswalk_path = "https://raw.githubusercontent.com/Breakthrough-Energy/camd-eia-crosswalk/master/epa_eia_crosswalk.csv"

volt_class_defaults = {
    "UNDER 100": 69,
    "220-287": 230,
    "345": 345,
    "500": 500,
}

eia_storage_gen_types = {
    "Batteries",
    "Flywheels",
}

balancingauthority2interconnect = {
    "AEC": "Eastern",
    "AECI": "Eastern",
    "AVA": "Western",
    "AVRN": "Western",
    "AZPS": "Western",
    "BANC": "Western",
    "BPAT": "Western",
    "CHPD": "Western",
    "CISO": "Western",
    "CPLE": "Eastern",
    "CPLW": "Eastern",
    "CSTO": "Western",
    "DEAA": "Western",
    "DOPD": "Western",
    "DUK": "Eastern",
    "EEI": "Eastern",
    "EPE": "Western",
    "ERCO": "ERCOT",
    "FMPP": "Eastern",
    "FPC": "Eastern",
    "FPL": "Eastern",
    "GCPD": "Western",
    "GRIF": "Western",
    "GRIS": "Western",
    "GRMA": "Western",
    "GVL": "Eastern",
    "GWA": "Western",
    "HGMA": "Western",
    "HST": "Eastern",
    "IID": "Western",
    "IPCO": "Western",
    "ISNE": "Eastern",
    "JEA": "Eastern",
    "LDWP": "Western",
    "LGEE": "Eastern",
    "MISO": "Eastern",
    "NBSO": "Eastern",
    "NEVP": "Western",
    "NSB": "Eastern",
    "NWMT": "Western",
    "NYIS": "Eastern",
    "OVEC": "Eastern",
    "PACE": "Western",
    "PACW": "Western",
    "PGE": "Western",
    "PJM": "Eastern",
    "PNM": "Western",
    "PSCO": "Western",
    "PSEI": "Western",
    "SC": "Eastern",
    "SCEG": "Eastern",
    "SCL": "Western",
    "SEC": "Eastern",
    "SEPA": "Eastern",
    "SOCO": "Eastern",
    "SPA": "Eastern",
    "SRP": "Western",
    "SWPP": "Eastern",
    "TAL": "Eastern",
    "TEC": "Eastern",
    "TEPC": "Western",
    "TIDC": "Western",
    "TPWR": "Western",
    "TVA": "Eastern",
    # "WACM": "Western",  # can be Western or Eastern
    # "WALC": "Western",  # can be Western or Eastern
    # "WAUW": "Western",  # can be Western or Eastern
    "WWA": "Western",
    "YAD": "Eastern",
}

# Usage of this is deprecated, since these data seem noisier than Balancing Authorities
nercregion2interconnect = {
    "ASCC": "Alaska",  # Not currently used
    "HICC": "Hawaii",  # Not currently used
    "MRO": "Eastern",
    "NPCC": "Eastern",
    "RFC": "Eastern",
    "SERC": "Eastern",
    "TRE": "ERCOT",
    "WECC": "Western",
}

interconnect2state = {
    "Eastern": {
        "AL",
        "AR",
        "CT",
        "DE",
        "FL",
        "GA",
        "IA",
        "IL",
        "IN",
        "KS",
        "KY",
        "LA",
        "MA",
        "MD",
        "ME",
        "MI",
        "MN",
        "MO",
        "MS",
        "NC",
        "ND",
        "NE",
        "NH",
        "NJ",
        "NY",
        "OH",
        "OK",
        "PA",
        "RI",
        "SC",
        "TN",
        "VA",
        "VT",
        "WI",
        "WV",
    },
    "ignore": {"AK", "HI"},
    "split": {"MT", "SD", "TX"},
    "Western": {"AZ", "CA", "CO", "ID", "NM", "NV", "OR", "UT", "WA", "WY"},
}

state_county_splits = {
    "MT": {
        "default": "Western",
        "Eastern": {
            "CARTER",
            "CUSTER",
            "DANIELS",
            "DAWSON",
            "FALLON",
            "GARFIELD",
            "MCCONE",
            "PHILLIPS",
            "POWDER RIVER",
            "PRAIRIE",
            "RICHLAND",
            "ROOSEVELT",
            "ROSEBUD",
            "SHERIDAN",
            "VALLEY",
            "WIBAUX",
        },
    },
    "NM": {
        "default": "Western",
        "Eastern": {"CURRY", "LEA", "QUAY", "ROOSEVELT", "UNION"},
    },
    "SD": {"default": "Eastern", "Western": {"BUTTE", "FALL RIVER", "LAWRENCE"}},
    "TX": {
        "default": "ERCOT",
        "Eastern": {
            "BAILEY",
            "BOWIE",
            "CAMP",
            "CASS",
            "COCHRAN",
            "DALLAM",
            "DONLEY",
            "GAINES",
            "GREGG",
            "HALE",
            "HANSFORD",
            "HARDIN",
            "HARRISON",
            "HARTLEY",
            "HEMPHILL",
            "HOCKLEY",
            "HUTCHINSON",
            "JASPER",
            "JEFFERSON",
            "LAMB",
            "LIBERTY",
            "LIPSCOMB",
            "LUBBOCK",
            "LYNN",
            "MARION",
            "MOORE",
            "MORRIS",
            "NEWTON",
            "OCHLTREE",
            "ORANGE",
            "PANOLA",
            "PARMER",
            "POLK",
            "RANDALL",
            "SABINE",
            "SAN AUGUSTINE",
            "SAN JACINTO",
            "SHELBY",
            "SHERMAN",
            "TERRY",
            "TRINITY",
            "TYLER",
            "UPSHUR",
            "WALKER",
            "YOAKUM",
        },
        "Western": {"EL PASO", "HUDSPETH"},
    },
}

heat_rate_estimation_columns = [
    "ORISPL_CODE",
    "UNITID",
    "GLOAD (MW)",
    "HEAT_INPUT (mmBtu)",
]

fuel_prices = {  # EIA Annual Energy Outlook, values for 2022, $/MMBTu (2020 USD)
    "BIT": 2.02,  # BITuminous coal
    "DFO": 17.85,  # Distillate Fuel Oil
    "JF": 11.41,  # Jet Fuel
    "KER": 11.41,  # KERosene
    "LIG": 2.02,  # LIGnite coal
    "NG": 3.60,  # Natural Gas
    "NUC": 0.69,  # NUClear (uranium)
    "PC": 2.02,  # Petroleum Coke
    "PG": 15.43,  # Propane (Gaseous)
    "RC": 2.02,  # Residual Coal
    "RFO": 9.75,  # Residual Fuel Oil
    "SUB": 2.02,  # SUB-bituminous coal
    "WC": 2.02,  # Waste Coal
}

fuel_translations = {
    "BIT": "coal",
    "DFO": "dfo",
    "GEO": "geothermal",
    "JF": "dfo",
    "KER": "dfo",
    "LIG": "coal",
    "NG": "ng",
    "NUC": "nuclear",
    "PC": "coal",
    "PG": "ng",
    "RC": "coal",
    "RFO": "dfo",
    "SUB": "coal",
    "SUN": "solar",
    "WAT": "hydro",
    "WC": "coal",
    "WND": "wind",
}

# Values from EPA's Power Sector Modeling Platform v6 - Summer 2021 Reference Case
reasonable_heat_rates_size_cutoffs = {
    ("Natural Gas Fired Combustion Turbine", "GT"): 80,
    ("Petroleum Liquids", "GT"): 80,
    ("Petroleum Liquids", "IC"): 5,
}
reasonable_heat_rates_by_type = {
    ("Conventional Steam Coal", "ST"): (8.3, 14.5),
    ("Natural Gas Fired Combined Cycle", "CA"): (5.5, 15.0),
    ("Natural Gas Fired Combined Cycle", "CS"): (5.5, 15.0),
    ("Natural Gas Fired Combined Cycle", "CT"): (5.5, 15.0),
    ("Natural Gas Internal Combustion Engine", "IC"): (8.7, 18.0),
    ("Natural Gas Steam Turbine", "ST"): (8.3, 14.5),
    ("Petroleum Coke", "ST"): (8.3, 14.5),
    ("Petroleum Liquids", "CA"): (6.0, 15.0),
    ("Petroleum Liquids", "CT"): (6.0, 15.0),
    ("Petroleum Liquids", "ST"): (8.3, 14.5),
}
reasonable_heat_rates_by_type_and_size = {
    ("Natural Gas Fired Combustion Turbine", "GT", "small"): (8.7, 36.8),
    ("Natural Gas Fired Combustion Turbine", "GT", "large"): (8.7, 18.7),
    ("Petroleum Liquids", "GT", "small"): (6.0, 36.8),
    ("Petroleum Liquids", "GT", "large"): (6.0, 25.0),
    ("Petroleum Liquids", "IC", "small"): (8.7, 42.5),
    ("Petroleum Liquids", "IC", "large"): (8.7, 20.5),
}

heat_rate_assumptions = {
    "Conventional Hydroelectric": 0,
    "Geothermal": 0,
    "Hydroelectric Pumped Storage": 0,
    "Nuclear": 10.5,  # From EIA's Electric Power Annual 2019, Table 8.1
    "Offshore Wind Turbine": 0,
    "Onshore Wind Turbine": 0,
    "Solar Photovoltaic": 0,
    "Solar Thermal with Energy Storage": 0,
    "Solar Thermal without Energy Storage": 0,
}


# These lines were manually identified based on a combination of: their 'TYPE'
# classification, their substation names, and their geographical paths. The capacities
# for each line were compiled from a variety of public sources.
dc_line_ratings = {  # MW
    108354: 500,  # Square Butte
    113313: 660,  # Neptune Cable
    131914: 2000,  # Quebec – New England Transmission (Ayer to Monroe)
    150123: 1000,  # CU
    157627: 330,  # Cross-Sound Cable
    157629: 660,  # Hudson Project
    158515: 2000,  # Quebec – New England Transmission (Quebec to Monroe)
    200823: 3100,  # Pacific DC Intertie (Path 65)
    308464: 2400,  # Intermountain Power Project (Path 27)
    310053: 400,  # Trans-Bay Cable
    311958: 5,  # Alamogordo Solar Energy Center
}

substation_load_share = 0.5
demand_per_person = 2.01e-3

contiguous_us_bounds = {
    "east": -66,
    "north": 50,
    "south": 25,
    "west": -125,
}


substations_lines_filter_override = {301995}

seams_substations = {
    "east_west": {
        202364,  # 'LAMAR HVDC TIE'
        202159,  # 'UNKNOWN202159', NE (effecitvely Sidney/Virginia Smith)
        202160,  # 'VIRGINIA SMITH CONVERTER STATION'
        202177,  # Sidney-adjacent
        202178,  # 'STEGAL', NE
        131797,  # Stegal-adjacent
        203572,  # 'MILES CITY', MT (the substation that appears more likely to be the real one)
        203590,  # 'RICHARDSON COULEE' (near MALTA, shouldn't be necessary?)
        303738,  # 'BLACKWATER TIE', NM
        304165,  # 'EDDY AC-DC-AC TIE', NM
        # Rapid City Disconnections
        131171,  # North of Rapid City
        131176,  # North of Rapid City
        202567,  # East of Rapid City
        # Highline NE/CO border
        205884,  # Julesburg, CO
        205888,  # Holyoke, CO
        203719,  # 'ALVIN' substation
    },
    "east_ercot": {
        161924,  # Logansport, TX
        300490,  # Vernon, TX
        301314,  # Valley Lake, TX connection to OK
        301729,  # Hawkins, TX
        302012,  # Vernon, TX
        302274,  # 'COTTONWOOD', Glenn, TX
        303004,  # Crowell, TX
        303646,  # San Augustine, TX
        303719,  # Big Sandy, TX
        304100,  # Matador, TX
        304328,  # Midland, TX
        304477,  # Oklaunion substation (B2B)
        304825,  # Dennison, TX connection to OK
        304391,  # Long Branch, TX
        304994,  # Welsh substation (B2B)
        306058,  # Munday, TX
        306638,  # Pittsburg, TX
        306738,  # Henderson, TX
        307121,  # Kirkland, TX
        307363,  # Navasota, TX
        307539,  # Mt. Pleasant, TX
        307735,  # Shiro, TX
        308062,  # Lufkin, TX
        308951,  # Beckville, TX
        308976,  # Dayton, TX
        309403,  # Kilgore, TX
        310861,  # Overton, TX
        310879,  # Huntsville, TX
    },
}

substation_interconnect_assumptions = {
    "Eastern": {
        131171,
        131172,
        131853,
        161925,
        167678,
        167679,
        167681,
        167682,
        167684,
        307364,
    },
    "Western": {
        201396,
        202172,
        205667,
        205889,
        205890,
    },
    "ERCOT": {
        301181,
        301291,
        302826,
        303024,  # Substations between East/ERCOT AC connector and Oklaunion B2B station
        303394,
        303406,
        303433,
        304994,  # Welsh B2B
        309433,
        309658,
    },
}

line_interconnect_assumptions = {
    "Eastern": {
        128641,
        132264,
        135527,
        141367,
        300170,
        303906,
        305887,
        306332,
        306885,
        310668,
        311279,
        311520,
    },
    "Western": {123525, 141873},
    "ERCOT": {305330},
}

line_voltage_assumptions = {
    128842: 230,
}


b2b_ratings = {  # MW
    "BLACKWATER TIE": 200,  # a.k.a. 'Clovis'/'Roosevelt County' (Eastern/Western)
    "EDDY AC-DC-AC TIE": 200,  # a.k.a. 'Artesia' (Eastern/Western)
    "LAMAR HVDC TIE": 210,  # (Eastern/Western)
    "MILES CITY": 200,  # (Eastern/Western)
    "NEW UNDERWOOD": 200,  # representative of the Rapid City DC Tie (Eastern/Western)
    "STEGALL": 110,  # (Eastern/Western)
    "UNKNOWN304477": 220,  # Oklaunion (Eastern/ERCOT)
    "UNKNOWN304994": 600,  # Welsh (Eastern/ERCOT)
    "VIRGINIA SMITH CONVERTER STATION": 200,  # a.k.a. 'Sidney' (Eastern/Western)
}

interconnect_size_rank = ["Eastern", "Western", "ERCOT"]

powersimdata_column_defaults = {
    "branch": {
        "r": 0,
        "b": 0,
        "ratio": 0,
        "rateB": 0,
        "rateC": 0,
        "angle": 0,
        "status": 1,
        "angmin": 0,
        "angmax": 0,
        "Pf": 0,
        "Qf": 0,
        "Pt": 0,
        "Qt": 0,
        "mu_Sf": 0,
        "mu_St": 0,
        "mu_angmin": 0,
        "mu_angmax": 0,
    },
    "bus": {
        "type": 1,
        "Qd": 0,
        "Gs": 0,
        "Bs": 0,
        "Vm": 1,
        "Va": 0,
        "loss_zone": 1,
        "Vmax": 1.1,
        "Vmin": 0.9,
        "lam_P": 0,
        "lam_Q": 0,
        "mu_Vmax": 0,
        "mu_Vmin": 0,
    },
    "dcline": {
        "status": 1,
        "Pf": 0,
        "Pt": 0,
        "Qf": 0,
        "Qt": 0,
        "Vf": 1,
        "Vt": 1,
        "QminF": 0,
        "QmaxF": 0,
        "QminT": 0,
        "QmaxT": 0,
        "loss0": 0,
        "loss1": 0,
        "muPmin": 0,
        "muPmax": 0,
        "muQminF": 0,
        "muQmaxF": 0,
        "muQminT": 0,
        "muQmaxT": 0,
    },
    "gencost": {"type": 2, "startup": 0, "shutdown": 0, "n": 3},
    "plant": {
        "Pg": 0,
        "Qg": 0,
        "Qmax": 0,
        "Qmin": 0,
        "Vg": 1,
        "mBase": 1000,
        "status": 1,
        "Pc1": 0,
        "Pc2": 0,
        "Qc1min": 0,
        "Qc1max": 0,
        "Qc2min": 0,
        "Qc2max": 0,
        "ramp_agc": 0,
        "ramp_10": 0,
        "ramp_30": 0,
        "ramp_q": 0,
        "apf": 0,
        "mu_Pmax": 0,
        "mu_Pmin": 0,
        "mu_Qmax": 0,
        "mu_Qmin": 0,
    },
}

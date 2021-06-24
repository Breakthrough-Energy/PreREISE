import pytest

from prereise.cli.download.download_manager import generate_parser

START_DATE = "2020-01-01"
END_DATE = "2021-01-01"
FILE_PATH = "./data.pkl"
REGION = "Texas"
EMAIL = "fakeemail@bev.com"
API_KEY = "FAKE_API_KEY"
STRING_YEAR_2020 = "2020"
METHOD = "sam"

WIND_DATA_RAP_ARG_LIST_FULL_FLAGS = [
    "wind_data_rap",
    f"--start_date={START_DATE}",
    f"--end_date={END_DATE}",
    f"--file_path={FILE_PATH}",
    f"--region={REGION}",
]

WIND_DATA_RAP_ARG_LIST_SHORT_FLAGS = [
    "wind_data_rap",
    f"-sd={START_DATE}",
    f"-ed={END_DATE}",
    f"-fp={FILE_PATH}",
    f"-r={REGION}",
]

SOLAR_DATA_GA_ARG_LIST_FULL_FLAGS = [
    "solar_data_ga",
    f"--start_date={START_DATE}",
    f"--end_date={END_DATE}",
    f"--file_path={FILE_PATH}",
    f"--region={REGION}",
    f"--key={API_KEY}",
]

SOLAR_DATA_GA_ARG_LIST_SHORT_FLAGS = [
    "solar_data_ga",
    f"-sd={START_DATE}",
    f"-ed={END_DATE}",
    f"-fp={FILE_PATH}",
    f"-r={REGION}",
    f"-k={API_KEY}",
]

SOLAR_DATA_NSRDB_ARG_LIST_FULL_FLAGS = [
    "solar_data_nsrdb",
    f"--year={STRING_YEAR_2020}",
    f"--email={EMAIL}",
    f"--file_path={FILE_PATH}",
    f"--region={REGION}",
    f"--key={API_KEY}",
    f"--method={METHOD}",
]

SOLAR_DATA_NSRDB_ARG_LIST_SHORT_FLAGS = [
    "solar_data_nsrdb",
    f"-y={STRING_YEAR_2020}",
    f"-e={EMAIL}",
    f"-fp={FILE_PATH}",
    f"-r={REGION}",
    f"-k={API_KEY}",
    f"-m={METHOD}",
]

ALL_ARGUMENTS = [
    WIND_DATA_RAP_ARG_LIST_FULL_FLAGS,
    WIND_DATA_RAP_ARG_LIST_SHORT_FLAGS,
    SOLAR_DATA_GA_ARG_LIST_FULL_FLAGS,
    SOLAR_DATA_GA_ARG_LIST_SHORT_FLAGS,
    SOLAR_DATA_NSRDB_ARG_LIST_FULL_FLAGS,
    SOLAR_DATA_NSRDB_ARG_LIST_SHORT_FLAGS,
]


@pytest.mark.parametrize("args", ALL_ARGUMENTS)
def test_parser(args):
    parser = generate_parser()
    parser.parse_args(args)


@pytest.mark.parametrize("args", ALL_ARGUMENTS)
def test_parser_missing_flags(args):
    parser = generate_parser()
    for arg in args:
        bad_arg_list = args.copy()
        bad_arg_list.remove(arg)
        with pytest.raises(SystemExit):
            parser.parse_args(bad_arg_list)

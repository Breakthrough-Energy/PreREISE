import pytest

from prereise.cli.download.download_manager import generate_parser

START_DATE = "2020-01-01"
END_DATE = "2021-01-01"
FILE_PATH = "./data.pkl"
REGION = "Texas"

WIND_DATA_ARG_LIST_FULL_FLAGS = [
    "wind_data",
    f"--start_date={START_DATE}",
    f"--end_date={END_DATE}",
    f"--file_path={FILE_PATH}",
    f"--region={REGION}",
]

WIND_DATA_ARG_LIST_SHORT_FLAGS = [
    "wind_data",
    f"-sd={START_DATE}",
    f"-ed={END_DATE}",
    f"-fp={FILE_PATH}",
    f"-r={REGION}",
]


@pytest.mark.parametrize(
    "args", [WIND_DATA_ARG_LIST_FULL_FLAGS, WIND_DATA_ARG_LIST_SHORT_FLAGS]
)
def test_parser_wind_data(args):
    parser = generate_parser()
    result = parser.parse_args(args)
    assert START_DATE == result.start_date
    assert END_DATE == result.end_date
    assert REGION in result.region
    assert FILE_PATH == result.file_path


@pytest.mark.parametrize(
    "args", [WIND_DATA_ARG_LIST_FULL_FLAGS, WIND_DATA_ARG_LIST_SHORT_FLAGS]
)
def test_parser_wind_data_missing_flags(args):
    parser = generate_parser()
    for arg in args:
        bad_arg_list = args.copy()
        bad_arg_list.remove(arg)
        with pytest.raises(SystemExit):
            parser.parse_args(bad_arg_list)

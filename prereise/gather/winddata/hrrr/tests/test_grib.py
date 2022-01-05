from prereise.gather.winddata.hrrr.grib import GribRecordInfo

GRIB_RECORD_INFO_ARRAY = [
    "52:38983378:d=2016010121:UGRD:10 m above ground:anl:",
    "53:40192462:d=2016010121:VGRD:10 m above ground:anl:",
]


def test_grib_info_from_string():
    g = GribRecordInfo.from_string(GRIB_RECORD_INFO_ARRAY[0])
    expected = GribRecordInfo(
        message_number="52",
        beginning_byte="38983378",
        ending_byte=None,
        initialization_date="d=2016010121",
        variable="UGRD",
        level="10 m above ground",
        forecast="anl",
    )
    assert g == expected


def test_grib_info_from_string_with_next_string():
    g = GribRecordInfo.from_string(*GRIB_RECORD_INFO_ARRAY)
    expected = GribRecordInfo(
        message_number="52",
        beginning_byte="38983378",
        ending_byte="40192461",
        initialization_date="d=2016010121",
        variable="UGRD",
        level="10 m above ground",
        forecast="anl",
    )
    assert g == expected


def test_grib_info_generate_grib_record_information_list():
    g_list = GribRecordInfo.generate_grib_record_information_list(
        GRIB_RECORD_INFO_ARRAY, [0, 1]
    )
    g = g_list[0]
    expected = GribRecordInfo(
        message_number="52",
        beginning_byte="38983378",
        ending_byte="40192461",
        initialization_date="d=2016010121",
        variable="UGRD",
        level="10 m above ground",
        forecast="anl",
    )
    assert g == expected

    g = g_list[1]
    expected = GribRecordInfo(
        message_number="53",
        beginning_byte="40192462",
        ending_byte=None,
        initialization_date="d=2016010121",
        variable="VGRD",
        level="10 m above ground",
        forecast="anl",
    )
    assert g == expected


def test_grib_info_byte_range_header_string():
    g = GribRecordInfo(None, "10", "20", None, None, None, None)
    assert g.byte_range_header_string() == "10-20"


def test_grib_info_byte_range_header_string_no_end_byte():
    g = GribRecordInfo(None, "10", None, None, None, None, None)
    assert g.byte_range_header_string() == "10-"

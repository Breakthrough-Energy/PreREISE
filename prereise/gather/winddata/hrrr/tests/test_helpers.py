from prereise.gather.winddata.hrrr.helpers import get_indices_that_contain_selector


def test_get_indices_that_contain_selector():
    input_list = [
        "61:42783532:d=2016010100:CSNOW:surface:anl:",
        "62:42816635:d=2016010100:CICEP:surface:anl:",
        "63:42816823:d=2016010100:CFRZR:surface:anl:",
        "64:42817132:d=2016010100:CRAIN:surface:anl:",
        "65:42853953:d=2016010100:VGTYP:surface:anl:",
    ]
    selectors = ["CRAIN", "CSNOW"]
    assert get_indices_that_contain_selector(input_list, selectors) == [0, 3]

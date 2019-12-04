from prereise.gather.get_monthly_net_generation import get_monthly_net_generation
from prereise.gather.tests.mock_generation_data_frame import create_mock_generation_data_frame


def test_get_monthly_net_generation():
    filename = 'dummy.csv'
    trim_eia_form_923 = lambda filename: create_mock_generation_data_frame()    
    state = 'CA'
    fuel_types = ['wind','solar','ng','dfo','hydro','geothermal','nuclear','coal']
    res = []
    for fuel_type in fuel_types:
        res.append(get_monthly_net_generation(state,filename,fuel_type,trim_eia_form_923))
    for i in range(8):
        print(i)
        assert res[i] == [i+1]*12
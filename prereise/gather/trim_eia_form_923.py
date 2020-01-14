import os
import pandas as pd


def trim_eia_form_923(filename):
    """Get rid of unnecessary columns of EIA form 923 for get_monthly_net_generation.py
    :param str filename: name of the reference file
    :return: (*pandas.DataFrame*) plant_generation -- trimmed EIA 923 with only necessary columns 
    """
    filedir = os.path.join(os.path.dirname(__file__),'data')
    plant_generation = pd.read_excel(io = os.path.join(filedir,filename),
                                     header = 0, usecols = 'A,D,G,I,P,CB:CM',skiprows = range(5))
    return plant_generation
import pandas as pd


def create_mock_generation_data_frame():
    """Create mock EIA 923 generation data frame.

    :return: (*pandas.DataFrame*) -- mock data frame.
    """
    mock_data = {
        "Plant id": [1, 2, 3, 4, 5, 6, 7, 8],
        "Plant Name": [
            "A wind plant",
            "A solar plant",
            "A ng plant",
            "A dfo plant",
            "A hydro plant",
            "A geothermal plant",
            "A nuclear plant",
            "A coal plant",
        ],
        "Plant State": ["CA"] * 8,
        "NREC Region": ["WECC"] * 8,
        "AER\nFuel Type Code": ["WND", "SUN", "NG", "DFO", "HYC", "GEO", "NUC", "COL"],
        "Jan": [1, 2, 3, 4, 5, 6, 7, 8],
        "Feb": [1, 2, 3, 4, 5, 6, 7, 8],
        "MAR": [1, 2, 3, 4, 5, 6, 7, 8],
        "APR": [1, 2, 3, 4, 5, 6, 7, 8],
        "MAY": [1, 2, 3, 4, 5, 6, 7, 8],
        "JUN": [1, 2, 3, 4, 5, 6, 7, 8],
        "JUY": [1, 2, 3, 4, 5, 6, 7, 8],
        "AUG": [1, 2, 3, 4, 5, 6, 7, 8],
        "SEP": [1, 2, 3, 4, 5, 6, 7, 8],
        "OCT": [1, 2, 3, 4, 5, 6, 7, 8],
        "NOV": [1, 2, 3, 4, 5, 6, 7, 8],
        "DEC": [1, 2, 3, 4, 5, 6, 7, 8],
    }

    return pd.DataFrame(data=mock_data)

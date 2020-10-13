from setuptools import find_packages, setup

setup(
    name="prereise",
    version="0.3",
    description="Create and run an energy scenario",
    url="https://github.com/Breakthrough-Energy/PreREISE",
    author="Kaspar Mueller",
    author_email="kaspar.mueller@breakthroughenergy.org",
    packages=find_packages(),
    package_data={
        "prereise": [
            "gather/winddata/data/*.csv",
            "gather/hydrodata/data/cf.csv",
            "gather/data/EIA923_Schedules_2_3_4_5_M_12_2016_Final_Revision.xlsx",
            "gather/hydrodata/data/hydro_gmt.csv",
            "gather/hydrodata/data/texas_hydro_gmt.csv",
            "gather/solardata/data/*.csv",
        ]
    },
    zip_safe=False,
)

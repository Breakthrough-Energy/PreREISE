Command Line Interface
++++++++++++++++++++++
Wind and solar data can be downloaded via our download manager python script. When in
the terminal at the project root directory, you can run:

.. code:: shell

    python -m prereise.cli.download.download_manager -h
    usage: download_manager.py [-h] {wind_data_rap,solar_data_ga,solar_data_nsrdb} ...

    positional arguments:
      {wind_data_rap,solar_data_ga,solar_data_nsrdb}
        wind_data_rap       Download wind data from National Centers for Environmental Prediction
        solar_data_ga       Download solar data from the Gridded Atmospheric Wind Integration National Dataset Toolkit
        solar_data_nsrdb    Download solar data from the National Solar Radiation Database

    optional arguments:
    -h, --help            show this help message and exit

Currently supported data sources to download from are:

+ Rapid Refresh from National Centers for Environmental Prediction:

.. code:: shell

    python -m prereise.cli.download.download_manager wind_data_rap \
    --region REGION \
    --start_date START_DATE \
    --end_date END_DATE \
    --file_path FILEPATH

+ Gridded Atmospheric Wind Integration National Dataset Toolkit:

.. code::

    python -m prereise.cli.download.download_manager solar_data_ga \
        --region REGION \
        --start_date START_DATE \
        --end_date END_DATE \
        --file_path FILEPATH \
        --key API_KEY

+ The National Solar Radiation Database:

.. code::

    python -m prereise.cli.download.download_manager solar_data_nsrdb \
        --region REGION \
        --method METHOD \
        --year YEAR \
        --file_path FILEPATH \
        --email EMAIL \
        --key API_KEY

As a concrete example, if you would like to download the wind data from Rapid Refresh
from National Centers for Environmental Prediction for the Texas and Western
interconnections between the dates of June 5th, 2020 and January 2nd, 2021 into
``data.pkl``, you can run:

.. code:: shell

    python -m prereise.cli.download.download_manager wind_data_rap \
    --region Texas \
    --region Western \
    --start_date 2020-05-06 \
    --end_date 2021-01-02 \
    --file_path ./data.pkl

Note that missing data, if existing, will be imputed using a naive Gaussian algorithm.
This can be avoided using the ``--no_impute`` flag.

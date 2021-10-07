![logo](https://raw.githubusercontent.com/Breakthrough-Energy/docs/master/source/_static/img/BE_Sciences_RGB_Horizontal_Color.svg)
[![codecov](https://codecov.io/gh/Breakthrough-Energy/PreREISE/branch/develop/graph/badge.svg?token=UFZ9CW4GND)](https://codecov.io/gh/Breakthrough-Energy/PreREISE)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Tests](https://github.com/Breakthrough-Energy/PreREISE/workflows/Pytest/badge.svg)
[![Documentation](https://github.com/Breakthrough-Energy/docs/actions/workflows/publish.yml/badge.svg)](https://breakthrough-energy.github.io/docs/)
![GitHub contributors](https://img.shields.io/github/contributors/Breakthrough-Energy/PreREISE?logo=GitHub)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/Breakthrough-Energy/PreREISE?logo=GitHub)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/Breakthrough-Energy/PreREISE/develop?logo=GitHub)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Breakthrough-Energy/PreREISE?logo=GitHub)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code of Conduct](https://img.shields.io/badge/code%20of-conduct-ff69b4.svg?style=flat)](https://breakthrough-energy.github.io/docs/communication/code_of_conduct.html)


# PreREISE
**PreREISE** is part of a Python software ecosystem developed by [Breakthrough
Energy Sciences](https://science.breakthroughenergy.org/) to carry out power flow study
in the U.S. electrical grid.


## Main Features
**PreREISE** is dedicated to the building of demand, hydro, solar and wind profiles. A detailed presentation of the data source and algorithms used to generate profiles can
be found on our [docs].

---
**NOTE**

Profiles are publicly available for the Breakthrough Energy Sciences (BES)
grid model. Therefore, you don’t need to generate any input data if you use the
scenario framework to carry out power flow study.

---


## Where to get it
For now, only the source code is available. Clone or Fork the code here on GitHub.


## Dependencies
**PreREISE** relies on:
* **PowerSimData**, another package developed by Breakthrough Energy Sciences and
available [here][PowerSimData].
* Several Python packages all available on [PyPi](https://pypi.org/) whose list can be
found in the ***requirements.txt*** or ***Pipfile*** files both located at the root of
this package.


## Installation
Clone **PowerSimData** in a folder adjacent to your clone of **PreREISE** as the
installation of packages depends on files in **PowerSimData**. Then, use the
***requirements.txt*** file (via `pip`) or ***Pipfile*** file (via `pipenv`) to install
third party dependencies.


## License
[MIT](LICENSE)


## Documentation
[Code documentation][docstrings] in form of Python docstrings along with an overview of
the [package][docs] are available on our [website][website].


## Communication Channels
[Sign up](https://science.breakthroughenergy.org/#get-updates) to our email list and
our Slack workspace to get in touch with us.


## Contributing
All contributions (bug report, documentation, feature development, etc.) are welcome. An
overview on how to contribute to this project can be found in our [Contribution
Guide](https://breakthrough-energy.github.io/docs/dev/contribution_guide.html).



[docs]: https://breakthrough-energy.github.io/docs/prereise/index.html
[docstrings]: https://breakthrough-energy.github.io/docs/prereise.html
[website]: https://breakthrough-energy.github.io/docs/
[PowerSimData]: https://github.com/Breakthrough-Energy/PowerSimData

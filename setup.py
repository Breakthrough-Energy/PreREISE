from setuptools import find_packages, setup

setup(
    name="prereise",
    version="0.4",
    description="Create and run an energy scenario",
    url="https://github.com/Breakthrough-Energy/PreREISE",
    author="Kaspar Mueller",
    author_email="kaspar@breakthroughenergy.org",
    packages=find_packages(),
    package_data={
        "prereise": [
            "gather/*/data/*",
            "gather/data/*",
        ]
    },
    zip_safe=False,
)

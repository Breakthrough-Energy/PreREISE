from setuptools import setup, find_packages

setup(name='prereise',
      version='0.2',
      description='Create and run an energy scenario',
      url='https://github.com/intvenlab/PreREISE',
      author='Kaspar Mueller',
      author_email='kmueller@intven.com',
      packages=find_packages(),
      package_data={'prereise':['call/add_path.m']},
      zip_safe=False)

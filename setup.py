#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='de_toolkit',
      version='0.1'
      ,description='Suite of tools for working with count data'
      ,author='Adam Labadorf'
      ,author_email='labadorf@bu.edu'
      ,install_requires=[
        'docopt'
        ,'pytest'
        ,'future'
      ]
      ,packages=find_packages()
      ,entry_points={
        'console_scripts': [
          'detk=de_toolkit.de_toolkit:main'
          ,'detk-norm=de_toolkit.norm:main'
          ,'detk-de=de_toolkit.de:main'
          ,'detk-transform=de_toolkit.transform:main'
          ,'detk-filter=de_toolkit.filter:main'
          ,'detk-stats=de_toolkit.stats:main'
        ]
      }
      ,setup_requires=['pytest-runner']
      ,tests_require=['pytest']
     )

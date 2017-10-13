#!/usr/bin/env python

from setuptools import setup, find_packages
import pkg_resources

setup(name='de_toolkit',
      version=open('VERSION').read().strip()
      ,description='Suite of tools for working with count data'
      ,author='Adam Labadorf'
      ,author_email='labadorf@bu.edu'
      ,install_requires=[_.strip() for _ in open('requirements.txt')]
      ,packages=find_packages()
      ,package_data={'de_toolkit':['html_template.html']}
      ,entry_points={
        'console_scripts': [
          'detk=de_toolkit.common:main'
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

#!/usr/bin/env python

from setuptools import setup, find_packages
import pkg_resources

setup(name='de_toolkit',
      version=open('VERSION').read().strip()
      ,description='Suite of tools for working with count data'
      ,author='Adam Labadorf and the BU Bioinformatics Hub Team'
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
      ,url='https://bitbucket.org/bubioinformaticshub/de_toolkit'
      ,license='MIT'
      ,classifiers=[
        'Development Status :: 3 - Alpha'
        ,'Intended Audience :: Science/Research'
        ,'Environment :: Console'
        ,'License :: OSI Approved :: MIT License'
        ,'Programming Language :: Python :: 3'
        ,'Topic :: Scientific/Engineering :: Bio-Informatics'
      ]
      ,keywords='bioinformatics'
      ,python_requires='~=3.3'
     )

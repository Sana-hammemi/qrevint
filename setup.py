# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE.md') as f:
    license = f.read()

setup(
    name='QRevInt',
    version='1.18.0',
    description='International version of the USGS QRev',
    long_description=readme,
    author='David S. Mueller',
    author_email='dave@genesishydrotech.com',
    url='https://www.genesishydrotech.com',
    license=license,
	REQUIRES_PYTHON = '>=3.6.6',
	packages=['QRev', 'QRev.Classes', 'QRev.MiscLibs', 'QRev.UI'],
	 install_requires=[
						"matplotlib==3.1.1",
                        "numba==0.53.1",
						"numpy==1.17.2",
						"pandas==0.25.1",
                        "profilehooks==1.12.0",
                        "PyQt5==5.13.1",
						"pytest==5.1.3",
						"scipy==1.3.1",
                        "simplekml==1.3.1",
						"sigfig==1.3.2",
						"utm==0.5.0",
						"xmltodict==0.12.0", 
					  ],
)

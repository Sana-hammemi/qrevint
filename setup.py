# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup

with open('README.md') as f:
    readme = f.read()

with open('LICENSE.md') as f:
    license = f.read()

setup(
    name='qrevpy',
    version='0.1.0',
    description='QRev port to python',
    long_description=readme,
    author='David S. Mueller',
    author_email='dmueller@usgs.gov',
    url="https://code.usgs.gov/QRev/QRevPy",
    license=license,
    REQUIRES_PYTHON='>=3.8.10',
    packages=['Classes', 'MiscLibs', 'UI'],
    install_requires=['PyInstaller',
                      'PyQt5',
                      'PyQt5-sip',
                      'PyQt5-stubs',
                      'altgraph==0.16.1',
                      'atomicwrites==1.3.0',
                      'attrs==19.1.0',
                      'click==7.1.2',
                      'colorama==0.4.1',
                      'cycler==0.10.0',
                      'future==0.17.1',
                      'importlib-metadata',
                      'macholib==1.11',
                      'matplotlib==3.3.3',
                      'more-itertools==7.2.0',
                      'statsmodels',
                      'numpy',
                      'numba==0.53.1',
                      'pandas',
                      'pefile==2019.4.18',
                      'pluggy==0.13.0',
                      'py==1.8.0',
                      'pyparsing==2.4.2',
                      'pytest==5.1.3',
                      'python-dateutil',
                      'python-dotenv==0.10.3',
                      'pytz',
                      'pywin32-ctypes==0.2.0',
                      'scipy',
                      'setuptools==41.2.0',
                      'simplekml~=1.3.6',
                      'sip',
                      'six==1.12.0',
                      'utm',
                      'wcwidth==0.1.7',
                      'xmltodict==0.12.0',
                      'zipp==0.6.0',
                      'sphinx-markdown-builder',
                      'sphinx',
                      'myst-parser',
                      'sphinx_book_theme'
                      ], )

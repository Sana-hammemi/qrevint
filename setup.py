# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup

with open("README.md") as f:
    readme = f.read()

with open("LICENSE.md") as f:
    license = f.read()

setup(
    name="QRevInt",
    version="1.44.0",
    description="International version of the USGS QRev",
    long_description=readme,
    author="David S. Mueller",
    author_email="dave@genesishydrotech.com",
    url="https://www.genesishydrotech.com",
    license=license,
    python_requires=">=3.13.11, <3.14",
    packages=['qrev', 'qrev.Classes', 'qrev.DischargeFunctions',
              'qrev.MiscLibs', 'qrev.UI', 'qrev.translation',
              'docs'],
    package_data={'docs': ['source/*',
                            'source/assets/files/*',
                            'source/assets/user_guide/*',
                            'source/assets/tech_manual/*',
                            'index.rst',
                            'make.bat',
                            'Makefile',
                            ],
                  'qrev.translation': ['*.qm']},
    include_package_data=True,

    install_requires=[
        'python-qt5',
        'altgraph==0.16.1',
        'atomicwrites==1.3.0',
        'attrs==19.1.0',
        'click>=7.1.2',
        'colorama~=0.4.1',
        'cycler==0.10.0',
        'future==0.17.1',
        'importlib-metadata',
        'macholib==1.11',
        'matplotlib==3.6.3',
        'more-itertools==7.2.0',
        'statsmodels~=0.13.5',
        'numpy==1.26.2',
        'numba~=0.61.0',
        'pandas==1.4.0',
        'pefile==2019.4.18',
        'pluggy==0.13.0',
        'py==1.8.0',
        'pyinstaller',
        'pyinstaller-hooks-contrib',
        'pyinstaller-versionfile',
        'pyparsing==2.4.2',
        'PyQt5',
        'PyQt5-sip',
        'PyQt5-stubs',
        'python-dateutil',
        'python-dotenv==0.10.3',
        'pytz',
        'pywin32-ctypes==0.2.0',
        'reportlab',
        'scipy==1.10.0',
        'scikit-learn==1.3.2',
        'setuptools~=80.9.0',
        'sigfig==1.3.3',
        'simplekml',',
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
    ],
)

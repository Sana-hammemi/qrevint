# QRev 4

**QRev** version 4 is a Python port of the Matlab code QRev developed by the USGS to to compute the discharge from a moving-boat ADCP measurement using data collected with any of the Teledyne RD Instrument (TRDI) or SonTek bottom tracking ADCPs. QRev improves the consistency and efficiency of processing streamflow measurements by providing:

* Automated data quality checks with feedback to the user
* Automated data filtering
* Automated application of extrap, LC, and SMBA algorithms
* Consistent processing algorithms independent of the ADCP used to collect the data
* Improved handing of invalid data
* An estimated uncertainty to help guide the user in rating the measurement


**For a full description and instructions on the use of QRev click** **[HERE](https://hydroacoustics.usgs.gov/movingboat/QRev.shtml)** **to view the QRev web page.**

***

# Development
**QRevPy** has been approved for release (IP-118174) and has been assigned a digital object identifier of 10.5066/P9OZ8QDL. Additional development of features in QRev are expected. Versions available in the master branch of this repository are currently in use by the USGS, however, no warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. If you would like to contribute, please use the pull request process to provide new or improved code. 

## Requirements and Dependencies
### Source Code

QRevPy is currently being developed using Python 3.8 and makes use of the following packages:

PyQt5~=5.15.6
PyQt5-sip
PyQt5-stubs
altgraph==0.16.1
atomicwrites==1.3.0
attrs==19.1.0
click==7.1.2
colorama==0.4.1
cycler==0.10.0
future==0.17.1
importlib-metadata==0.23
kiwisolver==1.4.2
macholib==1.11
matplotlib==3.3.3
more-itertools==7.2.0
numpy==1.22.1
numba~=0.53.0
packaging==19.2
pandas==1.4.0
patsy==0.5.1
pefile==2019.4.18
pluggy==0.13.0
py==1.8.0
pyparsing==2.4.2
pytest==5.1.3
python-dateutil
python-dotenv==0.10.3
pytz
pywin32-ctypes==0.2.0
scipy==1.7.3
setuptools==41.2.0
simplekml~=1.3.6
sip
six==1.12.0
statsmodels==0.10.1
utm~=0.7.0
wcwidth==0.1.7
xmltodict==0.12.0
zipp==0.6.0


## Bugs
Please report all bugs with appropriate instructions and files to reproduce the issue and add this to the issues tracking feature in this repository.

# [Disclaimer](https://code.usgs.gov/QRev/QRevPy/-/blob/master/DISCLAIMER.md)

# [License](https://code.usgs.gov/QRev/QRevPy/-/blob/master/LICENSE.md)


# Suggested citation
Mueller, D.S., 2020, QRev, U.S. Geological Survey software release, https://doi.org/10.5066/P9OZ8QDL.

# Author
David S Mueller  
U.S. Geological Survey  
9818 Bluegrass Parkway  
Louisville, KY  
<dmueller@usgs.gov>
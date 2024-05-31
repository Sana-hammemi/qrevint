# QRevInt

**QRevInt** is a fork, created by Genesis HydroTech LLC, of QRev version 4 developed by the USGS. Both QRevInt and QRev compute the discharge from a moving-boat ADCP measurement using data collected with any of the Teledyne RD Instrument (TRDI) or SonTek bottom tracking ADCPs. The software improves the consistency and efficiency of processing streamflow measurements by providing:

* Automated data quality checks with feedback to the user
* Automated data filtering
* Automated application of extrap, LC, and SMBA algorithms
* Consistent processing algorithms independent of the ADCP used to collect the data
* Improved handing of invalid data
* An estimated uncertainty to help guide the user in rating the measurement


**Click** **[HERE](https://hydroacoustics.usgs.gov/movingboat/QRev.shtml)** **to view the USGS QRev web page.**

## Download Windows Executables

Windows Executables can be downloaded from (https://www.genesishydrotech.com/qrevint)

# Development
Genesis HydroTech LLC is coordinating the modifications and enhancements for QRevInt with the guidance and contributions from the following agencies:  

* The Norwegian Water Resources and Energy Directorate
* Environment and Climate Change Canada
* New Zealand Hydrological Society
* Swedish Meteorological and Hydrological Institute
* Groupe Doppler Hydrométrie
* U.S. Geological Survey
* UK Centre for Ecology & Hydrology
* Queensland Government Department of Resources
* Australian Hydrographers Association

## Goal
The goal of this project is to: 

* improve and expand the features currently available in QRev, 
* assist in the development of a standard processing software that is used internationally, and 
* ensure long-term support of the open-source software.

## Bugs
Please report all bugs with appropriate instructions and files to reproduce the issue and add this to the issues tracking feature in this repository or email (dave@genesishydrotech.com).

## Feature Requests
Feature requests are welcome. But take a moment to find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to convince the project's developers of the merits of this feature. Please provide as much detail and context as possible. Your proposed feature will be shared with the guidance group to ensure the contributions are consistent with this project and save you from work that might not be accepted into QRevInt. Be aware there is already a long list of proposed enhancement, so even if you request is accepted, there is no guarantee when if might be implemented, without associated resources.

## Contributions
If you would like to contribute your expertise to this project you are encourage to email your proposed contributions to dave@genesishydrotech.com so that the guidance group can ensure the contributions are consistent with this project and save you from work that might not be accepted into QRevInt. Contributions could include research into improving or developing better methods, writing code, reviewing code, reviewing and updating manuals, etc. If your contributions involve writing code or updating manuals please refer to the [CONTRIBUTORS_GUIDELINES.md](https://bitbucket.org/genesishydrotech/qrevint/src/weighted_extrap/CONTRIBUTORS_GUIDELINES.md) in this repository. Adherence to these guidelines will facilitate efficient merging of your contributions into the project and keep the project style and documentation consistent.

If you would like to contribute to this project finacially please contact dave@genesishydrotech.com.

## Requirements and Dependencies
QRev is currently being developed using Python 3.8 and makes use of the following packages:

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

# Disclaimer
This software (QRevInt) is a fork of QRev, which was originally approved for release by the U.S. Geological Survey (USGS), IP-118174. Genesis HydroTech LLC through funding from various international agencies is working to improve and expand the capabilities and features available in QRevInt. While Genesis HydroTech LLC makes every effort to deliver high quality products, Genesis HydroTech LLC does not guarantee that the product is free from defects. QRevInt is provided “as is," and you use the software at your own risk. Genesis HydroTech LLC and contributing agencies make no warranties as to performance, merchantability, fitness for a particular purpose, or any other warranties whether expressed or implied. No oral or written communication from or information provided by Genesis HydroTech LLC or contributing agencies shall create a warranty. Under no circumstances shall Genesis HydroTech LLC or the contributing agencies be liable for direct, indirect, special, incidental, or consequential damages resulting from the use, misuse, or inability to use this software, even if Genesis HydroTech LLC or the contributing agencies have been advised of the possibility of such damages. 


# License
Unless otherwise noted, this project is in the public domain in the United States because it contains materials that originally came from the United States Geological Survey, an agency of the United States Department of Interior. For more information, see the official USGS copyright policy at https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits. Additionally, Genesis HydroTech LLC waives copyright and related rights in the work worldwide through the CC0 1.0 Universal public domain dedication.

QRevInt includes several open-source software packages. These open-source packages are governed by the terms and conditions of the applicable open-source license, and you are bound
by the terms and conditions of the applicable open-source license in connection with your use and
distribution of the open-source software in this product. 

Copyright / License - CC0 1.0: The person who associated a work with this deed has dedicated the work to the public domain by waiving all of his or her rights to the work worldwide under copyright law, including all related and neighboring rights, to the extent allowed by law. You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission. 

In no way are the patent or trademark rights of any person affected by CC0, nor are the rights that other persons may have in the work or in how the work is used, such as publicity or privacy rights.

Unless expressly stated otherwise, the person who associated a work with this deed makes no warranties about the work, and disclaims liability for all uses of the work, to the fullest extent permitted by applicable law.

When using or citing the work, you should not imply endorsement by the author or the affirmer.

Publicity or privacy: The use of a work free of known copyright restrictions may be otherwise regulated or limited. The work or its use may be subject to personal data protection laws, publicity, image, or privacy rights that allow a person to control how their voice, image or likeness is used, or other restrictions or limitations under applicable law.

Endorsement: In some jurisdictions, wrongfully implying that an author, publisher or anyone else endorses your use of a work may be unlawful.


# Suggested citations
Mueller, D.S., 2021, QRevInt, Version x.xx, Genesis HydroTech LLC, https://bitbucket.org/genesishydrotech/qrevint/src/master/.  
Mueller, D.S., 2020, QRev, U.S. Geological Survey software release, https://doi.org/10.5066/P9OZ8QDL.

# Author
David S Mueller  
Genesis HydroTech LLC 
Louisville, KY  
<dave@genesishydrotech.com>
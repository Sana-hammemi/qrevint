# Description:

**QRev** version 4 is a Python port of the Matlab code QRev developed by the USGS to compute the discharge from a 
moving-boat ADCP measurement using data collected with any of the Teledyne RD Instrument (TRDI) or SonTek bottom 
tracking ADCPs. QRev improves the consistency and efficiency of processing streamflow measurements by providing:

* Automated data quality checks with feedback to the user
* Automated data filtering
* Automated application of extrap, LC, and SMBA algorithms
* Consistent processing algorithms independent of the ADCP used to collect the data
* Improved handing of invalid data
* An estimated uncertainty to help guide the user in rating the measurement


A history of changes with links to various releases can be found **[here](./docs/source/changelog.md)**.

**IMPORTANT NOTES ON DISCHARGE COMPUTATION:**

Default QRev settings may result in discharge computations different from WinRiverII and RiverSurveyor Live. 
Potential differences in discharge are due to QRev data filters, interpolation algorithms, and computations 
that may differ from manufacturer software.

Discharges computed in QRev 4 and 3.43 may exhibit some differences in computed discharge, with identical 
processing settings. Changes in final values are due to a combination of improvements to filters, improvements 
to interpolation methods, and differences found in Python and MATLAB processing methods. Please see Important 
Changes for details.

[Office of Surface Water Technical Memorandum 2016.03](https://hydroacoustics.usgs.gov/memos/OSW2016-03.pdf) 
 *(Internal Link)* recommends and authorizes the use of QRev for processing 
discharge measurements made with an ADCP from a moving-boat.

[Office of Surface Water Technical Memorandum 2017.02](https://hydroacoustics.usgs.gov/memos/OSW2017-02.pdf) 
*(Internal Link)* mandates the use of QRev for processing moving-boat streamflow measurements mad with acoustic Doppler Current 
profilers that are stored in the National Water Information System.

[WMA Technical Note 69](https://doimspp.sharepoint.com/sites/usgs-water-mission-area/SitePages/news_technote.aspx?RootFolder=%2Fsites%2Fusgs%2Dwater%2Dmission%2Darea%2FLists%2Fnews%5Ftechnote%2FWMA%20Technical%20Note%20Number%2069%20Release%20and%20use%20of%20QRev%204%20for%20processing%20moving%2Dboat%20streamflow%20measurements%20made%20with%20acoustic%20Doppler%20current%20profilers&FolderCTID=0x01200200501EAAFB86995C4DA98D3E9D5C759CFE&View=%7B9FBE16D6%2D4746%2D44AD%2DAD95%2D4C4E47BA4B99%7D) 
*(Internal Link)* announces the release of QRev 4 and the phasing out of support for QRev 3.43.

QRev can be used on desktops, laptops, and tablets running 64-bit versions of the Windows operating system. 
QRev should be used in the field to process measurement immediately after data collection and in the office to 
review measurements. The graphical user interface for QRev was designed to work on tablets, so most controls are 
buttons, radio buttons, and check boxes that can be easily operated by tapping on the screen. QRev is written 
in Python and packaged using PyInstaller. Unlike the MATLAB version there in no need for installing any additional 
libraries.

Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by 
the U.S. Government.
---

# Installation Instructions
- Download the latest version of QRev.
- Select or create a folder for QRev and unzip the file into that folder.
- Run the program by double-clicking on QRev_*.exe in Windows Explorer or My Computer. You may wish to create a 
shortcut in a convenient location in the Start Menu or on the Desktop.
---

# Integration with Site Visit Mobile Aquarius (SVMAQ) and Aquarius (AQ)

The results of data processed with QRev can be efficiently loaded into AQ through the use of SVMAQ. Saving a 
processed measurement in QRev automatically creates an XML file (*_QRev.xml). This xml file can be loaded into SVMAQ. 
After completing the site visit information in SVMAQ, the saved SVMAQ file can be loaded into AQ using the normal 
procedures.
---

# Recommended Workflow
QRev is intended to be used for both field processing and office review. Thus, QRev should be installed on both field 
and office computers. The recommended workflow is:
- Collect data using the manufacturer's software (WinRiver II or RiverSurveyor Live)
- Immediately after data collection process the data with QRev. MATLAB output files for RiverSurveyor Live data are
- required.
- Investigate all messages and warnings provided by QRev and make any necessary changes.
- Use the comments feature in QRev to explain or justify warnings and changes made.
- If necessary, use WinRiver II or RiverSurveyor Live to review data that are not reviewable in QRev.
- Finalize the processing and save the QRev files. Using the default date and time in the filenames by QRev: 1) 
provides unique file names, 2) helps track changes to processing settings, 3) identifies the most recently 
processed data, and 4) helps prevents accidental overwritting of previously processed data.
- Import the QRev XML file into SVMAQ.
- Backup all files to separate media from your field computer.
- Follow office policy for storage and uploading of data into AQ.

Note: The _QRev.mat file contains all the original data and final processing settings. The _QRev.mat file is 
independent of the original manufacturer files. Thus data processed with QRev should only be reviewed by loading 
the _QRev.mat file. WinRiver II and RiverSurveyor Live files should be considered the original field data and not 
used for review or reprocessing of data previously processed in QRev. In the rare situation where a display of data 
in WinRiver II or RiverSurveyor Live is not available in QRev, WinRiver II or RiverSurveyor Live could be used to 
review that portion of the data.
---

# Development
**QRev** has been approved for release (IP-118174) and has been assigned a digital object identifier of 
10.5066/P9OZ8QDL. Additional development of features in QRev are expected. Versions available in the master branch 
of this repository are currently in use by the USGS, however, no warranty, expressed or implied, is made by the USGS 
or the U.S. Government as to the functionality of the software and related material nor shall the fact of release 
constitute any such warranty. If you would like to contribute, please use the pull request process to provide new 
or improved code. 
---

## Requirements and Dependencies
### Source Code

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
---

# Updates and Bugs
In order to provide support for QRev and to provide an efficient means to communicate with users and allow users an 
efficient and organized means of providing suggestions and comments, you are encouraged to register for the USGS 
Hydroacoustic Forum. In the forum you will find a "QRev" board under Hydroacoustics Moving-Boat Deployments. 
Open the QRev board and click "Notify" to automatically receive emails on any bug fixes or issues identified with 
QRev. You are also encouraged to report any problems you encounter with QRev and attach the associated 
files so that any identified problem can be resolved. To access the USGS Hydroacoustics Forums you must be a registered 
user of the forums.

Bugs and feature requests can also be reported using the [Issues](https://code.usgs.gov/QRev/QRevPy/-/issues/new) 
section of the QRev repository or by submitting comments through the form available [here](https://forms.office.com/Pages/ResponsePage.aspx?id=urWTBhhLe02TQfMvQApUlAlv4jGjsJhOstclxasDPuZUOE1UWkZIV0JKWVY0NDdHVVlDVkxNNkFKNiQlQCN0PWcu).

[Register for access to USGS Hydroacoustics Forums](https://hydroacoustics.usgs.gov/software/Forum_Reg1.html)

[USGS Hydroacoustics Forums for Registered Users](https://simon.er.usgs.gov/smf/index.php?board=53)

Although the Forum is the preferred means of communication you can also email the Hydroacoustics work group (Hawg) 
at GS-W HaWG All@usgs.gov with questions and bugs.

---

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
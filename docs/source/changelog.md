# QRev Change Log

## [**Version 4.38**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.38)

**Status**: *Testing*

**Added:**
- EDI PDF Export.
- Added Ctrl+M shortcut to maximize Select Transect dialog.

**Changed:**
- Package structure updated to better fit use by other applications.
- Increased default size of Select Transects dialog.

**Fixed:**
- Corrected end time in PDF Summary

## [**Version 4.37**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.37)

**Status**: *Recommended*

**Added:**
- MAP: Added radio buttons to plot SNR/RSSI and Number of transects used.

**Changed:**
- Now using QRev interpolated data for MAP computation.
- Moved MAP datatype combobox plot options for contour plots to radio 
  buttons to follow look and workflow of other tabs. 

**Fixed:**
- Crash when opening a measurement with a single transect.
- Duplicating signals as new measurements files are loaded without closing UI.
- Crash when click the Moving Bed Tab when there is no valid bottom track 
  data in a test.
- Crash when clicking the edge tab when there is no valid bottom track data 
  for an edge.
- Auto application of Moving Bed corrections when a moving bed is detected.
- Updating of MAP plot and table when MAP not able to run, ie no data to 
  display. 
- UI crash when MAP crashes due to no data to process.


## [**Version 4.36**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.36)

**Status**: *Allowed*

**Changes:**
- Updated Export Mean Cross-Option signal
- Fixed XML export fail related to Mean XS comp fail due to invalid data in 
  the XY data during the projection.
- Fix crash resulting from SonTek data with good GGA but no VTG data.
- Merged in QRevInt updates.
- Added Multitransect Averaged Profile (MAP) tab and connected to backend code.
- Added temperature to MAP computations.
- Added feature to display discharge using number of significant digits or number of decimal places
- Modified discharge time series graph to show selected transect, cumulative mean discharge, and +/- 5% band on cumulative mean discharge
- Modified instructions to indicate that zoom out can be done using the right click on the mouse
- Added ability to save figures in several common graphic formats
- Added ability to manual set the axes limits for a graph
- Added QA check for a custom transformation matrix for TRDI ADCPs
- Added ability to allow autonomous GPS by default
- Converted documentation from external pdfs to built-in html
- Fixed crash when using Nortek Sig500 ADCP.
- Added option to import additional compass calibrations and moving bed tests.
- Added additional row in main details' table to display difference between 
  left and right transects
- Added additional QA check using the difference in flow direction between 
  Left and Right transects.
- Added boat speed to speed plot on WT tab.
- Fix unit conversion on X-axis of BT Other plot with English is selected.
- Oursin simulation changed to use current draft rather than original draft.
- Added ability for agency or user to change the date format.
- Added PDF Summary Report

## [**Version 4.34**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.34)

**Status**: *Allowed*

**Changes:**
- Fixed RS5 frequency display.
- Fixed reading of SonTek files with long directories.
- Fix MB correction application.
- Fix crash resulting from very slow boat movement due to repeated 
  shiptrack coordinates.
___

## [**Version 4.33**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.33)

**Status**: *Allowed*

**Changes:**
- Fixed auto application of MBT correction when no bed is detected.
- Fix crash resulting from RS5 .mat files containing ping types labeled as 
  'Other' or '1'
___
 
## [**Version 4.32**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.32)

**Status**: *Allowed*

**Changes:**
- Fix plotting of error and vertical velocity time series data on WT tab.
- Add reading of ping types for BT data from RS5, available in the matlab 
  export of RSQ_V2.1.11 or later.
- Fix reading of firmware version for RS5.
___

## [**Version 4.31**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.31)

**Status**: *Allowed*

**Changes:**
- Fix plotting of error and vertical velocity time series data on the BT tab.
___


## [**Version 4.30**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.30) 

**Status**: *Allowed*

**Changes:**
- Upgraded Python to 3.8 2. Fixed crash on main tab due to lollipop plot if 
  oursin not used. 3. Fix crash when changing WT plot options on file loaded from RS5 Qrev matfile due to spaces in ping types when reloading. 4. Fix crash when plotting shiptrack on MvBedTst tab when viewing some older Qrev files.
- Added config file.
- Added creation of config file if one does not exist.
- Modified XML output. The Uncertainty node now contains only the total 
  uncertainty and the model used. Separate nodes are provided for QRev_UA 
  and Oursin details.
- Fixed issue with salinity entered in WR2 not being applied in QRev
- Added support for RSL manual speed of sound, temperature, and salinity 
  settings
- Fixed bug adjusting RSL data to raw values when manual speed of sound, 
  temperature, and salinity settings were applied in RSL
- Speed of sound correction now applied to vertical boat and water velocities.
- Fixed bug in Oursin uncertainty model when using GPS reference
- Fixed bug in GPS tab when all transects do not have GPS data
- Fixed bug causing Main tab not to update following user input in Oursin 
  uncertainty
- Fixed bug loading QRev.mat as View then changing to Oursin uncertainty
- Fixed bug on boat speed plot preventing invalid original data from plotting
- Fixed bug causing crash if total discharge equals zero
- Fixed bug for SonTek ADCPs showing no in the xml file 
  CompassCalibrationResult when there is a calibration
- Fixed bug in manual 3-beam filter setting for water track
- Fixed bug loading RS5 Matlab data with blank Operator and/or Measurement 
  Number
- Fixed bug in some dialogs if an edit box is left blank and OK is pressed
- Fixed bug associated with loading, reprocessing, saving, and then 
  reloading of older *_QRev.mat files
- Fixed bug causing crash when viewing SNR plot if transect had missing samples
- Fixed crash when opening a SonTek Matlab file that had no sample data
- Added scrollbar option to Options dialog for computers with scaling > 125%
- Added Default X-Axis setting to Options dialog.
- Added persons, measurement number, and stage start, end, and measurement 
  to xml file.
___

## [**Version 4.29**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.29) 
**Status**: *Allowed*

**Changes:**
- Fix crash associated with auto beam filters for TRDI data.
___

## [**Version 4.28**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.28) 
**Status**: *Allowed*

**Changes:**
- Fixed crash when opening an older QRev.mat file for a Sontek M9 that had 
  some of the Loop test data marked as edge data.
- Fixed crash when changing thresholds on older QRev.mat file where bad MBT 
  data was present.
- Fixed crash associated with plot controls.
- Fixed crash associated unchecking all options on the compass tab.
___

## [**Version 4.27**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.27) 
**Status**: *Allowed*

**Changes:**
- Changed composite depths to interpolate for invalid depths using the 
  composite data rather than the primary reference.
- WT error and vertical velocity filters are now applied based on ping type 
  for all new processing of data. Loading older QRev files without 
  reprocessing will display previous results.
- BT error and vertical velocity filters are now applied based on bottom 
  track ping frequency for all new processing of data. Loading older QRev 
  files without reprocessing will display previous results.
- An option for the jet color map has been added to the Options dialog.
- Added points to plots in Depth tab
- Fixed several bugs related to reading RS5 and older QRev files.
- Added advanced graph tab.
- Added keyboard shortcuts
- Added ability to switch x-axis to time or length for time series and 
  contour plots.
- Added option to export mean cross-section bathymetry within the XML.
- Fixed crash from nan values present in the Transect data.
- Fixed crash resulting from import of mmt file with no configuration 
  commands (streampro palm pilot). 13. Added filters for moving-bed tests 
- Added Uncertainty option to the Options dialog. 15. Changed the 
        options for loading existing *_QRev.mat files. The options now are 
        View or Reprocess.
- Fixed crash when changing the magnetic variation after loading a 
  previously saved QRev file.
- Added group number to default file name for split initiation save.
___

## [**Version 4.26**](https://code.usgs.gov/QRev/QRevPy/-/releases/V4.26) 
**Status**: *Allowed*

**Changes:**
- Fix crash resulting from NaN values in BT data for GPS class.
- Fix crash resulting from loading old QRev files missing setting dict in 
  mat file.
- Fix crash resulting from missing elements from sticky settings.
___

## **Version 4.25**
**Status**: *Allowed*

**Changes:**
- Fixed bug in EDI associated with GPS data.
- Technical manual update to include explanation of computing discharge in 
  shallow water and corrected table 10.
- Fixed bug in applying weighted medians when switching from automatic to 
  manual data type
- Modified extrap subsection so that subsectioning always works from left 
  to right
- Removed depth from Oursin measured discharge uncertainty
- Added start date and delta Q to summary table
- Extrap subsection label changes based on data loaded and processed.
- Fixed some compatibility issues with RS5 data.
- Fixed crash associated with Windows OS versions newer than 1909.
- Fix time formatting on Discharge TS plot so times do not overlap.
- Fix bug with loading data collected with a PDA and streampro.
___

## **Version 4.24**
**Status**: *Allowed*

**Changes:**
- Added user option to prompt for rating on save
- Added user option to compute extrapolation fit using discharge weighted 
  medians
- Total measurement discharge will ignore any transect with a discharge 
  that could not be computed
- Fixed bug reading some old QRev.mat files associated with new rating feature
___

## **Version 4.23**
**Status**: *Allowed*

**Changes:**
- New TRDI raw data reader that is 3+ times faster
- Fixed issue with depth reference drop down menu when depth sounder data 
  were collected
- Fixed issue so that GPS references that aren’t available cannot be selected
- Fixed several issues with new GPS-BT tab and GPS usage for moving-bed test
- Fixed bugs in heading interpolation
- Fixed bug reading *_QRev.mat having only 1 transect
- Fixed bug when loading measurement with no transects selected
- Fixed issue that could occur when processing moving-bed tests loaded from 
  *_QRev.mat
___

## **Version 4.22**
**Status**: *Allowed*

**Changes:**
- Added code to identify and notify of user changes to original values
- Added ability to use GPS as a reference for moving-bed tests
- Applying magvar or heading offset or heading source changes to all 
  transects applies them to moving-bed test also
- Moving-bed test flow speed now corrected for moving-bed velocity
- Added automatic checking of GPS lag
- Added GPS – BT comparison tab to GPS Tab
- Fixed issue with applying the correct moving-bed test when multiple tests 
  are available
- Modifications to allow QRev to work with Rowe and Nortek ADCPs.
- Added support for user edge discharge for WinRiver II 2.22
- “.mat” is always appended as suffix to saved QRev file
- Manual threshold for wt and bt saved and displayed when opening *_QRev.mat
- Modified code to use 1st checked transect rather than 1st transect for 
  general settings
- Modified code to accept measurements with inconsistent availability of 
  GPS data types
- Fixed issue loading data with no valid bottom track
- Added notification when SonTek data is loaded with other than Earth 
  coordinates
- Fixed issue with selecting transects in EDI if some transects were not 
  checked
- Fixed issue in EDI if no GPS data are available
- Fixed QA check for missing samples
- Fixed issue with invalid stationary moving-bed tests used for correction
___

## **Version 4.21**
**Status**: *Allowed*

**Changes:**
- Fixed incomplete system test for TRDI causing crash when saving
- Fixed issue with PT3 test status not displayed properly
- Fixed issue with VTG low speed message
- Fixed issue with VTG and composite tracks on causing switch to GGA
- Fixed issues with the edges tab: no valid GPS, 0 or 1 ensembles selected, 
  etc.
- Fixed issues with tab text color not updating properly
- Updated user’s manual to indicate that 4-beam composite is the default if 
  vertical beam or depth sounder data are available.
- Several issues with the interaction with RIVRS were fixed
- Fixed inconsistent behavior of the up/down arrows
- Improved speed of transect change using up/down arrows
- Fixed issue with files saving in previously used folder
- Modified code for compatibility with Nortek Signature 1000
___

## **Version 4.20**

**Status**: *Allowed*

**Changes:**
- Fixed issue with shiptrack when all GPS data are invalid
- Fixed bug when applying stationary moving-bed correction
___

## **Version 4.19**

**Status**: *Allowed*

**Changes:**
- Fixed issue with applying a loop test when preceded by a stationary test.
- Fixed issue with current settings when measurement has mixture of GPS and 
  no GPS
___

## **Version 4.13**

**Status**: *Allowed*

**Changes:**
- Ported code from Matlab to Python
- User interface redesigned using PyQt
- Main summary page includes contour, shiptrack, and discharge time series 
  graphics
- Ability to change navigation reference through the toolbar
- Ability to turn on or off composite tracks through the toolbar
- Changes to default settings are highlighted
- Opening and measurement loading speed has been improved
- Change water velocity interpolation from linear to ABBA
- Water velocities for all invalid bins are interpolated rather than added 
  to top or bottom extrapolation
- Fixed bug in vtg primary composite tracks, wasn't substituting GGA
- Added uncertainty to the automatic comment when a file is saved
- Statistics and interpolation methods in Python may result in small 
  differences from Matlab
 ___

## Software/Firmware Status Definitions
**Required Minimum**: Minimum version required. This version has proven 
stable and may contain enhancements that are significant over previous 
required versions

**Recommended**: Shown to have been reliable and contains features that 
result in a recommended upgrade over the required version. There could be a 
few specific use cases where this version may have issues that would result 
in some users not using this version. If so, those cases will be noted.

**Allowed**: Deemed reliable during initial testing. Any issues will be 
noted along with improvements available over prior versions. Use of allowed 
versions may be desired in cases when the changes benefit a significant 
number of the user's conditions or equipment. For example: a new version of 
software is released that adds support for new hardware. If the user has 
this hardware, they would need to upgrade to the newer software before it 
becomes recommended or required. Use of these versions by experienced users 
will also help OSW identify any unknown issues.

**Testing**: OSW is currently testing; any known issues or advantages over 
prior release will be noted. The use of a version that is in testing should 
usually be limited to advanced users that can trouble shoot potential 
issues and provide feedback on any irregularities or problems observed.

**Do Not Use**: A version either prior to the required minimum or that 
contains issues that significantly affect operations.


**Note**: A version may remain in **Allowed** or **Testing** indefinitely. 
Example: A new version is released while the prior version is still in 
Testing. In this case the prior version may remain in Testing, while future 
testing efforts are placed on the newer version.

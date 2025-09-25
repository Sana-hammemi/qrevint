# QRevInt Change Log
### Changes QRevInt 1.37 to 1.40
1. Python version upgraded to version 3.11.9
2. Modified processing of composite tracks to interpolate using the composite tracks results when on other source is valid
3. Fixed issues with displayed time and associated time zone
4. Fixed issues with some previously saved QRev.mat files
5. Fixed issues with reading some RSQ files
6. Fixed bug preventing configuration commands from being reported in the XML file
7. The Compass/P/R table now displays the magenetic variation and heading offset associated with the selected heading source
8. The Compass/P/R graph now  shows the external heading automatically, if available
9. Added support for external heading to RSQ data
10. Modified how blanking distance is reported in the XML file for data with multiple blanking distances
11. Added code to check that compass calibration precedes loop moving-bed test
12. Added code to check that compass calibration precedes data collection when GPS is present
13. Modifications from USGS and Groupe Doppler Hydrometrie:  
    a) Added additional MAP CSV export options and updated UI to show additional
    buttons to trigger exports   
    b) Optimized some of the MAP computations to increase processing speeds  
    c) Fixed issues causing MAP to crash  
    d) Added color scale to Google Earth plots
14. Added option to compute width and area perpendicular to mean flow direction
15. Maximum water speed includes correction for moving-bed condition
16. Temperature time series added to Advanced Graphics options
17. TRDI internal GPS can be used to georeference bottom track for display in Google Earth

### Changes QRevInt 1.36 to 1.37
1. Fixed bug computing 3-beam solutions for SNR filtered SonTek data

### Changes QRevInt 1.34 to 1.36
**Some of these changes will affect the computed discharge for SonTek data**
1. Fixed issue with SNR filter when 3-beam computations for SNR are used
2. Fixed bug in bottom track velocity guidance
3. Fixed bug display extrapolation on Main tab when velocity is selected
4. Added support for rsqmb data files without the need to export to Matlab
5. Ping type for rsqmb data files read from files rather than empirically 
   determined for some Matlab files
6. Added correct hpr matrix for Sontek ADCPs
7. Added code to identify and filter 3-beam solutions in SonTek Matlab files
8. Fixed error velocity scaling for bottom track for SonTek Matlab files
9. The number of ensembles in an edge is changed by clicking the Left or 
   Right # Ens. column rather than the # Valid column
10. Changed "Max MovBed" to "Avg MovBed" in pdf summary report.

### Changes QRevInt 1.33 to 1.34
1. Fixed bug introduced in 1.33 preventing saving moving-bed tests

### Changes QRevInt 1.32 to 1.33
1. Fixed bug preventing saving a measurement that did not have a moving-bed 
   test

### Changes QRevInt 1.31 to 1.32
1. Restructured code to facilitate easier use by other packages
2. Added a tooltip to all messages explaining the 
message and providing guidance on the impact on the measurement and suggest 
ways to resolve the issue.
3. Added wetted perimeter and hydraulic radius computations
4. Fixed bug when opening a saved QRev.mat with missing SNR range.
5. Display of edge units in exported PDF now honor unit system setting.
6. Fixed storing of measurement where qTotalThresholdWarning and 
   qTotalThresholdCaution were reversed.
7. Added code to recognize saved measurements where qTotalThresholdWarning and 
   qTotalThresholdCaution were reversed.
8. Added error logging with prevention for code crashing.
9. Fixed bugs in plots when an axis type of than length is selected
10. Modified code for pdf report to wrap field crew text
11. Added ADCP depth to pdf report
12. Mean ADCP temperature now displayed in pdf report if the user 
    does not manually enter an ADCP temperature.
13. Removed support for stylesheet.
14. Added time zone combo box to Premeasurement tab and option to make it 
    required.
15. Added option to show percent measured in details tab.
16. Added discharge display digits to options menu.
17. Add translation tags to all automated messages and guidance.
18. MAP added bathymetry export

### Changes QRevInt 1.30 to 1.31
1. Fixed bug identifying invalid edge ensembles
2. Add processing of vertical velocity
3. Fixed reporting of end time in pdf file
4. Fixed crash when using automatic scaling from Set Axis Limits context menu
5. Fixed bug in SNR filter for non-SonTek data
6. Fixed graphing of data with unspecified ping type
7. Fixed bug not reading SNR range for QRev.mat files
8. Fixed issues with side lobe cutoff data in QRev.mat files

### Changes QRevInt 1.29 to 1.30
1. Fixed issue with plots where there is no valid data, 
2. Fixed issue with plotting options on depth cross section plots
3. Fixed bug reading QRev.mat file with no system test
4. Added check for valid GPS data when creating kml
5. Fixed bug using GPS in moving-bed tests
6. Fixed bug in shiptrack options on moving-bed test tab
7. Added fixed for RS5 frequency code
8. Fixed QA check for invalid data in edges

### Changes QRevInt 1.28 to 1.29
1. Refactored MAP to use QRevInt processed data
2. Modified bottom side lobe cutoff in MAP
3. Revised user interface for MAP
4. Revised auto computation of MAP cell height and width
5. Vertical velocity processed like horizontal velocity
6. Fixed messages referring to QRevMS
7. Fixed bug in CompassPR when using external heading
8. Fixed bug preventing the discharge from being corrected by moving-bed tests when measurement is first loaded. Discharge is updated with any subsequent change to data.
9. Fixed bug when loading previously saved measurement with only one transect
10. Fixed bug in plots preventing invalid original data symbols from displaying
11. Fixed display of edges in depth plots
12. Fixed units bug in boat speed plot
13. Added code to prevent GUI crashes
14. Fixed issue if RiverRay matrix in system test is incorrect
15. Fixed issue with new ping type code for RS5
16. Fixed units for edge distances in PDF summary

### Changes QRevInt 1.27 to 1.28
1. Fixed bug exporting mean cross-section to xml file when there is no compass data

### Changes QRevInt 1.26 to 1.27
1. Fixed bug causing pdf report to crash on save
2. Fixed bug causing crash when loading some previously saved measurements

### Changes QRevInt 1.25 to 1.26
1. Fixed issue with displaying extrapolated data in the color contour plot when there was no valid data in an ensemble
2. Fixed crash when loading MB test from M9 data with ensembles labeled as edge data.
3. Fixed recall of Mag Var dialog with M9 files.
4. Oursin simulation changed to use current draft rather than original draft.
5. Added ability for agency or user to change the date format.
6. Added PDF Summary Report
7. Fixed issue loading previously saved QRev.mat files when no compass was present.
8. Corrected reporting of uncertainty values in comment and PDF Summary Report when saving.
9. Added code to search for serial number in system test if serial number not in mmt or mat files.
10. User's Manual updated

### Changes QRevInt 1.23 to 1.25
1. Updated Export Mean Cross-Option signal
2. Fixed XML export fail related to Mean XS comp fail due to invalid data in 
    the XY data during the projection.
3. Fixed saving XML file with manual HDOP set
4. Fix crash resulting from SonTek data with good GGA but no VTG data.
5. Message displayed if no cfg file and one automatically created
6. Added excluded distance settings to cfg file
7. Added Map Tab show option to Options dialog
8. Modified UI and improved speed using MAP
9. Added temperature to MAP computations.
10. Added feature to display discharge using number of significant digits or number of decimal places to cfg file
11. Modified discharge time series graph to show selected transect, cumulative mean discharge, and +/- 5% band on cumulative mean discharge
12. Modified instructions to indicate that zoom out can be done using the right click on the mouse
13. Added ability to save figures in several common graphic formats (right click)
14. Added ability to manual set the axes limits for a graph (right click)
15. Added QA check for a custom transformation matrix for TRDI ADCPs
16. Added ability to allow autonomous GPS by default to .cfg file
17. Converted documentation from external pdfs to built-in html
18. Documentation updated with new features
19. Fixed crash when using Nortek Sig500 ADCP.
20. Added option to import compass calibrations and moving bed tests from other measurements
21. Added additional row in main details' table to display difference between 
    left and right transects
22. Added additional QA check using the difference in flow direction between 
    Left and Right transects.
23. Added boat speed to speed plot on WT tab.
24. Fix unit conversion on X-axis of BT Other plot with English is selected.

### Changes QRevInt 1.21 to 1.23 
1.	Updated documentation  
2.	Added option to use 3-beam solutions when SNR filter marks an ensemble invalid 
3.	Fixed scaling issues for some graphics 
4.	Reduced redundant caution and warning messages to user 
5.	Added edge shape to contour graphs and shifted time series to match when using length for xaxis 
6.	Added extrapolated top, bottom and edge speeds to final color contour graph 
7.	Bug fixes to MAP 
8.	Fixed issues with data probe when graph is zoomed 
9.	Added QA check for low battery voltage 
10.	Updated code to support QRev.mat files created prior to new features 
11.	Fixed issue where SonTek files may not load in order data were collected 
12.	Other minor bug fixes 

### Changes QRevInt 1.20 to 1.21
1.	Fixed bug in Oursin related to Pandas version 
2.	Fixed typo related to discharge time series 

###  Changes QRevInt 1.18 to 1.20
1.	Merged code with USGS QRev code 
2.	CompTrack setting now retained from save file 
3.	Added ability to save mean cross section coordinates in xml file. 
4.	Improved handling of RS5 data files 
5.	Fixed issues with some graphs 
6.	Fixed issue with automatically selecting moving-bed tests 
7.	Other bug fixes 
8.	Added MAP tab 
9.	Added feature to display discharge using number of significant digits or number of decimal places  
10.	Modified discharge time series graph to show selected transect, cumulative mean discharge, and +/- 5% band on cumulative mean discharge 
11.	Modified instructions to indicate that zoom out can be done using the right click on the mouse 
12.	Added ability to save figures in several common graphic formats 
13.	Added ability to manual set the axes limits for a graph 
14.	Added QA check for a custom transformation matrix for TRDI ADCPs 
15.	Added ability to allow autonomous GPS by default 

### Changes QRevInt 1.17 to 1.18 
1. Fixed bug so that the uncertainty value from the selected uncertainty model is recorded in the comments.

### Changes QRevInt 1.16 to 1.17 
1. Modified XML output. The Uncertainty node now contains only the total uncertainty and the model used. Separate nodes are provided for QRev_UA and Oursin details. 

### Changes QRevInt 1.15 to 1.16 
1. Fixed crash when opening a file for a new installation with no existing QRev Settings file. 

### Changes QRevInt 1.14 to 1.15 
1. Fixed bug preventing new installations that didn’t have a QRev Settings file with the Folder key previously define from running and generating a “Failed to execute script QRev” message. 
### Changes QRevInt 1.11 to 1.14 
1. Fixed incorrect weighting when computing average water speed for time series plot 
2. Change ship track vectors to depth cell size weighted average for velocity components. 
3.	Fixed compatibility issue with older QRev.mat files where edge ensembles were excluded in the for moving-bed tests. 
4.	Fixed bug using Jet color map on WT tab 
5.	Fixed issue with salinity entered in WR2 not being applied in QRev 
6.	Added support for RSL manual speed of sound, temperature, and salinity settings 
7.	Fixed bug adjusting RSL data to raw values when manual speed of sound, temperature, and salinity settings were applied in RSL 
8.	Speed of sound correction now applied to vertical boat and water velocities. 
9.	Fixed bug in Oursin uncertainty model when using GPS reference 
10.	Fixed bug in GPS tab when all transects do not have GPS data 
11.	Fixed bug causing Main tab not to update following user input in Oursin uncertainty 
12.	Fixed bug loading QRev.mat as View then changing to Oursin uncertainty 
13.	Fixed bug on boat speed plot preventing invalid original data from plotting 
14.	Fixed bug causing crash if total discharge equals zero 
15.	Fixed bug for SonTek ADCPs showing no in the xml file CompassCalibrationResult when there is a calibration 
### Changes QRevInt 1.10 to 1.11 
1.	Fixed bug causing failure of *_QRev.mat files to open. 
2.	Added scrollbar option to Options dialog for computers with scaling > 125% 
### Changes QRevInt 1.09 to 1.10 
1.	Fixed bug causing crash when viewing SNR plot if transect had missing samples 
2.	Fixed crash when opening a SonTek Matlab file that had no sample data 
### Changes QRevInt 1.07 to 1.09 
1.	Fixed bug in manual 3-beam filter setting for water track 
2.	Fixed bug loading RS5 Matlab data with blank Operator and/or Measurement Number 
3.	Fixed bug in some dialogs if an edit box is left blank and OK is pressed 
4.	Fixed bug associated with loading, reprocessing, saving, and then reloading of older *_QRev.mat 
files 
5.	Modified handling of measurement path to allow simultaneous use of multiple instances of QRevInt and prevent saving data to the wrong folder 
6.	Added Default X-Axis setting to Options dialog. 
7.	Added persons, measurement number, and stage start, end, and measurement to xml file. 
8.	Update documentation 
### Changes QRevInt 1.06 to 1.07 
1.	Several minor bug fixes 
2.	Graphics for BT, GPS, Depths, and WT now share x-axis for zoom and pan 
3.	Added stage start, end, and measurement to Premeasurement tab 
4.	Modified messages for moving-bed conditions based on selected reference 
5.	New QA methods applied consistently when Viewing previously saved QRev.mat 
### Changes QRevInt 1.01 to QRevInt 1.06 
1.	Added shortcut keys 
2.	Added option to use length or time for x-axis 
3.	Added Advanced Graphics tab 
4.	Added correlation and RSSI/SNR to boat data 
5.	Fixed code identifying RS5 ADCP model 
6.	Fixed ping type and frequency identification 
7.	Updated Oursin uncertainty model to latest methods including Bayesian COV 
8.	Updated Oursin user interface and graphs 
9.	Added new data fields to *_QRev.mat while maintaining compatibility with older files 
10.	Added ability for agencies to configure the Options dialog and the default values 
11.	Added option to allow an observed no moving-bed condition 
12.	Added option to turn off use of heading data 
13.	Filter settings for transects are now applied to moving-bed tests 
14.	Added tooltips to all tables and labels that are highlighted due to ADQA 
15.	Uses Numba AOT compiling of robust loess smooth, Bayesian COV, and top and bottom discharge computations to improve overall speed. 70% average speed improvement. 
16.	Improvements to depth filter. May cause a small change in discharge for some measurements. 17. Added fields for Measurement Number and Person(s) to Premeasurement tab 
18.	All reported and/or discovered bugs were fixed. 
19.	User’s manual updated 
20.	Technical manual updated 
### Changes QRevInt 1.00 to QRevInt 1.01 
1.	Changed composite depths to interpolate for invalid depths using the composite data rather than the primary reference. 
2.	WT error and vertical velocity filters are now applied based on ping type for all new processing of data. Loading older QRev files without reprocessing will display previous results. 
3.	BT error and vertical velocity filters are now applied based on bottom track ping frequency for all new processing of data. Loading older QRev files without reprocessing will display previous results. 
4.	The user now has an option in the Options dialog to apply error and vertical velocity filters based on data from the entire measurement rather than based on data from individual measurements.  
5.	An option for the jet color map has been added to the Options dialog. 
6.	Added points to plots in Depth tab 
7.	Fixed several bugs related to reading RS5 and older QRev files. 

### Changes QRevInt 4.26 Beta to QRevInt 1.00 
1.	New versioning implemented. 
2.	Added disclaimer and license that must be agreed to prior to running the first time. 
3.	Modified code for compatibility with older QRev.mat files that lack the new features. 
4.	QRev.mat files previously saved can be view as saved but will apply new features upon any change. 
5.	Changed date format to YYYY.MM.DD. 
6.	Added background color to the main window to distinguish from QRev. 
7.	Extrap subsection label changes based on data loaded and processed. 
8.	Fixed some compatibility issues with RS5 data. 
### Changes QRev 4.23 to QRevInt 4.26 Beta 
1.	Due to development conducted outside the USGS the name was changed to QRevInt, so as to represent the international support and development. 
2.	Change icon to blue to distinguish from USGS version of QRev 
3.	Fixed bug in EDI associated with GPS data. 
4.	Technical manual update to include explanation of computing discharge in shallow water and corrected table 10. 
5.	Fixed bug in applying weighted medians when switching from automatic to manual data type 
6.	Modified extrap subsection so that subsectioning always works from left to right 
7.	Removed depth from Oursin measured discharge uncertainty 
8.	Added start date and delta Q to summary table 
9.	Modified documentation reflect change to QRevInt 
### Changes 4.23 to 4.24 
1.	Added user option to prompt for rating on save 
2.	Added user option to compute extrapolation fit using discharge weighted medians 
3.	Total measurement discharge will ignore any transect with a discharge that could not be computed 
4.	Fixed bug reading some old QRev.mat files associated with new rating feature 
### Changes 4.21 to 4.23 
5.	New TRDI raw data reader that is 3+ times faster 
6.	Fixed issue with depth reference drop down menu when depth sounder data were collected 
7.	Fixed issue so that GPS references that aren’t available cannot be selected 
8.	Fixed several issues with new GPS-BT tab and GPS usage for moving-bed test 
9.	Fixed bugs in heading interpolation 
10.	Fixed bug reading *_QRev.mat having only 1 transect 
11.	Fixed bug when loading measurement with no transects selected 
12.	Fixed issue that could occur when processing moving-bed tests loaded from *_QRev.mat 
### Changes 4.16 to 4.21 
1.	Added code to identify and notify of user changes to original values 
2.	Added ability to use GPS as a reference for moving-bed tests 
3.	Applying magvar or heading offset or heading source changes to all transects applies them to moving-bed test also 
4.	Moving-bed test flow speed now corrected for moving-bed velocity 
5.	Added automatic checking of GPS lag 
6.	Added GPS – BT comparison tab to GPS Tab 
7.	Fixed issue with applying the correct moving-bed test when multiple tests are available 
8.	Modifications to allow QRev to work with Rowe and Nortek ADCPs. 
9.	Added support for user edge discharge for WinRiver II 2.22 
10.	“.mat” is always appended as suffix to saved QRev file 
11.	Manual threshold for wt and bt saved and displayed when opening *_QRev.mat 
12.	Modified code to use 1st checked transect rather than 1st transect for general settings 
13.	Modified code to accept measurements with inconsistent availability of GPS data types 
14.	Fixed issue loading data with no valid bottom track 
15.	Added notification when SonTek data is loaded with other than Earth coordinates 
16.	Fixed issue with selecting transects in EDI if some transects were not checked 
17.	Fixed issue in EDI if no GPS data are available 
18.	Fixed QA check for missing samples 
19.	Fixed issue with invalid stationary moving-bed tests used for correction 

### Changes 4.15 to 4.16 
1.	Fixed incomplete system test for TRDI causing crash when saving 
2.	Fixed issue with PT3 test status not displayed properly 
3.	Fixed issue with VTG low speed message 
4.	Fixed issue with VTG and composite tracks on causing switch to GGA 
5.	Fixed issues with the edges tab: no valid GPS, 0 or 1 ensembles selected, etc. 
6.	Fixed issues with tab text color not updating properly 
7.	Updated user’s manual to indicate that 4-beam composite is the default if vertical beam or depth sounder data are available. 
8.	Several issues with the interaction with RIVRS were fixed 
9.	Fixed inconsistent behavior of the up/down arrows 
10.	Improved speed of transect change using up/down arrows 
11.	Fixed issue with files saving in previously used folder 
12.	Modified code for compatibility with Nortek Signature 1000 
### Changes 4.14 to 4.15 
1.	Fixed issue with shiptrack when all GPS data are invalid 
2.	Fixed bug when applying stationary moving-bed correction 
### Changes 4.13 to 4.14 
1.	Fixed issue with applying a loop test when preceded by a stationary test. 
2.	Fixed issue with current settings when measurement has mixture of GPS and no GPS 
### Changes 3.43 to 4.13 
1.	Ported code from Matlab to Python 
2.	User interface redesigned using PyQt 
3.	Main summary page includes contour, shiptrack, and discharge time series graphics 
4.	Ability to change navigation reference through the toolbar 
5.	Ability to turn on or off composite tracks through the toolbar 
6.	Changes to default settings are highlighted 
7.	Opening and measurement loading speed has been improved 
8.	Change water velocity interpolation from linear to ABBA  
9.	Water velocities for all invalid bins are interpolated rather than added to top or bottom extrapolation 
10.	Fixed bug in vtg primary composite tracks, wasn't substituting GGA 
11.	Added uncertainty to the automatic comment when a file is saved 
12.	Statistics and interpolation methods in Python may result in small differences from Matlab 
### Changes 3.42 to 3.43 
1. Fixed bug that did not properly identify missing (lost) ensembles if the typical ensemble duration was greater than 1.5 sec. This affected mode 13 StreamPro data. 
### Changes 3.41 to 3.42 
1. Fixed bug in bottom discharge extrapolation. Previous versions failed to estimate the bottom discharge for ensembles that had no valid data but where depth cell velocities were interpolated. 
### Changes 3.40 to 3.41 
1.	Fixed bug with discharge percent change not updating after multiple speed of sound changes. 
2.	Fixed bug in edges table where wrong row was highlighted if some transects were unchecked. 
3.	Fixed bug in edges shiptrack so it only displays valid orginal data and not interpolated data. 
4.	Fixed bug no allowing manual entry of 0 salinity. 
### Changes from 3.35 to 3.40 
1.	Fixed bug causing crash when TRDI PT3 test was incomplete. 
2.	Modified uncertainty estimate for invalid and edges to use absolute values. 
3.	Fixed issue with multi-line comments in XML file. 
4.	Fixed draft check to only evaluate checked transects. 
5.	XML file now only contains the summary information from a SonTek compass calibration. 
6.	Fixed bug in moving-bed test if loop compass error and direction could not be computed. 
7.	Added message for missing samples in SonTek data. 
8.	Modified PT3 tests to reduce false positives. 
9.	Added check to boat and wt to check warn if all data are invalid. 
10.	Edge sign check changed to only show message if edge discharge is greater than 0.5% 
11.	Added option to store a style sheet with the xml output file. 
12.	Added _ separator between date and time in default filename. 
13.	Default compass data view changed to evaluation if evaluation is available. 
14.	Added upper limit of 45 ppt to salinty input dialog. 
15.	Added Power/Power default exponent to XML output to support NVE request. 
16.	Update help file. 
### Changes to QRev from 3.34 to 3.35 
1. Fixed bug causing crash when ADCP had no compass. 
### Changes to QRev from 3.33 to 3.34 
1. Fixed bug causing 25 cm excluded distance to be applied to RiverPro data. 
### Changes to QRev from 3.31 to 3.33 
1.	Fixed bug using uncheck all. 
2.	Fixed bug manually loading system test or compass calibration or evaluation 
3.	Changed legend location to best 
4.	Fixed bugs in GUI causing wrong transects to be highlighted 
5.	Fixed bug reprocessing QRev files associated with moving-bed tests 
6.	Fixed bug causing changes in draft hOffset, hSource, and magVar to not update QA properly 
### Changes to QRev from 3.30 to 3.31 
1.	Fixed bug creating structure for test results from existing QRev files 
2.	Fixed bug setting status of system test results and button color 
3.	Fixed bug causing end edge discharge to be applied at start edge 
4.	Fixed bug preventing user uncertainty from being recomputed after changing a filter or extrapolation 
5.	Fixed bug displaying number of ensembles to use for edge 
6.	Changed the algorithm for determining PT3 failure 
7.	Modified the computation for extrapolation uncertainty to prevent a manual setting from biasing the uncertainty low 
8.	Added reprocessing of moving-bed tests to reprocessing of existing QRev data files. 
9.	The mag field, if available, is automatically displayed in the heading graph 
10.	Modified the excluded distance filter to round to 2 digits to prevent differences when converting between units. 
### Changes to QRev from 3.28 to 3.30 
1.	Fixed bugs in messages table that were opening wrong windows. 
2.	Modified code to interpolate invalid data from composite tracks using the composite tracks rather than the primary data. 
3.	Modified code to interpolate invalid data from composite depths using the composite depths rather than the primary data. 
4.	Modified draft check to use display units and limit the comparison to 2 decimal spots which is what is displayed in the GUI. 
5.	Added code to interpolate discharge for ensembles that are too shallow for a valid depth cell. 
6.	Modified code in the way that TRDI mmt file setting for composite depths are processed to QRev settings.  
7.	Moved composite depth computation to end of data input flow. 
8.	Modified code to allow the view comments button to be accessible even when another window is open. 
9.	Fixed bug with computePerDiff in extrapolation sensitivity when no transect data provided. 
10.	Added valid depth method to xml output. 
11.	Added code to check compass cal errors against USGS recommendations 
12.	Added code to handle files processed with QBatch. 
13.	Fixed bug with variable names for mean and max depth and max water speed. 
14.	Fixed bug with order of warnings and cautions for system test checks. 

### Changes to QRev from 3.24 to 3.28
1.	Messages are now in a table, sorted with warnings on top, and identified with a symbol and font. 
2.	Clicking on a message will open the associated window, same as clicking on associated button. 
3.	Extrapolation discharge sensitivity table is now referenced to the currently selected fit, rather than to power/power 0.1667. 
4.	Clicking a row in the extrapolation discharge sensitivity table will set the fit to those parameters. 
5.	The compass error from the evaluation of a TRDI ADCP and if available, from RiverSurveyor G3 compass is now shown in the Compass/P/R window. 
6.	The system test window now displays the total number of tests. 
7.	The PT3 test is now decoded and the correlation in lag 3 is checked to ensure that the correlation is less than 15% of the lag 0 correlation. 
8.	A minimum threshold for the boat track vertical velocity filter is set to 0.01 m/s. 
9.	A bug which applied both the magvar and heading offset to all compass data when loading has been fixed. Now the magvar is only applied to the internal compass and the heading offset only applied to the external compass. This is consistent with how it was handled in the Compass/P/R window. 
10.	Label for Google Earth plots was changed to filename only, not including the path. 
11.	Fixed other minor bugs. 
### Changes to QRev since from 3.23 to 3.24 
1.	Fixed compiler issue causing the plot to Google Earth to fail 
2.	Fixed a bug reading longitude data when preceded by a leading zero. 
### Changes to QRev since release of version 3.21 (in chronological order) 
1.	Improved the handling of illegal xml characters in mmt file. 
2.	Added a minimum threshold to the COV QA check for stationary tests. 
3.	Changed the QA check for number of valid ensembles to a duration based check for stationary moving-bed test. 
4.	Fixed bug causing edges GUI not to update with changes to table. 
5.	Added a button to copy comments from the view comments window so they could be pasted in another application. 
6.	Changed Display Units buttons to Options and created an Options window for units and save all or save checked only. 
7.	Added an icon button to main window for uncheck all. 
8.	Change version to 3.22. 
9.	Fixed bug in when selecting an extrapolation fit where numerical storage prevented 0.1 = 0.1 	 
10.	Fixed issue with RSL revision numbers which need to be 2 digits (02 not 2). 
11.	Fixed issue with UTC time from GGA which contained an invalid character causing the str2double function resulting in NaN. 
12.	Added fix for invalid prefPath from corrupt AppData/Local/QRev 
13.	Added code to reset the close option from extrap to the main window when extrap is closed. 
14.	Added code to compute the edge velocity using the full profile assuming a 1/6th power fit to estimate the unmeasured portions of the profile. 
15.	Fixed bug associated with changing all moving-bed tests to manual. 
16.	Added new message when moving-bed tests are selected manually. 
17.	Fixed issue with moving-bed tests when data were collected in language other than English. 
18.	Change version to 3.23 
### Changes in QRev from 3.12 to 3.21 
1.	Update help to add pdf file which can be searched. 
2.	Fixed bug when plotting multiple transects with magnetic data in the Compass/P/R window. 
3.	Fixed bug with transect name display when some transects were not checked in GPS window.  
4.	Fixed bug causing Use in main table to be shown in red when there were no errors. 
5.	Fixed bug checking for invalid edge ensembles due to excluded distance. 
6.	Fixed bug when using up arrow in Edge window. 
7.	Fixed bug in xml output for change in speed of sound. 
8.	Fixed crash when loading transect with only 1 ensemble. 
9.	Updated use of arrow keys in tables to avoid table and plots getting out of synch when arrow keys were pressed too quickly. 
10.	Added point marker to vertical beam in depth plots. 
11.	Modified code to make buttons inactive if no transects are checked. 
12.	Added EDI interface for Equal Discharge Increment sampling 
13.	In the extrap window, added message to user that they need to set Fit to manual if the want to use an automatically opitimized fit but they have change the threshold, subsection, or data type. 
### Changes in QRev from version 3.10 to 3.12 
1.	Fixed bug if number of unchecked transects was greater than number of checked 
2.	Fixed bug where comments on uncertainty table were not being saved 
3.	Fixed issue with edge distance check using all transects rather than just checked transects 
4.	Fixed bug where temperature messages were based on all transects rather than just the checked transects 
5.	Fixed bug where magError and GPS heading were saved as column vector rather than row vector 
6.	Fixed bug where max and min pitch and roll limits were not set for G2 compass, now set to nan 
7.	Improved scaling for magError and pitch and roll, 2) linked x axes of top and bottom plots 
8.	Added code to add qTotalCaution to older QRev files 
9.	Fixed bug when there is no pitch and roll data (old SonTek files) 
10.	Fixed bug when selecting use when moving-bed test is not user valid 
11.	Fixed bug when loading QRev files from 2.9x by adding code to create the qTotalCaution field 
12.	Fixed bug when G2 compass was processed with current RSL resulting in Compass pitch and roll limits set to large number 
13.	Added version numbers to popup when loading older QRev file 
14.	kml Google earth file now plots the full transect filename 
15.	Added a minimum threshold to the bottom track error velocity automatic filter 
16.	Fixed bug interpolating depths for lost ensembles 
17.	Fixed bug preventing automatic excluded distance for RioPro 
18.	Fixed bug graphing of invalid data when excluded distance is set 
19.	Fixed bug plotting data when all data are invalid 
20.	Fixed bug applying user specified edge Q in RiverSurveyor Live 
21.	Fixed bug when no station name or number was pro

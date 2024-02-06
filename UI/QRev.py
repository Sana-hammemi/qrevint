import copy
import ctypes
import getpass
import json
import multiprocessing as mp
import os
import shutil
import sys
import webbrowser
from contextlib import contextmanager
from datetime import datetime

import numpy as np
import scipy.io as sio
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QRegExp, pyqtSignal
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import AutoLocator

import UI.QRev_gui as QRev_gui
from Classes import __qrev_version__, __company__, myappid, __app__
from Classes.CoordError import CoordError
from Classes.Measurement import Measurement
from Classes.MovingBedTests import MovingBedTests
from Classes.Oursin import Oursin
from Classes.Python2Matlab import Python2Matlab
from Classes.Sensors import Sensors
from Classes.TransectData import TransectData
from Classes.MMT_TRDI import MMTtrdi
from Classes.createconfig import Config
from Classes.stickysettings import StickySettings as SSet
from MiscLibs.common_functions import (
    convert_temperature,
    units_conversion,
    sfrnd,
    dateformat,
)
from UI.AdvGraphs import AdvGraphs
from UI.AxesScale import AxesScale
from UI.BoatSpeed import BoatSpeed
from UI.Comment import Comment
from UI.DischargeTS import DischargeTS
from UI.Disclaimer import Disclaimer
from UI.Draft import Draft
from UI.EdgeDist import EdgeDist
from UI.EdgeEns import EdgeEns
from UI.EdgeType import EdgeType
from UI.ExtrapPlot import ExtrapPlot
from UI.HOffset import HOffset
from UI.HSource import HSource
from UI.HeadingTS import HeadingTS
from UI.MagVar import MagVar
from UI.MapTrack import Maptrack
from UI.MplCanvas import MplCanvas
from UI.OpenMeasurementDialog import OpenMeasurementDialog
from UI.Options import Options
from UI.PRTS import PRTS
from UI.Rating import Rating
from UI.SOSSource import SOSSource
from UI.Salinity import Salinity
from UI.ShipTrack import Shiptrack
from UI.StartEdge import StartEdge
from UI.StationaryGraphs import StationaryGraphs
from UI.TempSource import TempSource
from UI.TemperatureTS import TemperatureTS
from UI.Transects2Use import Transects2Use
from UI.ULollipopPlot import ULollipopPlot
from UI.UMeasQ import UMeasQ
from UI.UMeasurement import UMeasurement

# from UI.WTContour import WTContour
from UI.selectFile import SaveDialog
from UI.PDFSummaryReport import Report

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# if there is a splash screen close it
try:
    import pyi_splash

    pyi_splash.close()
except:
    pass


class QRev(QtWidgets.QMainWindow, QRev_gui.Ui_MainWindow):
    """This the primary class controlling the user interface which then
     controls the computational code.

    Attributes
    ----------
    meas: Measurement
        Object of Measurement class
    checked_transects_idx: list
        List of transect indices to be used in the discharge computation
    h_external_valid: bool
        Indicates if external heading is included in data
    main_initialized: bool
        Indicates if tab UI have been initialized
    systest_initialized: bool
        Indicates if tab UI have been initialized
    compass_pr_initialized: bool
        Indicates if tab UI have been initialized
    tempsal_initialized: bool
        Indicates if tab UI have been initialized
    mb_initialized: bool
        Indicates if tab UI have been initialized
    bt_initialized: bool
        Indicates if tab UI have been initialized
    gps_initialized: bool
        Indicates if tab UI have been initialized
    depth_initialized: bool
        Indicates if tab UI have been initialized
    wt_initialized: bool
        Indicates if tab UI have been initialized
    extrap_initialized: bool
        Indicates if tab UI have been initialized
    edges_initialized: bool
        Indicates if tab UI have been initialized
    adv_graph_initialized: bool
        Indicates if tab UI have been initialized
    transect_row: int
        Index of row currently selected for display
    change: bool
        Indicates data has changed and the main tab will need to be updated
    settingsFile: str
        Filename for settings that carryover between sessions
    sticky_settings: SSet
        Object of StickySettings class
    units: dict
        Dictionary containing units coversions and labels for length, area,
        velocity, and discharge
    save_stylesheet: bool
        Indicates whether to save a stylesheet with the measurement
    icon_caution: QtGui.QIcon
        Caution icon
    icon_warning: QtGui.QIcon
        Warning icon
    icon_good: QtGui.QIcon
        Good icon
    icon_allChecked: QtGui.QIcon
        Checked icon
    icon_unChecked: QtGui.QIcon
        Unchecked icon
    save_all: bool
        Indicates if all transects should be save (True) or only the checked
        transects (False)
    QRev_version: str
        QRev version number
    current_tab: str
        Name of currently viewed tab
    transect_row: int
        Row index of selected transect
    figs: list
        List of figure objects
    canvases: list
        List of canvas objects
    toolbars: list
        List of toolbar objects
    font_bold: QtGui.QFont
        Bold font
    font_normal: QtGui.QFont
        Normal font
    mb_row_selected: int
        Moving-bed test index to selected
    mb_row: int
        Moving-bed test to plot
    transect: TransectData
        Temporary storage to pass selected transect
    invalid_bt: np.array(bool)
        Array to facilitate sharing of invalid bottom track among some methods
    invalid_gps: np.array(bool)
        Array to facilitate sharing of invalid gps data among some methods
    invalid_wt: np.array(bool)
        Array to facilitate sharing of invalid water track data among some
         methods
    wt_max_limit: float
        Maximum water speed to allow consistent scaling of color contour graphs
         on same tab
    extrap_meas: Measurement
        Copy of measurement to allow resetting of changes made on the extrap
        tab
    start_bank: str
        Start bank for selected transect used in graphics methods
    idx: int
        Index of selected transect or measurement used in extrap tab
    edi_results: dict
        Dictionary of edi computed data
    groupings: list
        List of transect groupings used with interface with RIVRS
    group_idx: int
        Index to grouping being processed
    main_shiptrack_canvas: MplCanvas
        Shiptrack canvas for main tab
    main_shiptrack_toolbar: NavigationToolbar
        Shiptrack toolbar for main tab
    main_shiptrack_fig: ShipTrack
        Shiptrack figure for main tab
    main_wt_contour_canvas: MplCanvas
        Color contour canvas for main tab
    main_wt_contour_fig: AdvGraphs
        Color contour figure for main tab
    main_wt_contour_toolbar: NavigationToolbar
        Color contour toolbar for main tab
    main_extrap_canvas: MplCanvas
        Extrapolation canvas for main tab
    main_extrap_toolbar: NavigationToolbar
        Extrapolation toolbar for main tab
    main_extrap_fig: ExtrapPlot
        Extrapolation figure for main tab
    main_discharge_canvas: MplCanvas
        Discharge time series canvas for main tab
    main_discharge_toolbar: NavigationToolbar
        Discharge time series toolbar for main tab
    main_discharge_fig: DischargeTS
        Discharge time series figure for main tab
    heading_canvas: MplCanvas
        Heading time series canvas
    heading_toolbar: NavigationToolbar
        Heading time series toolbar
    heading_fig: HeadingTS
        Heading time series figure
    pr_canvas: MplCanvas
        Pitch and roll time series canvas
    pr_toolbar: NavigationToolbar
        Pitch and roll time series toolbar
    pr_fig: PRTS
        Pitch and roll time series figure
    tts_canvas: MplCanvas
        Temperature time series canvas
    tts_toolbar: NavigationToolbar
        Temperature time seriex toolbar
    tts_fig: TemperatureTS
        Temperature time series figure
    mb_shiptrack_canvas: MplCanvas
        Moving-bed test shiptrack canvas
    mb_shiptrack_toolbar: NavigationToolbar
        Moving-bed test shiptrack toolbar
    mb_shiptrack_fig: ShipTrack
        Moving-bed test shiptrack figure
    mb_ts_canvas: MplCanvas
        Moving-bed time series canvas
    mb_ts_toolbar: NavigationToolbar
        Moving-bed time seris toolbar
    mb_ts_fig: BoatSpeed, StationaryGraphs
        Moving-bed time series for loop and stationary tests
    bt_shiptrack_canvas: MplCanvas
        Bottom track shiptrack canvas
    bt_shiptrack_toolbar: NavigationToolbar
        Bottom track shiptrack toolbar
    bt_shiptrack_fig: ShipTrack
        Bottom track shiptrack figure
    bt_ts_canvas: MplCanvas
        Bottom track filter time series canvas
    bt_ts_toolbar: NavigationToolbar
        Bottom track filter time series toolbar
    bt_ts_fig: AdvGraphs
        Bottom track filters time series figure
    gps_shiptrack_canvas: MplCanvas
        GPS shiptrack canvas
    gps_shiptrack_toolbar: NavigationToolbar
        GPS shiptrack toolbar
    gps_shiptrack_fig: ShipTrack
        GPS shiptrack figure
    gps_ts_canvas: MplCanvas
        GPS filters time series canvases
    gps_ts_toolbar: NavigationToolbar
        GPS filters time series toolbar
    gps_ts_fig: AdvGraphs
        GPS filters times series figure
    gps_bt_shiptrack_canvas: MplCanvas
        GPS - BT shiptrack canvas
    gps_bt_shiptrack_toolbar: NavigationToolbar
        GPS - BT shiptrack toolbar
    gps_bt_shiptrack_fig: ShipTrack
        GPS - BT shiptrack figure
    gps_bt_speed_canvas: MplCanvas
        GPS - BT time series speed canvas
    gps_bt_speed_toolbar: NavigationToolbar
        GPS - BT time series speed toolbar
    gps_bt_speed_fig: ShipTrack
        GPS - BT time series speed figure
    depth_canvas: MplCanvas
        Depth final cross section canvas
    depth_toolbar: NavigationToolbar
        Depth final cross section toolbar
    depth_fig: AdvGraphs
        Depth final cross section figure
    wt_shiptrack_canvas: MplCanvas
        Water track shiptrack canvas
    wt_shiptrack_toolbar: NavigationToolbar
        Water track shiptrack toolbar
    wt_shiptrack_fig: ShipTrack
        Water track shiptrack figure
    wt_filter_canvas: MplCanvas
        Water track filters graph canvas
    wt_filter_toolbar: NavigationToolbar
        Water track filters graphs toolbar
    wt_filter_fig: AdvGraphs
        Water track filters graph figure
    extrap_canvas: MplCanvas
        Extrapolation canvas
    extrap_toolbar: NavigationToolbar
        Extrapolation toolbar
    extrap_fig: ExtrapPlot
        Extrapolation figure
    left_edge_contour_canvas: MplCanvas
        Left edge color contour canvas
    left_edge_contour_toolbar: NavigationToolbar
        Left edge color contour toolbar
    left_edge_contour_fig: AdvGraphs
        Left edge color contour figure
    right_edge_contour_canvas: MplCanvas
        Right edge color contour canvas
    right_edge_contour_toolbar: NavigationToolbar
        Right edge color contour toolbar
    right_edge_contour_fig: AdvGraphs
        Right edge color contour figure
    left_edge_st_canvas: MplCanvas
        Left edge shiptrack canvas
    left_edge_st_toolbar: NavigationToolbar
        Left edge shiptrack toolbar
    left_edge_st_fig: ShipTrack
        Left edge shiptrack figure
    right_edge_st_canvas: MplCanvas
        Right edge shiptrack canvas
    right_edge_st_toolbar: NavigationToolbar
        Right edge shiptrack toolbar
    right_edge_st_fig: ShipTrack
        Right edge shiptrack figure
    uncertainty_meas_q_canvas: MplCanvas
        Uncertainty measured discharge canvas
    uncertainty_meas_q_fig: UMeasQ
        Uncertainty measured discharge figure
    uncertainty_meas_q_toolbar: NavigationToolbar
        Uncertainty measured discharge toolbar
    uncertainty_measurement_canvas: MplCanvas
        Uncertainty measurement canvas
    uncertainty_measurement_fig: UMeasurement
        Uncertainty measurement figure
    uncertainty_measurement_toolbar: NavigationToolbar
        Uncertainty measurement toolbar
    adv_graph_canvas: MplCanvas
        Advanced graphics canvas
    adv_graph_fig: AdvGraphs
        Advanced graphics figure
    adv_graph_toolbar: NavigationToolbar
        Advanced graphics toolbar
    rating_prompt: bool
        Indicates that the user should be prompted to rate the measurement
        when saving
    use_weighted: bool
        Indicates if the discharge weighted medians should be used to determine
         the extrapolation
    agreement: bool
        Indicates that the user has agreed to the disclaimer and license
    show_below_sl: bool
        Advanced plots show data below sidelobe cutoff if available.
    adv_graph_types: list
        List of available graphs
    sc_bt: QtWidgets.QShortcut
        Shortcut to set BT reference
    sc_weighted: QtWidgets.QShortcut
        Shortcut to toggle discharge weighted extrapolation
    sc_options: QtWidgets.QShortcut
        Shortcut to open Options dialog
    sc_comment: QtWidgets.QShortcut
        Shortcut to open Comments dialog
    sc_select_transects: QtWidgets.QShortcut
        Shortcut to open select transects dialog
    sc_save: QtWidgets.QShortcut
        Shortcut to save file
    sc_x_time: QtWidgets.QShortcut
        Shortcut to change x-axis to time
    sc_x_length: QtWidgets.QShortcut
        Shortcut to change x-axis to length
    sc_x_ensembles: QtWidgets.QShortcut
        Shortcut to change x-asix to ensembles
    sc_advanced: QtWidgets.QShortcut
        Shortcut to show data below sidelobe
    sc_gga: QtWidgets.QShortcut
        Shortcut to set gga reference
    sc_vtg: QtWidgets.QShortcut
        Shortcut to set vtg reference
    path: str
        Path to loaded data file(s)
    xs_export: bool
        Indicates that the mean cross-section should be computed and included
        the XML when saving
    show_map: bool
        Indicates if the MAP tab should be shown and the MAP computed
    gps_quality_threshold: int
        Sets the threshold for which the GPS quality must equal to or greater than
    """

    handle_args_trigger = pyqtSignal()
    gui_initialized = False
    command_arg = ""

    def __init__(self, parent=None, groupings=None, data=None, caller=None):
        """Initializes the QRev class and sets up the user interface.

        Parameters
        ----------
        parent: QWidget
            Parent object
        groupings: list
            List of lists containing the transect indices that make up
            individual measurements
        data: Measurement
            Object of Measurement class
        caller: object
            Calling object, could be RIVRS
        """
        super(QRev, self).__init__(parent)
        self.setupUi(self)

        # Set window title
        self.setWindowTitle(__qrev_version__)

        qrev_icon = self.get_icon()

        if os.path.exists(qrev_icon):
            self.setWindowIcon(QtGui.QIcon(qrev_icon))

        self.version = __qrev_version__
        if "Int" in __qrev_version__:
            self.set_qrevint_ui()

        show_disclaimer = False

        # Disable ability to hide toolbar
        self.toolBar.toggleViewAction().setEnabled(False)

        # Get agency optional settings
        options_file = os.path.join(os.getcwd(), "QRev.cfg")

        if os.path.exists(options_file) is False:
            config = Config()
            if __company__ == "USGS":
                config.export_config()
            else:
                config.export_international_config()

            self.popup_message(
                self.tr(
                    "QRev.cfg was not found so a default configuration "
                    "file was created. This default configuration may not "
                    "comply with your agency standards. Obtain an approved "
                    "QRev.cfg before final processing of your measurement."
                )
            )

        # Read json into dictionary
        try:
            with open(options_file, "r") as f:
                self.agency_options = json.load(f)
        except json.decoder.JSONDecodeError:
            self.popup_message(
                self.tr(
                    "QRev.cfg could not be read due a formatting error. "
                    "A default configuration file will be created that might "
                    "not match your agency's policy."
                )
            )

            config = Config()
            config.export_config()
            with open(options_file, "r") as f:
                self.agency_options = json.load(f)

            # sys.exit()

        # Setting file for settings to carry over from one session to the next
        self.settingsFile = "QRev_Settings"
        # Create settings object which contains the default values from
        # previous use
        self.sticky_settings = SSet(self.settingsFile)

        if "XAxis" in self.sticky_settings.settings:
            self.x_axis_type = self.sticky_settings.get("XAxis")
        else:
            self.x_axis_type = "E"
            self.sticky_settings.new("XAxis", "E")

        # Set units based on previous session or default to English
        if "Units" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: Units parameter not found."))
            sys.exit()
        if "show" not in self.agency_options["Units"].keys():
            self.popup_message(self.tr("QRev.cfg Units: show parameter not " "found."))
            sys.exit()
        if "default" not in self.agency_options["Units"].keys():
            self.popup_message(
                self.tr("QRev.cfg Units: default parameter not " "found.")
            )
            sys.exit()
        try:
            if self.agency_options["Units"]["show"]:
                units_id = self.sticky_settings.get("UnitsID")
            else:
                units_id = self.agency_options["Units"]["default"]
            if not units_id:
                self.sticky_settings.set(
                    "UnitsID", self.agency_options["Units"]["default"]
                )
        except KeyError:
            self.sticky_settings.new("UnitsID", self.agency_options["Units"]["default"])
        self.units = units_conversion(units_id=self.sticky_settings.get("UnitsID"))

        # Save all transects by default
        self.save_all = True

        # Use unweighted medians for extrapolation by default
        if "ExtrapWeighting" not in self.agency_options.keys():
            self.popup_message(
                self.tr("QRev.cfg: ExtrapWeighting parameter not found.")
            )
            sys.exit()
        if "show" not in self.agency_options["ExtrapWeighting"].keys():
            self.popup_message(
                self.tr("QRev.cfg ExtrapWeighting: show parameter not found.")
            )
            sys.exit()
        if "default" not in self.agency_options["ExtrapWeighting"].keys():
            self.popup_message(
                self.tr("QRev.cfg ExtrapWeighting: default parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["ExtrapWeighting"]["show"]:
                wght = self.sticky_settings.get("UseWeighted")
            else:
                wght = self.agency_options["ExtrapWeighting"]["default"]
            self.use_weighted = wght
        except KeyError:
            self.sticky_settings.new(
                "UseWeighted", self.agency_options["ExtrapWeighting"]["default"]
            )
            self.use_weighted = self.agency_options["ExtrapWeighting"]["default"]

        # Use whole measurement or transects for error and vertical velocity
        # filters
        if "FilterUsingMeasurement" not in self.agency_options.keys():
            self.popup_message(
                self.tr("QRev.cfg: FilterUsingMeasurement parameter not found.")
            )
            sys.exit()
        if "show" not in self.agency_options["FilterUsingMeasurement"].keys():
            self.popup_message(
                self.tr("QRev.cfg FilterUsingMeasurement: show parameter not found.")
            )
            sys.exit()
        if "default" not in self.agency_options["FilterUsingMeasurement"].keys():
            self.popup_message(
                self.tr("QRev.cfg FilterUsingMeasurement: default parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["FilterUsingMeasurement"]["show"]:
                use_meas = self.sticky_settings.get("UseMeasurementThresholds")
            else:
                use_meas = self.agency_options["FilterUsingMeasurement"]["default"]
            self.use_measurement_thresholds = use_meas
        except KeyError:
            self.sticky_settings.new(
                "UseMeasurementThresholds",
                self.agency_options["FilterUsingMeasurement"]["default"],
            )
            self.use_measurement_thresholds = self.agency_options[
                "FilterUsingMeasurement"
            ]["default"]

        # Stylesheet setting
        if "SaveStyleSheet" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: SaveStyleSheet parameter not found."))
            sys.exit()
        if "show" not in self.agency_options["SaveStyleSheet"].keys():
            self.popup_message(
                self.tr("QRev.cfg SaveStyleSheet: show parameter not found.")
            )
            sys.exit()
        if "default" not in self.agency_options["SaveStyleSheet"].keys():
            self.popup_message(
                self.tr("QRev.cfg SaveStyleSheet: default parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["SaveStyleSheet"]["show"]:
                ss = self.sticky_settings.get("StyleSheet")
                self.save_stylesheet = ss
            else:
                self.save_stylesheet = self.agency_options["SaveStyleSheet"]["default"]
        except KeyError:
            self.sticky_settings.new(
                "StyleSheet", self.agency_options["SaveStyleSheet"]["default"]
            )
            self.save_stylesheet = self.agency_options["SaveStyleSheet"]["default"]

        # Prompt for user rating
        if "RatingPrompt" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: RatingPrompt parameter not found."))
            sys.exit()
        if "show" not in self.agency_options["RatingPrompt"].keys():
            self.popup_message(
                self.tr("QRev.cfg RatingPrompt: show parameter not found.")
            )
            sys.exit()
        if "default" not in self.agency_options["RatingPrompt"].keys():
            self.popup_message(
                self.tr("QRev.cfg RatingPrompt: default parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["RatingPrompt"]["show"]:
                ss = self.sticky_settings.get("UserRating")
                self.rating_prompt = ss
            else:
                self.rating_prompt = self.agency_options["RatingPrompt"]["default"]
        except KeyError:
            self.sticky_settings.new(
                "UserRating", self.agency_options["RatingPrompt"]["default"]
            )
            self.rating_prompt = self.agency_options["RatingPrompt"]["default"]

        # check xs export setting
        if "ExportCrossSection" not in self.agency_options.keys():
            self.popup_message(
                self.tr("QRev.cfg: ExportCrossSection parameter not found.")
            )
            sys.exit()
        if "show" not in self.agency_options["RatingPrompt"].keys():
            self.popup_message(
                self.tr("QRev.cfg ExportCrossSection: show parameter not found.")
            )
            sys.exit()
        if "default" not in self.agency_options["RatingPrompt"].keys():
            self.popup_message(
                self.tr("QRev.cfg ExportCrossSection: default parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["ExportCrossSection"]["show"]:
                ss = self.sticky_settings.get("XsExport")
                self.xs_export = ss
            else:
                self.xs_export = self.agency_options["ExportCrossSection"]["default"]
        except KeyError:
            self.sticky_settings.new(
                "XsExport", self.agency_options["ExportCrossSection"]["default"]
            )
            self.xs_export = self.agency_options["ExportCrossSection"]["default"]

        # MAP
        if "MAP" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: MAP parameter not found."))
            sys.exit()
        if "show" not in self.agency_options["MAP"].keys():
            self.popup_message(self.tr("QRev.cfg MAP: show parameter not found."))
            sys.exit()
        try:
            self.show_map = self.sticky_settings.get("MAP")
        except KeyError:
            if self.agency_options["MAP"]["show"]:
                self.show_map = True
            else:
                self.show_map = False
            self.sticky_settings.new("MAP", self.show_map)

        if self.show_map == False:
            self.tab_all.removeTab(
                self.tab_all.indexOf(
                    self.tab_all.findChild(QtWidgets.QWidget, "tab_map")
                )
            )

        # Autonomous GPS
        if "AutonomousGPS" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: AutonomousGPS parameter not found."))
            sys.exit()
        if "allow" not in self.agency_options["AutonomousGPS"].keys():
            self.popup_message(
                self.tr("QRev.cfg AutonomousGPS: allow parameter not found.")
            )
            sys.exit()
        if self.agency_options["AutonomousGPS"]["allow"]:
            self.gps_quality_threshold = 1
        else:
            self.gps_quality_threshold = 2

        # Color map
        if "ColorMap" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: ColorMap " "parameter not found."))
            sys.exit()
        if "show" not in self.agency_options["ColorMap"].keys():
            self.popup_message(
                self.tr("QRev.cfg ColorMap: " "show parameter not found.")
            )
            sys.exit()
        if "default" not in self.agency_options["ColorMap"].keys():
            self.popup_message(
                self.tr("QRev.cfg ColorMap: " "default parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["ColorMap"]["show"]:
                ss = self.sticky_settings.get("ColorMap")
                self.color_map = ss
            else:
                self.color_map = self.agency_options["ColorMap"]["default"]
        except KeyError:
            self.sticky_settings.new(
                "ColorMap", self.agency_options["ColorMap"]["default"]
            )
            self.color_map = self.agency_options["ColorMap"]["default"]

        # Uncertainty model
        if "Uncertainty" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: Uncertainty " "parameter not found."))
            sys.exit()
        if "show" not in self.agency_options["Uncertainty"].keys():
            self.popup_message(
                self.tr("QRev.cfg Uncertainty: " "show parameter not found.")
            )
            sys.exit()
        if "default" not in self.agency_options["Uncertainty"].keys():
            self.popup_message(
                self.tr("QRev.cfg Uncertainty: " "default parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["Uncertainty"]["show"]:
                ss = self.sticky_settings.get("Oursin")
                self.run_oursin = ss
            elif self.agency_options["Uncertainty"]["default"] == "Oursin":
                self.run_oursin = True
            else:
                self.run_oursin = False

        except KeyError:
            if self.agency_options["Uncertainty"]["default"] == "Oursin":
                self.run_oursin = True
            else:
                self.run_oursin = False
            self.sticky_settings.new("Oursin", self.run_oursin)

        if self.run_oursin:
            self.tab_all.addTab(self.tab_uncertainty, "Uncertainty")
        else:
            self.tab_all.removeTab(
                self.tab_all.indexOf(
                    self.tab_all.findChild(QtWidgets.QWidget, "tab_uncertainty")
                )
            )

        # Observed no moving-bed
        if "MovingBedObservation" not in self.agency_options.keys():
            self.popup_message(
                self.tr("QRev.cfg: MovingBedObservation parameter not found.")
            )
            sys.exit()
        if "show" not in self.agency_options["MovingBedObservation"].keys():
            self.popup_message(
                self.tr("QRev.cfg: MovingBedObservation: show parameter not found.")
            )
            sys.exit()
        if "default" not in self.agency_options["MovingBedObservation"].keys():
            self.popup_message(
                self.tr("QRev.cfg MovingBedObservation: default parameter not found.")
            )
            sys.exit()

        try:
            if self.agency_options["MovingBedObservation"]["show"]:
                ss = self.sticky_settings.get("AllowNoMB")
                self.allow_observed_no_moving_bed = ss
            else:
                self.allow_observed_no_moving_bed = self.agency_options[
                    "MovingBedObservation"
                ]["default"]
        except KeyError:
            self.sticky_settings.new(
                "AllowNoMB", self.agency_options["MovingBedObservation"]["default"]
            )
            self.allow_observed_no_moving_bed = self.agency_options[
                "MovingBedObservation"
            ]["default"]

        # Check for QA Settings
        if "QA" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: QA parameter not found."))
            sys.exit()
        if "MinTransects" not in self.agency_options["QA"].keys():
            self.popup_message(
                self.tr("QRev.cfg: QA MinTransects parameter " "not found.")
            )
            sys.exit()
        if "MinDuration" not in self.agency_options["QA"].keys():
            self.popup_message(
                self.tr("QRev.cfg QA MinDuration parameter " "not found.")
            )
            sys.exit()

        # SNR 3-beam computations setting
        if "SNR" not in self.agency_options.keys():
            self.popup_message(self.tr("QRev.cfg: SNR parameter not found."))
            sys.exit()
        if "Use3Beam" not in self.agency_options["SNR"].keys():
            self.popup_message(
                self.tr("QRev.cfg: SNR Use3Beam parameter " "not found.")
            )
            sys.exit()

        # Extrapolated speed display option
        if "ExtrapolatedSpeed" not in self.agency_options.keys():
            self.popup_message(
                self.tr("QRev.cfg: ExtrapolatedSpeed parameter not found.")
            )
            sys.exit()
        if "ShowIcon" not in self.agency_options["ExtrapolatedSpeed"].keys():
            self.popup_message(
                self.tr("QRev.cfg: ExtrapolatedSpeed ShowIcon parameter " "not found.")
            )
            sys.exit()

        # Excluded
        # Values not in agency options will be assigned recommended default values
        if "Excluded" not in self.agency_options.keys():
            self.agency_options["Excluded"] = {}
        if "RioPro" not in self.agency_options["Excluded"].keys():
            self.agency_options["Excluded"]["RioPro"] = 0.25
        if "M9" not in self.agency_options["Excluded"].keys():
            self.agency_options["Excluded"]["M9"] = 0.16

        # Left Right Flow Direction Difference
        if "LeftRightFlowDirDiff" not in self.agency_options.keys():
            self.popup_message(
                self.tr("QRev.cfg: LeftRightFlowDirDiff parameter not found.")
            )
            sys.exit()
        if "threshold" not in self.agency_options["LeftRightFlowDirDiff"].keys():
            self.popup_message(
                self.tr("QRev.cfg LeftRightFlowDirDiff: threshold parameter not found.")
            )
            sys.exit()

        # Date format
        if "DateFormat" not in self.agency_options.keys():
            self.popup_message(self.tr("QRevMS.cfg: DateFormat parameter not found."))
            sys.exit()
        if "default" not in self.agency_options["DateFormat"].keys():
            self.popup_message(
                self.tr("QRevMS.cfg DateFormat: default parameter not found.")
            )
            sys.exit()
        if "show" not in self.agency_options["DateFormat"].keys():
            self.popup_message(
                self.tr("QRevMS.cfg DateFormat: show parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["DateFormat"]["show"]:
                ss = self.sticky_settings.get("DateFormat")
                self.date_format = ss
            else:
                self.date_format = dateformat(
                    self.agency_options["DateFormat"]["default"]
                )
        except KeyError:
            self.sticky_settings.new(
                "DateFormat", dateformat(self.agency_options["DateFormat"]["default"])
            )
            self.date_format = dateformat(self.agency_options["DateFormat"]["default"])

        # PDF Summary
        if "PDFSummary" not in self.agency_options.keys():
            self.popup_message(self.tr("QRevMS.cfg: PDFSummary parameter not found."))
            sys.exit()
        if "default" not in self.agency_options["PDFSummary"].keys():
            self.popup_message(
                self.tr("QRevMS.cfg PDFSummary: default parameter not found.")
            )
            sys.exit()
        if "show" not in self.agency_options["PDFSummary"].keys():
            self.popup_message(
                self.tr("QRevMS.cfg PDFSummary: show parameter not found.")
            )
            sys.exit()
        try:
            if self.agency_options["PDFSummary"]["show"]:
                ss = self.sticky_settings.get("PDFSummary")
                self.pdf_setting = ss
            else:
                self.pdf_setting = dateformat(
                    self.agency_options["PDFSummary"]["default"]
                )
        except KeyError:
            self.sticky_settings.new(
                "PDFSummary", self.agency_options["PDFSummary"]["default"]
            )
            self.pdf_setting = dateformat(self.agency_options["PDFSummary"]["default"])

        self.manual_computational_settings = {
            "run_oursin": self.run_oursin,
            "use_measurement_thresholds": self.use_measurement_thresholds,
            "use_weighted": self.use_weighted,
        }

        # Set initial change switch to false
        self.change = False
        self.map_change = False

        # Set the initial tab to the main tab
        self.current_tab = "Main"
        self.transect_row = 0

        # Initialize emtpy tab setting dict
        self.tab_settings = {
            "tab_bt": "Default",
            "tab_wt": "Default",
            "tab_depth": "Default",
            "tab_extrap": "Default",
            "tab_tempsal": "Default",
            "tab_gps": "Default",
        }

        # Connect toolbar button to methods
        self.actionOpen.triggered.connect(self.select_measurement)
        self.actionComment.triggered.connect(self.add_comment)
        self.actionCheck.triggered.connect(self.select_q_transects)
        self.actionBT.triggered.connect(self.set_ref_bt)
        self.actionGGA.triggered.connect(self.set_ref_gga)
        self.actionVTG.triggered.connect(self.set_ref_vtg)
        self.actionOFF.triggered.connect(self.comp_tracks_off)
        self.actionON.triggered.connect(self.comp_tracks_on)
        self.actionOptions.triggered.connect(self.qrev_options)
        self.actionData_Cursor.triggered.connect(self.data_cursor)
        self.actionHome.triggered.connect(self.home)
        self.actionZoom.triggered.connect(self.zoom)
        self.actionPan.triggered.connect(self.pan)
        self.actionGoogle_Earth.triggered.connect(self.plot_google_earth)
        self.actionHelp.triggered.connect(self.help)
        self.actionShow_Extrapolated.triggered.connect(self.show_extrapolated)

        # Initialize lists for figure, canvas, and toolbar references
        self.figs = []
        self.canvases = []
        self.toolbars = []
        self.ui_parents = []
        self.fig_calls = []
        self.map_settings = None
        self.map_current_settings = None
        self.current_axis = None

        # Save figure menu with Right click
        self.figsMenu = QtWidgets.QMenu(self)
        self.figsMenu.addAction("Save figure", self.save_fig)
        self.figsMenu.addAction("Set Axes Limits", self.set_axes)

        # Connect a change in selected tab to the tab manager
        self.tab_all.currentChanged.connect(self.tab_manager)

        # Disable all tabs until data are loaded
        self.tab_all.setEnabled(False)

        # Set tooltips for toolbar icons
        self.actionOpen.setToolTip(self.tr("Open measurement [CNTL-F]"))
        self.actionComment.setToolTip(self.tr("Add comment [CNTL-N]"))
        self.actionCheck.setToolTip(self.tr("Select transects [CNTL-Q]"))
        self.actionBT.setToolTip(self.tr("Set BT as reference [CNTL-B]"))
        self.actionGGA.setToolTip(self.tr("Set GGA as reference [CNTL-G]"))
        self.actionVTG.setToolTip(self.tr("Set VGT as reference [CNTL-V]"))
        self.actionOFF.setToolTip(self.tr("Composite tracks off"))
        self.actionON.setToolTip(self.tr("Composite tracks on"))
        self.actionOptions.setToolTip(self.tr("Options [CNTL-O]"))
        self.actionData_Cursor.setToolTip(self.tr("Data cursor"))
        self.actionHome.setToolTip(self.tr("Reset graphs"))
        self.actionZoom.setToolTip(
            self.tr("Zoom Window (In: Left click, Out: Right click ")
        )
        self.actionPan.setToolTip(self.tr("Pan"))
        self.actionGoogle_Earth.setToolTip(self.tr("Plot transects in Google Earth"))
        self.actionHelp.setToolTip(self.tr("Open help documents."))
        self.actionShow_Extrapolated.setToolTip(self.tr("Show extrapolated speeds"))

        # Disable toolbar icons until data are loaded
        self.actionSave.setDisabled(True)
        self.actionComment.setDisabled(True)
        self.actionCheck.setDisabled(True)
        self.actionBT.setDisabled(True)
        self.actionGGA.setDisabled(True)
        self.actionVTG.setDisabled(True)
        self.actionOFF.setDisabled(True)
        self.actionON.setDisabled(True)
        self.actionOptions.setEnabled(True)
        self.actionGoogle_Earth.setDisabled(True)
        self.actionHome.setDisabled(True)
        self.actionZoom.setDisabled(True)
        self.actionPan.setDisabled(True)
        self.actionData_Cursor.setDisabled(True)
        self.actionShow_Extrapolated.setDisabled(True)

        # Configure bold and normal fonts
        self.font_bold = QtGui.QFont()
        self.font_bold.setBold(True)
        self.font_normal = QtGui.QFont()
        self.font_normal.setBold(False)
        self.message_font = QtGui.QFont()
        self.message_font.setPointSize(12)

        # Setup indicator icons
        self.icon_caution = QtGui.QIcon()
        self.icon_caution.addPixmap(
            QtGui.QPixmap(":/images/24x24/Warning.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )

        self.icon_warning = QtGui.QIcon()
        self.icon_warning.addPixmap(
            QtGui.QPixmap(":/images/24x24/Alert.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )

        self.icon_good = QtGui.QIcon()
        self.icon_good.addPixmap(
            QtGui.QPixmap(":/images/24x24/Yes.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off
        )

        self.icon_allChecked = QtGui.QIcon()
        self.icon_allChecked.addPixmap(
            QtGui.QPixmap(":/images/24x24/check-mark-green.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )

        self.icon_unChecked = QtGui.QIcon()
        self.icon_unChecked.addPixmap(
            QtGui.QPixmap(":/images/24x24/check-mark-orange.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )

        # Intialize attributes
        self.path = ""
        self.checked_transects_idx = []
        self.meas = None
        self.h_external_valid = False
        self.mb_row_selected = 0
        self.transect = None
        self.invalid_bt = None
        self.invalid_gps = None
        self.invalid_wt = None
        self.wt_max_limit = None
        self.extrap_meas = None
        self.start_bank = None
        self.idx = None
        self.edi_results = None
        self.groupings = None
        self.group_idx = None
        self.main_shiptrack_canvas = None
        self.main_shiptrack_toolbar = None
        self.main_shiptrack_fig = None
        self.main_wt_contour_canvas = None
        self.main_wt_contour_fig = None
        self.main_wt_contour_toolbar = None
        self.main_extrap_canvas = None
        self.main_extrap_toolbar = None
        self.main_extrap_fig = None
        self.main_discharge_canvas = None
        self.main_discharge_toolbar = None
        self.main_discharge_fig = None
        self.heading_canvas = None
        self.heading_toolbar = None
        self.heading_fig = None
        self.pr_canvas = None
        self.pr_toolbar = None
        self.pr_fig = None
        self.tts_canvas = None
        self.tts_toolbar = None
        self.tts_fig = None
        self.mb_shiptrack_canvas = None
        self.mb_shiptrack_toolbar = None
        self.mb_shiptrack_fig = None
        self.mb_ts_canvas = None
        self.mb_ts_toolbar = None
        self.mb_ts_fig = None
        self.bt_shiptrack_canvas = None
        self.bt_shiptrack_toolbar = None
        self.bt_shiptrack_fig = None
        self.bt_ts_canvas = None
        self.bt_ts_toolbar = None
        self.bt_ts_fig = None
        self.gps_shiptrack_canvas = None
        self.gps_shiptrack_toolbar = None
        self.gps_shiptrack_fig = None
        self.gps_ts_canvas = None
        self.gps_ts_toolbar = None
        self.gps_ts_fig = None
        self.gps_bt_shiptrack_canvas = None
        self.gps_bt_shiptrack_toolbar = None
        self.gps_bt_shiptrack_fig = None
        self.gps_bt_speed_canvas = None
        self.gps_bt_speed_toolbar = None
        self.gps_bt_speed_fig = None
        self.depth_canvas = None
        self.depth_toolbar = None
        self.depth_fig = None
        self.wt_shiptrack_canvas = None
        self.wt_shiptrack_toolbar = None
        self.wt_shiptrack_fig = None
        self.wt_filter_canvas = None
        self.wt_filter_toolbar = None
        self.wt_filter_fig = None
        self.wt_advanced_canvas = None
        self.wt_advanced_toolbar = None
        self.wt_advanced_fig = None
        self.extrap_canvas = None
        self.extrap_toolbar = None
        self.extrap_fig = None
        self.left_edge_contour_canvas = None
        self.left_edge_contour_toolbar = None
        self.left_edge_contour_fig = None
        self.right_edge_contour_canvas = None
        self.right_edge_contour_toolbar = None
        self.right_edge_contour_fig = None
        self.left_edge_st_canvas = None
        self.left_edge_st_toolbar = None
        self.left_edge_st_fig = None
        self.right_edge_st_canvas = None
        self.right_edge_st_toolbar = None
        self.right_edge_st_fig = None
        self.uncertainty_meas_q_canvas = None
        self.uncertainty_meas_q_fig = None
        self.uncertainty_meas_q_toolbar = None
        self.uncertainty_measurement_canvas = None
        self.uncertainty_measurement_fig = None
        self.uncertainty_measurement_toolbar = None
        self.uncertainty_lollipop_canvas = None
        self.uncertainty_lollipop_fig = None
        self.uncertainty_lollipop_toolbar = None
        self.adv_graph_canvas = None
        self.adv_graph_fig = None
        self.adv_graph_toolbar = None
        self.adv_graph_types = []
        self.map_canvas = None
        self.map_shiptrack_toolbar = None
        self.map_fig = None
        self.map_canvas = None
        self.map_toolbar = None
        self.map_fig = None
        self.current_fig = None
        self.edges_axis_type = "E"
        self.mb_row = 0
        self.show_below_sl = False
        self.plot_extrapolated = False

        # Tab initialization tracking setup
        self.main_initialized = False
        self.systest_initialized = False
        self.compass_pr_initialized = False
        self.tempsal_initialized = False
        self.mb_initialized = False
        self.bt_initialized = False
        self.gps_initialized = False
        self.depth_initialized = False
        self.wt_initialized = False
        self.extrap_initialized = False
        self.edges_initialized = False
        self.edi_initialized = False
        self.gps_bt_initialized = False
        self.adv_graph_initialized = False
        self.map_initialized = False

        self.setMouseTracking(True)

        # Special commands to ensure proper operation on Windows 10
        if QtCore.QSysInfo.windowsVersion() == QtCore.QSysInfo.WV_WINDOWS10:
            self.setStyleSheet(
                "QHeaderView::section{"
                "border-top: 0px solid #D8D8D8;"
                "border-left: 0px solid #D8D8D8;"
                "border-right: 1px solid #D8D8D8;"
                "border-bottom: 1px solid #D8D8D8;"
                "background-color: white;"
                "padding:4px;"
                "}"
                "QTableCornerButton::section{"
                "border-top: 0px solid #D8D8D8;"
                "border-left: 0px solid #D8D8D8;"
                "border-right: 1px solid #D8D8D8;"
                "border-bottom: 1px solid #D8D8D8;"
                "background-color: white;"
                "}"
            )

        # Used for command line interface
        self.gui_initialized = True

        # If called by RIVRS setup QRev for automated group processing
        if caller is not None:
            self.caller = caller
            self.split_initialization(groupings=groupings, data=data)
            self.actionSave.triggered.connect(self.split_save)
            self.config_gui()
            self.change = True
            self.map_change = True
            self.tab_manager(tab_idx=0)
            self.set_tab_color()
            self.processed_data = []
            self.processed_transects = []
        else:
            self.caller = None
            self.actionSave.triggered.connect(self.save_measurement)
            self.sc_open = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+F"), self)
            self.sc_open.activated.connect(self.select_measurement)

        # Setup shortcuts
        self.sc_bt = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+B"), self)
        self.sc_bt.activated.connect(self.set_ref_bt)
        self.sc_weighted = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        self.sc_weighted.activated.connect(self.set_use_weighted)
        self.sc_options = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        self.sc_options.activated.connect(self.qrev_options)
        self.sc_comment = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.sc_comment.activated.connect(self.add_comment)
        self.sc_select_transects = QtWidgets.QShortcut(
            QtGui.QKeySequence("Ctrl+Q"), self
        )
        self.sc_select_transects.activated.connect(self.select_q_transects)
        self.sc_save = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.sc_save.activated.connect(self.save_measurement)
        self.sc_x_time = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+T"), self)
        self.sc_x_time.activated.connect(self.x_axis_time)
        self.sc_x_length = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self)
        self.sc_x_length.activated.connect(self.x_axis_length)
        self.sc_x_ensembles = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+E"), self)
        self.sc_x_ensembles.activated.connect(self.x_axis_ensemble)
        self.sc_advanced = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+A"), self)
        self.sc_advanced.activated.connect(self.set_show_below_sl)
        self.sc_unmeasured = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+U"), self)
        self.sc_unmeasured.activated.connect(self.show_extrapolated)
        self.sc_gga = None
        self.sc_vtg = None

        # Show QRev maximized on the display
        self.showMaximized()

        # Disclaimer is for QRevInt
        if show_disclaimer:
            try:
                self.agreement = self.sticky_settings.get("Agreement")
                if not self.agreement:
                    self.close()
            except KeyError:
                # Open disclaimer and license
                disclaimer = Disclaimer(self)
                disclaimer_exec = disclaimer.exec_()
                if disclaimer_exec:
                    self.sticky_settings.new("Agreement", True)
                    self.agreement = True
                else:
                    self.agreement = False
                    self.close()
        else:
            self.agreement = True

    @staticmethod
    def get_icon():
        """Returns path to icon

        Returns:
            icon_path: str
        """

        # Code to call sphinx documentation adopted from SurfVelTool

        # Use development-specific settings. Using __file__ path, so it
        # will work when called by other projects using QRev.

        if __company__ == "USGS":
            icon = "QRev.ico"
        else:
            icon = "QRevInt.ico"

        icon_path = ""

        path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "docs",
                "source",
                "assets",
                "files",
                icon,
            )
        )

        if os.path.exists(path):
            icon_path = path

        else:
            # Use production-specific settings
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
            path = os.path.join(base_path, "qrev_files", icon)
            if os.path.exists(path):
                icon_path = path

        return icon_path

    def set_qrevint_ui(self):
        """If QRevInt set background of UI to blue."""

        # Todo fix toolbar color.
        # set main window pallete
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 128))
        brush.setStyle(QtCore.Qt.NoBrush)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 128))
        brush.setStyle(QtCore.Qt.NoBrush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 128))
        brush.setStyle(QtCore.Qt.NoBrush)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.PlaceholderText, brush)
        self.setPalette(palette)

        self.setStyleSheet("QToolBar{background: solid rgb(240, 240, 240)}")

    def set_qrevint_ui(self):
        """If QRevInt set background of UI to blue."""

        # set main window pallete
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 128))
        brush.setStyle(QtCore.Qt.NoBrush)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 128))
        brush.setStyle(QtCore.Qt.NoBrush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 175))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 128))
        brush.setStyle(QtCore.Qt.NoBrush)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.PlaceholderText, brush)
        self.setPalette(palette)

        self.toolBar.setStyleSheet("QToolBar{background: solid rgb(240, 240, 240)}")

    # Toolbar functions
    # =================
    def select_measurement(self):
        """Opens a dialog to allow the user to load measurement file(s) for
        viewing or processing.
        """

        # Open dialog
        select = OpenMeasurementDialog(parent=self)

        # Update sticky_settings
        self.sticky_settings = SSet(self.settingsFile)
        self.path = self.sticky_settings.get("Folder")

        # If a selection is made begin loading
        if len(select.type) > 0:
            self.tab_all.setEnabled(False)

            # Reset computational settings
            self.run_oursin = self.manual_computational_settings["run_oursin"]
            self.use_measurement_thresholds = self.manual_computational_settings[
                "use_measurement_thresholds"
            ]
            self.use_weighted = self.manual_computational_settings["use_weighted"]

            # Load and process Sontek data
            if select.type == "SonTek":
                with self.wait_cursor():
                    # Show folder name in GUI header
                    self.setWindowTitle(__qrev_version__ + ": " + select.pathName)

                    # Create measurement object
                    try:
                        self.meas = Measurement(
                            in_file=select.fullName,
                            source="SonTek",
                            proc_type="QRev",
                            run_oursin=self.run_oursin,
                            use_weighted=self.use_weighted,
                            use_measurement_thresholds=self.use_measurement_thresholds,
                            min_transects=self.agency_options["QA"]["MinTransects"],
                            min_duration=self.agency_options["QA"]["MinDuration"],
                            export_xs=self.xs_export,
                            gps_quality_threshold=self.gps_quality_threshold,
                            snr_3beam_comp=self.agency_options["SNR"]["Use3Beam"],
                            excluded=self.agency_options["Excluded"],
                            water_dir_diff_threshold=self.agency_options[
                                "LeftRightFlowDirDiff"
                            ]["threshold"],
                            date_format=self.date_format,
                        )
                    except CoordError as error:
                        self.popup_message(error.text)

            # Load and process Sontek data
            if select.type == "Nortek":
                with self.wait_cursor():
                    # Show folder name in GUI header
                    self.setWindowTitle(__qrev_version__ + ": " + select.pathName)
                    # Create measurement object
                    self.meas = Measurement(
                        in_file=select.fullName,
                        source="Nortek",
                        proc_type="QRev",
                        run_oursin=self.run_oursin,
                        use_weighted=self.use_weighted,
                        use_measurement_thresholds=self.use_measurement_thresholds,
                        min_transects=self.agency_options["QA"]["MinTransects"],
                        min_duration=self.agency_options["QA"]["MinDuration"],
                        export_xs=self.xs_export,
                        gps_quality_threshold=self.gps_quality_threshold,
                        water_dir_diff_threshold=self.agency_options[
                            "LeftRightFlowDirDiff"
                        ]["threshold"],
                        date_format=self.date_format,
                    )

            # Load and process TRDI data
            elif select.type == "TRDI":
                with self.wait_cursor():
                    # Show mmt filename in GUI header
                    self.setWindowTitle(__qrev_version__ + ": " + select.fullName[0])
                    # Create measurement object
                    self.meas = Measurement(
                        in_file=select.fullName[0],
                        source="TRDI",
                        proc_type="QRev",
                        checked=select.checked,
                        run_oursin=self.run_oursin,
                        use_weighted=self.use_weighted,
                        use_measurement_thresholds=self.use_measurement_thresholds,
                        min_transects=self.agency_options["QA"]["MinTransects"],
                        min_duration=self.agency_options["QA"]["MinDuration"],
                        export_xs=self.xs_export,
                        gps_quality_threshold=self.gps_quality_threshold,
                        excluded=self.agency_options["Excluded"],
                        water_dir_diff_threshold=self.agency_options[
                            "LeftRightFlowDirDiff"
                        ]["threshold"],
                        date_format=self.date_format,
                    )

            # Load QRev data
            elif select.type == "QRev":
                # Show QRev filename in GUI header
                self.setWindowTitle(__qrev_version__ + ": " + select.fullName[0])
                mat_data = sio.loadmat(
                    select.fullName[0], struct_as_record=False, squeeze_me=True
                )

                message = (
                    "Would you like to: <br><br>"
                    + "<b>View</b> the measurement as saved <br>"
                    + "<I>New quality checks will be "
                    "applied. </I><br><br>" + "<b>Reprocess</b> the measurement "
                    "using all the <br>"
                    + "current settings (extrapolation, filters,<br>"
                    + "uncertianty model, and the latest "
                    "algorithms).<br><br>" + "NOTE: Any changes will reprocess "
                    "the file  <br> " + "using the latest QRev algorithms, "
                    "however,  <br>" + "identifying ping type from older "
                    "QRev files  <br>"
                    + "cannot be done for TRDI ADCPs. <br>"
                    + "<I>To identify the ping type for TRDI "
                    "data you <br> " + "must load the raw data files.</I><<br><br>"
                )
                message = self.tr(message)
                msg_box = QtWidgets.QMessageBox()
                msg_box.setIcon(QtWidgets.QMessageBox.Question)
                msg_box.setWindowTitle("View or Reprocess")
                msg_box.setFont(self.message_font)
                msg_box.setText(message)
                view_btn = msg_box.addButton(
                    self.tr("View"), QtWidgets.QMessageBox.NoRole
                )
                reprocess_btn = msg_box.addButton(
                    self.tr("Reprocess"), QtWidgets.QMessageBox.YesRole
                )

                msg_box.exec_()
                # Process QRev data
                with self.wait_cursor():
                    if msg_box.clickedButton() == view_btn:
                        self.meas = Measurement(
                            in_file=mat_data,
                            source="QRev",
                            proc_type="None",
                            export_xs=self.xs_export,
                            gps_quality_threshold=self.gps_quality_threshold,
                        )
                    elif msg_box.clickedButton() == reprocess_btn:
                        self.meas = Measurement(
                            in_file=mat_data,
                            source="QRev",
                            proc_type="QRev",
                            run_oursin=self.run_oursin,
                            use_weighted=self.use_weighted,
                            use_measurement_thresholds=self.use_measurement_thresholds,
                            min_transects=self.agency_options["QA"]["MinTransects"],
                            min_duration=self.agency_options["QA"]["MinDuration"],
                            export_xs=self.xs_export,
                            gps_quality_threshold=self.gps_quality_threshold,
                            water_dir_diff_threshold=self.agency_options[
                                "LeftRightFlowDirDiff"
                            ]["threshold"],
                            date_format=self.date_format,
                        )

                # Settings based on measurement settings
                self.use_weighted = self.meas.use_weighted
                self.run_oursin = self.meas.run_oursin
                self.use_measurement_thresholds = self.meas.use_measurement_thresholds

                # Oursin uncertainty model
                if self.run_oursin:
                    self.tab_all.addTab(self.tab_uncertainty, "Uncertainty")
                else:
                    self.tab_all.removeTab(
                        self.tab_all.indexOf(
                            self.tab_all.findChild(QtWidgets.QWidget, "tab_uncertainty")
                        )
                    )

            if self.meas is not None:
                # Identify transects to be used in discharge computation
                self.checked_transects_idx = Measurement.checked_transects(self.meas)
                if len(self.checked_transects_idx) > 0:
                    with self.wait_cursor():
                        # Determine if external heading is included in the data
                        self.h_external_valid = Measurement.h_external_valid(self.meas)

                        # Initialize GUI
                        self.tab_settings = {
                            "tab_bt": "Default",
                            "tab_wt": "Default",
                            "tab_depth": "Default",
                            "tab_extrap": "Default",
                            "tab_tempsal": "Default",
                            "tab_gps": "Default",
                        }
                        self.transect_row = 0
                        self.config_gui()
                        self.change = True
                        self.map_change = True
                        self.tab_manager(tab_idx=0, subtab_idx=0)
                        # self.set_tab_color()
                else:
                    self.transect_row = 0
                    self.config_gui()
                    self.change = True
                    self.map_change = True
                    self.tab_manager(tab_idx=0, subtab_idx=0)

    def save_measurement(self):
        """Save measurement in Matlab format."""
        if len(self.checked_transects_idx) > 0:
            if self.rating_prompt:
                # Intialize dialog
                rating_dialog = Rating(self)
                if self.run_oursin:
                    uncertainty = self.meas.oursin.u_measurement_user["total_95"][0]
                else:
                    uncertainty = self.meas.uncertainty.total_95_user

                if np.isnan(uncertainty):
                    rating_dialog.uncertainty_value.setText("N/A")
                else:
                    rating_dialog.uncertainty_value.setText(
                        "{:4.1f}".format(uncertainty)
                    )

                if self.meas.user_rating in ["Not Rated", ""]:
                    if uncertainty < 3:
                        rating_dialog.rb_excellent.setChecked(True)
                    elif uncertainty < 5.01:
                        rating_dialog.rb_good.setChecked(True)
                    elif uncertainty < 8.01:
                        rating_dialog.rb_fair.setChecked(True)
                    else:
                        rating_dialog.rb_poor.setChecked(True)

                elif "Excellent" in self.meas.user_rating:
                    rating_dialog.rb_excellent.setChecked(True)
                elif "Good" in self.meas.user_rating:
                    rating_dialog.rb_good.setChecked(True)
                elif "Fair" in self.meas.user_rating:
                    rating_dialog.rb_fair.setChecked(True)
                elif "Poor" in self.meas.user_rating:
                    rating_dialog.rb_poor.setChecked(True)

                rating_entered = rating_dialog.exec_()

                # If data entered.
                with self.wait_cursor():
                    if rating_entered:
                        if rating_dialog.rb_excellent.isChecked():
                            rating = self.tr("Excellent")
                        elif rating_dialog.rb_good.isChecked():
                            rating = self.tr("Good")
                        elif rating_dialog.rb_fair.isChecked():
                            rating = self.tr("Fair")
                        else:
                            rating = self.tr("Poor")

                # Create default file name
                if rating_entered:
                    self.meas.user_rating = rating
                    self.set_user_rating()

            save_file = SaveDialog(parent=self)

            if len(save_file.full_Name) > 0:
                # Add comment when saving file
                time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_name = getpass.getuser()
                discharge = Measurement.mean_discharges(self.meas)
                uncertainty = "N/A"
                if self.run_oursin:
                    if not np.isnan(self.meas.oursin.u_measurement_user["total_95"][0]):
                        uncertainty = "{:4.1f}".format(
                            self.meas.oursin.u_measurement_user["total_95"][0]
                        )
                else:
                    if not np.isnan(self.meas.uncertainty.total_95_user):
                        uncertainty = "{:4.1f}".format(
                            self.meas.uncertainty.total_95_user
                        )
                text = (
                    "["
                    + time_stamp
                    + ", "
                    + user_name
                    + "]: File Saved Q = "
                    + "{:8.2f}".format(discharge["total_mean"] * self.units["Q"])
                    + " "
                    + self.units["label_Q"][1:-1]
                    + " (Uncertainty: "
                    + uncertainty
                    + "%)"
                )
                self.meas.comments.append(text)
                self.comments_tab()

                # Save PDF Summary Report
                create_pdf = False
                if self.pdf_setting == "Always":
                    create_pdf = True

                if self.pdf_setting == "Prompt":
                    reply = QtWidgets.QMessageBox.question(
                        self,
                        "PDF Summary",
                        "Would you like to save a PDF Report Summary",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                        QtWidgets.QMessageBox.No,
                    )
                    if reply == QtWidgets.QMessageBox.Yes:
                        create_pdf = True

                with self.wait_cursor():
                    if create_pdf:
                        try:
                            pdf_fullName = save_file.full_Name[:-4] + ".pdf"
                            pdf = Report(pdf_fullName, self)
                            pdf.create()
                        except:
                            self.popup_message(self.tr("Error saving PDF file."))

                    # Save data in Matlab format
                    if self.save_all:
                        Python2Matlab.save_matlab_file(
                            self.meas, save_file.full_Name, __qrev_version__
                        )
                    else:
                        Python2Matlab.save_matlab_file(
                            self.meas,
                            save_file.full_Name,
                            __qrev_version__,
                            checked=self.checked_transects_idx,
                        )

                    # Save xml file
                    self.meas.xml_output(save_file.full_Name[:-4] + ".xml")

                    # Save stylesheet in measurement folder
                    if self.save_stylesheet:
                        meas_folder, _ = os.path.split(save_file.full_Name)
                        dest = os.path.join(meas_folder, "QRevStylesheet.xsl")

                        if self.units["ID"] == "SI":
                            stylesheet = "QRevStylesheet_si.xsl"
                        else:
                            stylesheet = "QRevStylesheet_english.xsl"

                        self.export_stylesheet(stylesheet, dest)

                # Notify user save is complete
                QtWidgets.QMessageBox.about(
                    self,
                    self.tr("Save"),
                    self.tr("Files (*_QRev.mat and " "*_QRev.xml) have been " "saved."),
                )

                self.uncertainty_table()
        else:
            # Notify user save is complete
            QtWidgets.QMessageBox.warning(
                self,
                self.tr("Save"),
                self.tr("No transects are selected." " Save cancelled."),
            )

    def add_comment(self):
        """Add comment triggered by actionComment"""

        if self.meas is not None:
            # Initialize comment dialog
            tab_name = self.tab_all.tabText(self.tab_all.currentIndex())
            comment = Comment(tab_name)
            comment_entered = comment.exec_()

            # If comment entered and measurement open, save comment,
            # and update comments tab.
            if comment_entered:
                if self.meas is not None:
                    self.meas.comments.append(comment.text_edit_comment.toPlainText())
                self.change = True
                self.map_change = True
                self.update_comments()

    def select_q_transects(self):
        """Initializes a dialog to allow user to select or deselect
        transects to include in the measurement.
        """

        if self.meas is not None:
            # Open dialog
            transects_2_use = Transects2Use(self)
            transects_selected = transects_2_use.exec_()
            selected_transects = []

            # Identify currently selected transects
            if transects_selected:
                with self.wait_cursor():
                    for row in range(transects_2_use.tableSelect.rowCount()):
                        if (
                            transects_2_use.tableSelect.item(row, 0).checkState()
                            == QtCore.Qt.Checked
                        ):
                            selected_transects.append(row)

                    # Store selected transect indices
                    self.checked_transects_idx = selected_transects
                    if len(self.checked_transects_idx) > 0:
                        # Update measurement based on the currently selected
                        # transects
                        Measurement.selected_transects_changed(
                            self.meas, self.checked_transects_idx
                        )

                        # Update the transect select icon on the toolbar
                        self.update_toolbar_trans_select()

                        # Update display
                        self.transect_row = 0
                        self.config_gui()
                        self.change = True
                        self.map_change = True
                        self.tab_manager()

                if len(self.checked_transects_idx) == 0:
                    # Notify user
                    QtWidgets.QMessageBox.warning(
                        self, "Select", "No transects are " "selected. "
                    )
                    self.update_toolbar_trans_select()

    def set_ref_bt(self):
        """Changes the navigation reference to Bottom Track"""

        if self.meas is not None:
            with self.wait_cursor():
                # Get all current settings
                settings = Measurement.current_settings(self.meas)
                old_discharge = self.meas.discharge
                # Change NavRef setting to selected value
                settings["NavRef"] = "BT"
                # Update the measurement and GUI
                Measurement.apply_settings(self.meas, settings)
                self.update_toolbar_nav_ref()
                self.change = True
                self.map_change = True
                self.tab_manager(old_discharge=old_discharge)

    def set_ref_gga(self):
        """Changes the navigation reference to GPS GGA"""

        if self.meas is not None:
            # Get all current settings
            settings = Measurement.current_settings(self.meas)
            invalid_gga_idx = []
            # Check if gga quality is fine
            for idx in self.checked_transects_idx:
                if self.meas.transects[idx].boat_vel.gga_vel is not None:
                    if np.all(
                        self.meas.transects[idx].gps.diff_qual_ens[
                            ~np.isnan(self.meas.transects[idx].gps.diff_qual_ens)
                        ]
                        < settings["ggaDiffQualFilter"]
                    ):
                        invalid_gga_idx.append(idx)
            if len(invalid_gga_idx) > 0:
                error_gga = QtWidgets.QMessageBox()
                error_gga.setIcon(QtWidgets.QMessageBox.Warning)
                error_gga.setWindowTitle(self.tr("GGA Error"))
                error_gga.setText(
                    self.tr(
                        f"GGA quality is too low for transects {', '.join(map(str, invalid_gga_idx))}. "
                        f"\nPlease change settings or selected transects."
                    )
                )
                error_gga.setStandardButtons(QtWidgets.QMessageBox.Ok)
                error_gga.exec()
            else:
                with self.wait_cursor():
                    old_discharge = self.meas.discharge
                    # Change NavRef to selected setting
                    settings["NavRef"] = "GGA"
                    # Update measurement and GUI
                    Measurement.apply_settings(self.meas, settings)
                    self.update_toolbar_nav_ref()
                    self.change = True
                    self.map_change = True
                    self.tab_manager(old_discharge=old_discharge)

    def set_ref_vtg(self):
        """Changes the navigation reference to GPS VTG"""

        if self.meas is not None:
            with self.wait_cursor():
                # Get all current settings
                settings = Measurement.current_settings(self.meas)
                old_discharge = self.meas.discharge
                # Set NavRef to selected setting
                settings["NavRef"] = "VTG"
                # Update measurement and GUI
                Measurement.apply_settings(self.meas, settings)
                self.update_toolbar_nav_ref()
                self.change = True
                self.map_change = True
                self.tab_manager(old_discharge=old_discharge)

    def comp_tracks_on(self):
        """Change composite tracks setting to On and update measurement and
        display.
        """

        with self.wait_cursor():
            composite = True
            # Check to see if discharge is being corrected by a moving bed
            # test, if so composite tracks will not be used
            if len(self.meas.mb_tests) > 0:
                for test in self.meas.mb_tests:
                    if test.selected:
                        if (
                            test.moving_bed == "Yes"
                            and self.meas.transects[
                                self.checked_transects_idx[0]
                            ].w_vel.nav_ref
                            == "BT"
                        ):
                            QtWidgets.QMessageBox.about(
                                self,
                                "Composite Tracks " "Message",
                                "A moving-bed "
                                "condition exists "
                                "and BT is the "
                                "current reference,"
                                "composite tracks "
                                "cannot be used in "
                                "this situation.",
                            )
                            composite = False
            if composite:
                # Get all current settings
                settings = Measurement.current_settings(self.meas)
                old_discharge = self.meas.discharge
                # Change CompTracks to selected setting
                settings["CompTracks"] = "On"
                # Update measurement and GUI
                Measurement.apply_settings(self.meas, settings)
                self.update_toolbar_composite_tracks()
                self.change = True
                self.map_change = True
                self.tab_manager(old_discharge=old_discharge)

    def comp_tracks_off(self):
        """Change composite tracks setting to Off and update measurement and
        display.
        """

        with self.wait_cursor():
            # Get all current settings
            settings = Measurement.current_settings(self.meas)
            # Change CompTracks to selected setting
            settings["CompTracks"] = "Off"
            old_discharge = self.meas.discharge
            # Update measurement and GUI
            Measurement.apply_settings(self.meas, settings)
            self.update_toolbar_composite_tracks()
            self.change = True
            self.map_change = True
            self.tab_manager(old_discharge=old_discharge)

    def qrev_options(self):
        """Change options triggered by actionOptions"""

        # Initialize options dialog
        options = Options()

        # Set dialog to current settings
        if not self.agency_options["Units"]["show"]:
            options.gb_units.hide()
        if self.units["ID"] == "SI":
            options.rb_si.setChecked(True)
        else:
            options.rb_english.setChecked(True)

        if self.save_all:
            options.rb_All.setChecked(True)
        else:
            options.rb_checked.setChecked(True)

        if not self.agency_options["SaveStyleSheet"]["show"]:
            options.cb_stylesheet.hide()
        if self.save_stylesheet:
            options.cb_stylesheet.setChecked(True)
        else:
            options.cb_stylesheet.setChecked(False)

        if not self.agency_options["ExportCrossSection"]["show"]:
            options.cb_xs_export.hide()
        if self.xs_export:
            options.cb_xs_export.setChecked(True)
        else:
            options.cb_xs_export.setChecked(True)

        if not self.agency_options["ExtrapWeighting"]["show"]:
            options.gb_extrap_weighted.hide()
        if self.use_weighted:
            options.cb_weighted_extrap.setChecked(True)
        else:
            options.cb_weighted_extrap.setChecked(False)

        if not self.agency_options["RatingPrompt"]["show"]:
            options.cb_rating.hide()
        if self.rating_prompt:
            options.cb_rating.setChecked(True)
        else:
            options.cb_rating.setChecked(False)

        if not self.agency_options["Uncertainty"]["show"]:
            options.gb_uncertainty.hide()

        if self.run_oursin:
            options.rb_oursin_u.setChecked(True)
        else:
            options.rb_qrev_u.setChecked(True)

        if self.meas is not None:
            self.use_measurement_thresholds = self.meas.transects[
                self.meas.checked_transect_idx[0]
            ].boat_vel.bt_vel.use_measurement_thresholds

        if not self.agency_options["FilterUsingMeasurement"]["show"]:
            options.gb_filters.hide()
        if self.use_measurement_thresholds:
            options.rb_filter_meas.setChecked(True)
        else:
            options.rb_filter_transect.setChecked(True)

        if not self.agency_options["ColorMap"]["show"]:
            options.gb_color_map.hide()
        if self.color_map == "viridis":
            options.rb_viridis.setChecked(True)
        else:
            options.rb_jet.setChecked(True)

        if self.x_axis_type == "E":
            options.rb_opt_ensembles.setChecked(True)
        elif self.x_axis_type == "L":
            options.rb_opt_length.setChecked(True)
        elif self.x_axis_type == "T":
            options.rb_opt_time.setChecked(True)

        if not self.agency_options["MovingBedObservation"]["show"]:
            options.gb_moving_bed_option.hide()
        if self.allow_observed_no_moving_bed:
            options.cb_allow_manual_no_mb.setChecked(True)
        else:
            options.cb_allow_manual_no_mb.setChecked(False)

        if self.xs_export:
            options.cb_xs_export.setChecked(True)
        else:
            options.cb_xs_export.setChecked(False)

        if self.show_map:
            options.cb_map.setChecked(True)
        else:
            options.cb_map.setChecked(False)

        if not self.agency_options["PDFSummary"]["show"]:
            options.gb_pdf.hide()
        if self.pdf_setting == "No":
            options.rb_pdf_no.setChecked(True)
        elif self.pdf_setting == "Prompt":
            options.rb_pdf_prompt.setChecked(True)
        else:
            options.rb_pdf_always.setChecked(True)

        if not self.agency_options["DateFormat"]["show"]:
            options.gb_dateformat.hide()
        else:
            options.ed_dateformat.setText(self.date_format.replace("%", "").lower())

        # Execute the options window
        rsp = options.exec_()
        old_discharge = None

        with self.wait_cursor():
            # Apply settings from options window
            if rsp == QtWidgets.QDialog.Accepted:
                self.change = False
                # Units options
                if options.rb_english.isChecked():
                    if self.units["ID"] == "SI":
                        self.units = units_conversion(units_id="English")
                        self.sticky_settings.set("UnitsID", "English")
                        if self.meas is not None:
                            self.update_main()
                            self.change = True
                            self.map_change = True
                else:
                    if self.units["ID"] == "English":
                        self.units = units_conversion(units_id="SI")
                        self.sticky_settings.set("UnitsID", "SI")
                        if self.meas is not None:
                            self.update_main()
                            self.change = True
                            self.map_change = True

                # X Axis
                if options.rb_opt_ensembles.isChecked():
                    self.x_axis_type = "E"
                    self.sticky_settings.set("XAxis", "E")
                    if self.meas is not None:
                        self.update_main()
                        self.change = True
                elif options.rb_opt_length.isChecked():
                    self.x_axis_type = "L"
                    self.sticky_settings.set("XAxis", "L")
                    if self.meas is not None:
                        self.update_main()
                        self.change = True
                elif options.rb_opt_time.isChecked():
                    self.x_axis_type = "T"
                    self.sticky_settings.set("XAxis", "T")
                    if self.meas is not None:
                        self.update_main()
                        self.change = True
                # Color map
                if options.rb_viridis.isChecked():
                    if self.color_map != "viridis":
                        self.color_map = "viridis"
                        self.sticky_settings.set("ColorMap", "viridis")
                        if self.meas is not None:
                            self.update_main()
                            self.change = True
                            self.map_change = True
                else:
                    if self.color_map != "jet":
                        self.color_map = "jet"
                        self.sticky_settings.set("ColorMap", "jet")
                        if self.meas is not None:
                            self.update_main()
                            self.change = True
                            self.map_change = True

                # Save options
                if options.rb_All.isChecked():
                    self.save_all = True
                else:
                    self.save_all = False

                # Stylesheet option
                if options.cb_stylesheet.isChecked():
                    self.save_stylesheet = True
                    self.sticky_settings.set("StyleSheet", True)
                else:
                    self.save_stylesheet = False
                    self.sticky_settings.set("StyleSheet", False)

                # Prompt for user rating
                if options.cb_rating.isChecked():
                    self.rating_prompt = True
                    self.sticky_settings.set("UserRating", True)
                else:
                    self.rating_prompt = False
                    self.sticky_settings.set("UserRating", False)

                # PDF Summary
                if options.rb_pdf_no.isChecked():
                    self.pdf_setting = "No"
                elif options.rb_pdf_prompt.isChecked():
                    self.pdf_setting = "Prompt"
                elif options.rb_pdf_always.isChecked():
                    self.pdf_setting = "Always"
                self.sticky_settings.set("PDFSummary", self.pdf_setting)

                # Use of weighted medians for extrapolation fit
                if options.cb_weighted_extrap.isChecked():
                    use_weighted = True
                else:
                    use_weighted = False

                # Check for change in extraplation weighting
                if self.use_weighted != use_weighted:
                    self.change = True
                    self.map_change = True
                    # If change made with measurement loaded recompute
                    # measurement
                    if self.meas is not None:
                        old_discharge = self.meas.discharge
                        settings = self.meas.current_settings()
                        settings["UseWeighted"] = use_weighted
                        self.meas.apply_settings(settings)
                        self.sticky_settings.set("UseWeighted", use_weighted)
                        self.use_weighted = use_weighted

                    # If change made before measurement loaded, set value
                    else:
                        self.use_weighted = use_weighted
                        self.sticky_settings.set("UseWeighted", use_weighted)

                # Filter measurement
                if options.rb_filter_meas.isChecked():
                    filter_meas = True
                else:
                    filter_meas = False

                # Check for change in filter measurement
                if self.use_measurement_thresholds != filter_meas:
                    self.change = True
                    self.map_change = True
                    # If change made with measurement loaded recompute
                    # measurement
                    if self.meas is not None:
                        old_discharge = self.meas.discharge
                        settings = self.meas.current_settings()
                        settings["UseMeasurementThresholds"] = filter_meas
                        self.meas.apply_settings(settings)
                        self.sticky_settings.set(
                            "UseMeasurementThresholds", filter_meas
                        )
                        self.use_measurement_thresholds = filter_meas

                    # If change made before measurement loaded, set value
                    else:
                        self.sticky_settings.set(
                            "UseMeasurementThresholds", filter_meas
                        )
                        self.use_measurement_thresholds = filter_meas

                # Units options
                if options.rb_oursin_u.isChecked():
                    use_oursin = True
                else:
                    use_oursin = False

                # Check for change in uncertainty model
                if self.run_oursin != use_oursin:
                    self.run_oursin = use_oursin

                    try:
                        self.sticky_settings.set("Oursin", use_oursin)
                    except KeyError:
                        self.sticky_settings.new("Oursin", use_oursin)

                    if self.meas is not None:
                        if self.run_oursin:
                            # Uncertainty based on Oursin
                            self.meas.run_oursin = True
                            self.meas.oursin = Oursin()
                            self.meas.oursin.compute_oursin(self.meas)
                            self.tab_all.addTab(self.tab_uncertainty, "Uncertainty")
                        else:
                            # Uncertainty based on original QRev
                            self.tab_all.removeTab(
                                self.tab_all.indexOf(
                                    self.tab_all.findChild(
                                        QtWidgets.QWidget, "tab_uncertainty"
                                    )
                                )
                            )
                            self.meas.run_oursin = False
                            self.meas.oursin = None

                        # Change display of uncertainty on main tab depending
                        # on selection
                        self.update_main_uncertainty()

                    # If change made before measurement loaded, set value
                    else:
                        self.sticky_settings.set("Oursin", use_oursin)
                        self.run_oursin = use_oursin

                self.manual_computational_settings = {
                    "run_oursin": self.run_oursin,
                    "use_measurement_thresholds": self.use_measurement_thresholds,
                    "use_weighted": self.use_weighted,
                }
                # Allow observed no moving-bed
                if options.cb_allow_manual_no_mb.isChecked():
                    self.allow_observed_no_moving_bed = True
                    try:
                        self.sticky_settings.set("AllowNoMB", True)
                    except KeyError:
                        self.sticky_settings.new("AllowNoMB", True)
                else:
                    self.allow_observed_no_moving_bed = False
                    try:
                        self.sticky_settings.set("AllowNoMB", False)
                    except KeyError:
                        self.sticky_settings.new("AllowNoMB", False)

                # Export mean XS
                if options.cb_xs_export.isChecked():
                    self.xs_export = True
                    if self.meas is not None:
                        self.meas.export_xs = True
                    try:
                        self.sticky_settings.set("XsExport", True)
                    except KeyError:
                        self.sticky_settings.new("XsExport", True)
                else:
                    self.xs_export = False
                    if self.meas is not None:
                        self.meas.export_xs = False
                    try:
                        self.sticky_settings.set("XsExport", False)
                    except KeyError:
                        self.sticky_settings.new("XsExport", False)

                if options.cb_map.isChecked():
                    self.show_map = True
                    self.sticky_settings.set("MAP", True)
                    if (
                        self.tab_all.indexOf(
                            self.tab_all.findChild(QtWidgets.QWidget, "tab_map")
                        )
                        < 0
                    ):
                        self.tab_all.addTab(self.tab_map, "MAP")
                else:
                    self.show_map = False
                    self.sticky_settings.set("MAP", False)
                    tab_idx = self.tab_all.indexOf(
                        self.tab_all.findChild(QtWidgets.QWidget, "tab_map")
                    )
                    if tab_idx > 0:
                        self.tab_all.removeTab(tab_idx)

                if len(options.ed_dateformat.text()) > 0:
                    self.date_format = dateformat(options.ed_dateformat.text())
                    self.sticky_settings.set("DateFormat", self.date_format)

                # Update tabs
                if self.meas is not None:
                    if old_discharge is None:
                        self.tab_manager()
                    else:
                        self.tab_manager(old_discharge=old_discharge)

    def plot_google_earth(self):
        """Creates line plots of transects in Google Earth using GGA
        coordinates.
        """

        fullname = os.path.join(
            self.sticky_settings.get("Folder"),
            datetime.today().strftime("%Y%m%d_%H%M%S_QRev.kml"),
        )

        self.meas.export_kml(fullname)

        try:
            os.startfile(fullname)
        except os.error:
            self.popup_message(
                text="Google Earth is not installed or is not associated "
                "with kml files."
            )

    def help(self):
        """Opens pdf help file user's default pdf viewer."""

        """Opens the user guide using the default web browser on the
        user's system."""

        # Code to call sphinx documentation adopted from SurfVelTool

        # Use development-specific settings. Using __file__ path, so it
        # will work when called by other projects using AC3.
        if __company__ == "USGS":
            landing_page = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "docs",
                    "_build",
                    "html",
                    "index.html",
                )
            )
        else:
            landing_page = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "docs_QRevInt",
                    "_build",
                    "html",
                    "index.html",
                )
            )

        if os.path.exists(landing_page):
            webbrowser.open("file://" + landing_page)

        else:
            # Use production-specific settings
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
            landing_page = os.path.join(base_path, "qrev_documentation", "index.html")
            if os.path.exists(landing_page):
                webbrowser.open("file://" + landing_page)

    @staticmethod
    def export_stylesheet(stylesheet, destination):
        """Exports stylesheet on save.

        Parameters:
            stylesheet: str
                stylesheet to use
            destination: str
                path to copy stylesheet to
        """

        # Code to call sphinx documentation adopted from SurfVelTool

        # Use development-specific settings. Using __file__ path, so it
        # will work when called by other projects using QRev.
        path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "docs",
                "source",
                "assets",
                "files",
                stylesheet,
            )
        )

        if os.path.exists(path):
            shutil.copy2(path, destination)

        else:
            # Use production-specific settings
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
            path = os.path.join(base_path, "qrev_files", stylesheet)
            if os.path.exists(path):
                shutil.copy2(path, destination)

    def set_use_weighted(self):
        """Called by shortcut key cntrl+w toggle between use weighted and
        unweighted cells for extrapolation.
        """

        with self.wait_cursor():
            if self.use_weighted:
                self.use_weighted = False
            elif not self.use_weighted:
                self.use_weighted = True

            # If change made with measurement loaded recompute measurement
            if self.meas is not None:
                old_discharge = self.meas.discharge
                settings = self.meas.current_settings()
                settings["UseWeighted"] = self.use_weighted
                self.meas.apply_settings(settings)
                self.sticky_settings.set("UseWeighted", self.use_weighted)
                self.change = True
                self.map_change = True
                self.tab_manager(old_discharge=old_discharge)

    # Main tab
    # ========
    def update_main(self):
        """Update Gui"""

        if len(self.checked_transects_idx) > 0:
            with self.wait_cursor():
                # If this is the first time this tab is used setup interface
                # connections
                if not self.main_initialized:
                    self.main_table_summary.cellClicked.connect(self.select_transect)
                    self.ed_site_name.editingFinished.connect(self.update_site_name)
                    self.ed_site_number.editingFinished.connect(self.update_site_number)
                    self.ed_persons.editingFinished.connect(self.update_persons)
                    self.ed_meas_num.editingFinished.connect(self.update_meas_number)
                    self.ed_stage_start.editingFinished.connect(self.update_stage_start)
                    self.ed_stage_end.editingFinished.connect(self.update_stage_end)
                    self.ed_stage_meas.editingFinished.connect(self.update_stage_meas)
                    self.table_settings.cellClicked.connect(
                        self.settings_table_row_adjust
                    )
                    self.main_table_details.cellClicked.connect(
                        self.details_table_row_adjust
                    )
                    self.table_adcp.cellClicked.connect(self.refocus)
                    self.table_premeas.cellClicked.connect(self.refocus)
                    self.cb_user_rating.currentIndexChanged.connect(self.rating_change)

                    # Main tab has been initialized
                    self.main_initialized = True

                # Update the transect select icon on the toolbar
                self.update_toolbar_trans_select()

                # Set toolbar navigation reference
                self.update_toolbar_nav_ref()

                # Set toolbar composite tracks indicator
                self.update_toolbar_composite_tracks()

                # Setup and populate tables
                self.main_summary_table()
                self.uncertainty_table()
                self.qa_table()
                self.main_details_table()
                self.main_premeasurement_table()
                self.main_settings_table()
                self.main_adcp_table()
                self.messages_tab()
                self.comments_tab()

                # Setup and create graphs
                if len(self.checked_transects_idx) > 0:
                    self.contour_shiptrack(
                        self.checked_transects_idx[self.transect_row]
                    )
                    self.main_extrap_plot()
                    self.discharge_plot()
                    self.main_uncertainty_plot()
                    self.figs = []

                # If graphics have been created, update them
                else:
                    if self.main_extrap_canvas is not None:
                        self.main_extrap_fig.fig.clear()
                        self.main_extrap_canvas.draw()
                    if self.main_wt_contour_canvas is not None:
                        self.main_wt_contour_fig.fig.clear()
                        self.main_wt_contour_canvas.draw()
                    if self.main_discharge_canvas is not None:
                        self.main_discharge_fig.fig.clear()
                        self.main_discharge_canvas.draw()
                    if self.main_shiptrack_canvas is not None:
                        self.main_shiptrack_fig.fig.clear()
                        self.main_shiptrack_canvas.draw()

                self.update_main_uncertainty()
                if self.map_change:
                    self.meas.run_map = True
                self.set_user_rating()
                self.update_fig_list()

                # Toggles changes indicating the main has been updated
                self.change = False
                self.tab_all.setFocus()
        else:
            # Notify user
            QtWidgets.QMessageBox.warning(
                self, "Measurement", "No transects are selected."
            )
            self.update_toolbar_trans_select()

        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def update_fig_list(self):
        if self.current_tab == "Main":
            # Setup list for use by graphics controls
            if self.run_oursin:
                self.canvases = [
                    self.main_shiptrack_canvas,
                    self.main_wt_contour_canvas,
                    self.main_extrap_canvas,
                    self.main_discharge_canvas,
                    self.uncertainty_lollipop_canvas,
                ]
                self.figs = [
                    self.main_shiptrack_fig,
                    self.main_wt_contour_fig,
                    self.main_extrap_fig,
                    self.main_discharge_fig,
                    self.uncertainty_lollipop_fig,
                ]
                self.fig_calls = [
                    self.main_shiptrack,
                    self.main_wt_contour,
                    self.main_extrap_plot,
                    self.discharge_plot,
                    self.main_uncertainty_plot,
                ]
                self.toolbars = [
                    self.main_shiptrack_toolbar,
                    self.main_wt_contour_toolbar,
                    self.main_extrap_toolbar,
                    self.main_discharge_toolbar,
                    self.uncertainty_lollipop_toolbar,
                ]
            else:
                self.canvases = [
                    self.main_shiptrack_canvas,
                    self.main_wt_contour_canvas,
                    self.main_extrap_canvas,
                    self.main_discharge_canvas,
                ]
                self.figs = [
                    self.main_shiptrack_fig,
                    self.main_wt_contour_fig,
                    self.main_extrap_fig,
                    self.main_discharge_fig,
                ]
                self.fig_calls = [
                    self.main_shiptrack,
                    self.main_wt_contour,
                    self.main_extrap_plot,
                    self.discharge_plot,
                ]
                self.toolbars = [
                    self.main_shiptrack_toolbar,
                    self.main_wt_contour_toolbar,
                    self.main_extrap_toolbar,
                    self.main_discharge_toolbar,
                ]

    def refocus(self):
        self.tab_all.setFocus()

    def update_toolbar_trans_select(self):
        """Updates the icon for the select transects on the toolbar."""

        if self.meas is not None:
            if len(self.checked_transects_idx) == len(self.meas.transects):
                self.actionCheck.setIcon(self.icon_allChecked)
            elif len(self.checked_transects_idx) > 0:
                self.actionCheck.setIcon(self.icon_unChecked)
            else:
                self.actionCheck.setIcon(self.icon_warning)
                self.tab_all.setEnabled(False)

    def update_toolbar_composite_tracks(self):
        """Updates the toolbar to reflect the current setting for composite
        tracks.
        """

        # Set toolbar composite tracks indicator fonts
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        font_bold.setPointSize(11)

        font_normal = QtGui.QFont()
        font_normal.setBold(False)
        font_normal.setPointSize(11)

        # Set selection to bold
        if len(self.checked_transects_idx) > 0:
            if (
                self.meas.transects[self.checked_transects_idx[0]].boat_vel.composite
                == "On"
            ):
                self.actionON.setFont(font_bold)
                self.actionOFF.setFont(font_normal)
            else:
                self.actionON.setFont(font_normal)
                self.actionOFF.setFont(font_bold)

    def update_toolbar_nav_ref(self):
        """Update the display of the navigation reference on the toolbar."""

        # Get setting
        if len(self.checked_transects_idx) > 0:
            selected = self.meas.transects[
                self.checked_transects_idx[0]
            ].boat_vel.selected

            # Set toolbar navigation indicator fonts
            font_bold = QtGui.QFont()
            font_bold.setBold(True)
            font_bold.setPointSize(11)

            font_normal = QtGui.QFont()
            font_normal.setBold(False)
            font_normal.setPointSize(11)

            # Bold the selected reference only
            if selected == "bt_vel":
                self.actionBT.setFont(font_bold)
                self.actionGGA.setFont(font_normal)
                self.actionVTG.setFont(font_normal)
            elif selected == "gga_vel":
                self.actionBT.setFont(font_normal)
                self.actionGGA.setFont(font_bold)
                self.actionVTG.setFont(font_normal)
            elif selected == "vtg_vel":
                self.actionBT.setFont(font_normal)
                self.actionGGA.setFont(font_normal)
                self.actionVTG.setFont(font_bold)

    def uncertainty_table(self):
        """Create and populate uncertainty table."""

        # Setup table
        tbl = self.table_uncertainty
        tbl.clear()

        col_header = [self.tr("Uncertainty"), self.tr("Auto"), self.tr("  User  ")]
        ncols = len(col_header)
        nrows = 7
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(col_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.itemChanged.connect(self.recompute_uncertainty)
        tbl.itemChanged.disconnect()

        if self.meas.uncertainty is None:
            # Add labels and data
            row = 0
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Random 95%"))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(""))

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Invalid Data 95%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(""))

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Edge Q 95%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(""))

            row = row + 1
            tbl.setItem(
                row, 0, QtWidgets.QTableWidgetItem(self.tr("Extrapolation 95%"))
            )
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(""))

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Moving-Bed 95%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(""))

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Systematic 68%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(""))

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Estimated 95%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(row, 0).setFont(self.font_bold)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(row, 1).setFont(self.font_bold)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(""))
            tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(row, 2).setFont(self.font_bold)
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
        else:
            # Add labels and data
            row = 0
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Random 95%"))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            if self.meas.uncertainty is None:
                tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
            else:
                tbl.setItem(
                    row,
                    1,
                    QtWidgets.QTableWidgetItem(
                        "{:8.1f}".format(self.meas.uncertainty.cov_95)
                    ),
                )
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            if self.meas.uncertainty.cov_95_user is not None:
                tbl.setItem(
                    row,
                    2,
                    QtWidgets.QTableWidgetItem(
                        "{:8.1f}".format(self.meas.uncertainty.cov_95_user)
                    ),
                )

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Invalid Data 95%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:8.1f}".format(self.meas.uncertainty.invalid_95)
                ),
            )
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            if self.meas.uncertainty.cov_95_user is not None:
                tbl.setItem(
                    row,
                    2,
                    QtWidgets.QTableWidgetItem(
                        "{:8.1f}".format(self.meas.uncertainty.invalid_95_user)
                    ),
                )

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Edge Q 95%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:8.1f}".format(self.meas.uncertainty.edges_95)
                ),
            )
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            if self.meas.uncertainty.cov_95_user is not None:
                tbl.setItem(
                    row,
                    2,
                    QtWidgets.QTableWidgetItem(
                        "{:8.1f}".format(self.meas.uncertainty.edges_95_user)
                    ),
                )

            row = row + 1
            tbl.setItem(
                row, 0, QtWidgets.QTableWidgetItem(self.tr("Extrapolation 95%"))
            )
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:8.1f}".format(self.meas.uncertainty.extrapolation_95)
                ),
            )
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            if self.meas.uncertainty.cov_95_user is not None:
                tbl.setItem(
                    row,
                    2,
                    QtWidgets.QTableWidgetItem(
                        "{:8.1f}".format(self.meas.uncertainty.extrapolation_95_user)
                    ),
                )

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Moving-Bed 95%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:8.1f}".format(self.meas.uncertainty.moving_bed_95)
                ),
            )
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            if self.meas.uncertainty.cov_95_user is not None:
                tbl.setItem(
                    row,
                    2,
                    QtWidgets.QTableWidgetItem(
                        "{:8.1f}".format(self.meas.uncertainty.moving_bed_95_user)
                    ),
                )

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Systematic 68%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:8.1f}".format(self.meas.uncertainty.systematic)
                ),
            )
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            if self.meas.uncertainty.cov_95_user is not None:
                tbl.setItem(
                    row,
                    2,
                    QtWidgets.QTableWidgetItem(
                        "{:8.1f}".format(self.meas.uncertainty.systematic_user)
                    ),
                )

            row = row + 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Estimated 95%")))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(row, 0).setFont(self.font_bold)
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:8.1f}".format(self.meas.uncertainty.total_95)
                ),
            )
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(row, 1).setFont(self.font_bold)
            tbl.setItem(
                row,
                2,
                QtWidgets.QTableWidgetItem(
                    "{:8.1f}".format(self.meas.uncertainty.total_95_user)
                ),
            )
            tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(row, 2).setFont(self.font_bold)
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

        tbl.itemChanged.connect(self.recompute_uncertainty)

    def recompute_uncertainty(self):
        """Recomputes the uncertainty based on user input."""

        # Get edited value from table
        with self.wait_cursor():
            new_value = self.table_uncertainty.selectedItems()[0].text()
            if new_value == "":
                new_value = None
            else:
                new_value = float(new_value)

            # Identify uncertainty variable that was edited.
            row_index = self.table_uncertainty.selectedItems()[0].row()
            if row_index == 0:
                self.meas.uncertainty.cov_95_user = new_value
            elif row_index == 1:
                self.meas.uncertainty.invalid_95_user = new_value
            elif row_index == 2:
                self.meas.uncertainty.edges_95_user = new_value
            elif row_index == 3:
                self.meas.uncertainty.extrapolation_95_user = new_value
            elif row_index == 4:
                self.meas.uncertainty.moving_bed_95_user = new_value
            elif row_index == 5:
                self.meas.uncertainty.systematic_user = new_value

            # Compute new uncertainty values
            self.meas.uncertainty.estimate_total_uncertainty()

            # Update table
            if new_value is not None:
                self.table_uncertainty.item(row_index, 2).setText(
                    "{:8.1f}".format(new_value)
                )
            self.table_uncertainty.item(6, 2).setText(
                "{:8.1f}".format(self.meas.uncertainty.total_95_user)
            )

    def rating_change(self):
        """Stores the user selected rating."""

        self.meas.user_rating = self.cb_user_rating.currentText()

    def set_user_rating(self):
        """Sets the user rating from stored data."""

        rating = {
            "Excellent": self.tr("Excellent (<3%)"),
            "Good": self.tr("Good (3-5%)"),
            "Fair": self.tr("Fair (5-8%)"),
            "Poor": self.tr("Poor (>8%)"),
            "Not Rated": self.tr("Not Rated"),
            "": self.tr("Not Rated"),
            "Not ": self.tr("Not Rated"),
            "Exce": self.tr("Excellent (<3%)"),
        }
        if type(self.meas.user_rating) is np.ndarray:
            if len(self.meas.user_rating) > 0:
                item = rating[self.meas.user_rating[0:4]]
            else:
                item = self.tr("Not Rated")
        else:
            item = rating[self.meas.user_rating.split("(")[0].strip()]
        self.cb_user_rating.setCurrentText(item)

    def qa_table(self):
        """Create and populate quality assurance table."""

        # Setup table
        tbl = self.table_qa
        header = ["", self.tr("COV %"), "", self.tr("% Q")]
        ncols = len(header)
        nrows = 3
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Compute measurement properties
        trans_prop = self.meas.compute_measurement_properties(self.meas)
        discharge = self.meas.mean_discharges(self.meas)

        # Populate table
        row = 0

        # Discharge COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Q:")))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(self.font_bold)
        if self.meas.uncertainty is None or np.isnan(self.meas.uncertainty.cov):
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("N/A"))
        else:
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem("{:5.2f}".format(self.meas.uncertainty.cov)),
            )
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Left and right edge % Q
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr("L/R Edge:")))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(self.font_bold)
        left = (discharge["left_mean"] / discharge["total_mean"]) * 100
        right = (discharge["right_mean"] / discharge["total_mean"]) * 100
        if np.isnan(left) or np.isnan(right):
            tbl.setItem(row, 3, QtWidgets.QTableWidgetItem("N/A"))
        else:
            tbl.setItem(
                row,
                3,
                QtWidgets.QTableWidgetItem("{:5.2f} / {:5.2f}".format(left, right)),
            )
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        row = row + 1
        # Width COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Width:")))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(self.font_bold)
        if np.isnan(trans_prop["width_cov"][-1]):
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("N/A"))
        else:
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(trans_prop["width_cov"][-1])
                ),
            )
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Invalid cells
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr("Invalid Cells:")))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(self.font_bold)
        value = (discharge["int_cells_mean"] / discharge["total_mean"]) * 100
        if np.isnan(value):
            tbl.setItem(row, 3, QtWidgets.QTableWidgetItem("N/A"))
        else:
            tbl.setItem(row, 3, QtWidgets.QTableWidgetItem("{:5.2f}".format(value)))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        row = row + 1
        # Area COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr("Area:")))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(self.font_bold)
        if np.isnan(trans_prop["area_cov"][-1]):
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("N/A"))
        else:
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(trans_prop["area_cov"][-1])
                ),
            )
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Invalid ensembles
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr("Invalid Ens:")))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(self.font_bold)
        value = (discharge["int_ensembles_mean"] / discharge["total_mean"]) * 100
        if np.isnan(value):
            tbl.setItem(row, 3, QtWidgets.QTableWidgetItem("N/A"))
        else:
            tbl.setItem(row, 3, QtWidgets.QTableWidgetItem("{:5.2f}".format(value)))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def select_transect(self, row, column):
        """Update contour and shiptrack plots based on transect selected in
        main_summary_table.

        Parameters
        ----------
        row: int
            Row number selected.
        column: int
            Column number selected.
        """

        # Transect column was selected
        if column == 0 and row > 0:
            with self.wait_cursor():
                # Set all files to normal font
                nrows = len(self.checked_transects_idx)
                for nrow in range(1, nrows + 1):
                    self.main_table_summary.item(nrow, 0).setFont(self.font_normal)
                    self.main_table_details.item(nrow + 1, 0).setFont(self.font_normal)
                    self.table_settings.item(nrow + 2, 0).setFont(self.font_normal)

                # Set selected file to bold font
                self.main_table_summary.item(row, 0).setFont(self.font_bold)
                self.main_table_details.item(row + 1, 0).setFont(self.font_bold)
                self.table_settings.item(row + 2, 0).setFont(self.font_bold)
                self.transect_row = row - 1

                # Determine transect selected
                transect_id = self.checked_transects_idx[row - 1]
                self.clear_zphd()

                # Update contour and shiptrack plot
                self.contour_shiptrack(transect_id=transect_id)
                self.discharge_plot()

        self.tab_all.setFocus()

    def contour_shiptrack(self, transect_id=0):
        """Generates the color contour and shiptrack plot for the main tab.

        Parameters
        ----------
        transect_id: int
            Index to check transects to identify the transect to be plotted
        """

        # Get transect data to be plotted
        transect = self.meas.transects[transect_id]

        # Generate graphs
        self.main_shiptrack(transect=transect)
        self.main_wt_contour(transect_id=transect_id)

    def main_shiptrack(self, transect):
        """Creates shiptrack plot for data in transect.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        """

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.main_shiptrack_canvas is None:
            # Create the canvas
            self.main_shiptrack_canvas = MplCanvas(
                parent=self.graphics_shiptrack, width=4, height=3, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graphics_shiptrack)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.main_shiptrack_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.main_shiptrack_toolbar = NavigationToolbar(
                self.main_shiptrack_canvas, self
            )
            self.main_shiptrack_toolbar.hide()

        # Initialize the shiptrack figure and assign to the canvas
        self.main_shiptrack_fig = Shiptrack(canvas=self.main_shiptrack_canvas)
        # Create the figure with the specified data
        self.main_shiptrack_fig.create(transect=transect, units=self.units, cb=False)
        # Draw canvas
        self.main_shiptrack_canvas.draw()

    def main_wt_contour(self, transect_id):
        """Creates boat speed plot for data in transect.

        Parameters
        ----------
        transect_id: int
            Index of selected transect
        """

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.main_wt_contour_canvas is None:
            # Create the canvas
            self.main_wt_contour_canvas = MplCanvas(
                parent=self.graphics_wt_contour, width=12, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graphics_wt_contour)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.main_wt_contour_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.main_wt_contour_toolbar = NavigationToolbar(
                self.main_wt_contour_canvas, self
            )
            self.main_wt_contour_toolbar.hide()

        # Initialize the boat speed figure and assign to the canvas
        self.main_wt_contour_fig = AdvGraphs(canvas=self.main_wt_contour_canvas)
        # Create the figure with the specified data
        if self.plot_extrapolated:
            self.main_wt_contour_fig.create_main_contour(
                transect=self.meas.transects[transect_id],
                units=self.units,
                color_map=self.color_map,
                x_axis_type=self.x_axis_type,
                discharge=self.meas.discharge[transect_id],
            )
        else:
            self.main_wt_contour_fig.create_main_contour(
                transect=self.meas.transects[transect_id],
                units=self.units,
                color_map=self.color_map,
                x_axis_type=self.x_axis_type,
            )
        self.main_wt_contour_fig.fig.subplots_adjust(
            left=0.05, bottom=0.2, right=0.92, top=0.97, wspace=0.02, hspace=0
        )
        # self.figs = [self.main_wt_contour_fig]
        # self.fig_calls = [self.main_wt_contour]
        # Draw canvas
        self.main_wt_contour_canvas.draw()
        self.update_fig_list()

    def main_extrap_plot(self):
        """Creates extrapolation plot."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.main_extrap_canvas is None:
            # Create the canvas
            self.main_extrap_canvas = MplCanvas(
                parent=self.graphics_main_extrap, width=1, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graphics_main_extrap)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.main_extrap_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.main_extrap_toolbar = NavigationToolbar(self.main_extrap_canvas, self)
            self.main_extrap_toolbar.hide()

        # Initialize the figure and assign to the canvas
        self.main_extrap_fig = ExtrapPlot(canvas=self.main_extrap_canvas)
        # Create the figure with the specified data
        self.main_extrap_fig.create(
            meas=self.meas, checked=self.checked_transects_idx, auto=True
        )

        self.main_extrap_canvas.draw()

    def main_uncertainty_plot(self):
        """Creates a lollipop plot for the Oursin uncertainty model."""

        # If the canvas has not been previously created, create the canvas and
        # add the widget.
        if self.uncertainty_lollipop_canvas is None:
            # Create the canvas
            self.uncertainty_lollipop_canvas = MplCanvas(
                parent=self.uncertainty_lollipop, width=1, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.uncertainty_lollipop)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.uncertainty_lollipop_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.uncertainty_lollipop_toolbar = NavigationToolbar(
                self.uncertainty_lollipop_canvas, self
            )
            self.uncertainty_lollipop_toolbar.hide()

        # Initialize the figure and assign to the canvas
        self.uncertainty_lollipop_fig = ULollipopPlot(
            canvas=self.uncertainty_lollipop_canvas
        )
        # Create the figure with the specified data
        self.uncertainty_lollipop_fig.create(meas=self.meas)

        self.uncertainty_lollipop_canvas.draw()

    def update_main_uncertainty(self):
        """Updates the main tab to show the appropriate display based on the
        uncertainty model selected.
        """

        if self.run_oursin:
            self.main_uncertainty_plot()
            self.uncertainty_lollipop.show()
            self.table_uncertainty.hide()
            self.verticalLayout_right.setStretch(1, 45)
            self.verticalLayout_right.setStretch(2, 0)

        else:
            self.uncertainty_lollipop.hide()
            self.table_uncertainty.show()
            self.verticalLayout_right.setStretch(1, 0)
            self.verticalLayout_right.setStretch(2, 45)

    def discharge_plot(self):
        """Generates discharge time series plot for the main tab."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.main_discharge_canvas is None:
            # Create the canvas
            self.main_discharge_canvas = MplCanvas(
                parent=self.graphics_main_timeseries, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graphics_main_timeseries)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.main_discharge_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.main_discharge_toolbar = NavigationToolbar(
                self.main_discharge_canvas, self
            )
            self.main_discharge_toolbar.hide()

        # Initialize the figure and assign to the canvas
        self.main_discharge_fig = DischargeTS(canvas=self.main_discharge_canvas)
        # Create the figure with the specified data
        self.main_discharge_fig.create(
            meas=self.meas,
            checked=self.checked_transects_idx,
            transect_idx=self.transect_row,
            units=self.units,
        )
        self.main_discharge_canvas.draw()

    def combine_qa_messages(self):
        # Initialize local variables
        qa = self.meas.qa
        qa_check_keys = [
            "bt_vel",
            "compass",
            "depths",
            "edges",
            "extrapolation",
            "gga_vel",
            "movingbed",
            "system_tst",
            "temperature",
            "transects",
            "user",
            "vtg_vel",
            "w_vel",
        ]

        # For each qa check retrieve messages and set tab icon based on the
        # status
        messages = []
        for key in qa_check_keys:
            qa_type = getattr(qa, key)
            if qa_type["messages"]:
                for message in qa_type["messages"]:
                    if type(message) == np.ndarray:
                        message = message.tolist()
                    if type(message) is str:
                        if message[:3].isupper():
                            messages.append([message, 1])
                        else:
                            messages.append([message, 2])
                    else:
                        message[1] = int(message[1])
                        messages.append(message)
            self.set_icon(key, qa_type["status"])

        # Sort messages with warning at top
        messages.sort(key=lambda x: x[1])

        return messages

    def messages_tab(self):
        """Update messages tab."""

        messages = self.combine_qa_messages()
        # Setup table
        tbl = self.main_message_table
        tbl.clear()
        main_message_header = [self.tr("Status"), self.tr("Message")]
        ncols = len(main_message_header)
        nrows = len(messages)
        tbl.setRowCount(nrows + 1)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(main_message_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Populate table
        for row, message in enumerate(messages):
            # Handle messages from old QRev that did not have integer codes
            if type(message) is str:
                warn = message[:3].isupper()
                tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(message))
            # Handle newer style messages
            else:
                warn = int(message[1]) == 1
                tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(message[0]))
            if warn:
                tbl.item(row, 1).setFont(self.font_bold)
                item_warning = QtWidgets.QTableWidgetItem(self.icon_warning, "")
                tbl.setItem(row, 0, item_warning)
            else:
                item_caution = QtWidgets.QTableWidgetItem(self.icon_caution, "")
                tbl.setItem(row, 0, item_caution)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def update_tab_icons(self):
        """Update tab icons base on results of QA analysis."""

        qa = self.meas.qa
        qa_check_keys = [
            "bt_vel",
            "compass",
            "depths",
            "edges",
            "extrapolation",
            "gga_vel",
            "movingbed",
            "system_tst",
            "temperature",
            "transects",
            "user",
            "vtg_vel",
            "w_vel",
        ]
        for key in qa_check_keys:
            qa_type = getattr(qa, key)
            self.set_icon(key, qa_type["status"])
            self.set_tab_color()

        gga = getattr(qa, "gga_vel")
        vtg = getattr(qa, "vtg_vel")
        if gga["lag_status"] == "caution" or vtg["lag_status"] == "caution":
            self.set_icon("gps_bt", "caution")
            self.set_tab_color()
        if gga["lag_status"] == "warning" or vtg["lag_status"] == "warning":
            self.set_icon("gps_bt", "warning")
            self.set_tab_color()

    def set_icon(self, key, status):
        """Set tab icon based on qa check status.

        Parameters
        ----------
        key: str
            Identifies target tab
        status: str
            Quality status for data in that tab
        """

        tab_base = self.tab_all
        tab = ""
        # Identify tab name based on key
        if key == "bt_vel":
            tab = "tab_bt"
        elif key == "compass":
            tab = "tab_compass"
        elif key == "depths":
            tab = "tab_depth"
        elif key == "edges":
            tab = "tab_edges"
        elif key == "extrapolation":
            tab = "tab_extrap"
        elif key == "gga_vel" or key == "vtg_vel":
            gga_status = self.meas.qa.gga_vel["status"]
            vtg_status = self.meas.qa.vtg_vel["status"]
            status = "good"
            if gga_status == "caution" or vtg_status == "caution":
                status = "caution"
            elif gga_status == "inactive" and vtg_status == "inactive":
                status = "inactive"
            elif gga_status == "warning" or vtg_status == "warning":
                status = "warning"
            elif gga_status == "default" or vtg_status == "default":
                status = "default"
            tab = "tab_gps"
        elif key == "movingbed":
            tab = "tab_mbt"
        elif key == "system_tst":
            tab = "tab_systest"
        elif key == "temperature":
            tab = "tab_tempsal"
        elif key == "transects":  # or key == 'user':
            tab = "tab_main"
            transects_status = self.meas.qa.transects["status"]
            user_status = self.meas.qa.user["status"]
            status = "good"
            if transects_status == "caution" or user_status == "caution":
                status = "caution"
            if transects_status == "warning" or user_status == "warning":
                status = "warning"
        elif key == "w_vel":
            tab = "tab_wt"
        elif key == "user":
            tab = "tab_summary_premeasurement"
            tab_base = self.tab_summary
        elif key == "gps_bt":
            tab_base = self.tab_gps_2
            tab = "tab_gps_2_gpsbt"

        self.set_tab_icon(tab, status, tab_base=tab_base)

    def set_tab_icon(self, tab, status, tab_base=None):
        """Sets the text color and icon for the tab based on the quality
        status.

            Parameters
            ----------
            tab: str
                Tab identifier
            status: str
                Quality status
            tab_base: object
                Object of tab interface
        """

        if tab_base is None:
            tab_base = self.tab_all

        tab_base.tabBar().setTabTextColor(
            tab_base.indexOf(tab_base.findChild(QtWidgets.QWidget, tab)),
            QtGui.QColor(140, 140, 140),
        )
        tab_base.setTabIcon(
            tab_base.indexOf(tab_base.findChild(QtWidgets.QWidget, tab)), QtGui.QIcon()
        )
        # Set appropriate icon
        if status == "good":
            tab_base.setTabIcon(
                tab_base.indexOf(tab_base.findChild(QtWidgets.QWidget, tab)),
                self.icon_good,
            )
            tab_base.tabBar().setTabTextColor(
                tab_base.indexOf(tab_base.findChild(QtWidgets.QWidget, tab)),
                QtGui.QColor(0, 153, 0),
            )
        elif status == "caution":
            tab_base.setTabIcon(
                tab_base.indexOf(tab_base.findChild(QtWidgets.QWidget, tab)),
                self.icon_caution,
            )
            tab_base.tabBar().setTabTextColor(
                tab_base.indexOf(tab_base.findChild(QtWidgets.QWidget, tab)),
                QtGui.QColor(230, 138, 0),
            )
        elif status == "warning":
            tab_base.setTabIcon(
                tab_base.indexOf(tab_base.findChild(QtWidgets.QWidget, tab)),
                self.icon_warning,
            )
            tab_base.tabBar().setTabTextColor(
                tab_base.indexOf(tab_base.findChild(QtWidgets.QWidget, tab)),
                QtGui.QColor(255, 77, 77),
            )
        tab_base.setIconSize(QtCore.QSize(15, 15))

    def set_tab_color(self):
        """Updates tab font to Blue if a setting was changed from the
        default settings."""

        if self.meas.qa is not None:
            for tab in self.meas.qa.settings_dict:
                if tab != "tab_gps":
                    if self.meas.qa.settings_dict[tab] == "Custom":
                        self.tab_all.tabBar().setTabTextColor(
                            self.tab_all.indexOf(
                                self.tab_all.findChild(QtWidgets.QWidget, tab)
                            ),
                            QtGui.QColor(0, 0, 255),
                        )
                        if tab == "tab_uncertainty_2_advanced":
                            self.tab_uncertainty_2.tabBar().setTabTextColor(
                                self.tab_uncertainty_2.indexOf(
                                    self.tab_uncertainty_2.findChild(
                                        QtWidgets.QWidget, tab
                                    )
                                ),
                                QtGui.QColor(0, 0, 255),
                            )

                    elif tab == "tab_uncertainty":
                        self.tab_all.tabBar().setTabTextColor(
                            self.tab_all.indexOf(
                                self.tab_all.findChild(QtWidgets.QWidget, tab)
                            ),
                            QtGui.QColor(0, 0, 0),
                        )

                    elif tab == "tab_uncertainty_2_advanced":
                        self.tab_uncertainty_2.tabBar().setTabTextColor(
                            self.tab_uncertainty_2.indexOf(
                                self.tab_uncertainty_2.findChild(QtWidgets.QWidget, tab)
                            ),
                            QtGui.QColor(0, 0, 0),
                        )

                else:
                    if self.tab_all.isTabEnabled(6) is True:
                        if self.meas.qa.settings_dict[tab] == "Custom":
                            self.tab_all.tabBar().setTabTextColor(
                                self.tab_all.indexOf(
                                    self.tab_all.findChild(QtWidgets.QWidget, tab)
                                ),
                                QtGui.QColor(0, 0, 255),
                            )

    def comments_tab(self):
        """Display comments in comments tab."""

        self.display_comments.clear()
        if self.meas is not None:
            self.display_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                # Display each comment on a new line
                self.display_comments.textCursor().insertText(comment)
                self.display_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_comments.textCursor().insertBlock()

    # Main summary tabs
    # =================
    def main_summary_table(self):
        """Create and populate main summary table."""

        # Setup table
        tbl = self.main_table_summary
        summary_header = [
            self.tr("Transect"),
            self.tr("Start"),
            self.tr("Bank"),
            self.tr("End"),
            self.tr("Duration") + " " + self.tr("(sec)"),
            self.tr("Total Q") + " " + self.tr(self.units["label_Q"]),
            self.tr("Top Q") + " " + self.tr(self.units["label_Q"]),
            self.tr("Meas Q") + " " + self.tr(self.units["label_Q"]),
            self.tr("Bottom Q") + " " + self.tr(self.units["label_Q"]),
            self.tr("Left Q") + " " + self.tr(self.units["label_Q"]),
            self.tr("Right Q") + " " + self.tr(self.units["label_Q"]),
            self.tr("Delta Q (%)"),
        ]
        ncols = len(summary_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows + 1)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(summary_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        if len(self.checked_transects_idx) > 0:
            # Add transect data
            for row in range(nrows):
                col = 0
                transect_id = self.checked_transects_idx[row]

                # File/transect name
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].file_name[:-4]
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect start time
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        datetime.strftime(
                            datetime.utcfromtimestamp(
                                self.meas.transects[
                                    transect_id
                                ].date_time.start_serial_time
                            ),
                            "%H:%M:%S",
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect start edge
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].start_edge[0]
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect end time
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        datetime.strftime(
                            datetime.utcfromtimestamp(
                                self.meas.transects[
                                    transect_id
                                ].date_time.end_serial_time
                            ),
                            "%H:%M:%S",
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect duration
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.1f}".format(
                            self.meas.transects[
                                transect_id
                            ].date_time.transect_duration_sec
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect total discharge
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                self.meas.discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect top discharge
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:7}".format(
                            self.q_digits(
                                self.meas.discharge[transect_id].top * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect middle discharge
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:7}".format(
                            self.q_digits(
                                self.meas.discharge[transect_id].middle
                                * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect bottom discharge
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:7}".format(
                            self.q_digits(
                                self.meas.discharge[transect_id].bottom
                                * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect left discharge
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:7}".format(
                            self.q_digits(
                                self.meas.discharge[transect_id].left * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect right discharge
                col += 1
                tbl.setItem(
                    row + 1,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:7}".format(
                            self.q_digits(
                                self.meas.discharge[transect_id].right * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent difference from measurement mean
                discharge = Measurement.mean_discharges(self.meas)
                per_diff = (
                    (self.meas.discharge[transect_id].total - discharge["total_mean"])
                    / discharge["total_mean"]
                ) * 100
                col += 1
                if np.isnan(per_diff):
                    tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem("N/A"))
                else:
                    tbl.setItem(
                        row + 1,
                        col,
                        QtWidgets.QTableWidgetItem("{:7.3f}".format(per_diff)),
                    )
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Add measurement summaries

            # Row label
            col = 0

            meas_date = datetime.strftime(
                datetime.utcfromtimestamp(
                    self.meas.transects[
                        self.checked_transects_idx[0]
                    ].date_time.start_serial_time
                ),
                self.date_format,
            )
            item = self.tr("Measurement") + " (" + meas_date + ")"
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Measurement start time
            col += 1
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(tbl.item(1, col).text()))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Skip start bank
            col += 1
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(""))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Measurement end time
            col += 1
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(tbl.item(nrows, col).text()))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Measurement duration
            col += 1
            tbl.setItem(
                0,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.1f}".format(Measurement.measurement_duration(self.meas))
                ),
            )
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Mean total discharge
            discharge = Measurement.mean_discharges(self.meas)
            col += 1
            tbl.setItem(
                0,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:8}".format(
                        self.q_digits(discharge["total_mean"] * self.units["Q"])
                    )
                ),
            )
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Mean top discharge
            col += 1
            tbl.setItem(
                0,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(discharge["top_mean"] * self.units["Q"])
                    )
                ),
            )
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Mean middle discharge
            col += 1
            tbl.setItem(
                0,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(discharge["mid_mean"] * self.units["Q"])
                    )
                ),
            )
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Mean bottom discharge
            col += 1
            tbl.setItem(
                0,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(discharge["bot_mean"] * self.units["Q"])
                    )
                ),
            )
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Mean left discharge
            col += 1
            tbl.setItem(
                0,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(discharge["left_mean"] * self.units["Q"])
                    )
                ),
            )
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Mean right discharge
            col += 1
            tbl.setItem(
                0,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(discharge["right_mean"] * self.units["Q"])
                    )
                ),
            )
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Bold Measurement row
            for col in range(ncols - 1):
                tbl.item(0, col).setFont(self.font_bold)

            tbl.item(self.transect_row + 1, 0).setFont(self.font_bold)
            tbl.scrollToItem(tbl.item(self.transect_row + 1, 0))

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
        else:
            tbl.setRowCount(0)

    def main_details_table(self):
        """Initialize and populate the details table."""

        # Setup table
        tbl = self.main_table_details
        summary_header = [
            self.tr("Transect"),
            self.tr("Width" + "\n " + self.units["label_L"]),
            self.tr("Area" + "\n " + self.units["label_A"]),
            self.tr("Avg Boat \n Speed" + " " + self.units["label_V"]),
            self.tr("Course Made \n Good" + " (deg)"),
            self.tr("Q/A" + " " + self.units["label_V"]),
            self.tr("Avg Water \n Direction" + " (deg)"),
        ]
        ncols = len(summary_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows + 2)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(summary_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        if len(self.checked_transects_idx) > 0:
            trans_prop = Measurement.compute_measurement_properties(self.meas)
            left_width = []
            left_area = []
            left_boat_speed = []
            left_boat_course = []
            left_water_speed = []
            left_water_dir = []
            right_width = []
            right_area = []
            right_boat_speed = []
            right_boat_course = []
            right_water_speed = []
            right_water_dir = []

            # Add transect data
            for row in range(nrows):
                col = 0
                transect_id = self.checked_transects_idx[row]
                if trans_prop["start_bank"][transect_id] == "Left":
                    left_width.append(trans_prop["width"][transect_id])
                    left_area.append(trans_prop["area"][transect_id])
                    left_boat_speed.append(trans_prop["avg_boat_speed"][transect_id])
                    left_boat_course.append(trans_prop["avg_boat_course"][transect_id])
                    left_water_speed.append(trans_prop["avg_water_speed"][transect_id])
                    left_water_dir.append(trans_prop["avg_water_dir"][transect_id])
                else:
                    right_width.append(trans_prop["width"][transect_id])
                    right_area.append(trans_prop["area"][transect_id])
                    right_boat_speed.append(trans_prop["avg_boat_speed"][transect_id])
                    right_boat_course.append(trans_prop["avg_boat_course"][transect_id])
                    right_water_speed.append(trans_prop["avg_water_speed"][transect_id])
                    right_water_dir.append(trans_prop["avg_water_dir"][transect_id])

                # File/transect name
                tbl.setItem(
                    row + 2,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].file_name[:-4]
                    ),
                )
                tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect width
                col += 1
                item = ""
                if not np.isnan(trans_prop["width"][transect_id]):
                    item = "{:10.2f}".format(
                        trans_prop["width"][transect_id] * self.units["L"]
                    )
                tbl.setItem(row + 2, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect area
                col += 1
                item = ""
                if not np.isnan(trans_prop["area"][transect_id]):
                    item = "{:10.2f}".format(
                        trans_prop["area"][transect_id] * self.units["A"]
                    )
                tbl.setItem(row + 2, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect average boat speed
                col += 1
                item = ""
                if not np.isnan(trans_prop["avg_boat_speed"][transect_id]):
                    item = "{:6.2f}".format(
                        trans_prop["avg_boat_speed"][transect_id] * self.units["V"]
                    )
                tbl.setItem(row + 2, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect average boat course
                col += 1
                item = ""
                if not np.isnan(trans_prop["avg_boat_course"][transect_id]):
                    item = "{:6.2f}".format(trans_prop["avg_boat_course"][transect_id])
                tbl.setItem(row + 2, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect average water speed
                col += 1
                item = ""
                if not np.isnan(trans_prop["avg_water_speed"][transect_id]):
                    item = "{:6.2f}".format(
                        trans_prop["avg_water_speed"][transect_id] * self.units["V"]
                    )
                tbl.setItem(row + 2, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect average water direction
                col += 1
                item = ""
                if not np.isnan(trans_prop["avg_water_dir"][transect_id]):
                    item = "{:6.2f}".format(trans_prop["avg_water_dir"][transect_id])
                tbl.setItem(row + 2, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Add measurement summaries
            n_transects = len(self.meas.transects)
            col = 0

            # Row label
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(self.tr("Average")))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            tbl.setItem(1, col, QtWidgets.QTableWidgetItem(self.tr("L/R Difference")))
            tbl.item(1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average width
            col += 1
            item = "{:10.2f}".format(trans_prop["width"][n_transects] * self.units["L"])
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # LR difference width
            if len(left_width) > 0 and len(right_width) > 0:
                item = "{:10.2f}".format(
                    np.abs(np.nanmean(left_width) - np.nanmean(right_width))
                    * self.units["L"]
                )
            else:
                item = ""
            tbl.setItem(1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average area
            col += 1
            item = "{:10.2f}".format(trans_prop["area"][n_transects] * self.units["A"])
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # LR difference area
            if len(left_area) > 0 and len(right_area) > 0:
                item = "{:10.2f}".format(
                    np.abs(np.nanmean(left_area) - np.nanmean(right_area))
                    * self.units["L"]
                )
            else:
                item = ""
            tbl.setItem(1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average boat speed
            col += 1
            item = "{:6.2f}".format(
                trans_prop["avg_boat_speed"][n_transects] * self.units["V"]
            )
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # LR difference boat speed
            if len(left_boat_speed) > 0 and len(right_boat_speed) > 0:
                item = "{:6.2f}".format(
                    np.abs(np.nanmean(left_boat_speed) - np.nanmean(right_boat_speed))
                    * self.units["L"]
                )
            else:
                item = ""
            tbl.setItem(1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Skip average boat course
            col += 1

            # LR difference boat course
            if len(left_boat_course) > 0 and len(right_boat_course) > 0:
                diff_dir = np.abs(
                    np.nanmean(left_boat_course) - np.nanmean(right_boat_course)
                )
                if diff_dir > 180:
                    diff_dir = diff_dir - 360
                item = "{:6.2f}".format(diff_dir)
            else:
                item = ""
            tbl.setItem(1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average water speed
            col += 1
            item = "{:6.2f}".format(
                trans_prop["avg_water_speed"][n_transects] * self.units["V"]
            )
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # LR difference water_speed
            if len(left_water_speed) > 0 and len(right_water_speed) > 0:
                item = "{:6.2f}".format(
                    np.abs(np.nanmean(left_water_speed) - np.nanmean(right_water_speed))
                    * self.units["L"]
                )
            else:
                item = ""
            tbl.setItem(1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average water direction
            col += 1
            item = "{:6.2f}".format(trans_prop["avg_water_dir"][n_transects])
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # LR difference water_direction
            if len(left_water_dir) > 0 and len(right_water_dir) > 0:
                diff_dir = np.abs(
                    np.nanmean(left_water_dir) - np.nanmean(right_water_dir)
                )
                if diff_dir > 180:
                    diff_dir = diff_dir - 360
                item = "{:6.2f}".format(diff_dir)
            else:
                item = ""
            tbl.setItem(1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Set average row font to bold
            for col in range(ncols):
                if col != 4:
                    tbl.item(0, col).setFont(self.font_bold)
                tbl.item(1, col).setFont(self.font_bold)

            tbl.item(self.transect_row + 2, 0).setFont(self.font_bold)
            if self.transect_row < 3:
                tbl.scrollToItem(tbl.item(self.transect_row, 0))
            else:
                tbl.scrollToItem(tbl.item(self.transect_row + 2, 0))

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

    def details_table_row_adjust(self, row, col):
        """Allows proper selection of transect to display from the details
        table which has custom header rows.

            Parameter
            =========
            row: int
                row selected
            col: int
                column selected
        """
        row = row - 1
        self.select_transect(row, col)

    def main_premeasurement_table(self):
        """Initialize and populate the premeasurement table."""

        # Initialize and connect the station name and number fields
        font = self.label_site_name.font()
        font.setPointSize(13)
        self.label_site_name.setFont(font)
        self.label_site_number.setFont(font)
        self.ed_site_name.setText(self.meas.station_name)
        if self.meas.qa.user["sta_name"]:
            self.label_site_name.setStyleSheet("background: #ffcc00")
            self.label_site_name.setStyleSheet("QToolTip{font: 12pt}")
            self.label_site_name.setToolTip(self.tr("Missing site name."))
        else:
            self.label_site_name.setStyleSheet("background: white")
            self.label_site_name.setToolTip("")
        try:
            self.ed_site_number.setText(self.meas.station_number)
        except TypeError:
            self.ed_site_number.setText("")
        if self.meas.qa.user["sta_number"]:
            self.label_site_number.setStyleSheet("background: #ffcc00")
            self.label_site_number.setStyleSheet("QToolTip{font: 12pt}")
            self.label_site_number.setToolTip(self.tr("Missing site name."))
        else:
            self.label_site_number.setStyleSheet("background: white")
            self.label_site_number.setToolTip("")

        self.ed_persons.setText(self.meas.persons)
        self.ed_meas_num.setText(self.meas.meas_number)

        self.label_stage_start.setText("Stage start " + self.units["label_L"] + ":")
        self.ed_stage_start.setText(
            "{:3.4f}".format(self.meas.stage_start_m * self.units["L"])
        )
        self.label_stage_end.setText("Stage end " + self.units["label_L"] + ":")
        self.ed_stage_end.setText(
            "{:3.4f}".format(self.meas.stage_end_m * self.units["L"])
        )
        self.label_stage_meas.setText("Stage meas " + self.units["label_L"] + ":")
        self.ed_stage_meas.setText(
            "{:3.4f}".format(self.meas.stage_meas_m * self.units["L"])
        )

        # Setup table
        tbl = self.table_premeas
        ncols = 4
        nrows = 5
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        if len(self.checked_transects_idx) > 0:
            # ADCP Test
            tbl.setItem(0, 0, QtWidgets.QTableWidgetItem(self.tr("ADCP Test: ")))
            tbl.item(0, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(0, 0).setFont(self.font_bold)
            # Determine is a system test was recorded
            if not self.meas.system_tst:
                tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(self.tr("No")))
            else:
                tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(self.tr("Yes")))
            tbl.item(0, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # Report test fails
            tbl.setItem(0, 2, QtWidgets.QTableWidgetItem(self.tr("ADCP Test Fails: ")))
            tbl.item(0, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(0, 2).setFont(self.font_bold)
            num_tests_with_failure = 0
            for test in self.meas.system_tst:
                if hasattr(test, "result"):
                    if (
                        test.result["sysTest"]["n_failed"] is not None
                        and test.result["sysTest"]["n_failed"] > 0
                    ):
                        num_tests_with_failure += 1
            tbl.setItem(
                0,
                3,
                QtWidgets.QTableWidgetItem("{:2.0f}".format(num_tests_with_failure)),
            )
            tbl.item(0, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            # Compass Calibration
            tbl.setItem(
                1, 0, QtWidgets.QTableWidgetItem(self.tr("Compass Calibration: "))
            )
            tbl.item(1, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(1, 0).setFont(self.font_bold)
            if len(self.meas.compass_cal) == 0:
                tbl.setItem(1, 1, QtWidgets.QTableWidgetItem(self.tr("No")))
            else:
                tbl.setItem(1, 1, QtWidgets.QTableWidgetItem(self.tr("Yes")))
            tbl.item(1, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # Compass Evaluation
            tbl.setItem(
                1, 2, QtWidgets.QTableWidgetItem(self.tr("Compass Evaluation: "))
            )
            tbl.item(1, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(1, 2).setFont(self.font_bold)
            if len(self.meas.compass_eval) == 0:
                tbl.setItem(1, 3, QtWidgets.QTableWidgetItem(self.tr("No")))
            else:
                if self.meas.compass_eval[-1].result["compass"]["error"] != "N/A":
                    tbl.setItem(
                        1,
                        3,
                        QtWidgets.QTableWidgetItem(
                            "{:3.1f}".format(
                                self.meas.compass_eval[-1].result["compass"]["error"]
                            )
                        ),
                    )
                else:
                    tbl.setItem(
                        1,
                        3,
                        QtWidgets.QTableWidgetItem(
                            str(self.meas.compass_eval[-1].result["compass"]["error"])
                        ),
                    )
            tbl.item(1, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            # Moving-Bed Test
            tbl.setItem(2, 0, QtWidgets.QTableWidgetItem(self.tr("Moving-Bed Test: ")))
            tbl.item(2, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(2, 0).setFont(self.font_bold)
            if len(self.meas.mb_tests) < 1:
                tbl.setItem(2, 1, QtWidgets.QTableWidgetItem(self.tr("No")))
            else:
                tbl.setItem(2, 1, QtWidgets.QTableWidgetItem(self.tr("Yes")))
            tbl.item(2, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # Report if the test indicated a moving bed
            tbl.setItem(2, 2, QtWidgets.QTableWidgetItem(self.tr("Moving-Bed?: ")))
            tbl.item(2, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(2, 2).setFont(self.font_bold)
            if len(self.meas.mb_tests) < 1:
                tbl.setItem(2, 3, QtWidgets.QTableWidgetItem(self.tr("Unknown")))
            else:
                moving_bed = "No"
                for test in self.meas.mb_tests:
                    if test.selected:
                        if test.moving_bed == "Yes":
                            moving_bed = self.tr("Yes")
                tbl.setItem(2, 3, QtWidgets.QTableWidgetItem(moving_bed))
            tbl.item(2, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            # Independent Temperature
            tbl.setItem(
                3,
                0,
                QtWidgets.QTableWidgetItem(self.tr("Independent Temperature (C): ")),
            )
            tbl.item(3, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(3, 0).setFont(self.font_bold)
            if type(self.meas.ext_temp_chk["user"]) != float or np.isnan(
                self.meas.ext_temp_chk["user"]
            ):
                tbl.setItem(3, 1, QtWidgets.QTableWidgetItem(self.tr("N/A")))
            else:
                tbl.setItem(
                    3,
                    1,
                    QtWidgets.QTableWidgetItem(
                        "{:4.1f}".format(self.meas.ext_temp_chk["user"])
                    ),
                )
            tbl.item(3, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # ADCP temperature
            tbl.setItem(
                3, 2, QtWidgets.QTableWidgetItem(self.tr("ADCP Temperature (C): "))
            )
            tbl.item(3, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(3, 2).setFont(self.font_bold)
            if type(self.meas.ext_temp_chk["adcp"]) != float or np.isnan(
                self.meas.ext_temp_chk["adcp"]
            ):
                avg_temp = Sensors.avg_temperature(self.meas.transects)
                tbl.setItem(
                    3, 3, QtWidgets.QTableWidgetItem("{:4.1f}".format(avg_temp))
                )
            else:
                tbl.setItem(
                    3,
                    3,
                    QtWidgets.QTableWidgetItem(
                        "{:4.1f}".format(self.meas.ext_temp_chk["adcp"])
                    ),
                )
            tbl.item(3, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            # Magnetic variation
            tbl.setItem(
                4, 0, QtWidgets.QTableWidgetItem(self.tr("Magnetic Variation: "))
            )
            tbl.item(4, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(4, 0).setFont(self.font_bold)
            magvar = []
            for transect in self.meas.transects:
                if transect.checked:
                    magvar.append(transect.sensors.heading_deg.internal.mag_var_deg)
            if len(np.unique(magvar)) > 1:
                tbl.setItem(4, 1, QtWidgets.QTableWidgetItem(self.tr("Varies")))
            else:
                tbl.setItem(
                    4, 1, QtWidgets.QTableWidgetItem("{:4.1f}".format(magvar[0]))
                )
            tbl.item(4, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # Heading offset
            tbl.setItem(4, 2, QtWidgets.QTableWidgetItem(self.tr("Heading Offset: ")))
            tbl.item(4, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(4, 2).setFont(self.font_bold)
            hoffset = []
            for transect in self.meas.transects:
                if transect.sensors.heading_deg.external is None:
                    tbl.setItem(4, 3, QtWidgets.QTableWidgetItem(self.tr("N/A")))
                if transect.checked:
                    hoffset.append(
                        transect.sensors.heading_deg.internal.align_correction_deg
                    )
            if len(np.unique(hoffset)) > 1:
                tbl.setItem(4, 3, QtWidgets.QTableWidgetItem(self.tr("Varies")))
            else:
                tbl.setItem(
                    4, 3, QtWidgets.QTableWidgetItem("{:4.1f}".format(hoffset[0]))
                )
            tbl.item(4, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

    def update_site_name(self):
        """Sets the station name to the name entered by the user."""

        self.meas.station_name = self.ed_site_name.text()
        if len(self.meas.station_name) > 0:
            self.label_site_name.setStyleSheet("background: white")
        self.meas.qa.user_qa(self.meas)
        self.messages_tab()
        self.main_premeasurement_table()

    def update_site_number(self):
        """Sets the station number to the number entered by the user."""

        self.meas.station_number = self.ed_site_number.text()
        if len(self.meas.station_number) > 0:
            self.label_site_number.setStyleSheet("background: white")
        self.meas.qa.user_qa(self.meas)
        self.messages_tab()
        self.main_premeasurement_table()

    def update_persons(self):
        """Sets the person(s) to the information entered by the user."""

        self.meas.persons = self.ed_persons.text()
        self.main_premeasurement_table()

    def update_meas_number(self):
        """Sets the measurement number to the information entered by the user."""

        self.meas.meas_number = self.ed_meas_num.text()
        self.main_premeasurement_table()

    def update_stage_start(self):
        """Sets the measurement number to the information entered by the user."""

        stage = self.check_numeric_input(self.ed_stage_start)
        if stage is not None:
            self.meas.stage_start_m = stage / self.units["L"]
            self.meas.stage_meas_m = (
                self.meas.stage_start_m + self.meas.stage_end_m
            ) / 2.0
        self.main_premeasurement_table()

    def update_stage_end(self):
        """Sets the measurement number to the information entered by the user."""

        stage = self.check_numeric_input(self.ed_stage_end)
        if stage is not None:
            self.meas.stage_end_m = stage / self.units["L"]
            self.meas.stage_meas_m = (
                self.meas.stage_start_m + self.meas.stage_end_m
            ) / 2.0
        self.main_premeasurement_table()

    def update_stage_meas(self):
        """Sets the measurement number to the information entered by the user."""

        stage = self.check_numeric_input(self.ed_stage_meas)
        if stage is not None:
            self.meas.stage_meas_m = stage / self.units["L"]
        self.main_premeasurement_table()

    def main_settings_table(self):
        """Create and populate settings table."""

        # Setup table
        tbl = self.table_settings
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows + 3)
        tbl.setColumnCount(14)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        if len(self.checked_transects_idx) > 0:
            # Build column labels using custom_header to create appropriate
            # spans
            self.custom_header(tbl, 0, 0, 3, 1, self.tr("Transect"))
            self.custom_header(tbl, 0, 1, 1, 4, self.tr("Edge"))
            tbl.item(0, 1).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(
                tbl, 1, 1, 1, 2, self.tr("Distance " + self.units["label_L"])
            )
            tbl.item(1, 1).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 2, 1, 1, 1, self.tr("Left"))
            tbl.item(2, 1).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 2, 2, 1, 1, self.tr("Right"))
            tbl.item(2, 2).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 3, 1, 2, self.tr("Type"))
            tbl.item(1, 3).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 2, 3, 1, 1, self.tr("Left"))
            self.custom_header(tbl, 2, 4, 1, 1, self.tr("Right"))
            self.custom_header(
                tbl, 0, 5, 3, 1, self.tr("Draft " + self.units["label_L"])
            )
            self.custom_header(
                tbl,
                0,
                6,
                3,
                1,
                self.tr("Excluded \n Distance " + self.units["label_L"]),
            )
            self.custom_header(tbl, 0, 7, 2, 2, self.tr("Depth"))
            tbl.item(0, 7).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 2, 7, 1, 1, self.tr("Ref"))
            self.custom_header(tbl, 2, 8, 1, 1, self.tr("Comp"))
            self.custom_header(tbl, 0, 9, 2, 2, self.tr("Navigation"))
            tbl.item(0, 9).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 2, 9, 1, 1, self.tr("Ref"))
            self.custom_header(tbl, 2, 10, 1, 1, self.tr("Comp"))
            self.custom_header(tbl, 0, 11, 3, 1, self.tr("Top \n Method"))
            tbl.item(0, 11).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 0, 12, 3, 1, self.tr("Bottom \n Method"))
            tbl.item(0, 12).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 0, 13, 3, 1, self.tr("Exp"))
            tbl.item(0, 13).setTextAlignment(QtCore.Qt.AlignCenter)

            # Add transect data
            for row in range(nrows):
                col = 0
                transect_id = self.checked_transects_idx[row]

                # File/transect name
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].file_name[:-4]
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Left edge distance
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.3f}".format(
                            self.meas.transects[transect_id].edges.left.distance_m
                            * self.units["L"]
                        )
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Right edge distance
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.3f}".format(
                            self.meas.transects[transect_id].edges.right.distance_m
                            * self.units["L"]
                        )
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Left edge type
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].edges.left.type[0:3]
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Right edge type
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].edges.right.type[0:3]
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Draft or transducer depth
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.3f}".format(
                            self.meas.transects[
                                transect_id
                            ].depths.bt_depths.draft_use_m
                            * self.units["L"]
                        )
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Excluded distance below transducer
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:4.2f}".format(
                            self.meas.transects[transect_id].w_vel.excluded_dist_m
                            * self.units["L"]
                        )
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Selected depth reference
                col += 1
                if self.meas.transects[transect_id].depths.selected == "bt_depths":
                    item = "BT"
                elif self.meas.transects[transect_id].depths.selected == "ds_depths":
                    item = "DS"
                elif self.meas.transects[transect_id].depths.selected == "vb_depths":
                    item = "VB"
                else:
                    item = "?"
                tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Use of composite depths
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].depths.composite
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Navigation or velocity reference
                col += 1
                if self.meas.transects[transect_id].boat_vel.selected == "bt_vel":
                    item = "BT"
                elif self.meas.transects[transect_id].boat_vel.selected == "gga_vel":
                    item = "GGA"
                elif self.meas.transects[transect_id].boat_vel.selected == "vtg_vel":
                    item = "VTG"
                else:
                    item = "?"
                tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Composite tracks setting
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].boat_vel.composite
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Extrapolation top method
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].extrap.top_method
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Extrapolation bottom method
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].extrap.bot_method
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Extrapolation exponent
                col += 1
                tbl.setItem(
                    row + 3,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.4f}".format(
                            self.meas.transects[transect_id].extrap.exponent
                        )
                    ),
                )
                tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
                col += 1

                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()

                tbl.item(self.transect_row + 3, 0).setFont(self.font_bold)
                tbl.scrollToItem(tbl.item(self.transect_row + 3, 0))

    def settings_table_row_adjust(self, row, col):
        """Allows proper selection of transect to display from the settings
        table which has custom header rows.

            Parameter
            =========
            row: int
                row selected
            col: int
                column selected
        """
        row = row - 2
        self.select_transect(row, col)

    def main_adcp_table(self):
        """Display ADCP table."""

        # Setup table
        tbl = self.table_adcp
        tbl.setRowCount(4)
        tbl.setColumnCount(4)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        if len(self.checked_transects_idx) > 0:
            # Serial number
            tbl.setItem(0, 0, QtWidgets.QTableWidgetItem(self.tr("Serial Number: ")))
            tbl.item(0, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(0, 0).setFont(self.font_bold)
            # Get serial number from 1st checked transect
            tbl.setItem(
                0,
                1,
                QtWidgets.QTableWidgetItem(
                    self.meas.transects[self.checked_transects_idx[0]].adcp.serial_num
                ),
            )
            tbl.item(0, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # Manufacturer
            tbl.setItem(0, 2, QtWidgets.QTableWidgetItem(self.tr("Manufacturer: ")))
            tbl.item(0, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(0, 2).setFont(self.font_bold)
            tbl.setItem(
                0,
                3,
                QtWidgets.QTableWidgetItem(
                    self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
                ),
            )
            tbl.item(0, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            # Model
            tbl.setItem(1, 0, QtWidgets.QTableWidgetItem(self.tr("Model: ")))
            tbl.item(1, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(1, 0).setFont(self.font_bold)
            tbl.setItem(
                1,
                1,
                QtWidgets.QTableWidgetItem(
                    self.meas.transects[self.checked_transects_idx[0]].adcp.model
                ),
            )
            tbl.item(1, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # Firmware
            tbl.setItem(1, 2, QtWidgets.QTableWidgetItem(self.tr("Firmware: ")))
            tbl.item(1, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(1, 2).setFont(self.font_bold)
            if (
                type(self.meas.transects[self.checked_transects_idx[0]].adcp.firmware)
                == str
            ):
                firmware = self.meas.transects[
                    self.checked_transects_idx[0]
                ].adcp.firmware
            else:
                firmware = str(
                    self.meas.transects[self.checked_transects_idx[0]].adcp.firmware
                )
            tbl.setItem(1, 3, QtWidgets.QTableWidgetItem(firmware))
            tbl.item(1, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            # Frequency
            tbl.setItem(2, 0, QtWidgets.QTableWidgetItem(self.tr("Frequency (kHz): ")))
            tbl.item(2, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(2, 0).setFont(self.font_bold)
            if (
                self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
                == "SonTek"
            ):
                if (
                    self.meas.transects[self.checked_transects_idx[0]].adcp.model
                    == "RS5"
                ):
                    item = "{:4.0f}".format(
                        self.meas.transects[
                            self.checked_transects_idx[0]
                        ].adcp.frequency_khz[0]
                    )
                else:
                    item = "Variable"
            elif (
                self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
                == "Nortek"
            ):
                item = "{:4.0f}".format(
                    self.meas.transects[
                        self.checked_transects_idx[0]
                    ].adcp.frequency_khz[0]
                )
            else:
                item = "{:4.0f}".format(
                    self.meas.transects[
                        self.checked_transects_idx[0]
                    ].adcp.frequency_khz
                )
            tbl.setItem(2, 1, QtWidgets.QTableWidgetItem(item))
            tbl.item(2, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # Depth cell size
            tbl.setItem(
                2, 2, QtWidgets.QTableWidgetItem(self.tr("Depth Cell Size (cm): "))
            )
            tbl.item(2, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(2, 2).setFont(self.font_bold)
            # Check for and handle multiple cell sizes
            cell_sizes = np.array([])
            for n in range(len(self.checked_transects_idx)):
                transect = self.meas.transects[self.checked_transects_idx[n]]
                cell_sizes = np.append(
                    cell_sizes,
                    np.unique(transect.depths.bt_depths.depth_cell_size_m)[:],
                )
            max_cell_size = np.nanmax(cell_sizes) * 100
            min_cell_size = np.nanmin(cell_sizes) * 100
            if max_cell_size - min_cell_size < 1:
                size = "{:3.0f}".format(max_cell_size)
            else:
                size = "{:3.0f} - {:3.0f}".format(min_cell_size, max_cell_size)
            tbl.setItem(2, 3, QtWidgets.QTableWidgetItem(size))
            tbl.item(2, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            # Water mode
            tbl.setItem(3, 0, QtWidgets.QTableWidgetItem(self.tr("Water Mode: ")))
            tbl.item(3, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(3, 0).setFont(self.font_bold)
            if (
                self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
                == "SonTek"
            ):
                item = "Variable"
            elif (
                self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
                == "Nortek"
            ):
                item = "Variable"
            else:
                item = "{:2.0f}".format(
                    self.meas.transects[self.checked_transects_idx[0]].w_vel.water_mode
                )
            tbl.setItem(3, 1, QtWidgets.QTableWidgetItem(item))
            tbl.item(3, 1).setFlags(QtCore.Qt.ItemIsEnabled)

            # Bottom mode
            tbl.setItem(3, 2, QtWidgets.QTableWidgetItem(self.tr("Bottom Mode: ")))
            tbl.item(3, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(3, 2).setFont(self.font_bold)
            if (
                self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
                == "SonTek"
            ):
                item = "Variable"
            elif (
                self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
                == "Nortek"
            ):
                item = "Variable"
            else:
                item = "{:2.0f}".format(
                    self.meas.transects[
                        self.checked_transects_idx[0]
                    ].boat_vel.bt_vel.bottom_mode
                )
            tbl.setItem(3, 3, QtWidgets.QTableWidgetItem(item))
            tbl.item(3, 3).setFlags(QtCore.Qt.ItemIsEnabled)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

    def custom_header(self, tbl, row, col, row_span, col_span, text):
        """Creates custom header than can span multiple rows and columns.

        Parameters
        ----------
        tbl: QTableWidget
            Reference to table
        row: int
            Initial row
        col: int
            Initial column
        row_span: int
            Number of rows to span
        col_span:
            Number of columns to span
        text: str
            Header text"""
        tbl.setItem(row, col, QtWidgets.QTableWidgetItem(text))
        tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, col).setFont(self.font_bold)
        if row_span != 1 or col_span != 1:
            tbl.setSpan(row, col, row_span, col_span)
        tbl.setWordWrap(True)

    # System test tab
    # ===============
    def system_tab(self, idx_systest=0):
        """Initialize and display data in the systems tab.

        Parameters
        ----------
        idx_systest: int
            Identifies the system test to display in the text box.
        """

        # Setup table
        tbl = self.table_systest
        nrows = len(self.meas.system_tst)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(4)
        header_text = [
            self.tr("Date/Time"),
            self.tr("No. Tests"),
            self.tr("No. Failed"),
            self.tr("PT3"),
        ]
        tbl.setHorizontalHeaderLabels(header_text)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.setStyleSheet("QToolTip{font: 12pt}")
        self.display_systest.clear()

        # Add system tests
        if nrows > 0:
            for row, test in enumerate(self.meas.system_tst):
                # Test identifier
                col = 0
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(test.time_stamp))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Number of subtests run
                col += 1
                if test.result["sysTest"]["n_tests"] is None:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                else:
                    tbl.setItem(
                        row,
                        col,
                        QtWidgets.QTableWidgetItem(
                            "{:2.0f}".format(test.result["sysTest"]["n_tests"])
                        ),
                    )
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Number of subtests failed
                col += 1
                if test.result["sysTest"]["n_failed"] is None:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))
                    tbl.item(row, col).setToolTip(self.tr("No system test."))
                else:
                    tbl.setItem(
                        row,
                        col,
                        QtWidgets.QTableWidgetItem(
                            "{:2.0f}".format(test.result["sysTest"]["n_failed"])
                        ),
                    )
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                    if test.result["sysTest"]["n_failed"] > 0:
                        tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                        tbl.item(row, col).setToolTip(
                            self.tr(
                                "One or more system test sets have at least "
                                "one test that failed"
                            )
                        )

                # Status of PT3 tests
                col += 1
                if "pt3" in test.result:
                    if "hard_limit" in test.result["pt3"]:
                        if "high_wide" in test.result["pt3"]["hard_limit"]:
                            if (
                                "corr_table"
                                in test.result["pt3"]["hard_limit"]["high_wide"]
                            ):
                                corr_table = test.result["pt3"]["hard_limit"][
                                    "high_wide"
                                ]["corr_table"]
                                if len(corr_table) > 0:
                                    # All lags past lag 2 should be less
                                    # than 50% of lag 0
                                    qa_threshold = corr_table[0, :] * 0.5
                                    all_lag_check = np.greater(
                                        corr_table[3::, :], qa_threshold
                                    )

                                    # Lag 7 should be less than 25% of lag 0
                                    lag_7_check = np.greater(
                                        corr_table[7, :], corr_table[0, :] * 0.25
                                    )

                                    # If either condition is met for any
                                    # beam the test fails
                                    if (
                                        np.sum(np.sum(all_lag_check))
                                        + np.sum(lag_7_check)
                                        > 1
                                    ):
                                        tbl.setItem(
                                            row,
                                            col,
                                            QtWidgets.QTableWidgetItem("Failed"),
                                        )
                                        tbl.item(row, col).setBackground(
                                            QtGui.QColor(255, 204, 0)
                                        )
                                        tbl.item(row, col).setToolTip(
                                            self.tr(
                                                "One or more PT3 tests in "
                                                "the system test indicate "
                                                "potential EMI"
                                            )
                                        )
                                    else:
                                        tbl.setItem(
                                            row, col, QtWidgets.QTableWidgetItem("Pass")
                                        )
                                        tbl.item(row, col).setBackground(
                                            QtGui.QColor(255, 255, 255)
                                        )

                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Display selected test
            tbl.item(idx_systest, 0).setFont(self.font_bold)
            self.display_systest.clear()
            self.display_systest.textCursor().insertText(
                self.meas.system_tst[idx_systest].data
            )

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        if not self.systest_initialized:
            tbl.cellClicked.connect(self.select_systest)
            self.pb_add_systest.clicked.connect(self.add_systest)
            self.systest_initialized = True

        self.systest_comments_messages()

    def systest_comments_messages(self):
        """Display system test comments and messages in system tab."""

        # Clear current contents
        self.display_systest_comments.clear()
        self.display_systest_messages.clear()
        if self.meas is not None:
            # Comments
            self.display_systest_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                # Display each comment on a new line
                self.display_systest_comments.textCursor().insertText(comment)
                self.display_systest_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_systest_comments.textCursor().insertBlock()

            # Messages
            self.display_systest_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.system_tst["messages"]:
                # Display each comment on a new line
                if type(message) is str:
                    self.display_systest_messages.textCursor().insertText(message)
                else:
                    self.display_systest_messages.textCursor().insertText(message[0])
                self.display_systest_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_systest_messages.textCursor().insertBlock()

            self.update_tab_icons()

    def select_systest(self, row, column):
        """Displays selected system test in text box.

        Parameters
        ==========
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        if column == 0:
            with self.wait_cursor():
                # Set all files to normal font
                nrows = len(self.meas.system_tst)
                for nrow in range(nrows):
                    self.table_systest.item(nrow, 0).setFont(self.font_normal)

                # Set selected file to bold font
                self.table_systest.item(row, 0).setFont(self.font_bold)

                # Update contour and shiptrack plot
                self.system_tab(idx_systest=row)

    def add_systest(self):
        """Allows user to associate a system test with this measurement
        that was collected as part of another measurement.
        """
        add_file = []
        with self.wait_cursor():
            self.pb_add_systest.blockSignals(True)
            # Determine manufacturer
            for transect in self.meas.transects:
                if transect.adcp is not None:
                    manufacturer = transect.adcp.manufacturer
                    if manufacturer == "TRDI":
                        file_type = "TRDI mmt File (*.mmt);;"
                    else:
                        file_type = "System Test File (*.txt);;"
                    break

            # Get folder
            folder = self.default_folder()

            # Get the full names (path + file) of the selected files
            add_file = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                self.tr("Add System Test"),
                folder,
                self.tr(
                    file_type,
                ),
            )[0]

            if len(add_file) > 0:
                # Add TRDI system test(s)
                if manufacturer == "TRDI" and add_file[0].endswith("mmt"):
                    # Read mmt file
                    mmt = MMTtrdi(add_file[0])
                    self.meas.trdi_add_systest(mmt)

                else:
                    # Add multiple SonTek system tests
                    for file in add_file:
                        path, filename = os.path.split(file)
                        self.meas.sontek_add_systest(path, filename)

                # Add message to qa
                self.meas.qa.systest_added(self.meas)

                # Update system test tab
                self.change = True
                self.tab_manager()

            self.pb_add_systest.blockSignals(False)

        # Request user comment
        if len(add_file) > 0:
            self.add_comment()

    # Compass tab
    # ===========
    def compass_tab(self, old_discharge=None):
        """Initialize, setup settings, and display initial data in compass
        tabs.

        Parameters
        ----------
        old_discharge: list
            Discharges computed prior to change made while tab is
            displayed.
        """

        # Setup data table
        tbl = self.table_compass_pr
        tbl.clear()
        table_header = [
            self.tr("Plot / Transect"),
            self.tr("Magnetic \n Variation (deg)"),
            self.tr("Heading \n Offset (deg)"),
            self.tr("Heading \n Source"),
            self.tr("Pitch \n Mean (deg)"),
            self.tr("Pitch \n Std. Dev. (deg)"),
            self.tr("Roll \n Mean (deg)"),
            self.tr("Roll \n Std. Dev. (deg)"),
            self.tr("Discharge \n Previous \n" + self.units["label_Q"]),
            self.tr("Discharge \n Now \n" + self.units["label_Q"]),
            self.tr("Discharge \n % Change"),
        ]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.setStyleSheet("QToolTip{font: 12pt}")

        if not self.compass_pr_initialized:
            # Connect table
            tbl.cellClicked.connect(self.compass_table_clicked)
            tbl.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            tbl.customContextMenuRequested.connect(self.compass_table_right_click)
            # Connect plot variable checkboxes
            self.cb_adcp_compass.stateChanged.connect(self.compass_plot)
            self.cb_ext_compass.stateChanged.connect(self.compass_plot)
            self.cb_mag_field.stateChanged.connect(self.compass_plot)
            self.cb_pitch.stateChanged.connect(self.pr_plot)
            self.cb_roll.stateChanged.connect(self.pr_plot)
            self.compass_pr_initialized = True
            self.pb_add_compass_cal_eval.clicked.connect(self.add_compass_cal_eval)

        # Configure mag field error
        self.cb_mag_field.blockSignals(True)
        self.cb_mag_field.setEnabled(False)
        self.cb_mag_field.setChecked(False)
        for transect_idx in self.checked_transects_idx:
            if self.meas.transects[
                transect_idx
            ].sensors.heading_deg.internal.mag_error is not None and np.logical_not(
                np.all(
                    np.isnan(
                        self.meas.transects[
                            transect_idx
                        ].sensors.heading_deg.internal.mag_error
                    )
                )
            ):
                self.cb_mag_field.setEnabled(True)
                self.cb_mag_field.setChecked(True)
                break
        self.cb_mag_field.blockSignals(False)

        # Configure external heading
        self.cb_ext_compass.blockSignals(True)
        self.cb_ext_compass.setEnabled(False)
        for transect_idx in self.checked_transects_idx:
            if (
                self.meas.transects[transect_idx].sensors.heading_deg.external
                is not None
            ):
                self.cb_ext_compass.setEnabled(True)
                break
            else:
                self.cb_ext_compass.setChecked(False)
        self.cb_ext_compass.blockSignals(False)

        # Update table, graphs, messages, and comments
        if old_discharge is None:
            old_discharge = self.meas.discharge

        self.update_compass_tab(
            tbl=tbl,
            old_discharge=old_discharge,
            new_discharge=self.meas.discharge,
            initial=self.transect_row,
        )

        # Setup list for use by graphics controls
        self.canvases = [self.heading_canvas, self.pr_canvas]
        self.figs = [self.heading_fig, self.pr_fig]
        self.fig_calls = [self.compass_plot, self.pr_plot]
        self.toolbars = [self.heading_toolbar, self.pr_toolbar]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

        # Initialize the calibration/evaluation tab
        self.compass_cal_eval(idx_eval=None)

    def compass_cal_eval(self, idx_cal=None, idx_eval=None):
        """Displays data in the calibration / evaluation tab.

        Parameters
        ----------
        idx_cal: int
            Index of calibration to display in text box
        idx_eval: int
            Index of evaluation to display in text box
        """

        # Setup calibration table
        tblc = self.table_compass_cal
        nrows = len(self.meas.compass_cal)
        tblc.setRowCount(nrows)
        tblc.setColumnCount(1)
        header_text = [self.tr("Date/Time")]
        tblc.setHorizontalHeaderLabels(header_text)
        tblc.horizontalHeader().setFont(self.font_bold)
        tblc.verticalHeader().hide()
        tblc.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tblc.cellClicked.connect(self.select_calibration)

        # Add calibrations
        if nrows > 0:
            for row, test in enumerate(self.meas.compass_cal):
                col = 0
                tblc.setItem(row, col, QtWidgets.QTableWidgetItem(test.time_stamp))
                tblc.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Display selected calibration in text box
            self.display_compass_result.clear()
            if idx_cal is not None:
                tblc.item(idx_cal, 0).setFont(self.font_bold)
                self.display_compass_result.textCursor().insertText(
                    self.meas.compass_cal[idx_cal].data
                )

            tblc.resizeColumnsToContents()
            tblc.resizeRowsToContents()

        # Setup evaluation table
        tble = self.table_compass_eval

        # SonTek has no independent evaluation. Evaluation results are
        # reported with the calibration.
        if (
            self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
            == "SonTek"
        ):
            evals = self.meas.compass_cal
        else:
            evals = self.meas.compass_eval
        nrows = len(evals)
        tble.setRowCount(nrows)
        tble.setColumnCount(2)
        header_text = [self.tr("Date/Time"), self.tr("Error")]
        tble.setHorizontalHeaderLabels(header_text)
        tble.horizontalHeader().setFont(self.font_bold)
        tble.verticalHeader().hide()
        tble.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tble.cellClicked.connect(self.select_evaluation)

        # Add evaluations
        if nrows > 0:
            for row, test in enumerate(evals):
                col = 0
                tble.setItem(row, col, QtWidgets.QTableWidgetItem(test.time_stamp))
                tble.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                col = 1
                if type(test.result["compass"]["error"]) == str:
                    item = test.result["compass"]["error"]
                else:
                    item = "{:2.2f}".format(test.result["compass"]["error"])
                tble.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tble.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            if self.meas.qa.compass["status1"] == "warning":
                tble.item(nrows - 1, 1).setBackground(QtGui.QColor(255, 77, 77))
            elif self.meas.qa.compass["status1"] == "caution":
                tble.item(nrows - 1, 1).setBackground(QtGui.QColor(255, 204, 0))
            else:
                tble.item(nrows - 1, 1).setBackground(QtGui.QColor(255, 255, 255))

        # Display selected evaluation in text box
        if idx_eval is not None:
            self.display_compass_result.clear()
            tble.item(idx_eval, 0).setFont(self.font_bold)
            self.display_compass_result.setPlainText(evals[idx_eval].data)

        tble.resizeColumnsToContents()
        tble.resizeRowsToContents()

        if tble.rowCount() == 0 and tblc.rowCount() == 0:
            self.display_compass_result.clear()

    def compass_comments_messages(self):
        """Displays the messages associated with the compass, pitch,
        and roll and any comments provided by the user.
        """

        # Clear current content
        self.display_compass_comments.clear()
        self.display_compass_messages.clear()
        if self.meas is not None:
            # Comments
            self.display_compass_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                # Display each comment on a new line
                self.display_compass_comments.textCursor().insertText(comment)
                self.display_compass_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_compass_comments.textCursor().insertBlock()

            # Messages
            self.display_compass_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.compass["messages"]:
                # Display each comment on a new line
                if type(message) is str:
                    self.display_compass_messages.textCursor().insertText(message)
                else:
                    self.display_compass_messages.textCursor().insertText(message[0])
                self.display_compass_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_compass_messages.textCursor().insertBlock()

            self.update_tab_icons()
            if self.meas.qa.compass["status1"] != "default":
                self.set_tab_icon(
                    "tab_compass_2_cal",
                    self.meas.qa.compass["status1"],
                    tab_base=self.tab_compass_2,
                )

    def update_compass_tab(self, tbl, old_discharge, new_discharge, initial=None):
        """Populates the table and draws the graphs with the current data.

        Parameters
        ----------
        tbl: QTableWidget
            Reference to the QTableWidget
        old_discharge: list
            List of class QComp with discharge from previous settings,
            same as new if not changes
        new_discharge: list
            List of class QComp with discharge from current settings
        initial: int
            Identifies row that should be checked and displayed in the
            graphs. Used for initial display of data.
        """

        with self.wait_cursor():
            # Populate each row
            for row in range(tbl.rowCount()):
                transect_id = self.checked_transects_idx[row]

                # File/Transect name
                col = 0
                checked = QtWidgets.QTableWidgetItem(
                    self.meas.transects[transect_id].file_name[:-4]
                )
                checked.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(checked))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if transect_id in self.meas.qa.compass["mag_error_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("Change in mag field exceeds 2%")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Magnetic variation
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:3.2f}".format(
                            self.meas.transects[
                                transect_id
                            ].sensors.heading_deg.internal.mag_var_deg
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                # Inconsistent magvar
                if self.meas.qa.compass["magvar"] == 1:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr(
                            "Magnetic variation is not consistent among " "transects"
                        )
                    )

                elif (
                    self.meas.transects[
                        self.meas.checked_transect_idx[0]
                    ].sensors.heading_deg.selected
                    == "internal"
                    and self.meas.qa.compass["lr_water_dir"] == "caution"
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr(
                            "Difference in left and right water direction threshold exeeded"
                        )
                    )

                # Magvar is zero
                elif self.meas.qa.compass["magvar"] == 2:
                    if transect_id in self.meas.qa.compass["magvar_idx"]:
                        tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                        tbl.item(row, col).setToolTip(
                            self.tr(
                                "Magnetic variation is 0 and GPS data are " "present"
                            )
                        )
                        tbl.item(row, col).setToolTip(
                            self.tr("Magnetic variation is 0 and GPS data are present")
                        )

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Heading offset
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:3.2f}".format(
                            self.meas.transects[
                                transect_id
                            ].sensors.heading_deg.internal.align_correction_deg
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.transects[
                        self.meas.checked_transect_idx[0]
                    ].sensors.heading_deg.selected
                    == "external"
                    and self.meas.qa.compass["lr_water_dir"] == "caution"
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr(
                            "Difference in left and right water direction threshold exeeded"
                        )
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Heading source
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].sensors.heading_deg.selected
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Mean pitch
                col += 1
                pitch = getattr(
                    self.meas.transects[transect_id].sensors.pitch_deg,
                    self.meas.transects[transect_id].sensors.pitch_deg.selected,
                )
                item = np.nanmean(pitch.data)
                if np.isnan(item):
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                else:
                    tbl.setItem(
                        row, col, QtWidgets.QTableWidgetItem("{:3.1f}".format(item))
                    )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if transect_id in self.meas.qa.compass["pitch_mean_warning_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                    tbl.item(row, col).setToolTip(
                        self.tr("Mean pitch is greater than 8 deg")
                    )
                elif transect_id in self.meas.qa.compass["pitch_mean_caution_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("Mean pitch is greater than 4 deg")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Pitch standard deviation
                col += 1
                item = np.nanstd(pitch.data, ddof=1)
                if np.isnan(item):
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                else:
                    tbl.setItem(
                        row, col, QtWidgets.QTableWidgetItem("{:3.1f}".format(item))
                    )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if transect_id in self.meas.qa.compass["pitch_std_caution_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("Pitch standard deviation is greater than 5 deg")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Mean roll
                col += 1
                roll = getattr(
                    self.meas.transects[transect_id].sensors.roll_deg,
                    self.meas.transects[transect_id].sensors.roll_deg.selected,
                )
                item = np.nanmean(roll.data)
                if np.isnan(item):
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                else:
                    tbl.setItem(
                        row, col, QtWidgets.QTableWidgetItem("{:3.1f}".format(item))
                    )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if transect_id in self.meas.qa.compass["roll_mean_warning_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                    tbl.item(row, col).setToolTip(
                        self.tr("Mean roll is greater than 8 deg")
                    )
                elif transect_id in self.meas.qa.compass["roll_mean_caution_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("Mean roll is greater than 4 deg")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Roll standard deviation
                col += 1
                item = np.nanstd(roll.data, ddof=1)
                if np.isnan(item):
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                else:
                    tbl.setItem(
                        row, col, QtWidgets.QTableWidgetItem("{:3.1f}".format(item))
                    )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if transect_id in self.meas.qa.compass["roll_std_caution_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("Roll standard deviation is greater than 5 deg")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Discharge from previous settings
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                old_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge from new/current settings
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                new_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent difference in old and new discharges
                col += 1
                if np.abs(old_discharge[transect_id].total) > 0:
                    per_change = (
                        (
                            new_discharge[transect_id].total
                            - old_discharge[transect_id].total
                        )
                        / old_discharge[transect_id].total
                    ) * 100
                    tbl.setItem(
                        row,
                        col,
                        QtWidgets.QTableWidgetItem("{:3.1f}".format(per_change)),
                    )
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # If initial is specified uncheck all rows
                if initial is not None:
                    tbl.item(row, 0).setCheckState(QtCore.Qt.Unchecked)

            # Check the row specified by initial
            if initial is None:
                tbl.item(0, 0).setCheckState(QtCore.Qt.Checked)
            else:
                tbl.item(initial, 0).setCheckState(QtCore.Qt.Checked)

            # Automatically resize rows and columns
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

            # Update graphics, comments, and messages
            self.compass_plot()
            self.pr_plot()
            self.compass_comments_messages()

    def change_table_data(self, tbl, old_discharge, new_discharge):
        """Populates the table and draws the graphs with the current data.

        Parameters
        ----------
        tbl: QTableWidget
            Reference to the QTableWidget
        old_discharge: list
            List class QComp with discharge from previous settings,
            same as new if not changes
        new_discharge: list
            List of class QComp with discharge from current settings
        """

        with self.wait_cursor():
            # Populate each row
            tbl.blockSignals(True)
            for row in range(tbl.rowCount()):
                transect_id = self.checked_transects_idx[row]

                # File/Transect name
                col = 0
                # Magnetic variation
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:3.2f}".format(
                            self.meas.transects[
                                transect_id
                            ].sensors.heading_deg.internal.mag_var_deg
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Heading offset
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:3.2f}".format(
                            self.meas.transects[
                                transect_id
                            ].sensors.heading_deg.internal.align_correction_deg
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Heading source
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].sensors.heading_deg.selected
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Mean pitch
                col += 1

                # Pitch standard deviation
                col += 1

                # Mean roll
                col += 1

                # Roll standard deviation
                col += 1

                # Discharge from previous settings
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                old_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge from new/current settings
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                new_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent difference in old and new discharges
                col += 1
                if np.abs(old_discharge[transect_id].total) > 0:
                    per_change = (
                        (
                            new_discharge[transect_id].total
                            - old_discharge[transect_id].total
                        )
                        / old_discharge[transect_id].total
                    ) * 100
                    tbl.setItem(
                        row,
                        col,
                        QtWidgets.QTableWidgetItem("{:3.1f}".format(per_change)),
                    )
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Update graphics, comments, and messages
            self.compass_plot()
            self.pr_plot()
            self.compass_comments_messages()
            tbl.blockSignals(False)

    @QtCore.pyqtSlot(QtCore.QPoint)
    def compass_table_right_click(self, pos):
        """Manages actions caused by the user right clicking in selected
        columns of the table.

        Parameters
        ----------
        pos: QPoint
            A location in the table
        """

        tbl = self.table_compass_pr
        cell = tbl.itemAt(pos)
        column = cell.column()
        row = cell.row()

        # Change transects plotted
        if column == 0:
            if tbl.item(row, 0).checkState() == QtCore.Qt.Checked:
                tbl.item(row, 0).setCheckState(QtCore.Qt.Unchecked)
            else:
                tbl.item(row, 0).setCheckState(QtCore.Qt.Checked)
            self.compass_plot()
            self.pr_plot()
            self.figs = [self.heading_fig, self.pr_fig]
            self.fig_calls = [self.compass_plot, self.pr_plot]

    @QtCore.pyqtSlot(int, int)
    def compass_table_clicked(self, row, column):
        """Manages actions caused by the user clicking in selected columns
        of the table.

        Parameters
        ----------
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        tbl = self.table_compass_pr
        # Change transects plotted
        if column == 0:
            for nrow in range(tbl.rowCount()):
                tbl.item(nrow, 0).setCheckState(QtCore.Qt.Unchecked)
            self.transect_row = row
            tbl.item(row, 0).setCheckState(QtCore.Qt.Checked)
            tbl.scrollToItem(tbl.item(self.transect_row, 0))

            self.compass_plot()
            self.pr_plot()
            self.figs = [self.heading_fig, self.pr_fig]
            self.fig_calls = [self.compass_plot, self.pr_plot]
            self.change = True
            self.map_change = True

        # Magnetic variation
        if column == 1:
            # Initialize dialog
            magvar_dialog = MagVar(self)
            rsp = magvar_dialog.exec_()
            # Data entered.
            with self.wait_cursor():
                if rsp == QtWidgets.QDialog.Accepted:
                    old_discharge = copy.deepcopy(self.meas.discharge)
                    magvar = self.check_numeric_input(magvar_dialog.ed_magvar)
                    if magvar is not None:
                        # Apply change to selected or all transects
                        if magvar_dialog.rb_all.isChecked():
                            self.meas.change_magvar(magvar=magvar)
                        else:
                            self.meas.change_magvar(
                                magvar=magvar,
                                transect_idx=self.checked_transects_idx[row],
                            )

                        # Update compass tab
                        self.change_table_data(
                            tbl=tbl,
                            old_discharge=old_discharge,
                            new_discharge=self.meas.discharge,
                        )
                        self.change = True
                        self.map_change = True

        # Heading Offset
        elif column == 2:
            if self.h_external_valid:
                # Initialize dialog
                h_offset_dialog = HOffset(self)
                h_offset_entered = h_offset_dialog.exec_()
                # If data entered.
                with self.wait_cursor():
                    if h_offset_entered:
                        old_discharge = copy.deepcopy(self.meas.discharge)
                        h_offset = self.check_numeric_input(h_offset_dialog.ed_hoffset)
                        if h_offset is not None:
                            # Apply change to selected or all transects
                            if h_offset_dialog.rb_all.isChecked():
                                self.meas.change_h_offset(h_offset=h_offset)
                            else:
                                self.meas.change_h_offset(
                                    h_offset=h_offset,
                                    transect_idx=self.checked_transects_idx[row],
                                )

                            # Update compass tab
                            self.update_compass_tab(
                                tbl=tbl,
                                old_discharge=old_discharge,
                                new_discharge=self.meas.discharge,
                            )
                            self.change = True
                            self.map_change = True

        # Heading Source
        elif column == 3:
            # if self.h_external_valid:
            # Initialize dialog
            h_source_dialog = HSource(self)
            if not self.h_external_valid:
                h_source_dialog.rb_external.setEnabled(False)
            else:
                h_source_dialog.rb_external.setEnabled(True)

            current = tbl.item(row, column).text()
            if current == "internal":
                h_source_dialog.rb_internal.setChecked(True)
            elif current == "external":
                h_source_dialog.rb_external.setChecked(True)
            elif current == "user":
                h_source_dialog.rb_no_compass.setChecked(True)

            h_source_entered = h_source_dialog.exec_()
            # If data entered.
            with self.wait_cursor():
                if h_source_entered:
                    old_discharge = copy.deepcopy(self.meas.discharge)
                    if h_source_dialog.rb_internal.isChecked():
                        h_source = "internal"
                    elif h_source_dialog.rb_external.isChecked():
                        h_source = "external"
                    elif h_source_dialog.rb_no_compass.isChecked():
                        h_source = "user"

                    # Apply change to selected or all transects
                    if h_source_dialog.rb_all.isChecked():
                        self.meas.change_h_source(h_source=h_source)
                    else:
                        self.meas.change_h_source(
                            h_source=h_source,
                            transect_idx=self.checked_transects_idx[row],
                        )

                    # Update compass tab
                    self.update_compass_tab(
                        tbl=tbl,
                        old_discharge=old_discharge,
                        new_discharge=self.meas.discharge,
                    )
                    self.change = True
                    self.map_change = True
        self.tab_compass_2_data.setFocus()

    def select_calibration(self, row, column):
        """Displays selected compass calibration.

        Parameters
        ----------
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        if column == 0:
            with self.wait_cursor():
                # Set all files to normal font
                for nrow in range(self.table_compass_cal.rowCount()):
                    self.table_compass_cal.item(nrow, 0).setFont(self.font_normal)
                for nrow in range(self.table_compass_eval.rowCount()):
                    self.table_compass_eval.item(nrow, 0).setFont(self.font_normal)

                # Set selected file to bold font
                self.table_compass_cal.item(row, 0).setFont(self.font_bold)

                # Update
                self.display_compass_result.clear()
                self.display_compass_result.setPlainText(
                    self.meas.compass_cal[row].data
                )

    def select_evaluation(self, row, column):
        """Displays selected compass evaluation.

        Parameters
        ----------
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        if column == 0:
            with self.wait_cursor():
                # Set all files to normal font
                for nrow in range(self.table_compass_cal.rowCount()):
                    self.table_compass_cal.item(nrow, 0).setFont(self.font_normal)
                for nrow in range(self.table_compass_eval.rowCount()):
                    self.table_compass_eval.item(nrow, 0).setFont(self.font_normal)

                # Set selected file to bold font
                self.table_compass_eval.item(row, 0).setFont(self.font_bold)

                # Update
                self.display_compass_result.clear()
                # SonTek has no separate evalutations so the calibration is
                # displayed
                if (
                    self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
                    == "SonTek"
                ):
                    self.display_compass_result.setPlainText(
                        self.meas.compass_cal[row].data
                    )
                else:
                    self.display_compass_result.setPlainText(
                        self.meas.compass_eval[row].data
                    )

    def compass_plot(self):
        """Generates the graph of heading and magnetic change."""

        if self.heading_canvas is None:
            # Create the canvas
            self.heading_canvas = MplCanvas(
                self.graph_heading, width=6, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_heading)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.heading_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.heading_toolbar = NavigationToolbar(self.heading_canvas, self)
            self.heading_toolbar.hide()

            # Initialize the temperature figure and assign to the canvas
        self.heading_fig = HeadingTS(canvas=self.heading_canvas)
        # Create the figure with the specified data
        self.heading_fig.create(
            meas=self.meas,
            checked=self.checked_transects_idx,
            tbl=self.table_compass_pr,
            cb_internal=self.cb_adcp_compass,
            cb_external=self.cb_ext_compass,
            cb_merror=self.cb_mag_field,
            units=self.units,
            x_axis_type=self.x_axis_type,
        )
        if len(self.figs) > 0:
            self.figs[0] = self.heading_fig

        self.clear_zphd()

        # Draw canvas
        self.heading_canvas.draw()

        self.tab_compass_2_data.setFocus()

    def pr_plot(self):
        """Generates the graph of heading and magnetic change."""

        if self.pr_canvas is None:
            # Create the canvas
            self.pr_canvas = MplCanvas(self.graph_pr, width=6, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_pr)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.pr_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.pr_toolbar = NavigationToolbar(self.pr_canvas, self)
            self.pr_toolbar.hide()

            # Initialize the temperature figure and assign to the canvas
        self.pr_fig = PRTS(canvas=self.pr_canvas)
        # Create the figure with the specified data
        self.pr_fig.create(
            meas=self.meas,
            checked=self.checked_transects_idx,
            tbl=self.table_compass_pr,
            cb_pitch=self.cb_pitch,
            cb_roll=self.cb_roll,
            units=self.units,
            x_axis_type=self.x_axis_type,
        )

        self.clear_zphd()

        # Draw canvas
        self.pr_canvas.draw()

        self.tab_compass_2_data.setFocus()

    def add_compass_cal_eval(self):
        """Allows user to associate a compass calibration and/or evalution
        with this measurement that was collected as part of another measurement.
        """

        add_file = []
        with self.wait_cursor():
            self.pb_add_compass_cal_eval.blockSignals(True)
            # Determine manufacturer
            for transect in self.meas.transects:
                if transect.adcp is not None:
                    manufacturer = transect.adcp.manufacturer
                    if manufacturer == "TRDI":
                        file_type = "TRDI mmt File (*.mmt);;"
                    else:
                        file_type = "System Test File (*.txt *.ccal);;"
                    break

            # Get folder
            folder = self.default_folder()

            # Get the full names (path + file) of the selected files
            add_file = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                self.tr("Add Compass Cal/Eval"),
                folder,
                self.tr(
                    file_type,
                ),
            )[0]

            if len(add_file) > 0:
                # Add TRDI system test(s)
                if manufacturer == "TRDI" and add_file[0].endswith("mmt"):
                    # Read mmt file
                    mmt = MMTtrdi(add_file[0])
                    self.meas.trdi_add_compass_cal(mmt)
                    self.meas.trdi_add_compass_eval(mmt)

                else:
                    # Add multiple SonTek system tests
                    for file in add_file:
                        path, filename = os.path.split(file)
                        self.meas.sontek_add_compass_cal(path, filename)

                # Add message to qa
                self.meas.qa.compass_added(self.meas)

                # Update tab
                self.change = True
                self.tab_manager()

            self.pb_add_compass_cal_eval.blockSignals(False)

        # Request user comment
        if len(add_file) > 0:
            self.add_comment()

    # Temperature & Salinity Tab
    # ==========================
    def tempsal_tab(self, old_discharge=None):
        """Initialize tempsal tab and associated settings.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp before changes are made
        """

        # Setup data table
        tbl = self.table_tempsal
        table_header = [
            self.tr("Transect"),
            self.tr("Temperature \n Source"),
            self.tr("Average \n Temperature"),
            self.tr("Average \n Salinity (ppt)"),
            self.tr("Speed of \n Sound Source"),
            self.tr("Speed of \n Sound" + self.units["label_V"]),
            self.tr("Discharge \n Previous \n" + self.units["label_Q"]),
            self.tr("Discharge \n Now \n" + self.units["label_Q"]),
            self.tr("Discharge \n % Change"),
        ]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Update the table, independent, and user temperatures
        if old_discharge is None:
            old_discharge = self.meas.discharge
        self.update_tempsal_tab(
            tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge
        )

        # Display the times series plot of ADCP temperatures
        self.plot_temperature()

        if not self.tempsal_initialized:
            tbl.cellClicked.connect(self.tempsal_table_clicked)

            # Connect temperature units radio buttons
            self.rb_c.toggled.connect(self.change_temp_units)
            self.rb_f.toggled.connect(self.change_temp_units)

            # Setup input validator for independent and adcp user temperature
            reg_ex = QRegExp("^[0-9]*(\.\d*)")
            input_validator = QtGui.QRegExpValidator(reg_ex, self)

            # Connect independent and adcp input option
            self.ed_user_temp.setValidator(input_validator)
            self.ed_adcp_temp.setValidator(input_validator)
            self.pb_ind_temp_apply.clicked.connect(self.apply_user_temp)
            self.pb_adcp_temp_apply.clicked.connect(self.apply_adcp_temp)
            self.ed_user_temp.textChanged.connect(self.user_temp_changed)
            self.ed_adcp_temp.textChanged.connect(self.adcp_temp_changed)
            self.tempsal_initialized = True

        self.canvases = [self.tts_canvas]
        self.toolbars = [self.tts_toolbar]
        self.figs = [self.tts_fig]
        self.fig_calls = [self.plot_temperature]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def update_tempsal_tab(self, tbl, old_discharge, new_discharge):
        """Updates all data displayed on the tempsal tab.

        Parameters
        ----------
        tbl: QWidget
            Reference to QTableWidget
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp  after change applied
        """

        # Initialize array to accumalate all temperature data
        temp_all = np.array([])

        for row in range(tbl.rowCount()):
            # Identify transect associated with the row
            transect_id = self.checked_transects_idx[row]

            # File/transect name
            col = 0
            item = QtWidgets.QTableWidgetItem(
                self.meas.transects[transect_id].file_name[:-4]
            )
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Temperature source
            col += 1
            item = self.tr("Internal (ADCP)")
            if (
                self.meas.transects[transect_id].sensors.temperature_deg_c.selected
                == "user"
            ):
                item = "User"
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average temperature for transect
            col += 1
            temp = getattr(
                self.meas.transects[transect_id].sensors.temperature_deg_c,
                self.meas.transects[transect_id].sensors.temperature_deg_c.selected,
            )
            temp_converted = temp.data
            if self.rb_f.isChecked():
                temp_converted = convert_temperature(
                    temp_in=temp.data, units_in="C", units_out="F"
                )
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:3.1f}".format(np.nanmean(temp_converted))
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Salinity for transect
            col += 1
            sal = getattr(
                self.meas.transects[transect_id].sensors.salinity_ppt,
                self.meas.transects[transect_id].sensors.salinity_ppt.selected,
            )
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem("{:3.1f}".format(np.nanmean(sal.data))),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Speed of sound source
            col += 1
            item = self.tr("User")
            if (
                self.meas.transects[transect_id].sensors.speed_of_sound_mps.selected
                == "internal"
            ):
                if (
                    self.meas.transects[
                        transect_id
                    ].sensors.speed_of_sound_mps.internal.source.strip()
                    == "Calculated"
                ):
                    item = self.tr("Internal (ADCP)")
                else:
                    item = self.tr("Computed")

            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average speed of sound
            col += 1
            sos = getattr(
                self.meas.transects[transect_id].sensors.speed_of_sound_mps,
                self.meas.transects[transect_id].sensors.speed_of_sound_mps.selected,
            )
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:3.1f}".format(np.nanmean(sos.data) * self.units["V"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Discharge before changes
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:8}".format(
                        self.q_digits(
                            old_discharge[transect_id].total * self.units["Q"]
                        )
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Discharge after changes
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:8}".format(
                        self.q_digits(
                            new_discharge[transect_id].total * self.units["Q"]
                        )
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Percent change in discharge
            col += 1
            if np.abs(old_discharge[transect_id].total) > 0:
                per_change = (
                    (
                        new_discharge[transect_id].total
                        - old_discharge[transect_id].total
                    )
                    / old_discharge[transect_id].total
                ) * 100
                tbl.setItem(
                    row, col, QtWidgets.QTableWidgetItem("{:3.1f}".format(per_change))
                )
            else:
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Accumulate all temperature data in a single array used to compute
            # mean temperature
            temp_all = np.append(
                temp_all,
                self.meas.transects[
                    transect_id
                ].sensors.temperature_deg_c.internal.data,
            )

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Display independent temperature reading, if available
        try:
            if np.isnan(self.meas.ext_temp_chk["user"]):
                self.ed_user_temp.setText("")
                self.pb_ind_temp_apply.setEnabled(False)
                self.label_independent.setStyleSheet(
                    "background: #ffcc00; "
                    "font: 12pt MS Shell Dlg"
                    " 2;QToolTip{font: 12pt}"
                )
                self.label_independent.setToolTip(
                    self.tr("No user supplied " "temperature.")
                )
            else:
                temp = float(self.meas.ext_temp_chk["user"])
                if self.rb_f.isChecked():
                    temp = convert_temperature(
                        self.meas.ext_temp_chk["user"], units_in="C", units_out="F"
                    )
                self.ed_user_temp.setText("{:3.1f}".format(temp))
                self.pb_ind_temp_apply.setEnabled(False)
                self.label_independent.setStyleSheet(
                    "background: white; font:" " 12pt MS Shell Dlg 2"
                )
        except (ValueError, TypeError):
            self.ed_user_temp.setText("")
            self.pb_ind_temp_apply.setEnabled(False)

        # Display user provided adcp temperature reading if available
        if np.isnan(self.meas.ext_temp_chk["adcp"]):
            self.ed_adcp_temp.setText("")
            self.pb_adcp_temp_apply.setEnabled(False)
        else:
            try:
                temp = float(self.meas.ext_temp_chk["adcp"])
                if self.rb_f.isChecked():
                    temp = convert_temperature(
                        self.meas.ext_temp_chk["adcp"], units_in="C", units_out="F"
                    )
                self.ed_adcp_temp.setText("{:3.1f}".format(temp))
                self.pb_adcp_temp_apply.setEnabled(False)
            except (ValueError, TypeError):
                self.ed_adcp_temp.setText("")
                self.pb_adcp_temp_apply.setEnabled(False)

        # Display mean temperature measured by ADCP
        temp = np.nanmean(temp_all)
        if self.rb_f.isChecked():
            temp = convert_temperature(temp, units_in="C", units_out="F")
        self.txt_adcp_avg.setText("{:3.1f}".format(temp))

        # Display comments and messages in messages tab
        self.tempsal_comments_messages()

    @QtCore.pyqtSlot(int, int)
    def tempsal_table_clicked(self, row, column):
        """Coordinates changes to the temperature, salinity, and speed of
        sound settings based on the column in the table clicked by the user.

        Parameters
        ----------
        row: int
            row clicked by user
        column: int
            column clicked by user
        """

        tbl = self.table_tempsal
        transect_id = self.checked_transects_idx[row]
        tbl.blockSignals(True)

        # Change temperature
        if column == 1:
            user_temp = None

            # Intialize dialog for user input
            t_source_dialog = TempSource(self)
            if (
                self.meas.transects[transect_id].sensors.temperature_deg_c.selected
                == "internal"
            ):
                t_source_dialog.rb_internal.setChecked(True)
            else:
                t_source_dialog.rb_user.setChecked(True)

            if self.rb_f.isChecked():
                t_source_dialog.rb_user.setText(self.tr("User (F)"))
                if (
                    self.meas.transects[transect_id].sensors.temperature_deg_c.user
                    is not None
                ):
                    display_temp = convert_temperature(
                        self.meas.transects[
                            transect_id
                        ].sensors.temperature_deg_c.user.data[0],
                        units_in="C",
                        units_out="F",
                    )
                else:
                    display_temp = ""
            else:
                t_source_dialog.rb_user.setText(self.tr("User (C)"))
                if (
                    self.meas.transects[transect_id].sensors.temperature_deg_c.user
                    is not None
                ):
                    display_temp = self.meas.transects[
                        transect_id
                    ].sensors.temperature_deg_c.user.data[0]
                else:
                    display_temp = ""
            if type(display_temp) is str:
                t_source_dialog.ed_user_temp.setText(display_temp)
            else:
                t_source_dialog.ed_user_temp.setText("{:3.1f}".format(display_temp))
            t_source_entered = t_source_dialog.exec_()

            if t_source_entered:
                with self.wait_cursor():
                    # Assign data based on change made by user
                    old_discharge = copy.deepcopy(self.meas.discharge)
                    if t_source_dialog.rb_internal.isChecked():
                        t_source = "internal"
                    elif t_source_dialog.rb_user.isChecked():
                        t_source = "user"
                        try:
                            user_temp = float(t_source_dialog.ed_user_temp.text())
                            if self.rb_f.isChecked():
                                user_temp = convert_temperature(
                                    user_temp, units_in="F", units_out="C"
                                )
                        except ValueError:
                            t_source = "internal"

                    # Apply change to all or only selected transect based on
                    # user input
                    if t_source_dialog.rb_all.isChecked():
                        self.meas.change_sos(
                            parameter="temperatureSrc",
                            temperature=user_temp,
                            selected=t_source,
                        )
                    else:
                        self.meas.change_sos(
                            transect_idx=self.checked_transects_idx[row],
                            parameter="temperatureSrc",
                            temperature=user_temp,
                            selected=t_source,
                        )

                    # Update the tempsal tab
                    self.meas.qa.check_tempsal_settings(self.meas)
                    self.update_tempsal_tab(
                        tbl=tbl,
                        old_discharge=old_discharge,
                        new_discharge=self.meas.discharge,
                    )
                    self.change = True
                    self.map_change = True

        # Change salinity
        elif column == 3:
            # Intialize dialog for user input
            salinity_dialog = Salinity(self)
            salinity_entered = salinity_dialog.exec_()

            if salinity_entered:
                with self.wait_cursor():
                    # Assign data based on change made by user
                    old_discharge = copy.deepcopy(self.meas.discharge)
                    try:
                        salinity = float(salinity_dialog.ed_salinity.text())

                        # Apply change to all or only selected transect based on user input
                        if salinity_dialog.rb_all.isChecked():
                            self.meas.change_sos(
                                parameter="salinity", salinity=salinity
                            )
                        else:
                            self.meas.change_sos(
                                transect_idx=self.checked_transects_idx[row],
                                parameter="salinity",
                                salinity=salinity,
                            )
                        # Update the tempsal tab
                        self.meas.qa.check_tempsal_settings(self.meas)
                        self.update_tempsal_tab(
                            tbl=tbl,
                            old_discharge=old_discharge,
                            new_discharge=self.meas.discharge,
                        )
                        self.change = True
                        self.map_change = True
                    except ValueError:
                        pass

        # Change speed of sound
        elif column == 4:
            user_sos = None

            # Initialize dialog for user input
            sos_setting = self.meas.transects[
                transect_id
            ].sensors.speed_of_sound_mps.selected
            sos = None
            if sos_setting == "user":
                sos = getattr(
                    self.meas.transects[transect_id].sensors.speed_of_sound_mps,
                    self.meas.transects[
                        transect_id
                    ].sensors.speed_of_sound_mps.selected,
                ).data[0]

            sos_source_dialog = SOSSource(self.units, setting=sos_setting, sos=sos)
            sos_source_entered = sos_source_dialog.exec_()

            if sos_source_entered:
                with self.wait_cursor():
                    # Assign data based on change made by user
                    old_discharge = copy.deepcopy(self.meas.discharge)
                    if sos_source_dialog.rb_internal.isChecked():
                        sos_source = "internal"
                    elif sos_source_dialog.rb_user.isChecked():
                        sos_source = "user"
                        try:
                            user_sos = (
                                float(sos_source_dialog.ed_sos_user.text())
                                / self.units["V"]
                            )
                        except ValueError:
                            sos_source = "internal"

                    # Apply change to all or only selected transect based on
                    # user input
                    if sos_source_dialog.rb_all.isChecked():
                        self.meas.change_sos(
                            parameter="sosSrc", speed=user_sos, selected=sos_source
                        )
                    else:
                        self.meas.change_sos(
                            transect_idx=self.checked_transects_idx[row],
                            parameter="sosSrc",
                            speed=user_sos,
                            selected=sos_source,
                        )

                    # Update the tempsal tab
                    self.meas.qa.check_tempsal_settings(self.meas)
                    self.update_tempsal_tab(
                        tbl=tbl,
                        old_discharge=old_discharge,
                        new_discharge=self.meas.discharge,
                    )
                    self.change = True
                    self.map_change = True

        tbl.blockSignals(False)

    def tempsal_comments_messages(self):
        """Displays comments and messages associated with temperature,
        salinity, and speed of sound in Messages tab.
        """

        # Clear comments and messages
        self.display_tempsal_comments.clear()
        self.display_tempsal_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_tempsal_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_tempsal_comments.textCursor().insertText(comment)
                self.display_tempsal_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_tempsal_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_tempsal_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.temperature["messages"]:
                if type(message) is str:
                    self.display_tempsal_messages.textCursor().insertText(message)
                else:
                    self.display_tempsal_messages.textCursor().insertText(message[0])
                self.display_tempsal_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_tempsal_messages.textCursor().insertBlock()
            self.update_tab_icons()

    def plot_temperature(self):
        """Generates the graph of temperature."""

        if self.tts_canvas is None:
            # Create the canvas
            self.tts_canvas = MplCanvas(
                self.graph_temperature, width=4, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_temperature)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.tts_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.tts_toolbar = NavigationToolbar(self.tts_canvas, self)
            self.tts_toolbar.hide()

        # Initialize the temperature figure and assign to the canvas
        self.tts_fig = TemperatureTS(canvas=self.tts_canvas)
        # Create the figure with the specified data
        self.tts_fig.create(meas=self.meas, rb_f=self.rb_f)

        # Draw canvas
        self.tts_canvas.draw()

    def change_temp_units(self):
        """Updates the display when the user changes the temperature units.
        Note: changing the units does not change the actual data only the units
        used to display the data.
        """

        self.update_tempsal_tab(
            tbl=self.table_tempsal,
            old_discharge=self.meas.discharge,
            new_discharge=self.meas.discharge,
        )

        self.plot_temperature()

    def apply_user_temp(self):
        """Applies a user entered value for the independent temperature.
        This change does not affect the measured discharge but could change
        the automatic QA/QC messages.
        """

        # Set cursor focus onto the table to avoid multiple calls the the
        # adcp_temp_changed function
        self.table_tempsal.setFocus()

        # If data has been entered, convert the data to Celsius if necessary
        if len(self.ed_user_temp.text()) > 0:
            temp = float(self.ed_user_temp.text())
            if self.rb_f.isChecked():
                temp = convert_temperature(temp, "F", "C")
            self.label_independent.setStyleSheet(
                "background: white; font: 12pt MS Shell Dlg 2"
            )
        else:
            temp = np.nan

        # Update the measurement with the new ADCP temperature
        self.meas.ext_temp_chk["user"] = temp

        # Apply qa checks
        self.meas.qa.temperature_qa(self.meas)
        self.meas.qa.check_tempsal_settings(self.meas)

        # Update GUI
        try:
            if np.isnan(self.meas.ext_temp_chk["user"]):
                self.ed_user_temp.setText("")
                self.pb_ind_temp_apply.setEnabled(False)
                self.label_independent.setStyleSheet(
                    "background: #ffcc00; font: 12pt MS Shell Dlg "
                    "2;QToolTip{font: 12pt}"
                )
                self.label_independent.setToolTip(
                    self.tr("No user supplied temperature.")
                )
            else:
                temp = float(self.meas.ext_temp_chk["user"])
                if self.rb_f.isChecked():
                    temp = convert_temperature(
                        self.meas.ext_temp_chk["user"], units_in="C", units_out="F"
                    )
                self.ed_user_temp.setText("{:3.1f}".format(temp))
                self.pb_ind_temp_apply.setEnabled(False)
                self.label_independent.setStyleSheet(
                    "background: white; font: 12pt MS Shell Dlg 2"
                )
        except (ValueError, TypeError):
            self.ed_user_temp.setText("")
            self.pb_ind_temp_apply.setEnabled(False)
        self.tempsal_comments_messages()
        self.pb_ind_temp_apply.setEnabled(False)
        self.change = True
        self.map_change = True

    def apply_adcp_temp(self):
        """Applies a user entered value for the ADCP temperature. This
        change does not affect the measured discharge but could change the
        automatic QA/QC messages.
        """

        # Set cursor focus onto the table to avoid multiple calls the the
        # adcp_temp_changed funtion
        self.table_tempsal.setFocus()

        # If data has been entered, convert the data to Celsius if necessary
        if len(self.ed_adcp_temp.text()) > 0:
            temp = float(self.ed_adcp_temp.text())
            if self.rb_f.isChecked():
                temp = convert_temperature(temp, "F", "C")
        else:
            temp = np.nan

        # Update the measurement with the new ADCP temperature
        self.meas.ext_temp_chk["adcp"] = temp

        # Apply qa checks
        self.meas.qa.temperature_qa(self.meas)
        self.meas.qa.check_tempsal_settings(self.meas)

        # Update GUI
        self.tempsal_comments_messages()
        self.pb_adcp_temp_apply.setEnabled(False)
        self.change = True
        self.map_change = True

    def user_temp_changed(self):
        """Enables the apply button if the user enters a valid value in the
        independent temp box.
        """

        self.pb_ind_temp_apply.setEnabled(True)

    def adcp_temp_changed(self):
        """Enables the apply button if the user enters a valid value in the
        ADCP temp box.
        """

        self.pb_adcp_temp_apply.setEnabled(True)

    # Moving-Bed Test Tab
    # ===================
    def movbedtst_tab(self):
        """Initialize, setup settings, and display initial data in
        moving-bed test tab.
        """

        # Setup data table
        tbl = self.table_moving_bed
        table_header = [
            self.tr("User \n Valid"),
            self.tr("Used for \n Correction"),
            self.tr("Use GPS \n for Test"),
            self.tr("Filename"),
            self.tr("Type"),
            self.tr("Duration \n (s)"),
            self.tr("Distance \n Upstream" + self.units["label_L"]),
            self.tr("Moving-Bed \n Speed" + self.units["label_V"]),
            self.tr("Moving-Bed \n Direction (deg)"),
            self.tr("Flow \n Speed" + self.units["label_V"]),
            self.tr("Flow \n Direction (deg)"),
            self.tr("% Invalid \n BT"),
            self.tr("Compass \n Error (deg"),
            self.tr("% Moving \n Bed"),
            self.tr("Moving \n Bed"),
            self.tr("Quality"),
        ]

        ncols = len(table_header)
        nrows = len(self.meas.mb_tests)

        # Display option to manually certify there is no moving bed, if the
        # option is available or if the loaded data used that option.
        if nrows == 0 and (
            self.allow_observed_no_moving_bed or self.meas.observed_no_moving_bed
        ):
            self.cb_mb_observed_no.show()
            self.cb_mb_observed_no.setChecked(self.meas.observed_no_moving_bed)
        else:
            self.cb_mb_observed_no.hide()
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Display content
        self.update_mb_table()
        self.mb_comments_messages()

        if not self.mb_initialized:
            tbl.cellClicked.connect(self.mb_table_clicked)

            # Initialize checkbox settings
            self.cb_mb_bt.setCheckState(QtCore.Qt.Checked)
            self.cb_mb_gga.setCheckState(QtCore.Qt.Unchecked)
            self.cb_mb_vtg.setCheckState(QtCore.Qt.Unchecked)
            self.cb_mb_vectors.setCheckState(QtCore.Qt.Checked)

            # Connect plot variable checkboxes
            self.cb_mb_bt.stateChanged.connect(self.mb_plot_change)
            self.cb_mb_gga.stateChanged.connect(self.mb_plot_change)
            self.cb_mb_vtg.stateChanged.connect(self.mb_plot_change)
            self.cb_mb_vectors.stateChanged.connect(self.mb_plot_change)
            self.cb_mb_observed_no.stateChanged.connect(self.mb_observed_change)

            self.pb_add_moving_bed_test.clicked.connect(self.mb_add_test)

            self.mb_initialized = True
        self.mb_row = self.mb_row_selected
        self.mb_plots(idx=self.mb_row_selected)

    def update_mb_table(self):
        """Populates the moving-bed table with the current settings and data."""

        with self.wait_cursor():
            tbl = self.table_moving_bed
            tbl.blockSignals(True)
            self.mb_row_selected = 0
            has_gps = []
            # Hide GPS column unless GPS data are used
            tbl.setColumnHidden(2, True)
            # Populate each row
            for row in range(tbl.rowCount()):
                # User Valid
                col = 0
                checked = QtWidgets.QTableWidgetItem("")
                checked.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(checked))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if self.meas.mb_tests[row].user_valid:
                    tbl.item(row, col).setCheckState(QtCore.Qt.Checked)
                else:
                    tbl.item(row, col).setCheckState(QtCore.Qt.Unchecked)

                # Use for Correction
                col += 1
                checked2 = QtWidgets.QTableWidgetItem("")
                checked2.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(checked2))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                tbl.item(row, col).setCheckState(QtCore.Qt.Unchecked)
                if self.meas.mb_tests[row].use_2_correct:
                    if self.meas.mb_tests[row].selected:
                        tbl.item(row, col).setCheckState(QtCore.Qt.Checked)

                # Use GPS for test
                col += 1
                checked3 = QtWidgets.QTableWidgetItem("")
                checked3.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(checked3))
                tbl.item(row, col).setCheckState(QtCore.Qt.Unchecked)
                if self.meas.mb_tests[row].ref == "GPS":
                    tbl.item(row, col).setCheckState(QtCore.Qt.Checked)
                has_gps.append(
                    np.logical_not(np.isnan(self.meas.mb_tests[row].gps_percent_mb))
                )

                # Filename
                col += 1
                item = os.path.basename(self.meas.mb_tests[row].transect.file_name)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item[:-4]))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if self.meas.mb_tests[row].selected:
                    tbl.item(row, col).setFont(self.font_bold)
                    self.mb_row_selected = row

                # Type
                col += 1
                tbl.setItem(
                    row, col, QtWidgets.QTableWidgetItem(self.meas.mb_tests[row].type)
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Duration
                col += 1
                item = "{:4.1f}".format(self.meas.mb_tests[row].duration_sec)
                if "nan" in item:
                    item = ""
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Distance Upstream
                col += 1
                item = "{:4.1f}".format(
                    self.meas.mb_tests[row].dist_us_m * self.units["L"]
                )
                if "nan" in item:
                    item = ""
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving-Bed Speed
                col += 1
                item = "{:3.2f}".format(
                    self.meas.mb_tests[row].mb_spd_mps * self.units["V"]
                )
                if "nan" in item:
                    item = ""
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving-Bed Direction
                col += 1
                # Don't show direction for BT stationary
                if np.isnan(self.meas.mb_tests[row].mb_dir):
                    item = ""
                else:
                    item = "{:3.1f}".format(self.meas.mb_tests[row].mb_dir)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Flow Speed
                col += 1
                item = "{:3.1f}".format(
                    self.meas.mb_tests[row].flow_spd_mps * self.units["V"]
                )
                if "nan" in item:
                    item = ""
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Flow Direction
                col += 1
                if np.isnan(self.meas.mb_tests[row].flow_dir):
                    item = ""
                else:
                    item = "{:3.1f}".format(self.meas.mb_tests[row].flow_dir)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent Invalid BT
                col += 1
                item = "{:3.1f}".format(self.meas.mb_tests[row].percent_invalid_bt)
                if "nan" in item:
                    item = ""
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Compass Error
                col += 1
                if type(self.meas.mb_tests[row].compass_diff_deg) is not list:
                    item = "{:3.1f}".format(self.meas.mb_tests[row].compass_diff_deg)
                    if "nan" in item:
                        item = ""
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent Moving Bed
                col += 1
                item = "{:3.1f}".format(self.meas.mb_tests[row].percent_mb)
                if "nan" in item:
                    item = ""
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving Bed
                col += 1
                item = self.meas.mb_tests[row].moving_bed
                if "nan" in item:
                    item = ""
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Quality
                col += 1
                item = self.meas.mb_tests[row].test_quality
                if "nan" in item:
                    item = ""
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Automatically resize rows and columns
                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()
                tbl.blockSignals(False)

            # If GPS data are used in any test, show GPS column
            if any(has_gps):
                tbl.setColumnHidden(2, False)

    def mb_table_clicked(self, row, column):
        """Manages actions caused by the user clicking in selected columns of the table.

        Parameters
        ----------
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        tbl = self.table_moving_bed
        reprocess_measurement = True
        tbl.blockSignals(True)

        # User valid
        if column == 0:
            if tbl.item(row, 0).checkState() == QtCore.Qt.Checked:
                self.meas.mb_tests[row].user_valid = False
                self.add_comment()
            else:
                self.meas.mb_tests[row].user_valid = True
                self.add_comment()

            self.meas.mb_tests = MovingBedTests.auto_use_2_correct(
                moving_bed_tests=self.meas.mb_tests,
                boat_ref=self.meas.transects[
                    self.checked_transects_idx[0]
                ].w_vel.nav_ref,
            )

        # Use to correct, manual override
        if column == 1:
            if self.meas.transects[self.checked_transects_idx[0]].w_vel.nav_ref == "BT":
                quality = tbl.item(row, 15).text()
                # Identify a moving-bed condition
                moving_bed_idx = []
                for n, test in enumerate(self.meas.mb_tests):
                    if test.selected:
                        if test.moving_bed == "Yes":
                            moving_bed_idx.append(n)

                if quality == "Manual":
                    # Cancel Manual
                    self.meas.mb_tests[row].use_2_correct = False
                    self.meas.mb_tests[row].moving_bed = "Unknown"
                    self.meas.mb_tests[row].selected = False
                    self.meas.mb_tests[row].test_quality = "Errors"
                    self.meas.mb_tests = MovingBedTests.auto_use_2_correct(
                        moving_bed_tests=self.meas.mb_tests,
                        boat_ref=self.meas.transects[
                            self.checked_transects_idx[0]
                        ].w_vel.nav_ref,
                    )

                elif quality == "Errors":
                    # Manual override
                    # Warn user and force acknowledgement before proceeding
                    user_warning = QtWidgets.QMessageBox.question(
                        self,
                        self.tr("Moving-Bed Test Manual Override"),
                        self.tr(
                            "QRev has determined this moving-bed test has"
                            " critical errors and does not recommend "
                            "using it for correction. If you choose to "
                            "use the test anyway you will be required to "
                            "justify its use."
                        ),
                        QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                        QtWidgets.QMessageBox.Cancel,
                    )
                    if user_warning == QtWidgets.QMessageBox.Ok:
                        # Apply manual override
                        self.add_comment()
                        self.meas.mb_tests[row].use_2_correct = True
                        self.meas.mb_tests[row].moving_bed = "Yes"
                        self.meas.mb_tests[row].selected = True
                        self.meas.mb_tests[row].test_quality = "Manual"
                    else:
                        reprocess_measurement = False

                elif len(moving_bed_idx) > 0:
                    if row in moving_bed_idx:
                        if tbl.item(row, 1).checkState() == QtCore.Qt.Checked:
                            self.meas.mb_tests[row].use_2_correct = False
                            self.add_comment()
                        else:
                            # Apply setting
                            self.meas.mb_tests[row].use_2_correct = True

                            # Check to make sure the selected test are of the same type
                            test_type = []
                            test_quality = []
                            for test in self.meas.mb_tests:
                                if test.selected:
                                    test_type.append(test.type)
                                    test_quality = test.test_quality
                            unique_types = set(test_type)
                            if len(unique_types) == 1:
                                # Check for errors
                                if "Errors" not in test_quality:
                                    # Multiple loops not allowed
                                    if test_type == "Loop" and len(test_type) > 1:
                                        self.meas.mb_tests[row].use_2_correct = False
                                        reprocess_measurement = False
                                        self.popup_message(
                                            self.tr(
                                                "Only one loop can be applied. "
                                                "Select the best loop."
                                            )
                                        )

                            else:
                                # Mixing of stationary and loop tests are not allowed
                                self.meas.mb_tests[row].use_2_correct = False
                                reprocess_measurement = False
                                self.popup_message(
                                    self.tr(
                                        "Application of mixed moving-bed test types is "
                                        "not allowed.S elect only one loop or one or more"
                                        "stationary tests."
                                    )
                                )
                    else:
                        self.popup_message(
                            self.tr(
                                "This moving-bed test is not being used. "
                                "Only those tests with Bold file names can be used."
                            )
                        )

                else:
                    # No moving-bed, so no moving-bed correction is applied
                    reprocess_measurement = False
                    self.popup_message(
                        self.tr("There is no moving-bed. Correction cannot be applied.")
                    )
            else:
                self.popup_message(
                    self.tr(
                        "Bottom track is not the selected reference. "
                        "A moving-bed correction cannot be applied."
                    )
                )

        # Use GPS for Test
        elif column == 2:
            # Determine if selected test has been processed using GPS
            if np.isnan(self.meas.mb_tests[row].gps_percent_mb):
                tbl.item(row, column).setCheckState(QtCore.Qt.Unchecked)
                reprocess_measurement = False
                self.change = False
            else:
                if tbl.item(row, column).checkState() == QtCore.Qt.Checked:
                    self.meas.mb_tests[row].change_ref(ref="GPS")
                else:
                    self.meas.mb_tests[row].change_ref(ref="BT")
                self.meas.mb_tests = MovingBedTests.auto_use_2_correct(
                    moving_bed_tests=self.meas.mb_tests,
                    boat_ref=self.meas.transects[
                        self.checked_transects_idx[0]
                    ].w_vel.nav_ref,
                )

        # Data to plot
        elif column == 3:
            self.mb_plots(idx=row)
            self.mb_row = row
            reprocess_measurement = False
            self.change = False

        # If changes were made reprocess the measurement
        if reprocess_measurement:
            with self.wait_cursor():
                self.meas.compute_discharge()
                self.meas.compute_uncertainty()
                self.meas.qa.moving_bed_qa(self.meas)
                self.change = True
                self.map_change = True

        self.update_mb_table()
        self.mb_comments_messages()

        tbl.blockSignals(False)
        self.tab_mbt_2_data.setFocus()

    def mb_plots(self, idx=0):
        """Creates graphics specific to the type of moving-bed test.

        Parameters
        ----------
        idx: int
            Index of the test to be plotted.
        """
        self.cb_mb_bt.blockSignals(True)
        self.cb_mb_gga.blockSignals(True)
        self.cb_mb_vtg.blockSignals(True)
        self.cb_mb_vectors.blockSignals(True)

        if self.mb_shiptrack_fig is not None:
            self.mb_shiptrack_fig.fig.clear()
            self.mb_ts_fig.fig.clear()
            self.mb_shiptrack_canvas.draw()
            self.mb_ts_canvas.draw()

        if len(self.meas.mb_tests) > 0:
            # Show name of test plotted
            try:
                item = os.path.basename(self.meas.mb_tests[idx].transect.file_name)
            except IndexError:
                item = self.meas.mb_tests[idx].transect.file_name
            self.txt_mb_plotted.setText(item[:-4])

            # Always show the shiptrack plot
            self.mb_shiptrack(transect=self.meas.mb_tests[idx].transect)

            # Determine what plots to display based on test type
            if self.meas.mb_tests[idx].type == "Loop":
                self.mb_boat_speed(transect=self.meas.mb_tests[idx].transect)
            else:
                self.stationary(mb_test=self.meas.mb_tests[idx])

            # Setup list for use by graphics controls
            self.canvases = [self.mb_shiptrack_canvas, self.mb_ts_canvas]
            self.figs = [self.mb_shiptrack_fig, self.mb_ts_fig]
            self.fig_calls = [self.mb_shiptrack, self.mb_plots]
            self.toolbars = [self.mb_shiptrack_toolbar, self.mb_ts_toolbar]
            self.ui_parents = [i.parent() for i in self.canvases]
            self.figs_menu_connection()

            # Reset data cursor to work with new figure
            if self.actionData_Cursor.isChecked():
                self.data_cursor()
        else:
            # Disable user checkboxes if no tests are available
            self.cb_mb_bt.setEnabled(False)
            self.cb_mb_gga.setEnabled(False)
            self.cb_mb_vtg.setEnabled(False)
            self.cb_mb_vectors.setEnabled(False)
            self.txt_mb_plotted.setText("")

        self.cb_mb_bt.blockSignals(False)
        self.cb_mb_gga.blockSignals(False)
        self.cb_mb_vtg.blockSignals(False)
        self.cb_mb_vectors.blockSignals(False)

    def mb_shiptrack(self, transect):
        """Creates shiptrack plot for data in transect.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData with data to be plotted.
        """

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.mb_shiptrack_canvas is None:
            # Create the canvas
            self.mb_shiptrack_canvas = MplCanvas(
                parent=self.graph_mb_st, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_mb_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.mb_shiptrack_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.mb_shiptrack_toolbar = NavigationToolbar(
                self.mb_shiptrack_canvas, self
            )
            self.mb_shiptrack_toolbar.hide()

        # Initialize the shiptrack figure and assign to the canvas
        self.mb_shiptrack_fig = Shiptrack(canvas=self.mb_shiptrack_canvas)
        # Create the figure with the specified data
        self.mb_shiptrack_fig.create(
            transect=transect,
            units=self.units,
            cb=True,
            cb_bt=self.cb_mb_bt,
            cb_gga=self.cb_mb_gga,
            cb_vtg=self.cb_mb_vtg,
            cb_vectors=self.cb_mb_vectors,
            edge_start=True,
        )

        # Draw canvas
        self.mb_shiptrack_canvas.draw()

    def mb_boat_speed(self, transect):
        """Creates boat speed plot for data in transect.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData with data to be plotted.
        """

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.mb_ts_canvas is None:
            # Create the canvas
            self.mb_ts_canvas = MplCanvas(
                parent=self.graph_mb_ts, width=8, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_mb_ts)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.mb_ts_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.mb_ts_toolbar = NavigationToolbar(self.mb_ts_canvas, self)
            self.mb_ts_toolbar.hide()

        # Initialize the boat speed figure and assign to the canvas
        self.mb_ts_fig = BoatSpeed(canvas=self.mb_ts_canvas)
        # Create the figure with the specified data
        self.mb_ts_fig.create(
            transect=transect,
            units=self.units,
            cb=True,
            cb_bt=self.cb_mb_bt,
            cb_gga=self.cb_mb_gga,
            cb_vtg=self.cb_mb_vtg,
            x_axis_type=self.x_axis_type,
        )

        # Draw canvas
        self.mb_ts_canvas.draw()

    def stationary(self, mb_test):
        """Creates the plots for analyzing stationary moving-bed tests.

        Parameters
        ----------
        mb_test: MovingBedTests
            Object of MovingBedTests with data to be plotted.
        """

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.mb_ts_canvas is None:
            # Create the canvas
            self.mb_ts_canvas = MplCanvas(
                parent=self.graph_mb_ts, width=8, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_mb_ts)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add canvas
            layout.addWidget(self.mb_ts_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.mb_ts_toolbar = NavigationToolbar(self.mb_ts_canvas, self)
            self.mb_ts_toolbar.hide()

        # Initialize the stationary figure and assign to the canvas
        self.mb_ts_fig = StationaryGraphs(canvas=self.mb_ts_canvas)
        # Create the figure with the specified data
        self.mb_ts_fig.create(
            mb_test=mb_test, units=self.units, x_axis_type=self.x_axis_type
        )
        # Draw canvas
        self.mb_ts_canvas.draw()

    def mb_plot_change(self):
        """Coordinates changes in what references should be displayed in the
        boat speed and shiptrack plots.
        """

        # Shiptrack
        self.mb_shiptrack_fig.change()

        # Boat speed
        # Note if mb_ts_fig is set to stationary the StationaryGraphs class
        # has a change method with does nothing, to maintain compatibility.
        self.mb_ts_fig.change()
        self.tab_mbt_2_data.setFocus()

    def mb_observed_change(self):
        """Sets observation of no moving bed."""

        with self.wait_cursor():
            if self.cb_mb_observed_no.isChecked():
                self.meas.observed_no_moving_bed = True
            else:
                self.meas.observed_no_moving_bed = False

            self.meas.compute_discharge()
            self.meas.compute_uncertainty()
            self.meas.qa.moving_bed_qa(self.meas)
            self.update_tab_icons()
            self.change = True
            self.map_change = True

    def mb_comments_messages(self):
        """Displays comments and messages associated with moving-bed tests
        in Messages tab.
        """

        # Clear comments and messages
        self.display_mb_comments.clear()
        self.display_mb_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_mb_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_mb_comments.textCursor().insertText(comment)
                self.display_mb_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_mb_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_mb_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.movingbed["messages"]:
                if type(message) is str:
                    self.display_mb_messages.textCursor().insertText(message)
                else:
                    self.display_mb_messages.textCursor().insertText(message[0])
                self.display_mb_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_mb_messages.textCursor().insertBlock()

            for test in self.meas.mb_tests:
                test_file = test.transect.file_name[:-4]
                if len(test.messages) > 0:
                    self.display_mb_messages.textCursor().insertText(" ")
                    self.display_mb_messages.moveCursor(QtGui.QTextCursor.End)
                    self.display_mb_messages.textCursor().insertBlock()
                    self.display_mb_messages.textCursor().insertText(test_file)
                    self.display_mb_messages.moveCursor(QtGui.QTextCursor.End)
                    self.display_mb_messages.textCursor().insertBlock()
                    for message in test.messages:
                        self.display_mb_messages.textCursor().insertText(message)
                        self.display_mb_messages.moveCursor(QtGui.QTextCursor.End)
                        self.display_mb_messages.textCursor().insertBlock()

            self.update_tab_icons()

    def mb_add_test(self):
        """Allows user to associate a moving-bed test
        with this measurement that was collected as part of another measurement.
        """

        add_file = []

        with self.wait_cursor():
            self.pb_add_moving_bed_test.blockSignals(True)
            # Determine manufacturer
            for transect in self.meas.transects:
                if transect.adcp is not None:
                    manufacturer = transect.adcp.manufacturer
                    if manufacturer == "TRDI":
                        file_type = "TRDI mmt File (*.mmt);;"
                    else:
                        file_type = "Moving-bed test file (*.mat);;"
                    break

            # Get folder
            folder = self.default_folder()

            # Get the full names (path + file) of the selected files
            add_file = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                self.tr("Add Moving-Bed Test"),
                folder,
                self.tr(
                    file_type,
                ),
            )[0]

            if len(add_file) > 0:
                # Add TRDI system test(s)
                if manufacturer == "TRDI" and add_file[0].endswith("mmt"):
                    # Read mmt file
                    mmt = MMTtrdi(add_file[0])
                    self.meas.trdi_add_moving_bed_tests(mmt)

                else:
                    # Add multiple SonTek system tests
                    for file in add_file:
                        path, filename = os.path.split(file)
                        self.meas.sontek_moving_bed_tests(
                            path, filename, self.agency_options["SNR"]["Use3Beam"]
                        )

                # Add message to qa
                self.meas.qa.moving_bed_test_added(self.meas)

                # Process moving-bed tests and update measurement processing
                settings = self.meas.current_settings()
                self.meas.apply_settings(settings)

                # Update tab
                self.change = True
                self.tab_manager()

            self.pb_add_moving_bed_test.blockSignals(False)

        # Request user comment
        if len(add_file) > 0:
            self.add_comment()

    # Bottom track tab
    # ================
    def bt_tab(self, old_discharge=None):
        """Initialize, setup settings, and display initial data in bottom
        track tab.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        """

        # Setup data table
        tbl = self.table_bt
        table_header = [
            self.tr("Filename"),
            self.tr("Number or \n Ensembles"),
            self.tr("Beam \n % <4"),
            self.tr("Total \n % Invalid"),
            self.tr("Orig Data \n % Invalid"),
            self.tr("<4 Beam \n % Invalid"),
            self.tr("Error Vel \n % Invalid"),
            self.tr("Vert Vel \n % Invalid"),
            self.tr("Other \n % Invalid"),
            self.tr("Discharge \n Previous \n" + self.units["label_Q"]),
            self.tr("Discharge \n Now \n" + self.units["label_Q"]),
            self.tr("Discharge \n % Change"),
        ]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.setStyleSheet("QToolTip{font: 12pt}")

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Intialize connections
        if not self.bt_initialized:
            tbl.cellClicked.connect(self.bt_table_clicked)

            # Connect plot variable checkboxes
            self.cb_bt_bt.stateChanged.connect(self.bt_plot_change)
            self.cb_bt_gga.stateChanged.connect(self.bt_plot_change)
            self.cb_bt_vtg.stateChanged.connect(self.bt_plot_change)
            self.cb_bt_vectors.stateChanged.connect(self.bt_plot_change)

            # Connect radio buttons
            self.rb_bt_beam.toggled.connect(self.bt_radiobutton_control)
            self.rb_bt_error.toggled.connect(self.bt_radiobutton_control)
            self.rb_bt_vert.toggled.connect(self.bt_radiobutton_control)
            self.rb_bt_other.toggled.connect(self.bt_radiobutton_control)
            self.rb_bt_source.toggled.connect(self.bt_radiobutton_control)

            # Connect manual entry
            self.ed_bt_error_vel_threshold.editingFinished.connect(
                self.change_error_vel_threshold
            )
            self.ed_bt_vert_vel_threshold.editingFinished.connect(
                self.change_vert_vel_threshold
            )

            # Connect filters
            self.combo_bt_3beam.currentIndexChanged[str].connect(self.change_bt_beam)
            self.combo_bt_error_velocity.activated[str].connect(self.change_bt_error)
            self.combo_bt_vert_velocity.currentIndexChanged[str].connect(
                self.change_bt_vertical
            )
            self.combo_bt_other.currentIndexChanged[str].connect(self.change_bt_other)

            self.bt_initialized = True

        selected = self.meas.transects[self.checked_transects_idx[0]].boat_vel.selected

        # Turn signals off
        self.cb_bt_bt.blockSignals(True)
        self.cb_bt_gga.blockSignals(True)
        self.cb_bt_vtg.blockSignals(True)
        self.cb_bt_vectors.blockSignals(True)
        self.combo_bt_3beam.blockSignals(True)
        self.combo_bt_error_velocity.blockSignals(True)
        self.combo_bt_vert_velocity.blockSignals(True)
        self.combo_bt_other.blockSignals(True)

        if selected == "gga_vel":
            self.cb_bt_gga.setChecked(True)
        elif selected == "vtg_vel":
            self.cb_bt_vtg.setChecked(True)

        self.cb_bt_vectors.setChecked(True)

        # Transect selected for display
        self.transect = self.meas.transects[
            self.checked_transects_idx[self.transect_row]
        ]

        # Set beam filter from transect data
        if self.transect.boat_vel.bt_vel.beam_filter < 0:
            self.combo_bt_3beam.setCurrentIndex(0)
        elif self.transect.boat_vel.bt_vel.beam_filter == 3:
            self.combo_bt_3beam.setCurrentIndex(1)
        elif self.transect.boat_vel.bt_vel.beam_filter == 4:
            self.combo_bt_3beam.setCurrentIndex(2)
        else:
            self.combo_bt_3beam.setCurrentIndex(0)

        # Set error velocity filter from transect data
        index = self.combo_bt_error_velocity.findText(
            self.transect.boat_vel.bt_vel.d_filter, QtCore.Qt.MatchFixedString
        )
        self.combo_bt_error_velocity.setCurrentIndex(index)

        s = self.meas.current_settings()

        if self.transect.boat_vel.bt_vel.d_filter == "Manual":
            threshold = "{:3.2f}".format(s["BTdFilterThreshold"] * self.units["V"])
            self.ed_bt_error_vel_threshold.setText(threshold)
            self.ed_bt_error_vel_threshold.setEnabled(True)

        # Set vertical velocity filter from transect data
        index = self.combo_bt_vert_velocity.findText(
            self.transect.boat_vel.bt_vel.w_filter, QtCore.Qt.MatchFixedString
        )
        self.combo_bt_vert_velocity.setCurrentIndex(index)

        if self.transect.boat_vel.bt_vel.w_filter == "Manual":
            threshold = "{:3.2f}".format(s["BTwFilterThreshold"] * self.units["V"])
            self.ed_bt_vert_vel_threshold.setText(threshold)
            self.ed_bt_vert_vel_threshold.setText(threshold)
            self.ed_bt_vert_vel_threshold.setEnabled(True)

        # Set smooth filter from transect data
        if self.transect.boat_vel.bt_vel.smooth_filter == "Off":
            self.combo_bt_other.setCurrentIndex(0)
        elif self.transect.boat_vel.bt_vel.smooth_filter == "On":
            self.combo_bt_other.setCurrentIndex(1)

        # Display content
        if old_discharge is None:
            old_discharge = self.meas.discharge
        self.update_bt_table(
            old_discharge=old_discharge, new_discharge=self.meas.discharge
        )
        self.bt_plots()
        self.bt_comments_messages()

        # Setup lists for use by graphics controls
        self.canvases = [self.bt_shiptrack_canvas, self.bt_ts_canvas]
        self.figs = [self.bt_shiptrack_fig, self.bt_ts_fig]
        self.fig_calls = [self.bt_shiptrack, self.bt_ts_plots]
        self.toolbars = [self.bt_shiptrack_toolbar, self.bt_ts_toolbar]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

        # Turn signals on
        self.cb_bt_bt.blockSignals(False)
        self.cb_bt_gga.blockSignals(False)
        self.cb_bt_vtg.blockSignals(False)
        self.cb_bt_vectors.blockSignals(False)
        self.combo_bt_3beam.blockSignals(False)
        self.combo_bt_error_velocity.blockSignals(False)
        self.combo_bt_vert_velocity.blockSignals(False)
        self.combo_bt_other.blockSignals(False)

    def update_bt_table(self, old_discharge, new_discharge):
        """Updates the bottom track table with new or reprocessed data.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp with new settings
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_bt

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]
                valid_data = transect.boat_vel.bt_vel.valid_data
                num_ensembles = len(valid_data[0, :])
                not_4beam = np.nansum(np.isnan(transect.boat_vel.bt_vel.d_mps))
                num_invalid = np.nansum(np.logical_not(valid_data[0, :]))
                num_orig_invalid = np.nansum(np.logical_not(valid_data[1, :]))
                num_beam_invalid = np.nansum(np.logical_not(valid_data[5, :]))
                num_error_invalid = np.nansum(np.logical_not(valid_data[2, :]))
                num_vert_invalid = np.nansum(np.logical_not(valid_data[3, :]))
                num_other_invalid = np.nansum(np.logical_not(valid_data[4, :]))

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                tbl.item(row, 0).setFont(self.font_normal)
                if (
                    self.meas.qa.bt_vel["q_total_warning"][transect_id, 0]
                    or self.meas.qa.bt_vel["q_max_run_warning"][transect_id, 0]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.bt_vel["q_total_caution"][transect_id, 0]
                    or self.meas.qa.bt_vel["q_max_run_caution"][transect_id, 0]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                tbl.item(row, col).setToolTip(
                    self.tr(self.bt_create_tooltip(self, row, col))
                )

                # Total number of ensembles
                col += 1
                item = "{:5d}".format(num_ensembles)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Less than 4 beams
                col += 1
                item = "{:3.2f}".format((not_4beam / num_ensembles) * 100.0)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Invalid total
                col += 1
                item = "{:3.2f}".format((num_invalid / num_ensembles) * 100.0)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if self.meas.qa.bt_vel["all_invalid"][transect_id]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                tbl.item(row, col).setToolTip(
                    self.tr(self.bt_create_tooltip(self, row, col))
                )

                # Invalid original data
                col += 1
                percent_invalid = (num_orig_invalid / num_ensembles) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.bt_vel["q_total_warning"][transect_id, 1]
                    or self.meas.qa.bt_vel["q_max_run_warning"][transect_id, 1]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.bt_vel["q_total_caution"][transect_id, 1]
                    or self.meas.qa.bt_vel["q_max_run_caution"][transect_id, 1]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.bt_create_tooltip(self, row, col))
                    )

                # Invalid 3 beam
                col += 1
                percent_invalid = (num_beam_invalid / num_ensembles) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.bt_vel["q_total_warning"][transect_id, 5]
                    or self.meas.qa.bt_vel["q_max_run_warning"][transect_id, 5]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.bt_vel["q_total_caution"][transect_id, 5]
                    or self.meas.qa.bt_vel["q_max_run_caution"][transect_id, 5]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.bt_create_tooltip(self, row, col))
                    )

                # Error velocity invalid
                col += 1
                percent_invalid = (num_error_invalid / num_ensembles) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.bt_vel["q_total_warning"][transect_id, 2]
                    or self.meas.qa.bt_vel["q_max_run_warning"][transect_id, 2]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.bt_vel["q_total_caution"][transect_id, 2]
                    or self.meas.qa.bt_vel["q_max_run_caution"][transect_id, 2]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.bt_create_tooltip(self, row, col))
                    )

                # Vertical velocity invalid
                col += 1
                percent_invalid = (num_vert_invalid / num_ensembles) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.bt_vel["q_total_warning"][transect_id, 3]
                    or self.meas.qa.bt_vel["q_max_run_warning"][transect_id, 3]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.bt_vel["q_total_caution"][transect_id, 3]
                    or self.meas.qa.bt_vel["q_max_run_caution"][transect_id, 3]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.bt_create_tooltip(self, row, col))
                    )

                # Other
                col += 1
                percent_invalid = (num_other_invalid / num_ensembles) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.bt_vel["q_total_warning"][transect_id, 4]
                    or self.meas.qa.bt_vel["q_max_run_warning"][transect_id, 4]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.bt_vel["q_total_caution"][transect_id, 4]
                    or self.meas.qa.bt_vel["q_max_run_caution"][transect_id, 4]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.bt_create_tooltip(self, row, col))
                    )

                # Discharge before changes
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8.3f}".format(
                            old_discharge[transect_id].total * self.units["Q"]
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge after changes
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8.3f}".format(
                            new_discharge[transect_id].total * self.units["Q"]
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent change in discharge
                col += 1
                if np.abs(old_discharge[transect_id].total) > 0:
                    per_change = (
                        (
                            new_discharge[transect_id].total
                            - old_discharge[transect_id].total
                        )
                        / old_discharge[transect_id].total
                    ) * 100
                    tbl.setItem(
                        row,
                        col,
                        QtWidgets.QTableWidgetItem("{:3.1f}".format(per_change)),
                    )
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Set selected file to bold font
            tbl.item(self.transect_row, 0).setFont(self.font_bold)
            tbl.scrollToItem(tbl.item(self.transect_row, 0))

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

            self.bt_comments_messages()

    @staticmethod
    def bt_create_tooltip(self, row, column):
        """Create bottom track tooltips."""

        # Identify transect associated with the row
        transect_id = self.checked_transects_idx[row]

        cat_idx = None
        tt = ""

        if column == 0:
            cat_idx = 0
        elif column == 3:
            cat_idx = 0
        elif column == 4:
            cat_idx = 1
        elif column == 5:
            cat_idx = 5
        elif column == 6:
            cat_idx = 2
        elif column == 7:
            cat_idx = 3
        elif column == 8:
            cat_idx = 4

        if cat_idx is not None:
            tt = "".join(
                self.q_qa_message(
                    qa_data=self.meas.qa.bt_vel,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )
        return tt

    def bt_plots(self):
        """Creates graphics for BT tab."""

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)
            for nrow in range(nrows):
                self.table_bt.item(nrow, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_bt.item(self.transect_row, 0).setFont(self.font_bold)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.transect_row]
            self.transect = self.meas.transects[transect_id]

            # Update plots
            self.bt_shiptrack()
            self.bt_ts_plots()

            # Update list of figs
            self.figs = [self.bt_shiptrack_fig, self.bt_ts_fig]
            self.fig_calls = [self.bt_shiptrack, self.bt_ts_plots]

            # Reset data cursor to work with new figure
            if self.actionData_Cursor.isChecked():
                self.data_cursor()

    def bt_shiptrack(self):
        """Creates shiptrack plot for data in transect."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.bt_shiptrack_canvas is None:
            # Create the canvas
            self.bt_shiptrack_canvas = MplCanvas(
                parent=self.graph_bt_st, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_bt_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.bt_shiptrack_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.bt_shiptrack_toolbar = NavigationToolbar(
                self.bt_shiptrack_canvas, self
            )
            self.bt_shiptrack_toolbar.hide()

        # Initialize the shiptrack figure and assign to the canvas
        self.bt_shiptrack_fig = Shiptrack(canvas=self.bt_shiptrack_canvas)
        # Create the figure with the specified data
        self.bt_shiptrack_fig.create(
            transect=self.transect,
            units=self.units,
            cb=True,
            cb_bt=self.cb_bt_bt,
            cb_gga=self.cb_bt_gga,
            cb_vtg=self.cb_bt_vtg,
            cb_vectors=self.cb_bt_vectors,
        )

        # Draw canvas
        self.bt_shiptrack_canvas.draw()

    def bt_ts_plots(self):
        """Creates plots of filter characteristics."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.bt_ts_canvas is None:
            # Create the canvas
            self.bt_ts_canvas = MplCanvas(
                parent=self.graph_bt_ts, width=8, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_bt_ts)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(0, 0, 0, 0)
            # Add the canvas
            layout.addWidget(self.bt_ts_canvas)
            self.bt_ts_toolbar = NavigationToolbar(self.bt_ts_canvas, self)
            self.bt_ts_toolbar.hide()

        # Initialize the boat speed figure and assign to the canvas
        self.bt_ts_fig = AdvGraphs(canvas=self.bt_ts_canvas)

        # Create the figure with the specified data

        self.bt_ts_fig.create_bt_tab_graphs(
            transect=self.transect,
            units=self.units,
            beam=self.rb_bt_beam.isChecked(),
            error=self.rb_bt_error.isChecked(),
            vert=self.rb_bt_vert.isChecked(),
            other=self.rb_bt_other.isChecked(),
            source=self.rb_bt_source.isChecked(),
            bt=self.cb_bt_bt.isChecked(),
            gga=self.cb_bt_gga.isChecked(),
            vtg=self.cb_bt_vtg.isChecked(),
            x_axis_type=self.x_axis_type,
        )

        # Update list of figs
        self.figs = [self.bt_shiptrack_fig, self.bt_ts_fig]
        self.fig_calls = [self.bt_shiptrack, self.bt_ts_plots]

        # Reset data cursor to work with new figure
        if self.actionData_Cursor.isChecked():
            self.data_cursor()
        # Draw canvas
        self.bt_ts_canvas.draw()

    @QtCore.pyqtSlot()
    def bt_radiobutton_control(self):
        """Identifies a change in radio buttons and calls the plot routine
        to update the graph.
        """

        with self.wait_cursor():
            if self.sender().isChecked():
                self.bt_plots()

    def bt_table_clicked(self, row, column):
        """Changes plotted data to the transect of the transect clicked.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        """

        if column == 0:
            self.transect_row = row
            self.bt_plots()
            self.change = True
            self.map_change = True
        self.tab_bt_2_data.setFocus()

    @QtCore.pyqtSlot()
    def bt_plot_change(self):
        """Coordinates changes in what references should be displayed in the
        boat speed and shiptrack plots.
        """

        with self.wait_cursor():
            self.bt_plots()
            self.tab_bt_2_data.setFocus()

    def update_bt_tab(self, s):
        """Updates the measurement and bottom track tab (table and graphics)
        after a change to settings has been made.

        Parameters
        ----------
        s: dict
            Dictionary of all process settings for the
            measurement
        """

        # Save discharge from previous settings
        old_discharge = copy.deepcopy(self.meas.discharge)

        # Apply new settings
        self.meas.apply_settings(settings=s)

        # Update table
        self.update_bt_table(
            old_discharge=old_discharge, new_discharge=self.meas.discharge
        )
        self.bt_comments_messages()

        # Update plots
        self.bt_plots()

        self.tab_bt_2_data.setFocus()

    @QtCore.pyqtSlot(str)
    def change_bt_beam(self, text):
        """Coordinates user initiated change to the beam settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            self.combo_bt_3beam.blockSignals(True)
            # Get current settings
            s = self.meas.current_settings()

            if text == "Auto":
                s["BTbeamFilter"] = -1
            elif text == "Allow":
                s["BTbeamFilter"] = 3
            elif text == "4-Beam Only":
                s["BTbeamFilter"] = 4

            # Update measurement and display
            self.update_bt_tab(s)
            self.change = True
            self.map_change = True
            self.combo_bt_3beam.blockSignals(False)

    @QtCore.pyqtSlot(str)
    def change_bt_error(self, text):
        """Coordinates user initiated change to the error velocity settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            self.combo_bt_error_velocity.blockSignals(True)

            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s["BTdFilter"] = text
            if text == "Manual":
                # If Manual enable the line edit box for user input. Updates
                # are not applied until the user has entered a value in the line edit box.
                self.ed_bt_error_vel_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and
                # disabled and the updates applied.
                self.ed_bt_error_vel_threshold.setEnabled(False)
                self.ed_bt_error_vel_threshold.setText("")
                self.update_bt_tab(s)
            self.change = True
            self.map_change = True
            self.combo_bt_error_velocity.blockSignals(False)

    @QtCore.pyqtSlot(str)
    def change_bt_vertical(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            self.combo_bt_vert_velocity.blockSignals(True)

            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s["BTwFilter"] = text

            if text == "Manual":
                # If Manual enable the line edit box for user input. Updates
                # are not applied until the user has entered a value in the line edit box.
                self.ed_bt_vert_vel_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and
                # disabled and the updates applied.
                self.ed_bt_vert_vel_threshold.setEnabled(False)
                self.ed_bt_vert_vel_threshold.setText("")
                self.update_bt_tab(s)
                self.change = True
                self.map_change = True
            self.combo_bt_vert_velocity.blockSignals(False)

    @QtCore.pyqtSlot(str)
    def change_bt_other(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            self.combo_bt_other.blockSignals(True)

            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            if text == "Off":
                s["BTsmoothFilter"] = "Off"
            elif text == "Smooth":
                s["BTsmoothFilter"] = "On"

            # Update measurement and display
            self.update_bt_tab(s)
            self.change = True
            self.map_change = True
            self.combo_bt_other.blockSignals(False)

    @QtCore.pyqtSlot()
    def change_error_vel_threshold(self):
        """Coordinates application of a user specified error velocity
        threshold.
        """

        self.ed_bt_error_vel_threshold.blockSignals(True)
        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = self.check_numeric_input(self.ed_bt_error_vel_threshold)
            if threshold is not None:
                threshold = threshold / self.units["V"]

                # Get current settings
                s = self.meas.current_settings()
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get twice.
                # This line checks to see if there was and actual change.
                compute = False
                if type(s["BTdFilterThreshold"]) is dict:
                    compute = True
                else:
                    if np.abs(threshold - s["BTdFilterThreshold"]) > 0.0001:
                        compute = True
                if compute:
                    # Change settings to manual and the associated threshold
                    s["BTdFilter"] = "Manual"
                    s["BTdFilterThreshold"] = threshold

                    # Update measurement and display
                    self.update_bt_tab(s)
                    self.change = True
                    self.map_change = True

        self.ed_bt_error_vel_threshold.blockSignals(False)

    @QtCore.pyqtSlot()
    def change_vert_vel_threshold(self):
        """Coordinates application of a user specified vertical velocity threshold."""

        self.ed_bt_vert_vel_threshold.blockSignals(True)
        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = self.check_numeric_input(self.ed_bt_vert_vel_threshold)
            if threshold is not None:
                threshold = threshold / self.units["V"]

                # Get current settings
                s = self.meas.current_settings()
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get twice. This line checks
                # to see if there was and actual change.
                compute = False
                if type(s["BTwFilterThreshold"]) is dict:
                    compute = True
                else:
                    if np.abs(threshold - s["BTwFilterThreshold"]) > 0.0001:
                        compute = True
                if compute:
                    # Change settings to manual and the associated threshold
                    s["BTwFilter"] = "Manual"
                    s["BTwFilterThreshold"] = threshold

                    # Update measurement and display
                    self.update_bt_tab(s)
                    self.change = True
                    self.map_change = True
        self.ed_bt_vert_vel_threshold.blockSignals(False)

    def bt_comments_messages(self):
        """Displays comments and messages associated with bottom track
        filters in Messages tab.
        """

        # Clear comments and messages
        self.display_bt_comments.clear()
        self.display_bt_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_bt_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_bt_comments.textCursor().insertText(comment)
                self.display_bt_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_bt_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_bt_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.bt_vel["messages"]:
                if type(message) is str:
                    self.display_bt_messages.textCursor().insertText(message)
                else:
                    self.display_bt_messages.textCursor().insertText(message[0])
                self.display_bt_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_bt_messages.textCursor().insertBlock()

            self.update_tab_icons()

    # GPS tab
    # =======
    def gps_tab(self, old_discharge=None):
        """Initialize, setup settings, and display initial data in gps tab.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        """

        # Setup data table
        tbl = self.table_gps
        table_header = [
            self.tr("Filename"),
            self.tr("Number or \n Ensembles"),
            self.tr("GGA \n % Invalid"),
            self.tr("VTG \n % Invalid"),
            self.tr("Diff. Qual. \n % Invalid"),
            self.tr("Alt. Change \n % Invalid"),
            self.tr("HDOP \n % Invalid"),
            self.tr("Sat Change \n % "),
            self.tr("Other \n % Invalid"),
            self.tr("Discharge \n Previous \n" + self.units["label_Q"]),
            self.tr("Discharge \n Now \n" + self.units["label_Q"]),
            self.tr("Discharge \n % Change"),
        ]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.setStyleSheet("QToolTip{font: 12pt}")

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Turn signals off
        self.cb_gps_bt.blockSignals(True)
        self.cb_gps_gga.blockSignals(True)
        self.cb_gps_vtg.blockSignals(True)
        self.cb_gps_vectors.blockSignals(True)
        self.combo_gps_qual.blockSignals(True)
        self.combo_gps_altitude.blockSignals(True)
        self.combo_gps_hdop.blockSignals(True)
        self.combo_gps_other.blockSignals(True)

        # Initialize checkbox settings for boat reference
        self.cb_gps_bt.setCheckState(QtCore.Qt.Checked)
        if (
            self.meas.transects[self.checked_transects_idx[0]].boat_vel.gga_vel
            is not None
        ):
            self.cb_gps_gga.setCheckState(QtCore.Qt.Checked)
        if (
            self.meas.transects[self.checked_transects_idx[0]].boat_vel.vtg_vel
            is not None
        ):
            self.cb_gps_vtg.setCheckState(QtCore.Qt.Checked)

        self.cb_gps_vectors.setCheckState(QtCore.Qt.Checked)

        # Transect selected for display
        self.transect = self.meas.transects[
            self.checked_transects_idx[self.transect_row]
        ]

        # Check for presence of gga data
        gga_transect = None
        for idx in self.checked_transects_idx:
            if self.meas.transects[idx].boat_vel.gga_vel is not None:
                gga_transect = self.meas.transects[idx]
                break

        if gga_transect is not None:
            # Set gps quality filter
            if gga_transect.boat_vel.gga_vel.gps_diff_qual_filter == 1:
                self.combo_gps_qual.setCurrentIndex(0)
            elif gga_transect.boat_vel.gga_vel.gps_diff_qual_filter == 2:
                self.combo_gps_qual.setCurrentIndex(1)
            elif gga_transect.boat_vel.gga_vel.gps_diff_qual_filter == 4:
                self.combo_gps_qual.setCurrentIndex(2)
            else:
                self.combo_gps_qual.setCurrentIndex(0)

            # Set altitude filter from transect data
            index = self.combo_gps_altitude.findText(
                gga_transect.boat_vel.gga_vel.gps_altitude_filter,
                QtCore.Qt.MatchFixedString,
            )
            self.combo_gps_altitude.setCurrentIndex(index)

            s = self.meas.current_settings()

            if s["ggaAltitudeFilter"] == "Manual":
                self.ed_gps_altitude_threshold.setEnabled(True)
                threshold = "{:3.2f}".format(
                    s["ggaAltitudeFilterChange"] * self.units["L"]
                )
                self.ed_gps_altitude_threshold.setText(threshold)

            # Set hdop filter from transect data
            index = self.combo_gps_hdop.findText(
                gga_transect.boat_vel.gga_vel.gps_HDOP_filter,
                QtCore.Qt.MatchFixedString,
            )
            self.combo_gps_hdop.setCurrentIndex(index)

            if s["GPSHDOPFilter"] == "Manual":
                self.ed_gps_hdop_threshold.setEnabled(True)
                threshold = "{:3.2f}".format(s["GPSHDOPFilterChange"])
                self.ed_gps_hdop_threshold.setText(threshold)
            if s["ggaAltitudeFilter"] == "Manual":
                self.ed_gps_altitude_threshold.setEnabled(True)
                threshold = "{:3.2f}".format(
                    s["ggaAltitudeFilterChange"] * self.units["L"]
                )
                self.ed_gps_altitude_threshold.setText(threshold)
            # Set smooth filter from transect data
            if gga_transect.boat_vel.gga_vel.smooth_filter == "Off":
                self.combo_gps_other.setCurrentIndex(0)
            elif gga_transect.boat_vel.gga_vel.smooth_filter == "On":
                self.combo_gps_other.setCurrentIndex(1)

            # Set hdop filter from transect data
            index = self.combo_gps_hdop.findText(
                gga_transect.boat_vel.gga_vel.gps_HDOP_filter,
                QtCore.Qt.MatchFixedString,
            )
            self.combo_gps_hdop.setCurrentIndex(index)

        # Check for presence of vtg data
        vtg_transect = None
        for idx in self.checked_transects_idx:
            if self.meas.transects[idx].boat_vel.vtg_vel is not None:
                vtg_transect = self.meas.transects[idx]
                break

        if vtg_transect is not None:
            # Set smooth filter from transect data
            if vtg_transect.boat_vel.vtg_vel.smooth_filter == "Off":
                self.combo_gps_other.setCurrentIndex(0)
            elif vtg_transect.boat_vel.vtg_vel.smooth_filter == "On":
                self.combo_gps_other.setCurrentIndex(1)

        # Turn signals on
        self.cb_gps_bt.blockSignals(False)
        self.cb_gps_gga.blockSignals(False)
        self.cb_gps_vtg.blockSignals(False)
        self.cb_gps_vectors.blockSignals(False)
        self.combo_gps_qual.blockSignals(False)
        self.combo_gps_altitude.blockSignals(False)
        self.combo_gps_hdop.blockSignals(False)
        self.combo_gps_other.blockSignals(False)

        # Display content
        if old_discharge is None:
            old_discharge = self.meas.discharge
        self.update_gps_table(
            old_discharge=old_discharge, new_discharge=self.meas.discharge
        )
        self.gps_plots()
        self.gps_comments_messages()
        self.gps_bt()

        # Setup lists for use by graphics controls
        self.canvases = [self.gps_shiptrack_canvas, self.gps_ts_canvas]
        self.figs = [self.gps_shiptrack_fig, self.gps_ts_fig]
        self.fig_calls = [self.gps_shiptrack, self.gps_ts_plots]
        self.toolbars = [self.gps_shiptrack_toolbar, self.gps_ts_toolbar]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

        if not self.gps_initialized:
            tbl.cellClicked.connect(self.gps_table_clicked)
            # Connect plot variable checkboxes
            self.cb_gps_bt.stateChanged.connect(self.gps_plot_change)
            self.cb_gps_gga.stateChanged.connect(self.gps_plot_change)
            self.cb_gps_vtg.stateChanged.connect(self.gps_plot_change)
            self.cb_gps_vectors.stateChanged.connect(self.gps_plot_change)

            # Connect radio buttons
            self.rb_gps_quality.toggled.connect(self.gps_radiobutton_control)
            self.rb_gps_altitude.toggled.connect(self.gps_radiobutton_control)
            self.rb_gps_hdop.toggled.connect(self.gps_radiobutton_control)
            self.rb_gps_sats.toggled.connect(self.gps_radiobutton_control)
            self.rb_gps_other.toggled.connect(self.gps_radiobutton_control)
            self.rb_gps_source.toggled.connect(self.gps_radiobutton_control)

            # Connect manual entry
            self.ed_gps_altitude_threshold.editingFinished.connect(
                self.change_altitude_threshold
            )
            self.ed_gps_hdop_threshold.editingFinished.connect(
                self.change_hdop_threshold
            )

            # Connect filters
            self.combo_gps_qual.currentIndexChanged[str].connect(self.change_quality)
            self.combo_gps_altitude.currentIndexChanged[str].connect(
                self.change_altitude
            )
            self.combo_gps_hdop.currentIndexChanged[str].connect(self.change_hdop)
            self.combo_gps_other.currentIndexChanged[str].connect(self.change_gps_other)

            self.gps_initialized = True

    def update_gps_table(self, old_discharge, new_discharge):
        """Updates the gps table with new or reprocessed data.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp with new settings
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_gps

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]
                num_ensembles = len(transect.boat_vel.bt_vel.u_processed_mps)
                # Determine GPS characteristics for gga
                if (
                    transect.boat_vel.gga_vel is not None
                    and transect.boat_vel.gga_vel.u_mps is not None
                ):
                    valid_data = transect.boat_vel.gga_vel.valid_data
                    num_other_invalid = np.nansum(np.logical_not(valid_data[4, :]))
                    num_invalid_gga = np.nansum(np.logical_not(valid_data[0, :]))
                    num_altitude_invalid = np.nansum(np.logical_not(valid_data[3, :]))
                    num_quality_invalid = np.nansum(np.logical_not(valid_data[2, :]))
                    num_hdop_invalid = np.nansum(np.logical_not(valid_data[5, :]))
                    sats = np.copy(transect.gps.num_sats_ens)
                    if np.nansum(sats) == 0:
                        num_sat_changes = -1
                    else:
                        sats = sats[np.logical_not(np.isnan(sats))]
                        diff_sats = np.diff(sats)
                        num_sat_changes = np.nansum(np.logical_not(diff_sats == 0))
                else:
                    num_invalid_gga = -1
                    num_altitude_invalid = -1
                    num_quality_invalid = -1
                    num_hdop_invalid = -1
                    num_sat_changes = -1
                    num_other_invalid = -1

                # Determine characteristics for vtg
                if (
                    transect.boat_vel.vtg_vel is not None
                    and transect.boat_vel.vtg_vel.u_mps is not None
                ):
                    num_invalid_vtg = np.nansum(
                        np.logical_not(transect.boat_vel.vtg_vel.valid_data[0, :])
                    )
                else:
                    num_invalid_vtg = -1

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Total number of ensembles
                col += 1
                item = "{:5d}".format(num_ensembles)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of ensembles with invalid gga
                col += 1
                if num_invalid_gga > 0:
                    item = "{:3.2f}".format((num_invalid_gga / num_ensembles) * 100.0)
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                if (
                    self.meas.qa.gga_vel["q_total_warning"][transect_id, 1]
                    or self.meas.qa.gga_vel["q_max_run_warning"][transect_id, 1]
                    or self.meas.qa.gga_vel["all_invalid"][transect_id]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.gga_vel["q_total_caution"][transect_id, 1]
                    or self.meas.qa.gga_vel["q_max_run_caution"][transect_id, 1]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                tbl.item(row, col).setToolTip(self.gps_create_tooltip(self, row, col))

                # Percent of ensembles with invalid vtg
                col += 1
                if num_invalid_vtg >= 0:
                    item = "{:3.2f}".format((num_invalid_vtg / num_ensembles) * 100.0)
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.vtg_vel["q_total_warning"][transect_id, 1]
                    or self.meas.qa.vtg_vel["q_max_run_warning"][transect_id, 1]
                    or self.meas.qa.vtg_vel["all_invalid"][transect_id]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.vtg_vel["q_total_caution"][transect_id, 1]
                    or self.meas.qa.vtg_vel["q_max_run_caution"][transect_id, 1]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                tbl.item(row, col).setToolTip(self.gps_create_tooltip(self, row, col))

                # Percent of ensembles with invalid quality
                col += 1
                percent_invalid = 0
                if num_quality_invalid >= 0:
                    percent_invalid = (num_quality_invalid / num_ensembles) * 100.0
                    item = "{:3.2f}".format(percent_invalid)
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.gga_vel["q_total_warning"][transect_id, 2]
                    or self.meas.qa.gga_vel["q_max_run_warning"][transect_id, 2]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.gga_vel["q_total_caution"][transect_id, 2]
                    or self.meas.qa.gga_vel["q_max_run_caution"][transect_id, 2]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.gps_create_tooltip(self, row, col))
                    )

                # Percent ensembles with invalid altitude
                col += 1
                percent_invalid = 0
                if num_altitude_invalid >= 0:
                    percent_invalid = (num_altitude_invalid / num_ensembles) * 100.0
                    item = "{:3.2f}".format(percent_invalid)
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.gga_vel["q_total_warning"][transect_id, 3]
                    or self.meas.qa.gga_vel["q_max_run_warning"][transect_id, 3]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.gga_vel["q_total_caution"][transect_id, 3]
                    or self.meas.qa.gga_vel["q_max_run_caution"][transect_id, 3]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.gps_create_tooltip(self, row, col))
                    )

                # Percent ensembles with invalid HDOP
                col += 1
                percent_invalid = 0
                if num_hdop_invalid >= 0:
                    percent_invalid = (num_hdop_invalid / num_ensembles) * 100.0
                    item = "{:3.2f}".format(percent_invalid)
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.gga_vel["q_total_warning"][transect_id, 5]
                    or self.meas.qa.gga_vel["q_max_run_warning"][transect_id, 5]
                    or self.meas.qa.vtg_vel["q_total_warning"][transect_id, 5]
                    or self.meas.qa.vtg_vel["q_max_run_warning"][transect_id, 5]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.gga_vel["q_total_caution"][transect_id, 5]
                    or self.meas.qa.gga_vel["q_max_run_caution"][transect_id, 5]
                    or self.meas.qa.vtg_vel["q_total_caution"][transect_id, 5]
                    or self.meas.qa.vtg_vel["q_max_run_caution"][transect_id, 5]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.gps_create_tooltip(self, row, col))
                    )

                # Percent of ensembles with satellite changes
                col += 1
                if num_sat_changes >= 0:
                    item = "{:3.2f}".format((num_sat_changes / num_ensembles) * 100.0)
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent other filter
                col += 1
                percent_invalid = 0
                if num_other_invalid >= 0:
                    percent_invalid = (num_other_invalid / num_ensembles) * 100.0
                    item = "{:3.2f}".format(percent_invalid)
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.gga_vel["q_total_warning"][transect_id, 4]
                    or self.meas.qa.gga_vel["q_max_run_warning"][transect_id, 4]
                    or self.meas.qa.vtg_vel["q_total_warning"][transect_id, 4]
                    or self.meas.qa.vtg_vel["q_max_run_warning"][transect_id, 4]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.gga_vel["q_total_caution"][transect_id, 4]
                    or self.meas.qa.gga_vel["q_max_run_caution"][transect_id, 4]
                    or self.meas.qa.vtg_vel["q_total_caution"][transect_id, 4]
                    or self.meas.qa.vtg_vel["q_max_run_caution"][transect_id, 4]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.gps_create_tooltip(self, row, col))
                    )

                # Discharge before changes
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                old_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge after changes
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                new_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent change in discharge
                col += 1
                if np.abs(old_discharge[transect_id].total) > 0:
                    per_change = (
                        (
                            new_discharge[transect_id].total
                            - old_discharge[transect_id].total
                        )
                        / old_discharge[transect_id].total
                    ) * 100
                    tbl.setItem(
                        row,
                        col,
                        QtWidgets.QTableWidgetItem("{:3.1f}".format(per_change)),
                    )
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                self.table_gps.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_gps.item(self.transect_row, 0).setFont(self.font_bold)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.scrollToItem(tbl.item(self.transect_row, 0))

            self.gps_comments_messages()

    @staticmethod
    def gps_create_tooltip(self, row, column):
        # Identify transect associated with the row
        transect_id = self.checked_transects_idx[row]

        tt = ""
        qa_data = None

        if column == 2:
            cat_idx = 1
            qa_data = self.meas.qa.gga_vel
            tt = tt.join(
                self.q_qa_message(
                    qa_data=qa_data,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )
            cat_idx = 0
            tt = tt.join(
                self.q_qa_message(
                    qa_data=qa_data,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )
        elif column == 3:
            cat_idx = 1
            qa_data = self.meas.qa.vtg_vel
            tt = tt.join(
                self.q_qa_message(
                    qa_data=qa_data,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )
            cat_idx = 0
            tt = tt.join(
                self.q_qa_message(
                    qa_data=qa_data,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )

        elif column == 4:
            cat_idx = 2
            qa_data = self.meas.qa.gga_vel
            tt = tt.join(
                self.q_qa_message(
                    qa_data=qa_data,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )

        elif column == 5:
            cat_idx = 3
            qa_data = self.meas.qa.gga_vel
            tt = tt.join(
                self.q_qa_message(
                    qa_data=qa_data,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )

        elif column == 6:
            cat_idx = 5
            if (
                self.meas.transects[
                    self.meas.checked_transect_idx[row]
                ].boat_vel.gga_vel
                is not None
            ):
                qa_data = self.meas.qa.gga_vel
            elif (
                self.meas.transects[
                    self.meas.checked_transect_idx[row]
                ].boat_vel.vtg_vel
                is not None
            ):
                qa_data = self.meas.qa.vtg_vel
            if qa_data is not None:
                tt = tt.join(
                    self.q_qa_message(
                        qa_data=qa_data,
                        cat_idx=cat_idx,
                        transect_id=transect_id,
                        total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                        total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                        run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                        run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                    )
                )

        elif column == 8:
            cat_idx = 4
            if (
                self.meas.transects[
                    self.meas.checked_transect_idx[row]
                ].boat_vel.gga_vel
                is not None
            ):
                qa_data = self.meas.qa.gga_vel
                tt = tt.join(
                    self.q_qa_message(
                        qa_data=qa_data,
                        cat_idx=cat_idx,
                        transect_id=transect_id,
                        total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                        total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                        run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                        run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                    )
                )
            if (
                self.meas.transects[
                    self.meas.checked_transect_idx[row]
                ].boat_vel.vtg_vel
                is not None
            ):
                qa_data = self.meas.qa.vtg_vel
                tt = tt.join(
                    self.q_qa_message(
                        qa_data=qa_data,
                        cat_idx=cat_idx,
                        transect_id=transect_id,
                        total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                        total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                        run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                        run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                    )
                )
        return tt

    def gps_plots(self):
        """Creates graphics for GPS tab."""

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.transect_row]
            self.transect = self.meas.transects[transect_id]

            # Identify transect to be plotted in table
            for row in range(nrows):
                self.table_gps.item(row, 0).setFont(self.font_normal)
            # Set selected file to bold font
            self.table_gps.item(self.transect_row, 0).setFont(self.font_bold)

            # Update plots
            self.gps_shiptrack()
            self.gps_ts_plots()

            # Update list of figs
            self.figs = [self.gps_shiptrack_fig, self.gps_ts_fig]
            self.fig_calls = [self.gps_shiptrack, self.gps_ts_plots]

            # Reset data cursor to work with new data plot
            if self.actionData_Cursor.isChecked():
                self.data_cursor()

        self.tab_gps_2_data.setFocus()

    def gps_shiptrack(self):
        """Creates shiptrack plot for data in transect."""

        self.cb_gps_bt.blockSignals(True)
        self.cb_gps_gga.blockSignals(True)
        self.cb_gps_vtg.blockSignals(True)
        self.cb_gps_vectors.blockSignals(True)
        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.gps_shiptrack_canvas is None:
            # Create the canvas
            self.gps_shiptrack_canvas = MplCanvas(
                parent=self.graph_gps_st, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_gps_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.gps_shiptrack_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.gps_shiptrack_toolbar = NavigationToolbar(
                self.gps_shiptrack_canvas, self
            )
            self.gps_shiptrack_toolbar.hide()

        # Initialize the shiptrack figure and assign to the canvas
        self.gps_shiptrack_fig = Shiptrack(canvas=self.gps_shiptrack_canvas)
        # Create the figure with the specified data
        self.gps_shiptrack_fig.create(
            transect=self.transect,
            units=self.units,
            cb=True,
            cb_bt=self.cb_gps_bt,
            cb_gga=self.cb_gps_gga,
            cb_vtg=self.cb_gps_vtg,
            cb_vectors=self.cb_gps_vectors,
        )

        # Draw canvas
        self.gps_shiptrack_canvas.draw()

        self.cb_gps_bt.blockSignals(False)
        self.cb_gps_gga.blockSignals(False)
        self.cb_gps_vtg.blockSignals(False)
        self.cb_gps_vectors.blockSignals(False)

    @QtCore.pyqtSlot()
    def gps_radiobutton_control(self):
        """Identifies a change in radio buttons and calls the plot routine
        to update the graph.
        """

        with self.wait_cursor():
            if self.sender().isChecked():
                self.gps_ts_plots()

    def gps_ts_plots(self):
        """Creates plots of filter characteristics."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.gps_ts_canvas is None:
            # Create the canvas
            self.gps_ts_canvas = MplCanvas(
                parent=self.graph_gps_ts, width=8, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_gps_ts)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(0, 0, 0, 0)
            # Add the canvas
            layout.addWidget(self.gps_ts_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.gps_ts_toolbar = NavigationToolbar(self.gps_ts_canvas, self)
            self.gps_ts_toolbar.hide()

        # Initialize the boat speed figure and assign to the canvas
        self.gps_ts_fig = AdvGraphs(canvas=self.gps_ts_canvas)
        self.gps_ts_fig.create_gps_tab_graphs(
            transect=self.transect,
            units=self.units,
            quality=self.rb_gps_quality.isChecked(),
            altitude=self.rb_gps_altitude.isChecked(),
            hdop=self.rb_gps_hdop.isChecked(),
            n_sats=self.rb_gps_sats.isChecked(),
            other=self.rb_gps_other.isChecked(),
            source=self.rb_gps_source.isChecked(),
            bt=self.cb_gps_bt.isChecked(),
            gga=self.cb_gps_gga.isChecked(),
            vtg=self.cb_gps_vtg.isChecked(),
            x_axis_type=self.x_axis_type,
        )

        # Update list of figs
        self.figs = [self.gps_shiptrack_fig, self.gps_ts_fig]
        self.fig_calls = [self.gps_shiptrack, self.gps_ts_plots]

        # Reset data cursor to work with new data plot
        if self.actionData_Cursor.isChecked():
            self.data_cursor()

        # Draw canvas
        self.gps_ts_canvas.draw()

    def gps_table_clicked(self, row, column, caller=None):
        """Changes plotted data to the transect of the transect clicked.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        caller: str
            Identifies the tab from which the method is called
        """

        if column == 0:
            self.transect_row = row
            self.gps_plots()
            self.change = True
            self.map_change = True
        if caller is None:
            self.gps_bt_table_clicked(row + 2, column, caller="gps")
        self.tab_gps_2_data.setFocus()

    @QtCore.pyqtSlot()
    def gps_plot_change(self):
        """Coordinates changes in what references should be displayed in the
        boat speed and shiptrack plots.
        """

        with self.wait_cursor():
            self.gps_plots()
            self.tab_gps_2_data.setFocus()

    def update_gps_tab(self, s):
        """Updates the measurement and bottom track tab (table and graphics)
        after a change to settings has been made.

        Parameters
        ----------
        s: dict
            Dictionary of all process settings for the
            measurement
        """

        # Save discharge from previous settings
        old_discharge = copy.deepcopy(self.meas.discharge)

        # Apply new settings
        self.meas.apply_settings(settings=s)

        # Update table
        self.update_gps_table(
            old_discharge=old_discharge, new_discharge=self.meas.discharge
        )
        self.gps_bt()

        # Update plots
        self.gps_plots()
        self.tab_gps_2_data.setFocus()

    @QtCore.pyqtSlot(str)
    def change_quality(self, text):
        """Coordinates user initiated change to the minumum GPS quality.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change settings based on combo box selection
            if text == "1-Autonomous":
                s["ggaDiffQualFilter"] = 1
            elif text == "2-Differential":
                s["ggaDiffQualFilter"] = 2
            elif text == "4+-RTK":
                s["ggaDiffQualFilter"] = 4

            # Update measurement and display
            self.update_gps_tab(s)
            self.change = True
            self.map_change = True

    @QtCore.pyqtSlot(str)
    def change_altitude(self, text):
        """Coordinates user initiated change to the error velocity settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s["ggaAltitudeFilter"] = text

            if text == "Manual":
                # If Manual enable the line edit box for user input. Updates
                # are not applied until the user has entered
                # a value in the line edit box.
                self.ed_gps_altitude_threshold.setEnabled(True)

            else:
                # If manual is not selected the line edit box is cleared and
                # disabled and the updates applied.
                self.ed_gps_altitude_threshold.setEnabled(False)
                self.ed_gps_altitude_threshold.setText("")
                self.update_gps_tab(s)
            self.change = True
            self.map_change = True

    @QtCore.pyqtSlot(str)
    def change_hdop(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s["GPSHDOPFilter"] = text

            if text == "Manual":
                # If Manual enable the line edit box for user input. Updates
                # are not applied until the user has entered
                # a value in the line edit box.
                self.ed_gps_hdop_threshold.setEnabled(True)

            else:
                # If manual is not selected the line edit box is cleared and
                # disabled and the updates applied.
                self.ed_gps_hdop_threshold.setEnabled(False)
                self.ed_gps_hdop_threshold.setText("")
                self.update_gps_tab(s)
            self.change = True
            self.map_change = True

    @QtCore.pyqtSlot(str)
    def change_gps_other(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            if text == "Off":
                s["GPSSmoothFilter"] = "Off"
            elif text == "Smooth":
                s["GPSSmoothFilter"] = "On"

            # Update measurement and display
            self.update_gps_tab(s)
            self.change = True
            self.map_change = True

    @QtCore.pyqtSlot()
    def change_altitude_threshold(self):
        """Coordinates application of a user specified error velocity
        threshold.
        """

        self.ed_gps_altitude_threshold.blockSignals(True)
        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = self.check_numeric_input(self.ed_gps_altitude_threshold)
            if threshold is not None:
                threshold = threshold / self.units["L"]

                # Get current settings
                s = self.meas.current_settings()
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get
                # twice. This line checks to see if there was and actual
                # change.
                if np.abs(threshold - s["ggaAltitudeFilterChange"]) > 0.0001:
                    # Change settings to manual and the associated threshold
                    s["ggaAltitudeFilter"] = "Manual"
                    s["ggaAltitudeFilterChange"] = threshold

                    # Update measurement and display
                    self.update_gps_tab(s)
                    self.change = True
                    self.map_change = True

        self.ed_gps_altitude_threshold.blockSignals(False)

    @QtCore.pyqtSlot()
    def change_hdop_threshold(self):
        """Coordinates application of a user specified vertical velocity
        threshold.
        """

        self.ed_gps_hdop_threshold.blockSignals(True)
        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = self.check_numeric_input(self.ed_gps_hdop_threshold)
            if threshold is not None:
                # Get current settings
                s = self.meas.current_settings()
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get
                # twice. This line checks to see if there was and actual
                # change.
                if np.abs(threshold - s["GPSHDOPFilterMax"]) > 0.0001:
                    # Change settings to manual and the associated threshold
                    s["GPSHDOPFilter"] = "Manual"
                    s["GPSHDOPFilterMax"] = threshold

                    # Update measurement and display
                    self.update_gps_tab(s)
                    self.change = True
                    self.map_change = True

        self.ed_gps_hdop_threshold.blockSignals(False)

    def gps_bt(self):
        """Displays the comparison of bottom track to GPS characteristics."""

        # Setup table
        tbl = self.table_gps_bt
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows + 2)
        tbl.setColumnCount(11)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.setStyleSheet("QToolTip{font: 12pt}")

        if len(self.checked_transects_idx) > 0:
            # Build column labels using custom_header to create appropriate
            # spans
            self.custom_header(tbl, 0, 0, 2, 1, self.tr("Transect"))
            self.custom_header(tbl, 0, 1, 1, 5, self.tr("GGA"))
            tbl.item(0, 1).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 1, 1, 1, self.tr(" Lag \n(sec)"))
            tbl.item(1, 1).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(
                tbl, 1, 2, 1, 1, self.tr("BMG-GMG\nmag " + self.units["label_L"])
            )
            tbl.item(1, 2).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 3, 1, 1, self.tr("BMG-GMG\ndir (deg)"))
            tbl.item(1, 3).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 4, 1, 1, self.tr("GC-BC\n(deg)"))
            tbl.item(1, 4).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 5, 1, 1, self.tr("BC/GC"))
            tbl.item(1, 5).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 0, 6, 1, 5, self.tr("VTG"))
            tbl.item(0, 6).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 6, 1, 1, self.tr(" Lag \n(sec)"))
            tbl.item(1, 6).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(
                tbl, 1, 7, 1, 1, self.tr("BMG-GMG\nmag " + self.units["label_L"])
            )
            tbl.item(1, 7).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 8, 1, 1, self.tr("BMG-GMG\ndir (deg)"))
            tbl.item(1, 8).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 9, 1, 1, self.tr("GC-BC\n(deg)"))
            tbl.item(1, 9).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 10, 1, 1, self.tr("BC/GC"))
            tbl.item(1, 10).setTextAlignment(QtCore.Qt.AlignCenter)

            # Add transect data
            for row in range(nrows):
                col = 0
                transect_id = self.checked_transects_idx[row]

                # File/transect name
                tbl.setItem(
                    row + 2,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].file_name[:-4]
                    ),
                )
                tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                gga_lag, vtg_lag = TransectData.compute_gps_lag(
                    self.meas.transects[transect_id]
                )

                # GGA lag
                if gga_lag is not None:
                    col = 1
                    tbl.setItem(
                        row + 2,
                        col,
                        QtWidgets.QTableWidgetItem("{:10.1f}".format(gga_lag)),
                    )
                    if self.meas.qa.gga_vel["lag_status"] == "warning":
                        tbl.item(row + 2, col).setBackground(QtGui.QColor(255, 77, 77))
                        tbl.item(row + 2, col).setToolTip(
                            "GGA: BT and GGA do not appear to be sychronized"
                        )

                    elif self.meas.qa.gga_vel["lag_status"] == "caution":
                        tbl.item(row + 2, col).setBackground(QtGui.QColor(255, 204, 0))
                        tbl.item(row + 2, col).setToolTip(
                            "gga: BT and GGA do not appear to be sychronized"
                        )

                    else:
                        tbl.item(row + 2, col).setBackground(
                            QtGui.QColor(255, 255, 255)
                        )

                if self.meas.transects[transect_id].boat_vel.gga_vel is not None:
                    gga_bt = TransectData.compute_gps_bt(
                        self.meas.transects[transect_id], gps_ref="gga_vel"
                    )

                    if len(gga_bt) > 0:
                        # GGA BMG-GMG mag
                        col = 2
                        tbl.setItem(
                            row + 2,
                            col,
                            QtWidgets.QTableWidgetItem(
                                "{:10.3f}".format(gga_bt["mag"] * self.units["L"])
                            ),
                        )
                        tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                        # GGA BMG-GMG dir
                        col = 3
                        tbl.setItem(
                            row + 2,
                            col,
                            QtWidgets.QTableWidgetItem(
                                "{:10.2f}".format(gga_bt["dir"])
                            ),
                        )
                        tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                        # GGA GC-BC
                        col = 4
                        tbl.setItem(
                            row + 2,
                            col,
                            QtWidgets.QTableWidgetItem(
                                "{:10.2f}".format(gga_bt["course"])
                            ),
                        )
                        tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                        # GGA BC/GC
                        col = 5
                        tbl.setItem(
                            row + 2,
                            col,
                            QtWidgets.QTableWidgetItem(
                                "{:10.4f}".format(gga_bt["ratio"])
                            ),
                        )
                        tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # VTG lag
                if vtg_lag is not None:
                    col = 6
                    tbl.setItem(
                        row + 2,
                        col,
                        QtWidgets.QTableWidgetItem("{:10.1f}".format(vtg_lag)),
                    )
                    tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)
                    if self.meas.qa.vtg_vel["lag_status"] == "warning":
                        tbl.item(row + 2, col).setBackground(QtGui.QColor(255, 77, 77))
                        tbl.item(row + 2, col).setToolTip(
                            "VTG: BT and VTG do not appear to be sychronized"
                        )

                    elif self.meas.qa.vtg_vel["lag_status"] == "caution":
                        tbl.item(row + 2, col).setBackground(QtGui.QColor(255, 204, 0))
                        tbl.item(row + 2, col).setToolTip(
                            "vtg: BT and VTG do not appear to be sychronized"
                        )

                    else:
                        tbl.item(row + 2, col).setBackground(
                            QtGui.QColor(255, 255, 255)
                        )

                if self.meas.transects[transect_id].boat_vel.vtg_vel is not None:
                    vtg_bt = TransectData.compute_gps_bt(
                        self.meas.transects[transect_id], gps_ref="vtg_vel"
                    )

                    if len(vtg_bt) > 0:
                        # VTG BMG-GMG mag
                        col = 7
                        tbl.setItem(
                            row + 2,
                            col,
                            QtWidgets.QTableWidgetItem(
                                "{:10.3f}".format(vtg_bt["mag"] * self.units["L"])
                            ),
                        )
                        tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                        # VTG BMG-GMG dir
                        col = 8
                        tbl.setItem(
                            row + 2,
                            col,
                            QtWidgets.QTableWidgetItem(
                                "{:10.2f}".format(vtg_bt["dir"])
                            ),
                        )
                        tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                        # VTG GC-BC
                        col = 9
                        tbl.setItem(
                            row + 2,
                            col,
                            QtWidgets.QTableWidgetItem(
                                "{:10.2f}".format(vtg_bt["course"])
                            ),
                        )
                        tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

                        # VTG BC/GC
                        col = 10
                        tbl.setItem(
                            row + 2,
                            col,
                            QtWidgets.QTableWidgetItem(
                                "{:10.4f}".format(vtg_bt["ratio"])
                            ),
                        )
                        tbl.item(row + 2, col).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        tbl.item(self.transect_row + 2, 0).setFont(self.font_bold)
        tbl.scrollToItem(tbl.item(self.transect_row + 2, 0))

        # Turn signals off
        self.cb_gps_bt_2.blockSignals(True)
        self.cb_gps_gga_2.blockSignals(True)
        self.cb_gps_vtg_2.blockSignals(True)
        self.cb_gps_vectors_2.blockSignals(True)

        # Initialize checkbox settings for boat reference
        self.cb_gps_bt_2.setCheckState(QtCore.Qt.Checked)
        if (
            self.meas.transects[self.checked_transects_idx[0]].boat_vel.gga_vel
            is not None
        ):
            self.cb_gps_gga_2.setCheckState(QtCore.Qt.Checked)
        if (
            self.meas.transects[self.checked_transects_idx[0]].boat_vel.vtg_vel
            is not None
        ):
            self.cb_gps_vtg_2.setCheckState(QtCore.Qt.Checked)

        self.cb_gps_vectors_2.setCheckState(QtCore.Qt.Checked)

        # Turn signals on
        self.cb_gps_bt_2.blockSignals(False)
        self.cb_gps_gga_2.blockSignals(False)
        self.cb_gps_vtg_2.blockSignals(False)
        self.cb_gps_vectors_2.blockSignals(False)

        self.gps_bt_plots()

        if not self.gps_initialized:
            tbl.cellClicked.connect(self.gps_bt_table_clicked)
            # Connect plot variable checkboxes
            self.cb_gps_bt_2.stateChanged.connect(self.gps_bt_plot_change)
            self.cb_gps_gga_2.stateChanged.connect(self.gps_bt_plot_change)
            self.cb_gps_vtg_2.stateChanged.connect(self.gps_bt_plot_change)
            self.cb_gps_vectors_2.stateChanged.connect(self.gps_bt_plot_change)

            self.gps_bt_initialized = True

    def gps_bt_table_clicked(self, row, column, caller=None):
        """Changes plotted data to the transect of the transect clicked.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        caller: str
            Identifies tab from which the method is called
        """

        if column == 0:
            self.transect_row = row - 2
            self.gps_bt_plots()
            self.change = True
            self.map_change = True
        if caller is None:
            self.gps_table_clicked(row - 2, column, caller="gps_bt")
        self.tab_gps_2_gpsbt.setFocus()

    def gps_bt_plots(self):
        """Creates graphic for GPS BT tab."""

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.transect_row]
            self.transect = self.meas.transects[transect_id]

            # Identify transect to be plotted in table
            for row in range(nrows):
                self.table_gps_bt.item(row + 2, 0).setFont(self.font_normal)
            # Set selected file to bold font
            self.table_gps_bt.item(self.transect_row + 2, 0).setFont(self.font_bold)

            # Update plots
            self.gps_bt_shiptrack()
            self.gps_bt_boat_speed()

            # Update list of figs
            self.figs = [self.gps_shiptrack_fig, self.gps_ts_fig]
            self.fig_calls = [self.gps_bt_shiptrack, self.gps_bt_boat_speed]

            # Reset data cursor to work with new data plot
            if self.actionData_Cursor.isChecked():
                self.data_cursor()

        self.tab_gps_2_gpsbt.setFocus()

    def gps_bt_shiptrack(self):
        """Creates shiptrack plot for data in transect."""

        self.cb_gps_bt_2.blockSignals(True)
        self.cb_gps_gga_2.blockSignals(True)
        self.cb_gps_vtg_2.blockSignals(True)
        self.cb_gps_vectors_2.blockSignals(True)
        self.cb_gps_bt_2.blockSignals(True)
        self.cb_gps_gga_2.blockSignals(True)
        self.cb_gps_vtg_2.blockSignals(True)
        self.cb_gps_vectors_2.blockSignals(True)

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.gps_bt_shiptrack_canvas is None:
            # Create the canvas
            self.gps_bt_shiptrack_canvas = MplCanvas(
                parent=self.graph_gps_st_2, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_gps_st_2)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.gps_bt_shiptrack_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.gps_bt_shiptrack_toolbar = NavigationToolbar(
                self.gps_bt_shiptrack_canvas, self
            )
            self.gps_bt_shiptrack_toolbar.hide()

        # Initialize the shiptrack figure and assign to the canvas
        self.gps_bt_shiptrack_fig = Shiptrack(canvas=self.gps_bt_shiptrack_canvas)
        # Create the figure with the specified data
        self.gps_bt_shiptrack_fig.create(
            transect=self.transect,
            units=self.units,
            cb=True,
            cb_bt=self.cb_gps_bt_2,
            cb_gga=self.cb_gps_gga_2,
            cb_vtg=self.cb_gps_vtg_2,
            cb_vectors=self.cb_gps_vectors_2,
        )

        # Draw canvas
        self.gps_bt_shiptrack_canvas.draw()

        self.cb_gps_bt_2.blockSignals(False)
        self.cb_gps_gga_2.blockSignals(False)
        self.cb_gps_vtg_2.blockSignals(False)
        self.cb_gps_vectors_2.blockSignals(False)

    def gps_bt_boat_speed(self):
        """Creates boat speed plot for data in transect."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.gps_bt_speed_canvas is None:
            # Create the canvas
            self.gps_bt_speed_canvas = MplCanvas(
                parent=self.graph_gps_bt_ts, width=8, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_gps_bt_ts)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.gps_bt_speed_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.gps_bt_speed_toolbar = NavigationToolbar(
                self.gps_bt_speed_canvas, self
            )
            self.gps_bt_speed_toolbar.hide()

        # Initialize the boat speed figure and assign to the canvas
        self.gps_bt_speed_fig = BoatSpeed(canvas=self.gps_bt_speed_canvas)
        # Create the figure with the specified data
        self.gps_bt_speed_fig.create(
            transect=self.transect,
            units=self.units,
            cb=True,
            cb_bt=self.cb_gps_bt_2,
            cb_gga=self.cb_gps_gga_2,
            cb_vtg=self.cb_gps_vtg_2,
        )

        # Draw canvas
        self.gps_bt_speed_canvas.draw()

    @QtCore.pyqtSlot()
    def gps_bt_plot_change(self):
        """Coordinates changes in what references should be displayed in the
        boat speed and shiptrack plots.
        """

        with self.wait_cursor():
            # Shiptrack
            self.gps_bt_shiptrack_fig.change()
            self.gps_bt_shiptrack_canvas.draw()

            # Boat speed
            self.gps_bt_speed_fig.change()
            self.gps_bt_speed_canvas.draw()

            self.tab_gps_2_gpsbt.setFocus()

    def gps_comments_messages(self):
        """Displays comments and messages associated with gps filters in
        Messages tab.
        """

        # Clear comments and messages
        self.display_gps_comments.clear()
        self.display_gps_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_gps_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_gps_comments.textCursor().insertText(comment)
                self.display_gps_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_gps_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_gps_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.gga_vel["messages"]:
                if type(message) is str:
                    self.display_gps_messages.textCursor().insertText(message)
                else:
                    self.display_gps_messages.textCursor().insertText(message[0])
                self.display_gps_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_gps_messages.textCursor().insertBlock()
            for message in self.meas.qa.vtg_vel["messages"]:
                if type(message) is str:
                    self.display_gps_messages.textCursor().insertText(message)
                else:
                    self.display_gps_messages.textCursor().insertText(message[0])
                self.display_gps_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_gps_messages.textCursor().insertBlock()

            self.update_tab_icons()

    # Depth tab
    # =======
    def depth_tab(self, old_discharge=None):
        """Initialize, setup settings, and display initial data in depth tab.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        """

        # Setup data table
        tbl = self.table_depth
        table_header = [
            self.tr("Filename"),
            self.tr("Draft \n" + self.units["label_L"]),
            self.tr("Number or \n Ensembles"),
            self.tr("Beam 1 \n % Invalid"),
            self.tr("Beam 2 \n % Invalid"),
            self.tr("Beam 3 \n % Invalid"),
            self.tr("Beam 4 \n % Invalid"),
            self.tr("Vertical \n % Invalid"),
            self.tr("Depth Sounder \n % Invalid"),
            self.tr("Discharge \n Previous \n" + self.units["label_Q"]),
            self.tr("Discharge \n Now \n" + self.units["label_Q"]),
            self.tr("Discharge \n % Change"),
        ]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.setStyleSheet("QToolTip{font: 12pt}")

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        if not self.depth_initialized:
            tbl.cellClicked.connect(self.depth_table_clicked)

            # Initialize checkbox settings top plot and build depth ref
            # combobox options
            self.cb_depth_beam1.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_beam2.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_beam3.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_beam4.setCheckState(QtCore.Qt.Checked)

            # Initialize checkbox settings bottom plot
            self.cb_depth_4beam_cs.setCheckState(QtCore.Qt.Unchecked)
            self.cb_depth_final_cs.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_vert_cs.setCheckState(QtCore.Qt.Unchecked)
            self.cb_depth_ds_cs.setCheckState(QtCore.Qt.Unchecked)

            # Initialize checkbox settings top plot and build depth ref
            # combobox options
            self.cb_depth_beam1.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_beam2.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_beam3.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_beam4.setCheckState(QtCore.Qt.Checked)

            # Connect top plot variable checkboxes
            self.cb_depth_beam1.stateChanged.connect(self.depth_top_plot_change)
            self.cb_depth_beam2.stateChanged.connect(self.depth_top_plot_change)
            self.cb_depth_beam3.stateChanged.connect(self.depth_top_plot_change)
            self.cb_depth_beam4.stateChanged.connect(self.depth_top_plot_change)
            self.cb_depth_vert.stateChanged.connect(self.depth_top_plot_change)
            self.cb_depth_ds.stateChanged.connect(self.depth_top_plot_change)

            # Connect bottom plot variable checkboxes
            self.cb_depth_4beam_cs.stateChanged.connect(self.depth_bottom_plot_change)
            self.cb_depth_final_cs.stateChanged.connect(self.depth_bottom_plot_change)
            self.cb_depth_vert_cs.stateChanged.connect(self.depth_bottom_plot_change)
            self.cb_depth_ds_cs.stateChanged.connect(self.depth_bottom_plot_change)

            # Connect options
            self.combo_depth_ref.currentIndexChanged[str].connect(self.change_ref)
            self.combo_depth_avg.currentIndexChanged[str].connect(
                self.change_avg_method
            )
            self.combo_depth_filter.currentIndexChanged[str].connect(self.change_filter)

            self.depth_initialized = True

        self.combo_depth_ref.blockSignals(True)
        depth_ref_options = [self.tr("4-Beam Avg")]

        # Setup depth reference combo box for vertical beam
        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].depths.vb_depths
            is not None
        ):
            self.cb_depth_vert.blockSignals(True)
            self.cb_depth_vert.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_vert.blockSignals(False)
            depth_ref_options.append(self.tr("Comp 4-Beam Preferred"))
            depth_ref_options.append(self.tr("Vertical"))
            depth_ref_options.append(self.tr("Comp Vertical Preferred"))
            self.cb_depth_vert.setEnabled(True)
            self.cb_depth_vert_cs.setEnabled(True)
        else:
            self.cb_depth_vert.setEnabled(False)
            self.cb_depth_vert_cs.setEnabled(False)

        # Setup depth reference combo box for depth sounder
        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].depths.ds_depths
            is not None
        ):
            self.cb_depth_ds.blockSignals(True)
            self.cb_depth_ds.setCheckState(QtCore.Qt.Checked)
            self.cb_depth_ds.blockSignals(False)
            depth_ref_options.append(self.tr("Comp 4-Beam Preferred"))
            depth_ref_options.append(self.tr("Depth Sounder"))
            depth_ref_options.append(self.tr("Comp DS Preferred"))
            self.cb_depth_ds.setEnabled(True)
            self.cb_depth_ds_cs.setEnabled(True)
        else:
            self.cb_depth_ds.setEnabled(False)
            self.cb_depth_ds_cs.setEnabled(False)

        self.combo_depth_ref.clear()
        self.combo_depth_ref.addItems(depth_ref_options)

        # Transect selected for display
        self.transect = self.meas.transects[
            self.checked_transects_idx[self.transect_row]
        ]
        depth_ref_selected = self.transect.depths.selected
        depth_composite = self.transect.depths.composite

        # Turn signals off
        self.combo_depth_avg.blockSignals(True)
        self.combo_depth_filter.blockSignals(True)

        # Set depth reference
        self.combo_depth_ref.blockSignals(True)
        if depth_ref_selected == "bt_depths":
            if depth_composite == "On":
                self.combo_depth_ref.setCurrentIndex(1)
            else:
                self.combo_depth_ref.setCurrentIndex(0)
        elif depth_ref_selected == "vb_depths":
            if depth_composite == "On":
                self.combo_depth_ref.setCurrentIndex(3)
            else:
                self.combo_depth_ref.setCurrentIndex(2)
        elif depth_ref_selected == "ds_depths":
            if depth_composite == "On":
                self.combo_depth_ref.setCurrentIndex(5)
            else:
                self.combo_depth_ref.setCurrentIndex(4)
        self.combo_depth_ref.blockSignals(False)

        # Set depth average method
        depths_selected = getattr(
            self.meas.transects[self.checked_transects_idx[self.transect_row]].depths,
            depth_ref_selected,
        )
        self.combo_depth_avg.blockSignals(True)
        if depths_selected.avg_method == "IDW":
            self.combo_depth_avg.setCurrentIndex(0)
        else:
            self.combo_depth_avg.setCurrentIndex(1)
        self.combo_depth_avg.blockSignals(False)

        # Set depth filter method
        self.combo_depth_filter.blockSignals(True)
        if depths_selected.filter_type == "Smooth":
            self.combo_depth_filter.setCurrentIndex(1)
        elif depths_selected.filter_type == "TRDI":
            self.combo_depth_filter.setCurrentIndex(2)
        else:
            self.combo_depth_filter.setCurrentIndex(0)
        self.combo_depth_filter.blockSignals(False)

        # Turn signals on
        self.combo_depth_ref.blockSignals(False)
        self.combo_depth_avg.blockSignals(False)
        self.combo_depth_filter.blockSignals(False)

        # Display content
        if old_discharge is None:
            old_discharge = self.meas.discharge
        self.update_depth_table(
            old_discharge=old_discharge, new_discharge=self.meas.discharge
        )
        self.depth_plots()
        self.depth_comments_messages()

        # Setup list for use by graphics controls
        self.canvases = [self.depth_canvas]
        self.figs = [self.depth_fig]
        self.fig_calls = [self.depth_plots]
        self.toolbars = [self.depth_toolbar]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def update_depth_table(self, old_discharge, new_discharge):
        """Updates the depth table with new or reprocessed data.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp with new settings
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_depth

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]
                valid_beam_data = transect.depths.bt_depths.valid_beams
                if transect.depths.vb_depths is not None:
                    valid_vert_beam = transect.depths.vb_depths.valid_beams
                else:
                    valid_vert_beam = None
                if transect.depths.ds_depths is not None:
                    valid_ds_beam = transect.depths.ds_depths.valid_beams
                else:
                    valid_ds_beam = None

                num_ensembles = len(valid_beam_data[0, :])

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.depths["q_total_warning"][transect_id]
                    or self.meas.qa.depths["q_max_run_warning"][transect_id]
                    or self.meas.qa.depths["all_invalid"][transect_id]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.depths["q_total_caution"][transect_id]
                    or self.meas.qa.depths["q_max_run_caution"][transect_id]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                tbl.item(row, col).setToolTip(self.depth_create_tooltip(self, row, col))

                # Draft
                col += 1
                item = "{:5.2f}".format(
                    transect.depths.bt_depths.draft_use_m * self.units["L"]
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if self.meas.qa.depths["draft"] == 2:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                elif self.meas.qa.depths["draft"] == 1:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                tbl.item(row, col).setToolTip(self.depth_create_tooltip(self, row, col))

                # Total number of ensembles
                col += 1
                item = "{:5d}".format(num_ensembles)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in beam 1
                col += 1
                item = "{:3.2f}".format(
                    ((num_ensembles - np.nansum(valid_beam_data[0, :])) / num_ensembles)
                    * 100.0
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in beam 2
                col += 1
                item = "{:3.2f}".format(
                    ((num_ensembles - np.nansum(valid_beam_data[1, :])) / num_ensembles)
                    * 100.0
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in beam 3
                col += 1
                item = "{:3.2f}".format(
                    ((num_ensembles - np.nansum(valid_beam_data[2, :])) / num_ensembles)
                    * 100.0
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in beam 4
                col += 1
                item = "{:3.2f}".format(
                    ((num_ensembles - np.nansum(valid_beam_data[3, :])) / num_ensembles)
                    * 100.0
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in vertical beam
                col += 1
                if valid_vert_beam is not None:
                    item = "{:3.2f}".format(
                        ((num_ensembles - np.nansum(valid_vert_beam)) / num_ensembles)
                        * 100.0
                    )
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in depth sounder
                col += 1
                if valid_ds_beam is not None:
                    item = "{:3.2f}".format(
                        ((num_ensembles - np.nansum(valid_ds_beam)) / num_ensembles)
                        * 100.0
                    )
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge before changes
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                old_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge after changes
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                new_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent change in discharge
                col += 1
                if np.abs(old_discharge[transect_id].total) > 0:
                    per_change = (
                        (
                            new_discharge[transect_id].total
                            - old_discharge[transect_id].total
                        )
                        / old_discharge[transect_id].total
                    ) * 100
                    tbl.setItem(
                        row,
                        col,
                        QtWidgets.QTableWidgetItem("{:3.1f}".format(per_change)),
                    )
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                tbl.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            tbl.item(self.transect_row, 0).setFont(self.font_bold)
            tbl.scrollToItem(tbl.item(self.transect_row, 0))
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

    @staticmethod
    def depth_create_tooltip(self, row, column):
        """Create tooltips for depth table."""

        # Identify transect associated with the row
        transect_id = self.checked_transects_idx[row]
        tt = ""
        if column == 0:
            cat_idx = 0
            tt = "".join(
                self.q_qa_message(
                    qa_data=self.meas.qa.depths,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )
            tt = "".join(tt)

        elif column == 1:
            if self.meas.qa.depths["draft"] == 1:
                tt = self.tr("Transducer depth is not consistent among transects.")
            elif self.meas.qa.depths["draft"] == 2:
                tt = self.tr("Transducer depth is too shallow, likely 0.")
        return tt

    def depth_plots(self):
        """Creates graphics for depth tab."""

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.transect_row]
            self.transect = self.meas.transects[transect_id]

            for row in range(nrows):
                self.table_depth.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_depth.item(self.transect_row, 0).setFont(self.font_bold)

            # If the canvas has not been previously created, create the
            # canvas and add the widget.
            if self.depth_canvas is None:
                # Create the canvas
                self.depth_canvas = MplCanvas(
                    parent=self.graph_depth, width=8, height=2, dpi=80
                )
                # Assign layout to widget to allow auto scaling
                layout = QtWidgets.QVBoxLayout(self.graph_depth)
                # Adjust margins of layout to maximize graphic area
                layout.setContentsMargins(0, 0, 0, 0)
                # Add the canvas
                layout.addWidget(self.depth_canvas)
                # Initialize hidden toolbar for use by graphics controls
                self.depth_toolbar = NavigationToolbar(self.depth_canvas, self)
                self.depth_toolbar.hide()

            # Initialize the top figure and assign to the canvas
            self.depth_fig = AdvGraphs(canvas=self.depth_canvas)
            # Create the figure with the specified data
            self.depth_fig.create_depth_tab_graphs(
                transect=self.transect,
                units=self.units,
                b1=self.cb_depth_beam1.isChecked(),
                b2=self.cb_depth_beam2.isChecked(),
                b3=self.cb_depth_beam3.isChecked(),
                b4=self.cb_depth_beam4.isChecked(),
                vb=self.cb_depth_vert.isChecked(),
                ds=self.cb_depth_ds.isChecked(),
                avg4_final=self.cb_depth_4beam_cs.isChecked(),
                vb_final=self.cb_depth_vert_cs.isChecked(),
                ds_final=self.cb_depth_ds_cs.isChecked(),
                final=self.cb_depth_final_cs.isChecked(),
                x_axis_type=self.x_axis_type,
            )

            # Draw canvas
            self.depth_canvas.draw()

            # Update list of figs
            self.figs = [self.depth_fig]
            self.fig_calls = [self.depth_plots]
            self.toolbars = [self.depth_toolbar]

            # Reset data cursor to work with new figure
            if self.actionData_Cursor.isChecked():
                self.data_cursor()
            self.tab_depth_2_data.setFocus()

    @QtCore.pyqtSlot(int, int)
    def depth_table_clicked(self, row, column):
        """Changes plotted data to the transect of the transect clicked or
        allows changing of the draft.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        """

        self.table_depth.blockSignals(True)
        # Change transect plotted
        if column == 0:
            self.transect_row = row
            self.depth_plots()
            self.change = True
            self.map_change = True

        # Change draft
        if column == 1:
            # Intialize dialog
            draft_dialog = Draft(self)
            draft_dialog.draft_units.setText(self.units["label_L"])
            draft_entered = draft_dialog.exec_()
            # If data entered.
            with self.wait_cursor():
                # Save discharge from previous settings
                old_discharge = copy.deepcopy(self.meas.discharge)
                if draft_entered:
                    draft = self.check_numeric_input(draft_dialog.ed_draft)
                    if draft is not None:
                        draft = draft / self.units["L"]
                        # Apply change to selected or all transects
                        if draft_dialog.rb_all.isChecked():
                            self.meas.change_draft(draft=draft)
                        else:
                            self.meas.change_draft(
                                draft=draft,
                                transect_idx=self.checked_transects_idx[row],
                            )

                        # Update table
                        self.update_depth_table(
                            old_discharge=old_discharge,
                            new_discharge=self.meas.discharge,
                        )

                        # Update plots
                        self.depth_plots()

                        self.depth_comments_messages()
                        self.change = True
                        self.map_change = True
        self.table_depth.blockSignals(False)
        self.tab_depth_2_data.setFocus()

    def update_depth_tab(self, s):
        """Updates the depth tab (table and graphics) after a change to
        settings has been made.

        Parameters
        ----------
        s: dict
            Dictionary of all process settings for the
            measurement
        """

        # Save discharge from previous settings
        old_discharge = copy.deepcopy(self.meas.discharge)

        # Apply new settings
        self.meas.apply_settings(settings=s)

        # Update table
        self.update_depth_table(
            old_discharge=old_discharge, new_discharge=self.meas.discharge
        )

        # Update plots
        self.depth_plots()

        self.depth_comments_messages()
        self.tab_depth_2_data.setFocus()

    @QtCore.pyqtSlot()
    def depth_top_plot_change(self):
        """Coordinates changes in user selected data to be displayed in the
        top plot.
        """

        self.depth_plots()

    @QtCore.pyqtSlot()
    def depth_bottom_plot_change(self):
        """Coordinates changes in user selected data to be displayed in
        the bottom plot."""

        self.depth_plots()

    @QtCore.pyqtSlot(str)
    def change_ref(self, text):
        """Coordinates user initiated change to depth reference.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            self.combo_depth_ref.blockSignals(True)
            # Get current settings
            s = self.meas.current_settings()

            # Change settings based on combo box selection
            if text == "4-Beam Avg":
                s["depthReference"] = "bt_depths"
                s["depthComposite"] = "Off"
            elif text == "Comp 4-Beam Preferred":
                s["depthReference"] = "bt_depths"
                s["depthComposite"] = "On"
            elif text == "Vertical":
                s["depthReference"] = "vb_depths"
                s["depthComposite"] = "Off"
            elif text == "Comp Vertical Preferred":
                s["depthReference"] = "vb_depths"
                s["depthComposite"] = "On"
            elif text == "Depth Sounder":
                s["depthReference"] = "ds_depths"
                s["depthComposite"] = "Off"
            elif text == "Comp DS Preferred":
                s["depthReference"] = "ds_depths"
                s["depthComposite"] = "On"

            # Update measurement and display
            self.update_depth_tab(s)
            self.change = True
            self.map_change = True
            self.combo_depth_ref.blockSignals(False)

    @QtCore.pyqtSlot(str)
    def change_filter(self, text):
        """Coordinates user initiated change to the depth filter.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            self.combo_depth_filter.blockSignals(True)
            # Get current settings
            s = self.meas.current_settings()
            s["depthFilterType"] = text

            # Update measurement and display
            self.update_depth_tab(s)
            self.change = True
            self.map_change = True
            self.combo_depth_filter.blockSignals(False)

    @QtCore.pyqtSlot(str)
    def change_avg_method(self, text):
        """Coordinates user initiated change to the averaging method.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            self.combo_depth_avg.blockSignals(True)

            # Get current settings
            s = self.meas.current_settings()
            s["depthAvgMethod"] = text

            # Update measurement and display
            self.update_depth_tab(s)
            self.change = True
            self.map_change = True
            self.combo_depth_avg.blockSignals(False)

    def depth_comments_messages(self):
        """Displays comments and messages associated with depth filters in
        Messages tab.
        """

        # Clear comments and messages
        self.display_depth_comments.clear()
        self.display_depth_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_depth_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_depth_comments.textCursor().insertText(comment)
                self.display_depth_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_depth_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_depth_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.depths["messages"]:
                if type(message) is str:
                    self.display_depth_messages.textCursor().insertText(message)
                else:
                    self.display_depth_messages.textCursor().insertText(message[0])
                self.display_depth_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_depth_messages.textCursor().insertBlock()

            self.update_tab_icons()

    # WT tab
    # ======
    def wt_tab(self, old_discharge=None):
        """Initialize, setup settings, and display initial data in water
        track tab.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        """

        # Setup data table
        tbl = self.table_wt
        table_header = [
            self.tr("Filename"),
            self.tr("Number of \n Depth Cells"),
            self.tr("Beam \n % <4"),
            self.tr("Total \n % Invalid"),
            self.tr("Orig Data \n % Invalid"),
            self.tr("<4 Beam \n % Invalid"),
            self.tr("Error Vel \n % Invalid"),
            self.tr("Vert Vel \n % Invalid"),
            self.tr("Other \n % Invalid"),
            self.tr("SNR \n % Invalid"),
            self.tr("Discharge \n Previous " + self.units["label_Q"]),
            self.tr("Discharge \n Now " + self.units["label_Q"]),
            self.tr("Discharge \n % Change"),
        ]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.setStyleSheet("QToolTip{font: 12pt}")

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Turn signals off
        self.cb_wt_bt.blockSignals(True)
        self.cb_wt_gga.blockSignals(True)
        self.cb_wt_vtg.blockSignals(True)
        self.cb_wt_vectors.blockSignals(True)
        self.combo_wt_3beam.blockSignals(True)
        self.combo_wt_error_velocity.blockSignals(True)
        self.combo_wt_vert_velocity.blockSignals(True)
        self.combo_wt_snr.blockSignals(True)

        # Initialize checkbox settings for boat reference
        self.cb_wt_bt.setCheckState(QtCore.Qt.Checked)
        self.cb_wt_gga.setCheckState(QtCore.Qt.Unchecked)
        self.cb_wt_vtg.setCheckState(QtCore.Qt.Unchecked)
        selected = self.meas.transects[
            self.checked_transects_idx[self.transect_row]
        ].boat_vel.selected
        if selected == "gga_vel":
            self.cb_wt_gga.setCheckState(QtCore.Qt.Checked)
        elif selected == "vtg_vel":
            self.cb_wt_vtg.setCheckState(QtCore.Qt.Checked)

        self.cb_wt_vectors.setCheckState(QtCore.Qt.Checked)

        # Connect plot variable checkboxes
        self.cb_wt_bt.stateChanged.connect(self.wt_plot_change)
        self.cb_wt_gga.stateChanged.connect(self.wt_plot_change)
        self.cb_wt_vtg.stateChanged.connect(self.wt_plot_change)
        self.cb_wt_vectors.stateChanged.connect(self.wt_plot_change)

        # Setup SNR option for SonTek
        if (
            self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer
            == "SonTek"
        ):
            self.rb_wt_snr.setEnabled(True)
            self.combo_wt_snr.setEnabled(True)
            self.rb_wt_snr.toggled.connect(self.wt_radiobutton_control)
        else:
            self.rb_wt_snr.setEnabled(False)
            self.combo_wt_snr.setEnabled(False)

        # Turn signals on
        self.cb_wt_bt.blockSignals(False)
        self.cb_wt_gga.blockSignals(False)
        self.cb_wt_vtg.blockSignals(False)
        self.cb_wt_vectors.blockSignals(False)
        self.combo_wt_3beam.blockSignals(False)
        self.combo_wt_error_velocity.blockSignals(False)
        self.combo_wt_vert_velocity.blockSignals(False)
        self.combo_wt_snr.blockSignals(False)

        # Initialize connections
        if not self.wt_initialized:
            tbl.cellClicked.connect(self.wt_table_clicked)
            # Connect radio buttons
            self.rb_wt_beam.toggled.connect(self.wt_radiobutton_control)
            self.rb_wt_error.toggled.connect(self.wt_radiobutton_control)
            self.rb_wt_vert.toggled.connect(self.wt_radiobutton_control)
            self.rb_wt_speed.toggled.connect(self.wt_radiobutton_control)
            self.rb_wt_contour.toggled.connect(self.wt_radiobutton_control)

            # Connect manual entry
            self.ed_wt_error_vel_threshold.editingFinished.connect(
                self.change_wt_error_vel_threshold
            )
            self.ed_wt_vert_vel_threshold.editingFinished.connect(
                self.change_wt_vert_vel_threshold
            )

            # Connect filters
            self.ed_wt_excluded_dist.editingFinished.connect(
                self.change_wt_excluded_dist
            )
            self.combo_wt_3beam.currentIndexChanged[str].connect(self.change_wt_beam)
            self.combo_wt_error_velocity.currentIndexChanged[str].connect(
                self.change_wt_error
            )
            self.combo_wt_vert_velocity.currentIndexChanged[str].connect(
                self.change_wt_vertical
            )
            self.combo_wt_snr.currentIndexChanged[str].connect(self.change_wt_snr)

            self.wt_initialized = True

        # Transect selected for display
        self.transect = self.meas.transects[
            self.checked_transects_idx[self.transect_row]
        ]
        if old_discharge is None:
            old_discharge = self.meas.discharge
        self.update_wt_table(
            old_discharge=old_discharge, new_discharge=self.meas.discharge
        )

        # Set beam filter from transect data
        if self.transect.w_vel.beam_filter < 0:
            self.combo_wt_3beam.setCurrentIndex(0)
        elif self.transect.w_vel.beam_filter == 3:
            self.combo_wt_3beam.setCurrentIndex(1)
        elif self.transect.w_vel.beam_filter == 4:
            self.combo_wt_3beam.setCurrentIndex(2)
        else:
            self.combo_wt_3beam.setCurrentIndex(0)

        # Set excluded distance from transect data
        ex_dist = (
            self.meas.transects[self.checked_transects_idx[0]].w_vel.excluded_dist_m
            * self.units["L"]
        )
        self.ed_wt_excluded_dist.setText("{:2.2f}".format(ex_dist))

        # Set error velocity filter from transect data
        index = self.combo_wt_error_velocity.findText(
            self.transect.w_vel.d_filter, QtCore.Qt.MatchFixedString
        )
        self.combo_wt_error_velocity.setCurrentIndex(index)
        s = self.meas.current_settings()

        if self.transect.w_vel.d_filter == "Manual":
            threshold = "{:3.2f}".format(s["WTdFilterThreshold"] * self.units["V"])
            self.ed_wt_error_vel_threshold.setText(threshold)

        # Set vertical velocity filter from transect data
        index = self.combo_wt_vert_velocity.findText(
            self.transect.w_vel.w_filter, QtCore.Qt.MatchFixedString
        )
        self.combo_wt_vert_velocity.setCurrentIndex(index)

        if self.transect.w_vel.w_filter == "Manual":
            threshold = "{:3.2f}".format(s["WTwFilterThreshold"] * self.units["V"])
            self.ed_wt_vert_vel_threshold.setText(threshold)

        # Set smooth filter from transect data
        self.combo_wt_snr.blockSignals(True)
        if self.transect.w_vel.snr_filter == "Auto":
            self.combo_wt_snr.setCurrentIndex(0)
        elif self.transect.w_vel.snr_filter == "Off":
            self.combo_wt_snr.setCurrentIndex(1)
        self.combo_wt_snr.blockSignals(False)

        # Display content
        self.wt_plots()
        self.wt_comments_messages()

        # Setup list for use by graphics controls
        self.canvases = [self.wt_shiptrack_canvas, self.wt_filter_canvas]
        self.figs = [self.wt_shiptrack_fig, self.wt_filter_fig]
        self.fig_calls = [self.wt_shiptrack, self.wt_filter_plots]
        self.toolbars = [self.wt_shiptrack_toolbar, self.wt_filter_toolbar]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def update_wt_table(self, old_discharge, new_discharge):
        """Updates the bottom track table with new or reprocessed data.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp with new settings
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_wt

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]

                # Prep data for table
                valid_data = transect.w_vel.valid_data
                useable_cells = transect.w_vel.valid_data[6, :, :]
                num_useable_cells = np.nansum(np.nansum(useable_cells.astype(int)))
                wt_temp = copy.deepcopy(transect.w_vel)
                wt_temp.filter_beam(4)
                not_4beam = np.nansum(
                    np.nansum(
                        np.logical_not(wt_temp.valid_data[5, :, :][useable_cells])
                    )
                )
                num_invalid = np.nansum(
                    np.nansum(np.logical_not(valid_data[0, :, :][useable_cells]))
                )
                num_orig_invalid = np.nansum(
                    np.nansum(np.logical_not(valid_data[1, :, :][useable_cells]))
                )
                num_beam_invalid = np.nansum(
                    np.nansum(np.logical_not(valid_data[5, :, :][useable_cells]))
                )
                num_error_invalid = np.nansum(
                    np.nansum(np.logical_not(valid_data[2, :, :][useable_cells]))
                )
                num_vert_invalid = np.nansum(
                    np.nansum(np.logical_not(valid_data[3, :, :][useable_cells]))
                )
                num_other_invalid = np.nansum(
                    np.nansum(np.logical_not(valid_data[4, :, :][useable_cells]))
                )
                num_snr_invalid = np.nansum(
                    np.nansum(np.logical_not(valid_data[7, :, :][useable_cells]))
                )

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                tbl.item(row, 0).setFont(self.font_normal)

                # Total number of depth cells
                col += 1
                item = "{:7d}".format(num_useable_cells)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Less than 4 beams
                col += 1
                item = "{:3.2f}".format((not_4beam / num_useable_cells) * 100.0)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Invalid total
                col += 1
                item = "{:3.2f}".format((num_invalid / num_useable_cells) * 100.0)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.w_vel["all_invalid"][transect_id]
                    or self.meas.qa.w_vel["q_total_warning"][transect_id, 0]
                    or self.meas.qa.w_vel["q_max_run_warning"][transect_id, 0]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.w_vel["q_total_caution"][transect_id, 0]
                    or self.meas.qa.w_vel["q_max_run_caution"][transect_id, 0]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                tbl.item(row, col).setToolTip(
                    self.tr(self.wt_create_tooltip(self, row, col))
                )

                # Invalid original data
                col += 1
                percent_invalid = (num_orig_invalid / num_useable_cells) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.w_vel["q_total_warning"][transect_id, 1]
                    or self.meas.qa.w_vel["q_max_run_warning"][transect_id, 1]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.w_vel["q_total_caution"][transect_id, 1]
                    or self.meas.qa.w_vel["q_max_run_caution"][transect_id, 1]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.wt_create_tooltip(self, row, col))
                    )

                # Invalid 3 beam
                col += 1
                percent_invalid = (num_beam_invalid / num_useable_cells) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.w_vel["q_total_warning"][transect_id, 5]
                    or self.meas.qa.w_vel["q_max_run_warning"][transect_id, 5]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.w_vel["q_total_caution"][transect_id, 5]
                    or self.meas.qa.w_vel["q_max_run_caution"][transect_id, 5]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.wt_create_tooltip(self, row, col))
                    )

                # Error velocity invalid
                col += 1
                percent_invalid = (num_error_invalid / num_useable_cells) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.w_vel["q_total_warning"][transect_id, 2]
                    or self.meas.qa.w_vel["q_max_run_warning"][transect_id, 2]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.w_vel["q_total_caution"][transect_id, 2]
                    or self.meas.qa.w_vel["q_max_run_caution"][transect_id, 2]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.wt_create_tooltip(self, row, col))
                    )

                # Vertical velocity invalid
                col += 1
                percent_invalid = (num_vert_invalid / num_useable_cells) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.w_vel["q_total_warning"][transect_id, 3]
                    or self.meas.qa.w_vel["q_max_run_warning"][transect_id, 3]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.w_vel["q_total_caution"][transect_id, 3]
                    or self.meas.qa.w_vel["q_max_run_caution"][transect_id, 3]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.wt_create_tooltip(self, row, col))
                    )

                # Other
                col += 1
                percent_invalid = (num_other_invalid / num_useable_cells) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if (
                    self.meas.qa.w_vel["q_total_warning"][transect_id, 4]
                    or self.meas.qa.w_vel["q_max_run_warning"][transect_id, 4]
                    or percent_invalid == 100
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                elif (
                    self.meas.qa.w_vel["q_total_caution"][transect_id, 4]
                    or self.meas.qa.w_vel["q_max_run_caution"][transect_id, 4]
                ):
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                if percent_invalid == 100:
                    tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                else:
                    tbl.item(row, col).setToolTip(
                        self.tr(self.wt_create_tooltip(self, row, col))
                    )

                # SNR
                col += 1
                percent_invalid = (num_snr_invalid / num_useable_cells) * 100.0
                item = "{:3.2f}".format(percent_invalid)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if self.meas.qa.w_vel["q_total_warning"].shape[1] > 7:
                    if (
                        self.meas.qa.w_vel["q_total_warning"][transect_id, 7]
                        or self.meas.qa.w_vel["q_max_run_warning"][transect_id, 7]
                        or percent_invalid == 100
                    ):
                        tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))

                    elif (
                        self.meas.qa.w_vel["q_total_caution"][transect_id, 7]
                        or self.meas.qa.w_vel["q_max_run_caution"][transect_id, 7]
                    ):
                        tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))

                    else:
                        tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                    if percent_invalid == 100:
                        tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                    else:
                        tbl.item(row, col).setToolTip(
                            self.tr(self.wt_create_tooltip(self, row, col))
                        )

                    if percent_invalid == 100:
                        tbl.item(row, col).setToolTip(self.tr("All data are invalid."))
                    else:
                        tbl.item(row, col).setToolTip(
                            self.tr(self.wt_create_tooltip(self, row, col))
                        )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Discharge before changes
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                old_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge after changes
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(
                            self.q_digits(
                                new_discharge[transect_id].total * self.units["Q"]
                            )
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent change in discharge
                col += 1
                if np.abs(old_discharge[transect_id].total) > 0:
                    per_change = (
                        (
                            new_discharge[transect_id].total
                            - old_discharge[transect_id].total
                        )
                        / old_discharge[transect_id].total
                    ) * 100
                    tbl.setItem(
                        row,
                        col,
                        QtWidgets.QTableWidgetItem("{:3.1f}".format(per_change)),
                    )
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Set selected file to bold font

            tbl.item(self.transect_row, 0).setFont(self.font_bold)
            tbl.scrollToItem(tbl.item(self.transect_row, 0))
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

            self.wt_comments_messages()
            self.tab_wt_2_data.setFocus()

    def wt_plots(self):
        """Creates graphics for WT tab."""

        with self.wait_cursor():
            self.cb_wt_bt.blockSignals(True)
            self.cb_wt_gga.blockSignals(True)
            self.cb_wt_vtg.blockSignals(True)
            self.cb_wt_vectors.blockSignals(True)
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)
            for nrow in range(nrows):
                self.table_wt.item(nrow, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_wt.item(self.transect_row, 0).setFont(self.font_bold)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.transect_row]
            self.transect = self.meas.transects[transect_id]
            self.invalid_wt = np.logical_not(self.transect.w_vel.valid_data)

            # Update plots
            self.wt_shiptrack()
            self.wt_filter_plots()

            # Update list of figs
            self.figs = [self.wt_shiptrack_fig, self.wt_filter_fig]
            self.fig_calls = [self.wt_shiptrack, self.wt_filter_plots]

            # Reset data cursor to work with new figure
            if self.actionData_Cursor.isChecked():
                self.data_cursor()

            self.cb_wt_bt.blockSignals(False)
            self.cb_wt_gga.blockSignals(False)
            self.cb_wt_vtg.blockSignals(False)
            self.cb_wt_vectors.blockSignals(False)

    def wt_shiptrack(self):
        """Creates shiptrack plot for data in transect."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.wt_shiptrack_canvas is None:
            # Create the canvas
            self.wt_shiptrack_canvas = MplCanvas(
                parent=self.graph_wt_st, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_wt_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.wt_shiptrack_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.wt_shiptrack_toolbar = NavigationToolbar(
                self.wt_shiptrack_canvas, self
            )
            self.wt_shiptrack_toolbar.hide()

        # Initialize the shiptrack figure and assign to the canvas
        self.wt_shiptrack_fig = Shiptrack(canvas=self.wt_shiptrack_canvas)
        # Create the figure with the specified data
        self.wt_shiptrack_fig.create(
            transect=self.transect,
            units=self.units,
            cb=True,
            cb_bt=self.cb_wt_bt,
            cb_gga=self.cb_wt_gga,
            cb_vtg=self.cb_wt_vtg,
            cb_vectors=self.cb_wt_vectors,
        )

        # Draw canvas
        self.wt_shiptrack_canvas.draw()

    @QtCore.pyqtSlot()
    def wt_radiobutton_control(self):
        """Identifies a change in radio buttons and calls the plot routine
        to update the graph.
        """

        with self.wait_cursor():
            if self.sender().isChecked():
                self.wt_filter_plots()

    def wt_filter_plots(self):
        """Creates plots of filter characteristics."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.wt_filter_canvas is None:
            # Create the canvas
            self.wt_filter_canvas = MplCanvas(
                parent=self.graph_wt, width=10, height=2, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_wt)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(0, 0, 0, 0)
            # Add the canvas
            layout.addWidget(self.wt_filter_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.wt_filter_toolbar = NavigationToolbar(self.wt_filter_canvas, self)
            self.wt_filter_toolbar.hide()

        # Initialize the water filters figure and assign to the canvas
        self.wt_filter_fig = AdvGraphs(canvas=self.wt_filter_canvas)
        if self.plot_extrapolated:
            self.wt_filter_fig.create_wt_tab_graphs(
                transect=self.transect,
                units=self.units,
                contour=self.rb_wt_contour.isChecked(),
                beam=self.rb_wt_beam.isChecked(),
                error=self.rb_wt_error.isChecked(),
                vert=self.rb_wt_vert.isChecked(),
                snr=self.rb_wt_snr.isChecked(),
                speed=self.rb_wt_speed.isChecked(),
                x_axis_type=self.x_axis_type,
                color_map=self.color_map,
                discharge=self.meas.discharge[
                    self.checked_transects_idx[self.transect_row]
                ],
            )
        else:
            self.wt_filter_fig.create_wt_tab_graphs(
                transect=self.transect,
                units=self.units,
                contour=self.rb_wt_contour.isChecked(),
                beam=self.rb_wt_beam.isChecked(),
                error=self.rb_wt_error.isChecked(),
                vert=self.rb_wt_vert.isChecked(),
                snr=self.rb_wt_snr.isChecked(),
                speed=self.rb_wt_speed.isChecked(),
                x_axis_type=self.x_axis_type,
                color_map=self.color_map,
            )

        # Draw canvas
        self.wt_filter_canvas.draw()

        # Update list of figs
        self.figs = [self.wt_shiptrack_fig, self.wt_filter_fig]
        self.fig_calls = [self.wt_shiptrack, self.wt_filter_plots]

        # Reset data cursor to work with new figure
        if self.actionData_Cursor.isChecked():
            self.data_cursor()
        self.tab_wt_2_data.setFocus()

    def wt_table_clicked(self, row, column):
        """Changes plotted data to the transect of the transect clicked.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        """

        if column == 0:
            self.transect_row = row
            self.wt_plots()
            self.change = True
            self.map_change = True
        self.tab_wt_2_data.setFocus()

    @staticmethod
    def wt_create_tooltip(self, row, column):
        """Create tooltips for WT table."""

        # Identify transect associated with the row
        transect_id = self.checked_transects_idx[row]

        cat_idx = None
        tt = ""

        if column == 3:
            cat_idx = 0
        elif column == 4:
            cat_idx = 1
        elif column == 5:
            cat_idx = 5
        elif column == 6:
            cat_idx = 2
        elif column == 7:
            cat_idx = 3
        elif column == 8:
            cat_idx = 4
        elif column == 9:
            cat_idx = 7

        if cat_idx is not None:
            tt = "".join(
                self.q_qa_message(
                    qa_data=self.meas.qa.w_vel,
                    cat_idx=cat_idx,
                    transect_id=transect_id,
                    total_threshold_warning=self.meas.qa.q_total_threshold_warning,
                    total_threshold_caution=self.meas.qa.q_total_threshold_caution,
                    run_threshold_warning=self.meas.qa.q_run_threshold_warning,
                    run_threshold_caution=self.meas.qa.q_run_threshold_caution,
                )
            )
        return tt

    @QtCore.pyqtSlot()
    def wt_plot_change(self):
        """Coordinates changes in what references should be displayed in the
        shiptrack plots.
        """

        with self.wait_cursor():
            # Shiptrack
            self.wt_shiptrack_fig.change()
            self.wt_shiptrack_canvas.draw()
            self.tab_wt_2_data.setFocus()

    def update_wt_tab(self, s):
        """Updates the measurement and water track tab (table and graphics)
        after a change to settings has been made.

        Parameters
        ----------
        s: dict
            Dictionary of all process settings for the
            measurement
        """

        # Save discharge from previous settings
        old_discharge = copy.deepcopy(self.meas.discharge)

        # Apply new settings
        self.meas.apply_settings(settings=s)

        # Update table
        self.update_wt_table(
            old_discharge=old_discharge, new_discharge=self.meas.discharge
        )
        self.wt_comments_messages()

        # Update plots
        self.wt_plots()
        self.tab_wt_2_data.setFocus()

    @QtCore.pyqtSlot(str)
    def change_wt_beam(self, text):
        """Coordinates user initiated change to the beam settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change beam filter setting
            if text == "Auto":
                s["WTbeamFilter"] = -1
            elif text == "Allow":
                s["WTbeamFilter"] = 3
            elif text == "4-Beam Only":
                s["WTbeamFilter"] = 4

            # Update measurement and display
            self.update_wt_tab(s)
            self.change = True
            self.map_change = True

    @QtCore.pyqtSlot(str)
    def change_wt_error(self, text):
        """Coordinates user initiated change to the error velocity settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s["WTdFilter"] = text

            if text == "Manual":
                # If Manual enable the line edit box for user input. Updates
                # are not applied until the user has entered
                # a value in the line edit box.
                self.ed_wt_error_vel_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and
                # disabled and the updates applied.
                self.ed_wt_error_vel_threshold.setEnabled(False)
                self.ed_wt_error_vel_threshold.setText("")
                self.update_wt_tab(s)

            self.change = True
            self.map_change = True

    @QtCore.pyqtSlot(str)
    def change_wt_vertical(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s["WTwFilter"] = text

            if text == "Manual":
                # If Manual enable the line edit box for user input. Updates
                # are not applied until the user has entered
                # a value in the line edit box.
                self.ed_wt_vert_vel_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and
                # disabled and the updates applied.
                self.ed_wt_vert_vel_threshold.setEnabled(False)
                self.ed_wt_vert_vel_threshold.setText("")
                self.update_wt_tab(s)
            self.change = True
            self.map_change = True

    @QtCore.pyqtSlot(str)
    def change_wt_snr(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            if text == "Off":
                s["WTsnrFilter"] = "Off"
            elif text == "Auto":
                s["WTsnrFilter"] = "Auto"

            # Update measurement and display
            self.update_wt_tab(s)
            self.change = True
            self.map_change = True

    @QtCore.pyqtSlot()
    def change_wt_error_vel_threshold(self):
        """Coordinates application of a user specified error velocity
        threshold.
        """

        self.ed_wt_error_vel_threshold.blockSignals(True)
        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = self.check_numeric_input(self.ed_wt_error_vel_threshold)
            if threshold is not None:
                threshold = threshold / self.units["V"]
                # Get current settings
                s = self.meas.current_settings()
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get
                # twice. This checks to see if there was and actual change.
                compute = False
                if type(s["WTdFilterThreshold"]) is dict:
                    compute = True
                else:
                    if np.abs(threshold - s["WTdFilterThreshold"]) > 0.0001:
                        compute = True
                if compute:
                    # Change settings to manual and the associated threshold
                    s["WTdFilter"] = "Manual"
                    s["WTdFilterThreshold"] = threshold

                    # Update measurement and display
                    self.update_wt_tab(s)
                    self.change = True
                    self.map_change = True

        self.ed_wt_error_vel_threshold.blockSignals(False)

    @QtCore.pyqtSlot()
    def change_wt_vert_vel_threshold(self):
        """Coordinates application of a user specified vertical velocity
        threshold.
        """

        self.ed_wt_vert_vel_threshold.blockSignals(True)
        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = self.check_numeric_input(self.ed_wt_vert_vel_threshold)
            if threshold is not None:
                threshold = threshold / self.units["V"]

                # Get current settings
                s = self.meas.current_settings()
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get twice. This checks
                # to see if there was and actual change.
                compute = False
                if type(s["WTwFilterThreshold"]) is dict:
                    compute = True
                else:
                    if np.abs(threshold - s["WTwFilterThreshold"]) > 0.0001:
                        compute = True
                if compute:
                    # Change settings to manual and the associated threshold
                    s["WTwFilter"] = "Manual"
                    s["WTwFilterThreshold"] = threshold

                    # Update measurement and display
                    self.update_wt_tab(s)
                    self.change = True
                    self.map_change = True

        self.ed_wt_vert_vel_threshold.blockSignals(False)

    @QtCore.pyqtSlot()
    def change_wt_excluded_dist(self):
        """Coordinates application of a user specified excluded distance."""

        self.ed_wt_excluded_dist.blockSignals(True)
        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = self.check_numeric_input(self.ed_wt_excluded_dist)
            if threshold is not None:
                threshold = threshold / self.units["L"]

                # Get current settings
                s = self.meas.current_settings()
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get twice. This line
                # checks to see if there was and actual change.
                if np.abs(threshold - s["WTExcludedDistance"]) > 0.0001:
                    # Change settings
                    s["WTExcludedDistance"] = threshold

                    # Update measurement and display
                    self.update_wt_tab(s)
                    self.change = True
                    self.map_change = True

        self.ed_wt_excluded_dist.blockSignals(False)

    def wt_comments_messages(self):
        """Displays comments and messages associated with bottom track
        filters in Messages tab.
        """

        # Clear comments and messages
        self.display_wt_comments.clear()
        self.display_wt_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_wt_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_wt_comments.textCursor().insertText(comment)
                self.display_wt_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_wt_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_wt_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.w_vel["messages"]:
                if type(message) is str:
                    self.display_wt_messages.textCursor().insertText(message)
                else:
                    self.display_wt_messages.textCursor().insertText(message[0])
                self.display_wt_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_wt_messages.textCursor().insertBlock()

            self.update_tab_icons()

    # Extrap Tab
    # ==========
    def extrap_tab(self):
        """Initializes all of the features on the extrap_tab."""

        # Make copy to allow resting to original if changes are made
        self.extrap_meas = copy.deepcopy(self.meas)

        self.extrap_index(len(self.checked_transects_idx))
        self.start_bank = None

        # ID Weighted Method
        if self.meas.extrap_fit.norm_data[-1].use_weighted:
            self.gb_fit.setTitle(self.tr("Fit Parameters (Weighted)"))
        else:
            self.gb_fit.setTitle(self.tr("Fit Parameters"))

        # Subsectioning
        if self.meas.extrap_fit.sub_from_left:
            self.txt_extrap_subsection.setText(self.tr("Subsection (% L to R, x:x):"))
        else:
            self.txt_extrap_subsection.setText(self.tr("Subsection (st%:end%)"))

        # Setup number of points data table
        tbl = self.table_extrap_n_points
        table_header = [self.tr("Z"), self.tr("No. Pts.")]
        ncols = len(table_header)
        nrows = len(self.meas.extrap_fit.norm_data[-1].unit_normalized_z)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.n_points_table()

        # Setup discharge sensitivity table
        tbl = self.table_extrap_qsen
        table_header = [
            self.tr("Top"),
            self.tr("Bottom"),
            self.tr("Exponent"),
            self.tr("% Diff"),
        ]
        ncols = len(table_header)
        nrows = 6
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.q_sensitivity_table()

        # Setup transect / measurement list table
        tbl = self.table_extrap_fit
        ncols = 1
        nrows = len(self.checked_transects_idx) + 1
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.verticalHeader().hide()
        tbl.horizontalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.fit_list_table()

        self.display_current_fit()
        self.set_fit_options()

        self.extrap_set_data()
        self.extrap_plot()

        self.extrap_comments_messages()

        # Initialize connections
        if not self.extrap_initialized:
            self.table_extrap_qsen.cellClicked.connect(self.sensitivity_change_fit)
            self.table_extrap_fit.cellClicked.connect(self.fit_list_table_clicked)
            # Connect fit options
            self.combo_extrap_fit.currentIndexChanged[str].connect(
                self.change_fit_method
            )
            self.combo_extrap_top.currentIndexChanged[str].connect(
                self.change_top_method
            )
            self.combo_extrap_bottom.currentIndexChanged[str].connect(
                self.change_bottom_method
            )
            self.ed_extrap_exponent.editingFinished.connect(self.change_exponent)

            # Connect display settings
            self.cb_extrap_data.stateChanged.connect(self.extrap_plot)
            self.cb_extrap_surface.stateChanged.connect(self.extrap_plot)
            self.cb_extrap_meas_medians.stateChanged.connect(self.extrap_plot)
            self.cb_extrap_meas_fit.stateChanged.connect(self.extrap_plot)
            self.cb_extrap_trans_medians.stateChanged.connect(self.extrap_plot)
            self.cb_extrap_trans_fit.stateChanged.connect(self.extrap_plot)

            # Connect data settings
            self.combo_extrap_data.currentIndexChanged[str].connect(self.change_data)
            self.ed_extrap_threshold.editingFinished.connect(self.change_threshold)
            self.ed_extrap_subsection.editingFinished.connect(self.change_subsection)
            self.combo_extrap_type.currentIndexChanged[str].connect(
                self.change_data_type
            )

            # Cancel and apply buttons
            self.pb_extrap_cancel.clicked.connect(self.cancel_extrap)

            self.extrap_initialized = True

        # Setup list for use by graphics controls
        self.canvases = [self.extrap_canvas]
        self.figs = [self.extrap_fig]
        self.fig_calls = [self.extrap_plot]
        self.toolbars = [self.extrap_toolbar]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def extrap_update(self):
        """Update the extrapolation tab."""

        # If change was to the measurement apply changes and update
        # sensitivity and messages
        if self.idx == len(self.meas.extrap_fit.sel_fit) - 1:
            s = self.meas.current_settings()
            self.meas.apply_settings(s)
            self.q_sensitivity_table()
            self.extrap_comments_messages()
            self.change = True
            self.map_change = True
        else:
            # Run qa to update messages for user data setting changes if
            # other than Measurement selected
            self.meas.update_qa()

        # ID Weighted Method
        if self.meas.extrap_fit.norm_data[-1].use_weighted:
            self.gb_fit.setTitle(self.tr("Fit Parameters (Weighted)"))
        else:
            self.gb_fit.setTitle(self.tr("Fit Parameters"))

        # Subsectioning
        if self.meas.extrap_fit.sub_from_left:
            self.txt_extrap_subsection.setText(self.tr("Subsection (% L to R, x:x):"))
        else:
            self.txt_extrap_subsection.setText(self.tr("Subsection (st%:end%)"))

        # Update tab
        self.n_points_table()
        self.set_fit_options()
        self.extrap_plot()
        self.extrap_comments_messages()

    def extrap_index(self, row):
        """Converts the row value to a transect index.

        Parameters
        ----------
        row: int
            Row selected from the fit list table
        """

        if row > len(self.checked_transects_idx) - 1:
            self.idx = len(self.meas.transects)
        else:
            self.idx = self.checked_transects_idx[row]

    def display_current_fit(self):
        """Displays the extrapolation methods currently used to compute
        discharge.
        """

        # Display Previous settings
        self.txt_extrap_p_fit.setText(self.meas.extrap_fit.sel_fit[-1].fit_method)
        self.txt_extrap_p_top.setText(self.meas.extrap_fit.sel_fit[-1].top_method)
        self.txt_extrap_p_bottom.setText(self.meas.extrap_fit.sel_fit[-1].bot_method)
        self.txt_extrap_p_exponent.setText(
            "{:6.4f}".format(self.meas.extrap_fit.sel_fit[-1].exponent)
        )

    def set_fit_options(self):
        """Sets the fit options for the currently selected transect or
        measurement.
        """

        # Setup fit method
        self.combo_extrap_fit.blockSignals(True)
        if self.meas.extrap_fit.sel_fit[self.idx].fit_method == "Automatic":
            self.combo_extrap_fit.setCurrentIndex(0)
            self.combo_extrap_top.setEnabled(False)
            self.combo_extrap_bottom.setEnabled(False)
            self.ed_extrap_exponent.setEnabled(False)
        else:
            self.combo_extrap_fit.setCurrentIndex(1)
            self.combo_extrap_top.setEnabled(True)
            self.combo_extrap_bottom.setEnabled(True)
            self.ed_extrap_exponent.setEnabled(True)
        self.combo_extrap_fit.blockSignals(False)

        # Set top method
        self.combo_extrap_top.blockSignals(True)
        if self.meas.extrap_fit.sel_fit[self.idx].top_method == "Power":
            self.combo_extrap_top.setCurrentIndex(0)
        elif self.meas.extrap_fit.sel_fit[self.idx].top_method == "Constant":
            self.combo_extrap_top.setCurrentIndex(1)
        else:
            self.combo_extrap_top.setCurrentIndex(2)
        self.combo_extrap_top.blockSignals(False)

        # Set bottom method
        self.combo_extrap_bottom.blockSignals(True)
        if self.meas.extrap_fit.sel_fit[self.idx].bot_method == "Power":
            self.combo_extrap_bottom.setCurrentIndex(0)
        else:
            self.combo_extrap_bottom.setCurrentIndex(1)
        self.combo_extrap_bottom.blockSignals(False)

        # Set exponent
        self.ed_extrap_exponent.blockSignals(True)
        self.ed_extrap_exponent.setText(
            "{:6.4f}".format(self.meas.extrap_fit.sel_fit[self.idx].exponent)
        )
        self.ed_extrap_exponent.blockSignals(False)

    def n_points_table(self):
        """Populates the table showing the normalized depth of each layer
        and how many data points are in each layer.
        """

        # Set table variable
        tbl = self.table_extrap_n_points

        # Get normalized data for transect or measurement selected
        norm_data = self.meas.extrap_fit.norm_data[self.idx]

        # Populate the table row by row substituting standard values if no
        # data exist.
        for row in range(len(norm_data.unit_normalized_z)):
            # Column 0 is normalized depth
            col = 0
            if np.isnan(norm_data.unit_normalized_z[row]):
                value = 1 - row / 20.0
            else:
                value = norm_data.unit_normalized_z[row]
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem("{:6.4f}".format(value)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Column 1 is number of points
            col = 1
            if np.isnan(norm_data.unit_normalized_no[row]):
                value = 0
            else:
                value = norm_data.unit_normalized_no[row]
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem("{:8.0f}".format(value)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

    def q_sensitivity_table(self):
        """Populates the discharge sensitivity table."""

        # Set table reference
        tbl = self.table_extrap_qsen

        # Get sensitivity data
        q_sen = self.meas.extrap_fit.q_sensitivity

        # Power / Power / 1/6
        row = 0
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Power"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("Power"))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.4f}".format(0.1667)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.2f}".format(q_sen.q_pp_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Power / Power / Optimize
        row = 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Power"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("Power"))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.4f}".format(q_sen.pp_exp)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.2f}".format(q_sen.q_pp_opt_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Constant / No Slip / 1/6
        row = 2
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Constant"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("No Slip"))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.4f}".format(0.1667)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.2f}".format(q_sen.q_cns_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Constant / No Slip / Optimize
        row = 3
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Constant"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("No Slip"))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.4f}".format(q_sen.ns_exp)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.2f}".format(q_sen.q_cns_opt_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # 3-Point / No Slip / 1/6
        row = 4
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("3-Point"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("No Slip"))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.4f}".format(0.1667)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.2f}".format(q_sen.q_3p_ns_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # 3-Point / No Slip / Optimize
        row = 5
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("3-Point"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem("No Slip"))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.4f}".format(q_sen.ns_exp)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = "{:6.2f}".format(q_sen.q_3p_ns_opt_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Manually set fit method
        if q_sen.q_man_mean is not None:
            row = tbl.rowCount()
            if row == 6:
                tbl.insertRow(row)
            else:
                row = row - 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(q_sen.man_top))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(q_sen.man_bot))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            item = "{:6.4f}".format(q_sen.man_exp)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            item = "{:6.2f}".format(q_sen.q_man_per_diff)
            tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)
        elif tbl.rowCount() == 7:
            tbl.removeRow(6)

        # Set reference
        if q_sen.q_man_mean is not None:
            self.set_extrap_reference(6)
        elif np.abs(q_sen.q_pp_per_diff) < 0.00000001:
            self.set_extrap_reference(0)
        elif np.abs(q_sen.q_pp_opt_per_diff) < 0.00000001:
            self.set_extrap_reference(1)
        elif np.abs(q_sen.q_cns_per_diff) < 0.00000001:
            self.set_extrap_reference(2)
        elif np.abs(q_sen.q_cns_opt_per_diff) < 0.00000001:
            self.set_extrap_reference(3)
        elif np.abs(q_sen.q_3p_ns_per_diff) < 0.00000001:
            self.set_extrap_reference(4)
        elif np.abs(q_sen.q_3p_ns_opt_per_diff) < 0.00000001:
            self.set_extrap_reference(5)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def set_extrap_reference(self, reference_row):
        """Sets the discharge sensitivity table to show the selected method
        as the reference.

        Parameters
        ----------
        reference_row: int
            Integer of the row in sensitivity table for the
            selected fit parameters
        """

        # Get table reference
        tbl = self.table_extrap_qsen

        # Set all data to normal font
        for row in range(tbl.rowCount()):
            for col in range(tbl.columnCount()):
                tbl.item(row, col).setFont(self.font_normal)

        # Set selected file to bold font
        for col in range(tbl.columnCount()):
            tbl.item(reference_row, col).setFont(self.font_bold)

    def fit_list_table(self):
        """Populates the fit list table to show all the checked transects
        and the composite measurement.
        """

        # Get table reference
        tbl = self.table_extrap_fit

        # Add transects and Measurement to table
        for n in range(len(self.checked_transects_idx)):
            item = self.meas.transects[self.checked_transects_idx[n]].file_name[:-4]
            tbl.setItem(n, 0, QtWidgets.QTableWidgetItem(item))
            tbl.item(n, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(n, 0).setFont(self.font_normal)
        tbl.setItem(
            len(self.checked_transects_idx),
            0,
            QtWidgets.QTableWidgetItem("Measurement"),
        )
        tbl.item(len(self.checked_transects_idx), 0).setFlags(QtCore.Qt.ItemIsEnabled)

        # Show the Measurement as the initial selection
        tbl.item(len(self.checked_transects_idx), 0).setFont(self.font_bold)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    @QtCore.pyqtSlot(int)
    def fit_list_table_clicked(self, selected_row):
        """Selects data to display and fit from list of transects and
        composite measurements.

        Parameters
        ----------
        selected_row: int
            Index to selected transect/measurement from list.
        """

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx) + 1

            for row in range(nrows):
                self.table_extrap_fit.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_extrap_fit.item(selected_row, 0).setFont(self.font_bold)

            self.extrap_index(selected_row)
            self.n_points_table()
            self.set_fit_options()
            self.extrap_plot()

    def extrap_plot(self):
        """Creates extrapolation plot."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.extrap_canvas is None:
            # Create the canvas
            self.extrap_canvas = MplCanvas(
                parent=self.graph_extrap, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_extrap)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.extrap_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.extrap_toolbar = NavigationToolbar(self.extrap_canvas, self)
            self.extrap_toolbar.hide()

        # Initialize the figure and assign to the canvas
        self.extrap_fig = ExtrapPlot(canvas=self.extrap_canvas)
        # Create the figure with the specified data
        self.extrap_fig.create(
            meas=self.meas,
            checked=self.checked_transects_idx,
            idx=self.idx,
            data_type=self.combo_extrap_type.currentText(),
            cb_data=self.cb_extrap_data.isChecked(),
            cb_surface=self.cb_extrap_surface.isChecked(),
            cb_trans_medians=self.cb_extrap_trans_medians.isChecked(),
            cb_trans_fit=self.cb_extrap_trans_fit.isChecked(),
            cb_meas_medians=self.cb_extrap_meas_medians.isChecked(),
            cb_meas_fit=self.cb_extrap_meas_fit.isChecked(),
        )

        # Update list of figs
        self.figs = [self.extrap_fig]

        # Reset data cursor to work with new figure
        if self.actionData_Cursor.isChecked():
            self.data_cursor()

        self.extrap_canvas.draw()

    def extrap_set_data(self):
        """Sets UI for data panel"""

        if self.meas.extrap_fit.sel_fit[-1].data_type.lower() != "q":
            self.extrap_set_data_manual()
        elif self.meas.extrap_fit.threshold != 20:
            self.extrap_set_data_manual()
        elif (
            self.meas.extrap_fit.subsection[0] != 0
            or self.meas.extrap_fit.subsection[1] != 100
        ):
            self.extrap_set_data_manual()
        else:
            self.extrap_set_data_auto()

    def extrap_set_data_manual(self):
        """Updates the UI when the user changes the data setting to manual."""

        if self.combo_extrap_data.currentIndex() == 0:
            self.combo_extrap_data.setCurrentIndex(1)
        self.ed_extrap_threshold.setEnabled(True)
        self.ed_extrap_subsection.setEnabled(True)
        self.combo_extrap_type.setEnabled(True)
        self.ed_extrap_threshold.setText(
            "{:3.0f}".format(self.meas.extrap_fit.threshold)
        )
        self.ed_extrap_subsection.setText(
            "{:.0f}:{:.0f}".format(
                self.meas.extrap_fit.subsection[0], self.meas.extrap_fit.subsection[1]
            )
        )

        if self.meas.extrap_fit.sel_fit[-1].data_type.lower() == "q":
            self.combo_extrap_type.setCurrentIndex(0)
        else:
            self.combo_extrap_type.setCurrentIndex(1)

    def extrap_set_data_auto(self):
        """Updates the UI when the user changes the data setting to automatic."""

        if self.combo_extrap_data.currentIndex() == 1:
            self.combo_extrap_data.setCurrentIndex(0)
        self.ed_extrap_threshold.setEnabled(False)
        self.ed_extrap_subsection.setEnabled(False)
        self.combo_extrap_type.setEnabled(False)
        self.ed_extrap_threshold.setText("20")
        self.ed_extrap_subsection.setText("0:100")
        self.combo_extrap_type.setCurrentIndex(0)

    @QtCore.pyqtSlot(str)
    def change_data(self, text):
        """Coordinates user initiated change to the data from automatic to
        manual.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            if text == "Manual":
                self.ed_extrap_threshold.setEnabled(True)
                self.ed_extrap_subsection.setEnabled(True)
                self.combo_extrap_type.setEnabled(True)
            else:
                self.ed_extrap_threshold.setEnabled(False)
                self.ed_extrap_subsection.setEnabled(False)
                self.combo_extrap_type.setEnabled(False)
                self.ed_extrap_threshold.setText("20")
                self.ed_extrap_subsection.setText("0:100")
                self.combo_extrap_type.setCurrentIndex(0)
                self.meas.extrap_fit.change_data_auto(self.meas.transects)
                self.extrap_update()

    @QtCore.pyqtSlot()
    def change_threshold(self):
        """Allows the user to change the threshold and then updates the data
        and display.
        """

        self.ed_extrap_threshold.blockSignals(True)

        # If data entered.
        with self.wait_cursor():
            threshold = self.check_numeric_input(self.ed_extrap_threshold)
            if threshold is not None:
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get
                # twice. This line checks to see if there was and actual
                # change.
                if np.abs(threshold - self.meas.extrap_fit.threshold) > 0.0001:
                    if 0 <= threshold <= 100:
                        self.meas.extrap_fit.change_threshold(
                            transects=self.meas.transects,
                            data_type=self.meas.extrap_fit.sel_fit[0].data_type,
                            threshold=threshold,
                        )
                        self.extrap_update()
                    else:
                        self.ed_extrap_threshold.setText(
                            "{:3.0f}".format(self.meas.extrap_fit.threshold)
                        )
            else:
                self.ed_extrap_threshold.setText(
                    "{:3.0f}".format(self.meas.extrap_fit.threshold)
                )

        self.ed_extrap_threshold.blockSignals(False)

    @QtCore.pyqtSlot()
    def change_subsection(self):
        """Allows the user to change the subsectioning and then updates the
        data and display.
        """

        self.ed_extrap_subsection.editingFinished.disconnect(self.change_subsection)

        # If data entered.
        with self.wait_cursor():
            try:
                use_q = True
                sub_from_left = True
                self.txt_extrap_subsection.setText("Subsection (% L to R, x:x):")

                sub_list = self.ed_extrap_subsection.text().split(":")
                subsection = [float(sub_list[0]), float(sub_list[1])]
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get twice. This line
                # checks to see if there was and actual change.
                if (
                    np.abs(subsection[0] - self.meas.extrap_fit.subsection[0]) > 0.0001
                    or np.abs(subsection[1] - self.meas.extrap_fit.subsection[1])
                    > 0.0001
                    or self.meas.extrap_fit.sub_from_left != sub_from_left
                ):
                    if (
                        0 <= subsection[0] <= 100
                        and subsection[0] < subsection[1] <= 100
                    ):
                        self.meas.extrap_fit.change_extents(
                            transects=self.meas.transects,
                            data_type=self.meas.extrap_fit.sel_fit[-1].data_type,
                            extents=subsection,
                            use_q=use_q,
                            sub_from_left=sub_from_left,
                        )
                        self.extrap_update()
                    else:
                        self.ed_extrap_subsection.setText(
                            "{:3.0f}:{:3.0f}".format(
                                self.meas.extrap_fit.subsection[0],
                                self.meas.extrap_fit.subsection[1],
                            )
                        )
            except (IndexError, TypeError):
                # If the user input is not valid, display message
                self.popup_message(
                    self.tr(
                        "Subsectioning requires data entry as two numbers "
                        "separated by a colon (example: 10:90) where the "
                        "first number is larger than the second"
                    )
                )

        self.ed_extrap_subsection.editingFinished.connect(self.change_subsection)

    @QtCore.pyqtSlot(str)
    def change_data_type(self, text):
        """Coordinates user initiated change to the data type.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Change setting based on combo box selection
            data_type = "q"
            if text == "Velocity":
                data_type = "v"

            self.meas.extrap_fit.change_data_type(
                transects=self.meas.transects, data_type=data_type
            )

            self.extrap_update()

    @QtCore.pyqtSlot(str)
    def change_fit_method(self, text):
        """Coordinates user initiated changing the fit type.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Change setting based on combo box selection
            self.meas.extrap_fit.change_fit_method(
                transects=self.meas.transects, new_fit_method=text, idx=self.idx
            )

            self.extrap_update()

    @QtCore.pyqtSlot(str)
    def change_top_method(self, text):
        """Coordinates user initiated changing the top method.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Change setting based on combo box selection
            self.meas.extrap_fit.change_fit_method(
                transects=self.meas.transects,
                new_fit_method="Manual",
                idx=self.idx,
                top=text,
            )

            self.extrap_update()

    @QtCore.pyqtSlot(str)
    def change_bottom_method(self, text):
        """Coordinates user initiated changing the bottom method.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Change setting based on combo box selection
            self.meas.extrap_fit.change_fit_method(
                transects=self.meas.transects,
                new_fit_method="Manual",
                idx=self.idx,
                bot=text,
            )

            self.extrap_update()

    @QtCore.pyqtSlot()
    def change_exponent(self):
        """Coordinates user initiated changing the bottom method."""

        self.ed_extrap_exponent.blockSignals(True)

        with self.wait_cursor():
            exponent = self.check_numeric_input(self.ed_extrap_exponent)
            if exponent is not None and 0 < exponent < 1.01:
                # Because editingFinished is used if return is pressed and
                # later focus is changed the method could get twice. This line
                # checks to see if there was and actual change.
                if (
                    np.abs(exponent - self.meas.extrap_fit.sel_fit[self.idx].exponent)
                    > 0.00001
                ):
                    # Change based on user input
                    self.meas.extrap_fit.change_fit_method(
                        transects=self.meas.transects,
                        new_fit_method="Manual",
                        idx=self.idx,
                        exponent=exponent,
                    )

                    self.extrap_update()
            else:
                self.ed_extrap_exponent.setText(
                    "{:6.4f}".format(self.meas.extrap_fit.sel_fit[self.idx].exponent)
                )

        self.ed_extrap_exponent.blockSignals(False)

    @QtCore.pyqtSlot(int)
    def sensitivity_change_fit(self, row):
        """Changes the fit based on the row in the discharge sensitivity
        table selected by the user.

        Parameters
        ----------
        row: int
            Index to selected fit combination from
            sensitivity table.
        """

        with self.wait_cursor():
            # Get fit settings from table
            top = self.table_extrap_qsen.item(row, 0).text()
            bot = self.table_extrap_qsen.item(row, 1).text()
            exponent = float(self.table_extrap_qsen.item(row, 2).text())

            # Change based on user selection
            self.meas.extrap_fit.change_fit_method(
                transects=self.meas.transects,
                new_fit_method="Manual",
                idx=self.idx,
                top=top,
                bot=bot,
                exponent=exponent,
            )

            self.extrap_update()

    def compare_medians(self):
        """This method computes and displays the median values for the
        measurement using an alternative method to allow comparison. If weighted
        is used the unweighted are computed and display. If the unweighted are used
        the method computes and displays the weighted. This method does not affect
        the computed discharge only the extrapolation display."""

        if self.meas.extrap_fit.norm_data[-1].data_type.lower() == "q":
            # Create a copy of the normalized values of the entire measurement
            compare_norm = copy.deepcopy(self.meas.extrap_fit.norm_data[-1])
            if self.meas.extrap_fit.use_weighted:
                # Compute unweighted medians
                compare_norm.use_weighted = False
                compare_norm.compute_stats(self.meas.extrap_fit.threshold)
            else:
                # Compute weighted medians
                compare_norm.use_weighted = True
                compare_norm.compute_stats(self.meas.extrap_fit.threshold)

            # Display data on extrapolation figure
            self.extrap_fig.extrap_plot_med_compare(compare_norm)
            self.extrap_canvas.draw()

    def cancel_extrap(self):
        """Rest extrapolation to settings that were inplace when the tab was
        opened.
        """

        self.meas = copy.deepcopy(self.extrap_meas)
        self.extrap_tab()
        self.change = False

    def extrap_comments_messages(self):
        """Displays comments and messages associated with bottom track
        filters in Messages tab.
        """

        # Clear comments and messages
        self.display_extrap_comments.clear()
        self.display_extrap_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_extrap_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_extrap_comments.textCursor().insertText(comment)
                self.display_extrap_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_extrap_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_extrap_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.extrapolation["messages"]:
                if type(message) is str:
                    self.display_extrap_messages.textCursor().insertText(message)
                else:
                    self.display_extrap_messages.textCursor().insertText(message[0])
                self.display_extrap_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_extrap_messages.textCursor().insertBlock()

            self.update_tab_icons()

    # Edges tab
    # =========
    def edges_tab(self):
        """Initializes all of the features of the edges tab."""

        # Setup data table
        tbl = self.table_edges
        table_header = [
            self.tr("Filename"),
            self.tr("Start \n Edge"),
            self.tr("Left \n Type"),
            self.tr("Left \n Coef."),
            self.tr("Left \n Dist. \n" + self.units["label_L"]),
            self.tr("Left \n # Ens."),
            self.tr("Left \n # Valid"),
            self.tr("Left \n Discharge \n" + self.units["label_Q"]),
            self.tr("Left \n % Q"),
            self.tr("Right \n Type"),
            self.tr("Right \n Coef."),
            self.tr("Right \n Dist. \n" + self.units["label_L"]),
            self.tr("Right \n # Ens."),
            self.tr("Right \n # Valid"),
            self.tr("Right \n Discharge \n" + self.units["label_Q"]),
            self.tr("Right \n % Q"),
        ]

        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.setStyleSheet("QToolTip{font: 12pt}")

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        if not self.edges_initialized:
            tbl.cellClicked.connect(self.edges_table_clicked)
            self.edges_initialized = True

        self.update_edges_table()

        self.edges_graphics()

        # Setup list for use by graphics controls
        self.canvases = [
            self.left_edge_contour_canvas,
            self.right_edge_contour_canvas,
            self.left_edge_st_canvas,
            self.right_edge_st_canvas,
        ]
        self.figs = [
            self.left_edge_contour_fig,
            self.right_edge_contour_fig,
            self.left_edge_st_fig,
            self.right_edge_st_fig,
        ]
        self.fig_calls = [
            self.edges_contour_plots,
            self.edges_contour_plots,
            self.edges_shiptrack_plots,
            self.edges_shiptrack_plots,
        ]
        self.toolbars = [
            self.left_edge_contour_toolbar,
            self.right_edge_contour_toolbar,
            self.left_edge_st_toolbar,
            self.right_edge_st_toolbar,
        ]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def update_edges_table(self):
        """Populates the edges table with the latest data and also updates
        the messages tab.
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_edges

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                tbl.item(row, 0).setFont(self.font_normal)

                # Start Edge
                col += 1
                item = transect.start_edge
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Left edge type
                col += 1
                item = transect.edges.left.type
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                # Format cell
                if self.meas.qa.edges["left_type"] == 2:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                    tbl.item(row, col).setToolTip(self.tr("Type is not consistent."))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Left edge coefficient
                col += 1
                if transect.edges.left.type == "Triangular":
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("0.3535"))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                elif transect.edges.left.type == "Rectangular":
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("0.91"))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                elif transect.edges.left.type == "Custom":
                    item = "{:1.4f}".format(transect.edges.left.cust_coef)
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(""))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Left edge dist
                col += 1
                item = "{:4.2f}".format(
                    transect.edges.left.distance_m * self.units["L"]
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                # Format cell
                if transect_id in self.meas.qa.edges["left_dist_moved_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(self.tr("Excessive boat movement."))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Left edge # ens
                col += 1
                # This allows the number of edge ensembles to be increased
                # to obtain total number of ensembles including invalid ensembles
                # for TRDI and report the specified number of ensembles
                # (even if all invalid) for SonTek
                left_idx = self.meas.discharge[transect_id].left_idx
                if len(left_idx) > 0:
                    if self.meas.transects[transect_id].start_edge == "Left":
                        n_ensembles = left_idx[-1] + 1
                    else:
                        n_ensembles = (
                            len(self.meas.transects[transect_id].in_transect_idx)
                            - left_idx[0]
                        )
                else:
                    n_ensembles = transect.edges.left.number_ensembles
                item = "{:4.0f}".format(n_ensembles)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Left edge # valid ens
                col += 1
                valid_ens = (
                    np.nansum(
                        self.meas.transects[transect_id].w_vel.valid_data[
                            0, :, self.meas.discharge[transect_id].left_idx
                        ],
                        1,
                    )
                    > 0
                )

                item = "{:4.0f}".format(np.nansum(valid_ens))
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                if transect_id in self.meas.qa.edges["invalid_transect_left_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("The percent of invalid ensembles exceeds 25%.")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Left edge discharge
                col += 1
                item = "{:6}".format(
                    self.q_digits(
                        self.meas.discharge[transect_id].left * self.units["Q"]
                    )
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                # Format cell
                if transect_id in self.meas.qa.edges["left_zero_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                    tbl.item(row, col).setToolTip(self.tr("Edge has zero Q."))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Left edge discharge %
                col += 1
                if np.abs(self.meas.discharge[transect_id].total) > 0:
                    item = "{:2.2f}".format(
                        (
                            self.meas.discharge[transect_id].left
                            / self.meas.discharge[transect_id].total
                        )
                        * 100
                    )
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if transect_id in self.meas.qa.edges["left_q_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("Edge Q is greater than 5% of the mean discharge.")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Right edge type
                col += 1
                item = transect.edges.right.type
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                # Format cell
                if self.meas.qa.edges["right_type"] == 2:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                    tbl.item(row, col).setToolTip(self.tr("Type is not consistent."))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Right edge coefficient
                col += 1
                if transect.edges.right.type == "Triangular":
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("0.3535"))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                elif transect.edges.right.type == "Rectangular":
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem("0.91"))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                elif transect.edges.right.type == "Custom":
                    item = "{:1.4f}".format(transect.edges.right.cust_coef)
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(""))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Right edge dist
                col += 1
                item = "{:4.2f}".format(
                    transect.edges.right.distance_m * self.units["L"]
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                # Format cell
                if transect_id in self.meas.qa.edges["right_dist_moved_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(self.tr("Excessive boat movement."))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Right edge # ens
                col += 1
                # This allows the number of edge ensembles to be increased
                # to obtain total number of ensembles including invalid ensembles
                # for TRDI and report the specified number of ensembles
                # (even if all invalid) for SonTek
                right_idx = self.meas.discharge[transect_id].right_idx
                if len(right_idx) > 0:
                    if self.meas.transects[transect_id].start_edge == "Right":
                        n_ensembles = right_idx[-1] + 1
                    else:
                        n_ensembles = (
                            len(self.meas.transects[transect_id].in_transect_idx)
                            - right_idx[0]
                        )
                else:
                    n_ensembles = transect.edges.right.number_ensembles
                item = "{:4.0f}".format(n_ensembles)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Right edge # valid ens
                col += 1
                valid_ens = (
                    np.nansum(
                        self.meas.transects[transect_id].w_vel.valid_data[
                            0, :, self.meas.discharge[transect_id].right_idx
                        ],
                        1,
                    )
                    > 0
                )

                item = "{:4.0f}".format(np.nansum(valid_ens))
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                if transect_id in self.meas.qa.edges["invalid_transect_right_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("The percent of invalid ensembles exceeds 25%.")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Right edge discharge
                col += 1
                item = "{:6}".format(
                    self.q_digits(
                        self.meas.discharge[transect_id].right * self.units["Q"]
                    )
                )
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if transect_id in self.meas.qa.edges["right_zero_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 77, 77))
                    tbl.item(row, col).setToolTip(self.tr("Edge has zero Q."))
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

                # Right edge discharge %
                col += 1
                if np.abs(self.meas.discharge[transect_id].total) > 0:
                    item = "{:2.2f}".format(
                        (
                            self.meas.discharge[transect_id].right
                            / self.meas.discharge[transect_id].total
                        )
                        * 100
                    )
                else:
                    item = "N/A"
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if transect_id in self.meas.qa.edges["right_q_idx"]:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 204, 0))
                    tbl.item(row, col).setToolTip(
                        self.tr("Edge Q is greater than 5% of the mean discharge.")
                    )
                else:
                    tbl.item(row, col).setBackground(QtGui.QColor(255, 255, 255))

            tbl.item(self.transect_row, 0).setFont(self.font_bold)
            tbl.scrollToItem(tbl.item(self.transect_row, 0))

            # Automatically resize rows and columns
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
        self.edges_comments_messages()

    @QtCore.pyqtSlot(int, int)
    def edges_table_clicked(self, row, col):
        """Coordinates user changes to edge settings.

        Parameters
        ----------
        row: int
            Row in table clicked
        col: int
            Column in table clicked
        """

        tbl = self.table_edges
        tbl.blockSignals(True)
        self.change = True
        self.map_change = True

        # Show transect
        if col == 0:
            with self.wait_cursor():
                self.transect_row = row
                for r in range(tbl.rowCount()):
                    tbl.item(r, 0).setFont(self.font_normal)
                tbl.item(self.transect_row, 0).setFont(self.font_bold)

                self.edges_graphics()
                self.change = True
                self.map_change = True

        # Start edge
        if col == 1:
            # Initialize dialog
            start_dialog = StartEdge()
            if (
                self.meas.transects[self.checked_transects_idx[row]].start_edge
                == "Left"
            ):
                start_dialog.rb_left.setChecked(True)
                start_dialog.rb_right.setChecked(False)
            else:
                start_dialog.rb_left.setChecked(False)
                start_dialog.rb_right.setChecked(True)

            rsp = start_dialog.exec_()
            # Data entered.
            with self.wait_cursor():
                if rsp == QtWidgets.QDialog.Accepted:
                    # Apply change
                    if start_dialog.rb_left.isChecked():
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].start_edge = "Left"
                    else:
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].start_edge = "Right"
                    # Reprocess measurement
                    s = self.meas.current_settings()
                    self.meas.apply_settings(s)
                    self.update_edges_table()
                    self.edges_graphics()
                    self.change = True
                    self.map_change = True
                    QtWidgets.QMessageBox.about(
                        self,
                        self.tr("Start Edge Change"),
                        self.tr(
                            "You changed the start "
                            "edge, verify that the "
                            "left and right "
                            "distances and edge types "
                            "are correct."
                        ),
                    )

        # Left edge type and coefficient
        elif col == 2 or col == 3 or col == 7:
            # Initialize dialog
            type_dialog = EdgeType()
            type_dialog.rb_transect.setChecked(True)
            if (
                self.meas.transects[self.checked_transects_idx[row]].edges.left.type
                == "Triangular"
            ):
                type_dialog.rb_triangular.setChecked(True)
            elif (
                self.meas.transects[self.checked_transects_idx[row]].edges.left.type
                == "Rectangular"
            ):
                type_dialog.rb_rectangular.setChecked(True)
            elif (
                self.meas.transects[self.checked_transects_idx[row]].edges.left.type
                == "Custom"
            ):
                type_dialog.rb_custom.setChecked(True)
                type_dialog.ed_custom.setText(
                    "{:1.4f}".format(
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.left.cust_coef
                    )
                )
            elif (
                self.meas.transects[self.checked_transects_idx[row]].edges.left.type
                == "User Q"
            ):
                type_dialog.rb_user.setChecked(True)
                type_dialog.ed_q_user.setText(
                    "{:6.2f}".format(
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.left.user_discharge_cms
                        * self.units["Q"]
                    )
                )
            rsp = type_dialog.exec_()

            # Data entered.
            with self.wait_cursor():
                if rsp == QtWidgets.QDialog.Accepted:
                    if type_dialog.rb_triangular.isChecked():
                        edge_type = "Triangular"
                        cust_coef = None
                        user_discharge_cms = None
                    elif type_dialog.rb_rectangular.isChecked():
                        edge_type = "Rectangular"
                        cust_coef = None
                        user_discharge_cms = None
                    elif type_dialog.rb_custom.isChecked():
                        edge_type = "Custom"
                        cust_coef = self.check_numeric_input(type_dialog.ed_custom)
                        if cust_coef is None:
                            cust_coef = 0
                        user_discharge_cms = None
                    elif type_dialog.rb_user.isChecked():
                        edge_type = "User Q"
                        cust_coef = None
                        user_discharge_cms = self.check_numeric_input(
                            type_dialog.ed_q_user
                        )
                        if user_discharge_cms is not None:
                            user_discharge_cms = user_discharge_cms / self.units["Q"]
                        else:
                            user_discharge_cms = 0
                    # Determine where to apply change and apply change
                    if type_dialog.rb_all.isChecked():
                        for idx in self.checked_transects_idx:
                            transect = self.meas.transects[idx]
                            transect.edges.left.type = edge_type
                            transect.edges.left.cust_coef = cust_coef
                            transect.edges.left.user_discharge_cms = user_discharge_cms
                    else:
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.left.type = edge_type
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.left.cust_coef = cust_coef
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.left.user_discharge_cms = user_discharge_cms

                    # Reprocess measurement
                    s = self.meas.current_settings()
                    self.meas.apply_settings(s)
                    self.update_edges_table()
                    self.edges_graphics()

        # Left edge distance
        elif col == 4:
            # Initialize dialog
            dist_dialog = EdgeDist()
            dist_dialog.rb_transect.setChecked(True)
            dist_dialog.ed_edge_dist.setText(
                "{:5.2f}".format(
                    self.meas.transects[
                        self.checked_transects_idx[row]
                    ].edges.left.distance_m
                    * self.units["L"]
                )
            )
            rsp = dist_dialog.exec_()

            # Data entered.
            with self.wait_cursor():
                if rsp == QtWidgets.QDialog.Accepted:
                    dist = self.check_numeric_input(dist_dialog.ed_edge_dist)
                    if dist is not None:
                        dist = dist / self.units["L"]
                        # Determine where to apply change and apply change
                        if dist_dialog.rb_all.isChecked():
                            for idx in self.checked_transects_idx:
                                self.meas.transects[idx].edges.left.distance_m = dist
                        else:
                            self.meas.transects[
                                self.checked_transects_idx[row]
                            ].edges.left.distance_m = dist

                        # Reprocess measurement
                        s = self.meas.current_settings()
                        self.meas.apply_settings(s)
                        self.update_edges_table()
                        self.edges_graphics()

        # Left number of ensembles
        elif col == 6:
            # Initialize dialog
            ens_dialog = EdgeEns()
            ens_dialog.rb_transect.setChecked(True)
            ens_dialog.ed_edge_ens.setText(
                "{:4.0f}".format(
                    self.meas.transects[
                        self.checked_transects_idx[row]
                    ].edges.left.number_ensembles
                )
            )
            rsp = ens_dialog.exec_()

            # Data entered.
            with self.wait_cursor():
                if rsp == QtWidgets.QDialog.Accepted:
                    num_ens = self.check_numeric_input(ens_dialog.ed_edge_ens)
                    if num_ens is not None:
                        # Determine where to apply change and apply change
                        if ens_dialog.rb_all.isChecked():
                            for idx in self.checked_transects_idx:
                                self.meas.transects[
                                    idx
                                ].edges.left.number_ensembles = num_ens
                        else:
                            self.meas.transects[
                                self.checked_transects_idx[row]
                            ].edges.left.number_ensembles = num_ens

                        # Reprocess measurement
                        s = self.meas.current_settings()
                        self.meas.apply_settings(s)
                        self.update_edges_table()
                        self.edges_graphics()

        # Right edge type and coefficient
        elif col == 9 or col == 10 or col == 14:
            # Initialize dialog
            type_dialog = EdgeType()
            type_dialog.rb_transect.setChecked(True)
            if (
                self.meas.transects[self.checked_transects_idx[row]].edges.right.type
                == "Triangular"
            ):
                type_dialog.rb_triangular.setChecked(True)
            elif (
                self.meas.transects[self.checked_transects_idx[row]].edges.right.type
                == "Rectangular"
            ):
                type_dialog.rb_rectangular.setChecked(True)
            elif (
                self.meas.transects[self.checked_transects_idx[row]].edges.right.type
                == "Custom"
            ):
                type_dialog.rb_custom.setChecked(True)
                type_dialog.ed_custom.setText(
                    "{:1.4f}".format(
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.right.cust_coef
                    )
                )
            elif (
                self.meas.transects[self.checked_transects_idx[row]].edges.right.type
                == "User Q"
            ):
                type_dialog.rb_user.setChecked(True)
                type_dialog.ed_q_user.setText(
                    "{:6.2f}".format(
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.right.user_discharge_cms
                        * self.units["Q"]
                    )
                )
            rsp = type_dialog.exec_()

            # Data entered.
            with self.wait_cursor():
                if rsp == QtWidgets.QDialog.Accepted:
                    if type_dialog.rb_triangular.isChecked():
                        edge_type = "Triangular"
                        cust_coef = None
                        user_discharge_cms = None
                    elif type_dialog.rb_rectangular.isChecked():
                        edge_type = "Rectangular"
                        cust_coef = None
                        user_discharge_cms = None
                    elif type_dialog.rb_custom.isChecked():
                        edge_type = "Custom"
                        cust_coef = self.check_numeric_input(type_dialog.ed_custom)
                        if cust_coef is None:
                            cust_coef = 0
                        user_discharge_cms = None
                    elif type_dialog.rb_user.isChecked():
                        edge_type = "User Q"
                        cust_coef = None
                        user_discharge_cms = self.check_numeric_input(
                            type_dialog.ed_q_user
                        )
                        if user_discharge_cms is not None:
                            user_discharge_cms = user_discharge_cms / self.units["Q"]
                        else:
                            user_discharge_cms = 0
                    # Determine where to apply change and apply
                    if type_dialog.rb_all.isChecked():
                        for idx in self.checked_transects_idx:
                            transect = self.meas.transects[idx]
                            transect.edges.right.type = edge_type
                            transect.edges.right.cust_coef = cust_coef
                            transect.edges.right.user_discharge_cms = user_discharge_cms
                    else:
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.right.type = edge_type
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.right.cust_coef = cust_coef
                        self.meas.transects[
                            self.checked_transects_idx[row]
                        ].edges.right.user_discharge_cms = user_discharge_cms

                    # Reprocess measurement
                    s = self.meas.current_settings()
                    self.meas.apply_settings(s)
                    self.update_edges_table()
                    self.edges_graphics()

        # Right edge distance
        elif col == 11:
            # Initialize dialog
            dist_dialog = EdgeDist()
            dist_dialog.rb_transect.setChecked(True)
            dist_dialog.ed_edge_dist.setText(
                "{:5.2f}".format(
                    self.meas.transects[
                        self.checked_transects_idx[row]
                    ].edges.right.distance_m
                    * self.units["L"]
                )
            )
            rsp = dist_dialog.exec_()
            # Data entered.
            with self.wait_cursor():
                if rsp == QtWidgets.QDialog.Accepted:
                    dist = self.check_numeric_input(dist_dialog.ed_edge_dist)
                    if dist is not None:
                        dist = dist / self.units["L"]
                        # Determine where to apply change and apply change
                        if dist_dialog.rb_all.isChecked():
                            for idx in self.checked_transects_idx:
                                self.meas.transects[idx].edges.right.distance_m = dist
                        else:
                            self.meas.transects[
                                self.checked_transects_idx[row]
                            ].edges.right.distance_m = dist

                        # Reprocess measurement
                        s = self.meas.current_settings()
                        self.meas.apply_settings(s)
                        self.update_edges_table()
                        self.edges_graphics()

        # Right number of ensembles
        elif col == 13:
            # Initialize dialog
            ens_dialog = EdgeEns()
            ens_dialog.rb_transect.setChecked(True)
            ens_dialog.ed_edge_ens.setText(
                "{:4.0f}".format(
                    self.meas.transects[
                        self.checked_transects_idx[row]
                    ].edges.right.number_ensembles
                )
            )
            rsp = ens_dialog.exec_()

            # Data entered.
            with self.wait_cursor():
                if rsp == QtWidgets.QDialog.Accepted:
                    num_ens = self.check_numeric_input(ens_dialog.ed_edge_ens)
                    if num_ens is not None:
                        # Determine where to apply change and apply change
                        if ens_dialog.rb_all.isChecked():
                            for idx in self.checked_transects_idx:
                                self.meas.transects[
                                    idx
                                ].edges.right.number_ensembles = num_ens
                        else:
                            self.meas.transects[
                                self.checked_transects_idx[row]
                            ].edges.right.number_ensembles = num_ens

                        # Reprocess measurement
                        s = self.meas.current_settings()
                        self.meas.apply_settings(s)
                        self.update_edges_table()
                        self.edges_graphics()

        self.tab_edges_2_data.setFocus()
        tbl.blockSignals(False)

    def edges_graphics(self):
        """Generate graphs for edges tab."""

        self.edges_shiptrack_plots()
        self.edges_contour_plots()

        self.figs = [
            self.left_edge_contour_fig,
            self.right_edge_contour_fig,
            self.left_edge_st_fig,
            self.right_edge_st_fig,
        ]
        self.fig_calls = [
            self.edges_contour_plots,
            self.edges_contour_plots,
            self.edges_shiptrack_plots,
            self.edges_shiptrack_plots,
        ]

    def edges_contour_plots(self):
        """Create or update color contour plot for edges."""

        transect = self.meas.transects[self.checked_transects_idx[self.transect_row]]
        tbl = self.table_edges
        # Left edge
        n_ensembles = int(tbl.item(self.transect_row, 5).text())

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.left_edge_contour_canvas is None:
            # Create the canvas
            self.left_edge_contour_canvas = MplCanvas(
                parent=self.graph_left_contour, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_left_contour)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.left_edge_contour_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.left_edge_contour_toolbar = NavigationToolbar(
                self.left_edge_contour_canvas, self
            )
            self.left_edge_contour_toolbar.hide()

        # Initialize the contour figure and assign to the canvas
        self.left_edge_contour_fig = AdvGraphs(canvas=self.left_edge_contour_canvas)
        # Create the figure with the specified data
        self.left_edge_contour_fig.create_edge_contour(
            transect=transect,
            units=self.units,
            x_axis_type=self.edges_axis_type,
            color_map=self.color_map,
            n_ensembles=n_ensembles,
            edge="Left",
        )

        # Set margins and padding for figure
        self.left_edge_contour_canvas.fig.subplots_adjust(
            left=0.15, bottom=0.1, right=0.90, top=0.98, wspace=0.1, hspace=0
        )

        # Draw canvas
        self.left_edge_contour_canvas.draw()

        # Right edge
        n_ensembles = int(tbl.item(self.transect_row, 12).text())

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.right_edge_contour_canvas is None:
            # Create the canvas
            self.right_edge_contour_canvas = MplCanvas(
                parent=self.graph_right_contour, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_right_contour)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.right_edge_contour_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.right_edge_contour_toolbar = NavigationToolbar(
                self.right_edge_contour_canvas, self
            )
            self.right_edge_contour_toolbar.hide()

        # Initialize the contour figure and assign to the canvas
        self.right_edge_contour_fig = AdvGraphs(canvas=self.right_edge_contour_canvas)
        # Create the figure with the specified data
        self.right_edge_contour_fig.create_edge_contour(
            transect=transect,
            units=self.units,
            x_axis_type=self.edges_axis_type,
            color_map=self.color_map,
            n_ensembles=n_ensembles,
            edge="Right",
        )

        # Set margins and padding for figure
        self.right_edge_contour_canvas.fig.subplots_adjust(
            left=0.15, bottom=0.1, right=0.90, top=0.98, wspace=0.1, hspace=0
        )

        # Draw canvas
        self.right_edge_contour_canvas.draw()

    def edges_shiptrack_plots(self):
        """Create or update the shiptrack graphs for the edges tab."""

        transect = self.meas.transects[self.checked_transects_idx[self.transect_row]]

        # Left edge
        tbl = self.table_edges
        n_ensembles = int(tbl.item(self.transect_row, 5).text())
        if transect.start_edge == "Left":
            edge_start = True
        else:
            edge_start = False

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.left_edge_st_canvas is None:
            # Create the canvas
            self.left_edge_st_canvas = MplCanvas(
                parent=self.graph_left_st, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_left_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.left_edge_st_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.left_edge_st_toolbar = NavigationToolbar(
                self.left_edge_st_canvas, self
            )
            self.left_edge_st_toolbar.hide()

        # Initialize the shiptrack figure and assign to the canvas
        self.left_edge_st_fig = Shiptrack(canvas=self.left_edge_st_canvas)
        # Create the figure with the specified data
        self.left_edge_st_fig.create(
            transect=transect,
            units=self.units,
            cb=False,
            cb_bt=self.cb_wt_bt,
            cb_gga=self.cb_wt_gga,
            cb_vtg=self.cb_wt_vtg,
            cb_vectors=self.cb_wt_vectors,
            n_ensembles=n_ensembles,
            edge_start=edge_start,
        )

        if transect.w_vel.nav_ref == "BT":
            for item in self.left_edge_st_fig.bt:
                item.set_visible(True)
        else:
            for item in self.left_edge_st_fig.bt:
                item.set_visible(False)
        # GGA
        if transect.w_vel.nav_ref == "GGA":
            if self.left_edge_st_fig.gga is not None:
                for item in self.left_edge_st_fig.gga:
                    item.set_visible(True)
        elif transect.boat_vel.gga_vel is not None:
            if self.left_edge_st_fig.gga is not None:
                for item in self.left_edge_st_fig.gga:
                    item.set_visible(False)
        # VTG
        if transect.w_vel.nav_ref == "VTG":
            if self.left_edge_st_fig.vtg is not None:
                for item in self.left_edge_st_fig.vtg:
                    item.set_visible(True)
        elif transect.boat_vel.vtg_vel is not None:
            if self.left_edge_st_fig.vtg is not None:
                for item in self.left_edge_st_fig.vtg:
                    item.set_visible(False)

        self.left_edge_st_canvas.draw()

        # Right edge
        n_ensembles = int(tbl.item(self.transect_row, 12).text())
        if transect.start_edge == "Left":
            edge_start = False
        else:
            edge_start = True

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.right_edge_st_canvas is None:
            # Create the canvas
            self.right_edge_st_canvas = MplCanvas(
                parent=self.graph_right_st, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_right_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.right_edge_st_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.right_edge_st_toolbar = NavigationToolbar(
                self.right_edge_st_canvas, self
            )
            self.right_edge_st_toolbar.hide()

        # Initialize the shiptrack figure and assign to the canvas
        self.right_edge_st_fig = Shiptrack(canvas=self.right_edge_st_canvas)
        # Create the figure with the specified data
        self.right_edge_st_fig.create(
            transect=transect,
            units=self.units,
            cb=False,
            cb_bt=self.cb_wt_bt,
            cb_gga=self.cb_wt_gga,
            cb_vtg=self.cb_wt_vtg,
            cb_vectors=self.cb_wt_vectors,
            n_ensembles=n_ensembles,
            edge_start=edge_start,
        )

        if transect.w_vel.nav_ref == "BT":
            for item in self.right_edge_st_fig.bt:
                item.set_visible(True)
        else:
            for item in self.right_edge_st_fig.bt:
                item.set_visible(False)
        # GGA
        if transect.w_vel.nav_ref == "GGA":
            if self.right_edge_st_fig.gga is not None:
                for item in self.right_edge_st_fig.gga:
                    item.set_visible(True)
        elif transect.boat_vel.gga_vel is not None:
            if self.right_edge_st_fig.gga is not None:
                for item in self.right_edge_st_fig.gga:
                    item.set_visible(False)
        # VTG
        if transect.w_vel.nav_ref == "VTG":
            if self.right_edge_st_fig.vtg is not None:
                for item in self.right_edge_st_fig.vtg:
                    item.set_visible(True)
        elif transect.boat_vel.vtg_vel is not None:
            if self.right_edge_st_fig.vtg is not None:
                for item in self.right_edge_st_fig.vtg:
                    item.set_visible(False)

        self.right_edge_st_canvas.draw()

    def edges_comments_messages(self):
        """Displays comments and messages associated with edge filters in
        Messages tab.
        """

        # Clear comments and messages
        self.display_edges_comments.clear()
        self.display_edges_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_edges_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_edges_comments.textCursor().insertText(comment)
                self.display_edges_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_edges_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_edges_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.edges["messages"]:
                if type(message) is str:
                    self.display_edges_messages.textCursor().insertText(message)
                else:
                    self.display_edges_messages.textCursor().insertText(message[0])
                self.display_edges_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_edges_messages.textCursor().insertBlock()

            self.update_tab_icons()

    # Uncertainty tab
    # ===============
    def uncertainty_tab(self):
        """Initializes and configures Oursin uncertainty tab."""

        self.uncertainty_results_table()
        self.advanced_settings_table()
        self.uncertainty_meas_q_plot()
        self.uncertainty_measurement_plot()
        self.uncertainty_comments_messages()

        # Setup list for use by graphics controls
        self.canvases = [
            self.uncertainty_meas_q_canvas,
            self.uncertainty_measurement_canvas,
        ]
        self.figs = [self.uncertainty_meas_q_fig, self.uncertainty_measurement_fig]
        self.fig_calls = [
            self.uncertainty_meas_q_plot,
            self.uncertainty_measurement_plot,
        ]
        self.toolbars = [
            self.uncertainty_meas_q_toolbar,
            self.uncertainty_measurement_toolbar,
        ]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def uncertainty_results_table(self):
        """Create and populate uncertainty results table."""

        # Setup table
        tbl = self.table_uncertainty_results
        tbl.setRowCount(0)
        n_transects = len(self.checked_transects_idx)

        tbl.setRowCount(n_transects + 5)
        tbl.setColumnCount(16)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.itemChanged.connect(self.user_uncertainty_change)
        tbl.itemChanged.disconnect()

        if len(self.checked_transects_idx) > 0:
            # Build column labels using custom_header to create appropriate
            # spans
            self.custom_header(tbl, 0, 0, 3, 1, self.tr("Transect"))
            self.custom_header(
                tbl, 0, 1, 1, 12, self.tr("Uncertainty (Standard Deviation in Percent)")
            )
            tbl.item(0, 1).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 1, 1, 2, 1, self.tr("System"))
            self.custom_header(tbl, 1, 2, 2, 1, self.tr("Compass"))
            self.custom_header(tbl, 1, 3, 2, 1, self.tr("Moving-bed"))
            self.custom_header(tbl, 1, 4, 2, 1, self.tr("# Ensembles"))
            self.custom_header(tbl, 1, 5, 2, 1, self.tr("Meas. Q"))
            self.custom_header(tbl, 1, 6, 2, 1, self.tr("Top Q"))
            self.custom_header(tbl, 1, 7, 2, 1, self.tr("Bottom Q"))
            self.custom_header(tbl, 1, 8, 2, 1, self.tr("Left Q"))
            self.custom_header(tbl, 1, 9, 2, 1, self.tr("Right Q"))
            self.custom_header(tbl, 1, 10, 1, 3, self.tr("Invalid Data"))
            tbl.item(1, 10).setTextAlignment(QtCore.Qt.AlignCenter)
            self.custom_header(tbl, 2, 10, 1, 1, self.tr("Boat"))
            self.custom_header(tbl, 2, 11, 1, 1, self.tr("Depth"))
            self.custom_header(tbl, 2, 12, 1, 1, self.tr("Water"))
            self.custom_header(
                tbl,
                0,
                13,
                3,
                1,
                self.tr(" Bayesian \n Coefficient \n of Variation \n (percent)"),
            )
            self.custom_header(
                tbl, 0, 14, 3, 1, self.tr(" Automatic \n Total 95% \n Uncertainty")
            )
            self.custom_header(
                tbl, 0, 15, 3, 1, self.tr(" User \n Total 95% \n Uncertainty")
            )

            # Add data
            for trans_row in range(n_transects):
                row = trans_row + 5
                col = 0
                transect_id = self.checked_transects_idx[trans_row]

                # File/transect name
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        self.meas.transects[transect_id].file_name[:-4]
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # System
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_syst"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Compass
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.u.iloc[trans_row]["u_compass"]
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving-bed
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_movbed"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Ensembles
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_ens"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Measured Q
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_meas"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Left Q
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_top"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Right Q
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_bot"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Top Q
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_left"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Bottom Q
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_right"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Boat
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_boat"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Depth
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_depth"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Water
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_water"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # COV
                col += 1
                # tbl.setItem(row, col, QtWidgets.QTableWidgetItem(''))
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["u_cov"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Auto 95
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(self.meas.oursin.u.iloc[trans_row]["total_95"])
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # User 95
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.u_user.iloc[trans_row]["total_95"]
                        )
                    ),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            row = 4
            row_user = 3
            col = 0

            # File/transect name
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem("Measurement"))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # System
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_syst"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_syst_mean_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_syst_mean_user"]
                        )
                    ),
                )

            # Compass
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.u_measurement.iloc[0]["u_compass"]
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_compass_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_compass_user"]
                        )
                    ),
                )

            # Moving-bed
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_movbed"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_movbed_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_movbed_user"]
                        )
                    ),
                )

            # Ensembles
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_ens"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_ens_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_ens_user"]
                        )
                    ),
                )

            # Measured Q
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_meas"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_meas_mean_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_meas_mean_user"]
                        )
                    ),
                )

            # Left Q
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_top"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_top_mean_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_top_mean_user"]
                        )
                    ),
                )

            # Right Q
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_bot"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_bot_mean_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_bot_mean_user"]
                        )
                    ),
                )

            # Top Q
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_left"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_left_mean_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_left_mean_user"]
                        )
                    ),
                )

            # Bottom Q
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_right"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_right_mean_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_right_mean_user"]
                        )
                    ),
                )

            # Boat
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_boat"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_invalid_boat_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_invalid_boat_user"]
                        )
                    ),
                )

            # Depth
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_depth"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_invalid_depth_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_invalid_depth_user"]
                        )
                    ),
                )

            # Water
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_water"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            if not np.isnan(self.meas.oursin.user_specified_u["u_invalid_water_user"]):
                tbl.setItem(
                    row_user,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:5.2f}".format(
                            self.meas.oursin.user_specified_u["u_invalid_water_user"]
                        )
                    ),
                )

            # COV
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["u_cov"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Auto 95
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(self.meas.oursin.u_measurement.iloc[0]["total_95"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # User 95
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.u_measurement_user.iloc[0]["total_95"]
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Bold Measurement row
            for col in range(tbl.columnCount()):
                tbl.item(4, col).setFont(self.font_bold)

            # User specified
            col = 0
            tbl.setItem(3, col, QtWidgets.QTableWidgetItem("User Specified"))
            tbl.item(3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(3, col).setFont(self.font_bold)
            tbl.setItem(3, 13, QtWidgets.QTableWidgetItem(""))
            tbl.item(3, 13).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(3, 14, QtWidgets.QTableWidgetItem(""))
            tbl.item(3, 14).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(3, 15, QtWidgets.QTableWidgetItem(""))
            tbl.item(3, 15).setFlags(QtCore.Qt.ItemIsEnabled)

            tbl.item(3, 13).setBackground(QtGui.QColor(150, 150, 150))
            tbl.item(3, 14).setBackground(QtGui.QColor(150, 150, 150))
            tbl.item(3, 15).setBackground(QtGui.QColor(150, 150, 150))

            tbl.resizeColumnsToContents()

            tbl.setRowHeight(0, 40)
            tbl.setRowHeight(1, 40)
            tbl.setRowHeight(2, 40)

            for col in range(1, 15):
                tbl.setColumnWidth(col, 76)

        tbl.itemChanged.connect(self.user_uncertainty_change)

    def advanced_settings_table(self):
        """Create and populate uncertainty results table."""

        # Setup table
        tbl = self.table_uncertainty_settings
        tbl.setRowCount(13)
        tbl.setColumnCount(2)
        v_header = [
            self.tr("Draft (m)"),
            self.tr("Left edge distance (%)"),
            self.tr("Right edge distance (%)"),
            self.tr("Depth cell size (%)"),
            self.tr("Extrap: power exponent minimum"),
            self.tr("Extrap: power exponent maximum"),
            self.tr("Extrap: no slip exponent minimum"),
            self.tr("Extrap: no slip exponent maximum"),
            self.tr("GGA boat speed (m/s)"),
            self.tr("VTG boat speed (m/s)"),
            self.tr("Compass error (deg)"),
            self.tr("Bayesian COV Prior"),
            self.tr("Bayesian COV Prior Uncertainty"),
        ]
        tbl.setHorizontalHeaderLabels([self.tr("Default"), self.tr("User")])
        tbl.setVerticalHeaderLabels(v_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().setFont(self.font_bold)
        tbl.itemChanged.connect(self.user_advanced_settings_change)
        tbl.itemChanged.disconnect()

        # Draft
        row = 0
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Computed"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["draft_error_m_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["draft_error_m_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # Left edge
        row += 1
        tbl.setItem(
            row,
            0,
            QtWidgets.QTableWidgetItem(
                "{:5.2f}".format(
                    self.meas.oursin.default_advanced_settings["left_edge_dist_prct"]
                )
            ),
        )
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(
            self.meas.oursin.user_advanced_settings["left_edge_dist_prct_user"]
        ):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings[
                            "left_edge_dist_prct_user"
                        ]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # Right edge
        row += 1
        tbl.setItem(
            row,
            0,
            QtWidgets.QTableWidgetItem(
                "{:5.2f}".format(
                    self.meas.oursin.default_advanced_settings["right_edge_dist_prct"]
                )
            ),
        )
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(
            self.meas.oursin.user_advanced_settings["right_edge_dist_prct_user"]
        ):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings[
                            "right_edge_dist_prct_user"
                        ]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # Depth cell size
        row += 1
        tbl.setItem(
            row,
            0,
            QtWidgets.QTableWidgetItem(
                "{:5.2f}".format(self.meas.oursin.default_advanced_settings["dzi_prct"])
            ),
        )
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["dzi_prct_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["dzi_prct_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # Power minimum
        row += 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Computed"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["exp_pp_min_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["exp_pp_min_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # Power maximum
        row += 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Computed"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["exp_pp_max_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["exp_pp_max_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # No slip minimum
        row += 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Computed"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["exp_ns_min_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["exp_ns_min_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # No slip maximum
        row += 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Computed"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["exp_ns_max_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["exp_ns_max_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # GGA
        row += 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem("Computed"))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["gga_boat_mps_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["gga_boat_mps_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # VTG
        row += 1
        tbl.setItem(
            row,
            0,
            QtWidgets.QTableWidgetItem(
                "{:5.2f}".format(
                    self.meas.oursin.default_advanced_settings["vtg_boat_mps"]
                )
            ),
        )
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["vtg_boat_mps_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["vtg_boat_mps_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # Compass
        row += 1
        tbl.setItem(
            row,
            0,
            QtWidgets.QTableWidgetItem(
                "{:5.2f}".format(
                    self.meas.oursin.default_advanced_settings["compass_error_deg"]
                )
            ),
        )
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(
            self.meas.oursin.user_advanced_settings["compass_error_deg_user"]
        ):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings[
                            "compass_error_deg_user"
                        ]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # Bayesian COV Prior
        row += 1
        tbl.setItem(
            row,
            0,
            QtWidgets.QTableWidgetItem(
                "{:5.2f}".format(
                    self.meas.oursin.default_advanced_settings["cov_prior"]
                )
            ),
        )
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["cov_prior_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["cov_prior_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        # Bayesian COV Prior Uncertainty
        row += 1
        tbl.setItem(
            row,
            0,
            QtWidgets.QTableWidgetItem(
                "{:5.2f}".format(
                    self.meas.oursin.default_advanced_settings["cov_prior_u"]
                )
            ),
        )
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        if not np.isnan(self.meas.oursin.user_advanced_settings["cov_prior_u_user"]):
            tbl.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    "{:5.2f}".format(
                        self.meas.oursin.user_advanced_settings["cov_prior_u_user"]
                    )
                ),
            )
        else:
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

        tbl.itemChanged.connect(self.user_advanced_settings_change)

    def user_uncertainty_change(self):
        """Recomputes the uncertainty based on user input."""

        # Get edited value from table
        with self.wait_cursor():
            new_value = self.check_numeric_input(
                obj=self.table_uncertainty_results.selectedItems()[0], block=False
            )
            if new_value is None:
                new_value = np.nan

            # Identify uncertainty variable that was edited.
            col_index = self.table_uncertainty_results.selectedItems()[0].column()
            if col_index == 1:
                self.meas.oursin.user_specified_u["u_syst_mean_user"] = new_value
            elif col_index == 2:
                self.meas.oursin.user_specified_u["u_compass_user"] = new_value
            elif col_index == 3:
                self.meas.oursin.user_specified_u["u_movbed_user"] = new_value
            elif col_index == 4:
                self.meas.oursin.user_specified_u["u_ens_user"] = new_value
            elif col_index == 5:
                self.meas.oursin.user_specified_u["u_meas_mean_user"] = new_value
            elif col_index == 6:
                self.meas.oursin.user_specified_u["u_top_mean_user"] = new_value
            elif col_index == 7:
                self.meas.oursin.user_specified_u["u_bot_mean_user"] = new_value
            elif col_index == 8:
                self.meas.oursin.user_specified_u["u_left_mean_user"] = new_value
            elif col_index == 9:
                self.meas.oursin.user_specified_u["u_right_mean_user"] = new_value
            elif col_index == 10:
                self.meas.oursin.user_specified_u["u_invalid_boat_user"] = new_value
            elif col_index == 11:
                self.meas.oursin.user_specified_u["u_invalid_depth_user"] = new_value
            elif col_index == 12:
                self.meas.oursin.user_specified_u["u_invalid_water_user"] = new_value

            # Compute new uncertainty values
            self.meas.oursin.compute_oursin(meas=self.meas)

            # Update
            self.uncertainty_results_table()
            self.uncertainty_meas_q_plot()
            self.uncertainty_measurement_plot()
            self.uncertainty_comments_messages()
            self.change = True
            self.map_change = True

    def user_advanced_settings_change(self):
        """User advanced settings have changed, update settings and
        recompute uncertainty.
        """

        # Get edited value from table
        with self.wait_cursor():
            new_value = self.check_numeric_input(
                obj=self.table_uncertainty_settings.selectedItems()[0], block=False
            )
            if new_value is None:
                new_value = np.nan

            # Identify uncertainty variable that was edited.
            row_index = self.table_uncertainty_settings.selectedItems()[0].row()
            if row_index == 0:
                self.meas.oursin.user_advanced_settings[
                    "draft_error_m_user"
                ] = new_value
            elif row_index == 1:
                self.meas.oursin.user_advanced_settings[
                    "left_edge_dist_prct_user"
                ] = new_value
            elif row_index == 2:
                self.meas.oursin.user_advanced_settings[
                    "right_edge_dist_prct_user"
                ] = new_value
            elif row_index == 3:
                self.meas.oursin.user_advanced_settings["dzi_prct_user"] = new_value
            elif row_index == 4:
                self.meas.oursin.user_advanced_settings["exp_pp_min_user"] = new_value
            elif row_index == 5:
                self.meas.oursin.user_advanced_settings["exp_pp_max_user"] = new_value
            elif row_index == 6:
                self.meas.oursin.user_advanced_settings["exp_ns_min_user"] = new_value
            elif row_index == 7:
                self.meas.oursin.user_advanced_settings["exp_ns_max_user"] = new_value
            elif row_index == 8:
                self.meas.oursin.user_advanced_settings["gga_boat_mps_user"] = new_value
            elif row_index == 9:
                self.meas.oursin.user_advanced_settings["vtg_boat_mps_user"] = new_value
            elif row_index == 10:
                self.meas.oursin.user_advanced_settings[
                    "compass_error_deg_user"
                ] = new_value
            elif row_index == 11:
                self.meas.oursin.user_advanced_settings["cov_prior_user"] = new_value
            elif row_index == 12:
                self.meas.oursin.user_advanced_settings["cov_prior_u_user"] = new_value

            # Compute new uncertainty values
            self.meas.oursin.compute_oursin(meas=self.meas)

            # Update
            self.uncertainty_results_table()
            self.advanced_settings_table()
            self.uncertainty_meas_q_plot()
            self.uncertainty_measurement_plot()
            self.uncertainty_comments_messages()

    def uncertainty_measurement_plot(self):
        """Create or update measurement uncertainty plot."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.uncertainty_measurement_canvas is None:
            # Create the canvas
            self.uncertainty_measurement_canvas = MplCanvas(
                parent=self.graph_u_measurement, width=20, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_u_measurement)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.uncertainty_measurement_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.uncertainty_measurement_toolbar = NavigationToolbar(
                self.uncertainty_measurement_canvas, self
            )
            self.uncertainty_measurement_toolbar.hide()

        # Initialize the contour figure and assign to the canvas
        self.uncertainty_measurement_fig = UMeasurement(
            canvas=self.uncertainty_measurement_canvas
        )
        # Create the figure with the specified data
        self.uncertainty_measurement_fig.create(self.meas.oursin)

        # Set margins and padding for figure
        self.uncertainty_measurement_canvas.fig.subplots_adjust(
            left=0.05, bottom=0.1, right=0.88, top=0.98, wspace=0, hspace=0
        )
        # Draw canvas
        self.uncertainty_measurement_canvas.draw()

    def uncertainty_meas_q_plot(self):
        """Create or update measured discharge uncertainty plot."""

        # If the canvas has not been previously created, create the canvas
        # and add the widget.
        if self.uncertainty_meas_q_canvas is None:
            # Create the canvas
            self.uncertainty_meas_q_canvas = MplCanvas(
                parent=self.graph_u_meas, width=4, height=4, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_u_meas)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.uncertainty_meas_q_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.uncertainty_meas_q_toolbar = NavigationToolbar(
                self.uncertainty_meas_q_canvas, self
            )
            self.uncertainty_meas_q_toolbar.hide()

        # Initialize the contour figure and assign to the canvas
        self.uncertainty_meas_q_fig = UMeasQ(canvas=self.uncertainty_meas_q_canvas)
        # Create the figure with the specified data
        self.uncertainty_meas_q_fig.create(self.meas.oursin)

        # Set margins and padding for figure
        self.uncertainty_meas_q_canvas.fig.subplots_adjust(
            left=0.12, bottom=0.1, right=0.77, top=0.98, wspace=0.1, hspace=0
        )
        # Draw canvas
        self.uncertainty_meas_q_canvas.draw()

    def uncertainty_comments_messages(self):
        """Displays comments and messages associated with uncertainty in
        Messages tab.
        """

        # Clear comments and messages
        self.display_uncertainty_comments.clear()
        self.display_uncertainty_messages.clear()

        if self.meas is not None:
            # Display each comment on a new line
            self.display_uncertainty_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_uncertainty_comments.textCursor().insertText(comment)
                self.display_uncertainty_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_uncertainty_comments.textCursor().insertBlock()

            self.meas.qa.check_oursin(self.meas)
            self.update_tab_icons()

    # EDI tab
    # =======
    def edi_tab(self):
        """Initializes the EDI tab."""

        # Setup transect selection table
        tbl = self.tbl_edi_transect
        units = self.units
        summary_header = [
            self.tr("Select Transect"),
            self.tr("Start"),
            self.tr("Bank"),
            self.tr("End"),
            self.tr("Duration (sec)"),
            self.tr("Total Q" + self.units["label_Q"]),
            self.tr("Top Q" + self.units["label_Q"]),
            self.tr("Meas Q" + self.units["label_Q"]),
            self.tr("Bottom Q" + self.units["label_Q"]),
            self.tr("Left Q" + self.units["label_Q"]),
            self.tr("Right Q" + self.units["label_Q"]),
        ]
        ncols = len(summary_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(summary_header)
        header_font = QtGui.QFont()
        header_font.setBold(True)
        header_font.setPointSize(14)
        tbl.horizontalHeader().setFont(header_font)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Add transect data
        for row in range(nrows):
            col = 0
            transect_id = self.checked_transects_idx[row]

            checked = QtWidgets.QTableWidgetItem(
                self.meas.transects[transect_id].file_name[:-4]
            )
            checked.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            checked.setCheckState(QtCore.Qt.Unchecked)
            tbl.setItem(row, col, checked)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    datetime.strftime(
                        datetime.utcfromtimestamp(
                            self.meas.transects[transect_id].date_time.start_serial_time
                        ),
                        "%H:%M:%S",
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    self.meas.transects[transect_id].start_edge[0]
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    datetime.strftime(
                        datetime.utcfromtimestamp(
                            self.meas.transects[transect_id].date_time.end_serial_time
                        ),
                        "%H:%M:%S",
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.1f}".format(
                        self.meas.transects[transect_id].date_time.transect_duration_sec
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:8}".format(
                        self.q_digits(
                            self.meas.discharge[transect_id].total * units["Q"]
                        )
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(self.meas.discharge[transect_id].top * units["Q"])
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(
                            self.meas.discharge[transect_id].middle * units["Q"]
                        )
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(
                            self.meas.discharge[transect_id].bottom * units["Q"]
                        )
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(
                            self.meas.discharge[transect_id].left * units["Q"]
                        )
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:7}".format(
                        self.q_digits(
                            self.meas.discharge[transect_id].right * units["Q"]
                        )
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Setup EDI table
        tbl_edi = self.tbl_edi_results
        self.txt_edi_offset.setText(
            self.tr("Zero Distance Offset" + self.units["label_L"])
        )
        edi_header = [
            self.tr("Percent Q"),
            self.tr("Target Q " + self.units["label_Q"]),
            self.tr("Actual Q " + self.units["label_Q"]),
            self.tr("Distance " + self.units["label_L"]),
            self.tr("Depth " + self.units["label_L"]),
            self.tr("Velocity " + self.units["label_V"]),
            self.tr("Latitude (D M.M)"),
            self.tr("Longitude (D M.M)"),
        ]
        ncols = len(edi_header)
        nrows = 5
        tbl_edi.setRowCount(nrows)
        tbl_edi.setColumnCount(ncols)
        tbl_edi.setHorizontalHeaderLabels(edi_header)
        header_font = QtGui.QFont()
        header_font.setBold(True)
        header_font.setPointSize(14)
        tbl_edi.horizontalHeader().setFont(header_font)
        tbl_edi.verticalHeader().hide()

        # Initialize values in results table
        tbl_edi.setItem(0, 0, QtWidgets.QTableWidgetItem("10"))
        tbl_edi.setItem(1, 0, QtWidgets.QTableWidgetItem("30"))
        tbl_edi.setItem(2, 0, QtWidgets.QTableWidgetItem("50"))
        tbl_edi.setItem(3, 0, QtWidgets.QTableWidgetItem("70"))
        tbl_edi.setItem(4, 0, QtWidgets.QTableWidgetItem("90"))

        # Configure table so first column is the only editable column
        for row in range(tbl_edi.rowCount()):
            for col in range(1, 8):
                tbl_edi.setItem(row, col, QtWidgets.QTableWidgetItem(" "))
                tbl_edi.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl_edi.resizeColumnsToContents()
        tbl_edi.resizeRowsToContents()

        self.pb_edi_compute.setEnabled(False)

        # Setup connections to other methods
        if not self.edi_initialized:
            tbl.cellClicked.connect(self.edi_select_transect)
            self.pb_edi_add_row.clicked.connect(self.edi_add_row)
            self.pb_edi_compute.clicked.connect(self.edi_compute)
            self.edi_initialized = True

    def edi_select_transect(self, row, col):
        """Handles checkbox so only one box can be checked.
        Updates the GUI to reflect the start bank of the transect selected

        Parameters
        ----------
        row: int
            Row clicked by user
        col: int
            Column clicked by user
        """

        # Checkbox control
        if col == 0:
            # Ensures only one box can be checked
            for r in range(self.tbl_edi_transect.rowCount()):
                if r == row:
                    self.tbl_edi_transect.item(r, col).setCheckState(QtCore.Qt.Checked)
                else:
                    self.tbl_edi_transect.item(r, col).setCheckState(
                        QtCore.Qt.Unchecked
                    )

            # Update the GUI to reflect the start bank of the selected transect
            if (
                self.meas.transects[self.checked_transects_idx[row]].start_edge[0]
                == "R"
            ):
                self.txt_edi_bank.setText(self.tr("From Right Bank"))
            else:
                self.txt_edi_bank.setText(self.tr("From Left Bank"))

            # After a transect is selected enable the compute button in the GUI
            self.pb_edi_compute.setEnabled(True)

    def edi_add_row(self):
        """Allows the user to add a row to the results table so that more
        than 5 verticals can be defined."""

        # Insert row at bottom
        row_position = self.tbl_edi_results.rowCount()
        self.tbl_edi_results.insertRow(row_position)

        # Allow editing of first column only
        for col in range(1, 7):
            self.tbl_edi_results.setItem(
                row_position, col, QtWidgets.QTableWidgetItem(" ")
            )
            self.tbl_edi_results.item(row_position, col).setFlags(
                QtCore.Qt.ItemIsEnabled
            )

    def edi_update_table(self):
        """Updates the results table with the computed data."""

        tbl = self.tbl_edi_results

        # Add data to table
        for row in range(len(self.edi_results["percent"])):
            col = 0
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:2.0f}".format(self.edi_results["percent"][row])
                ),
            )

            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:6.2f}".format(
                        self.edi_results["target_q"][row] * self.units["Q"]
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:6.2f}".format(
                        self.edi_results["actual_q"][row] * self.units["Q"]
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            # Code to handle either blank or user supplied data
            try:
                offset = float(self.edi_offset.text())
            except ValueError:
                offset = 0
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:6.1f}".format(
                        (self.edi_results["distance"][row] * self.units["L"]) + offset
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:5.1f}".format(self.edi_results["depth"][row] * self.units["L"])
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:4.1f}".format(
                        self.edi_results["velocity"][row] * self.units["L"]
                    )
                ),
            )
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Convert lat and lon for decimal degrees to degrees and decimal
            # minutes
            try:
                latd = int(self.edi_results["lat"][row])
                latm = np.abs((self.edi_results["lat"][row] - latd) * 60)
                lond = int(self.edi_results["lon"][row])
                lonm = np.abs((self.edi_results["lon"][row] - lond) * 60)
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem("{:3.0f} {:3.7f}".format(latd, latm)),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                col += 1
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem("{:3.0f} {:3.7f}".format(lond, lonm)),
                )
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            except ValueError:
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(""))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(""))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # If nothing in Percent Q column, clear the rest of the row
        for row in range(tbl.rowCount()):
            try:
                if tbl.item(row, 0).text() == "":
                    for col in range(1, 8):
                        tbl.setItem(row, col, QtWidgets.QTableWidgetItem(""))
                        tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                        col += 1
            except AttributeError:
                pass

        # Clear rows that should be blank
        # If Percent Q has been deleted from the middle of the table, the
        # final row(s) can be duplicated
        if tbl.rowCount() > len(self.edi_results["percent"]):
            for row in range(len(self.edi_results["percent"]), tbl.rowCount()):
                tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
                for col in range(1, 8):
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(""))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                    col += 1

    def edi_compute(self):
        """Coordinates the computation of the EDI results."""

        selected_idx = 0

        # Find selected transect index
        for row in range(self.tbl_edi_transect.rowCount()):
            if self.tbl_edi_transect.item(row, 0).checkState() == QtCore.Qt.Checked:
                selected_idx = self.checked_transects_idx[row]
                break

        # Find specified percentages
        percents = []
        for row in range(self.tbl_edi_results.rowCount()):
            try:
                percent = float(self.tbl_edi_results.item(row, 0).text())
                percents.append(percent)
            except (AttributeError, ValueError):
                pass

        # Warn user if less than 3 verticals are entered
        if len(percents) < 3:
            self.popup_message(
                self.tr("3 verticals are required for EDI calculations.")
            )
        else:
            # If the selected transect has computed discharge compute EDI
            # results
            if np.abs(self.meas.discharge[selected_idx].total) > 0:
                # Check that no Percent Q values are >= 100
                if not any(percent >= 100.0 for percent in percents):
                    # Compute EDI results
                    self.edi_results = Measurement.compute_edi(
                        self.meas, selected_idx, percents
                    )
                else:
                    # Warn user if vertical >= 100 is entered
                    self.popup_message(self.tr("Percent Q must be less than 100."))

                # Update EDI results table
                self.edi_update_table()
                # Create topoquad file is requested
                if self.cb_edi_topoquad.checkState() == QtCore.Qt.Checked:
                    self.create_topoquad_file()
            else:
                # Display message to user
                self.popup_message(self.tr("The selected transect has no discharge"))

    def create_topoquad_file(self):
        """Create an ASCII file that can be loaded into TopoQuads to mark
        the EDI locations with a yellow dot.
        """

        # Get user defined filename
        text, ok_pressed = QtWidgets.QInputDialog.getText(
            self,
            self.tr("TopoQuad File"),
            self.tr("Enter " "filename (no " "suffix)for " "TopoQuad " "file:"),
            QtWidgets.QLineEdit.Normal,
            "edi_topoquad",
        )
        # Create and save file to folder containing measurement data
        if ok_pressed and text != "":
            filename = text + ".txt"
            fullname = os.path.join(self.sticky_settings.get("Folder"), filename)
            with open(fullname, "w") as outfile:
                outfile.write("BEGIN SYMBOL \n")
                for n in range(len(self.edi_results["lat"])):
                    outfile.write(
                        "{:15.10f}, {:15.10f}, Yellow Dot\n".format(
                            self.edi_results["lat"][n], self.edi_results["lon"][n]
                        )
                    )
                outfile.write("END")
        else:
            # Report error to user
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage(
                self.tr("Invalid output filename. TopoQuad file not created.")
            )

    # Adv. Graph tab
    # ==============
    def adv_graph_tab(self):
        """Initializes all of the features of the advanced graphics tab."""

        if not self.adv_graph_initialized:
            # Advanced tab setup
            self.pb_adv_graph_create_plots.clicked.connect(self.adv_graph_plots)
            self.pb_adv_graph_controls.clicked.connect(self.adv_graph_show_hide)
            self.combo_adv_graph_transect.currentIndexChanged.connect(
                self.adv_graph_transect_select
            )
            self.rb_adv_graph_ensemble.toggled.connect(self.x_axis_ensemble)
            self.rb_adv_graph_length.toggled.connect(self.x_axis_length)
            self.rb_adv_graph_time.toggled.connect(self.x_axis_time)
            self.pb_adv_graph_auto_flow_direction.clicked.connect(
                self.adv_graph_auto_flow_direction
            )

            # Configure dictionary of plot options
            self.adv_graph_types = [
                ("cb_speed_filtered_cc", self.cb_adv_graph_speed_filtered),
                ("cb_speed_final_cc", self.cb_adv_graph_speed_final),
                ("cb_projected_cc", self.cb_adv_graph_projected),
                ("cb_vertical_cc", self.cb_adv_graph_vertical),
                ("cb_error_cc", self.cb_adv_graph_error),
                ("cb_direction_cc", self.cb_adv_graph_direction),
                ("cb_avg_corr_cc", self.cb_adv_graph_avg_corr),
                ("cb_corr_beam_cc", self.cb_adv_graph_corr_beam),
                ("cb_avg_rssi_cc", self.cb_adv_graph_avg_rssi),
                ("cb_rssi_beam_cc", self.cb_adv_graph_rssi_beam),
                ("cb_ping_type_cc", self.cb_adv_graph_ping_type),
                ("cb_discharge_ts", self.cb_adv_graph_discharge),
                ("cb_discharge_percent_ts", self.cb_adv_graph_discharge_percent),
                ("cb_avg_speed_ts", self.cb_adv_graph_avg_speed),
                ("cb_projected_speed_ts", self.cb_adv_graph_projected_speed_ts),
                ("cb_wt_beams_ts", self.cb_adv_graph_wt_beams_ts),
                ("cb_wt_error_ts", self.cb_adv_graph_wt_error_ts),
                ("cb_wt_vert_ts", self.cb_adv_graph_wt_vert_ts),
                ("cb_wt_snr_ts", self.cb_adv_graph_wt_snr_ts),
                ("cb_bt_boat_speed_ts", self.cb_adv_graph_bt_boat_speed),
                ("cb_bt_3beam_ts", self.cb_adv_graph_bt_3beam),
                ("cb_bt_error_ts", self.cb_adv_graph_bt_error),
                ("cb_bt_vertical_ts", self.cb_adv_graph_bt_vertical),
                ("cb_bt_source_ts", self.cb_adv_graph_bt_source),
                ("cb_bt_corr_ts", self.cb_adv_graph_bt_correlation),
                ("cb_bt_rssi_ts", self.cb_adv_graph_bt_rssi),
                ("cb_gga_boat_speed_ts", self.cb_adv_graph_gga_boat_speed),
                ("cb_vtg_boat_speed_ts", self.cb_adv_graph_vtg_boat_speed),
                ("cb_gga_quality_ts", self.cb_adv_graph_gga_quality),
                ("cb_gga_hdop_ts", self.cb_adv_graph_gga_hdop),
                ("cb_gga_altitude_ts", self.cb_adv_graph_gga_altitude),
                ("cb_gga_sats_ts", self.cb_adv_graph_gga_satellites),
                ("cb_gga_source_ts", self.cb_adv_graph_gga_source),
                ("cb_vtg_source_ts", self.cb_adv_graph_vtg_source),
                ("cb_adcp_heading_ts", self.cb_adv_graph_adcp_heading),
                ("cb_ext_heading_ts", self.cb_adv_graph_ext_heading),
                ("cb_mag_error_ts", self.cb_adv_graph_mag_error),
                ("cb_pitch_ts", self.cb_adv_graph_pitch),
                ("cb_roll_ts", self.cb_adv_graph_roll),
                ("cb_beam_depths_ts", self.cb_adv_graph_beam_depths),
                ("cb_final_depths_ts", self.cb_adv_graph_final_depths),
                ("cb_depths_source_ts", self.cb_adv_graph_depth_source),
                ("cb_battery_voltage_ts", self.cb_adv_graph_battery_voltage),
            ]

            trans_prop = Measurement.compute_measurement_properties(self.meas)
            direction = trans_prop["avg_water_dir"][
                self.checked_transects_idx[self.transect_row]
            ]
            self.ed_adv_graph_flow_dir.setText("{:6.2f}".format(direction))

            self.adv_graph_initialized = True

        # Populate combo box
        self.combo_adv_graph_transect.blockSignals(True)
        self.combo_adv_graph_transect.clear()
        for idx in self.checked_transects_idx:
            self.combo_adv_graph_transect.addItem(self.meas.transects[idx].file_name)

        # Set selected
        self.combo_adv_graph_transect.setCurrentIndex(self.transect_row)
        self.combo_adv_graph_transect.blockSignals(False)

        # Set x-axis radio button
        self.rb_adv_graph_ensemble.blockSignals(True)
        self.rb_adv_graph_length.blockSignals(True)
        self.rb_adv_graph_time.blockSignals(True)
        if self.x_axis_type == "E":
            self.rb_adv_graph_ensemble.setChecked(True)
        elif self.x_axis_type == "L":
            self.rb_adv_graph_length.setChecked(True)
        elif self.x_axis_type == "T":
            self.rb_adv_graph_time.setChecked(True)
        self.rb_adv_graph_ensemble.blockSignals(False)
        self.rb_adv_graph_length.blockSignals(False)
        self.rb_adv_graph_time.blockSignals(False)

        self.available_plot_types()

        self.adv_graph_plots()

        # Setup list for use by graphics controls
        self.canvases = [self.adv_graph_canvas]
        self.figs = [self.adv_graph_fig]
        self.fig_calls = [self.adv_graph_plots]
        self.toolbars = [self.adv_graph_toolbar]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def adv_graph_transect_select(self):
        """Updates advanced graphics with newly selected transect."""

        self.transect_row = self.combo_adv_graph_transect.currentIndex()
        self.available_plot_types()
        self.adv_graph_plots()

    def adv_graph_auto_flow_direction(self):
        """Computes the mean flow direction and populates the flow direction
        edit box.
        """

        trans_prop = Measurement.compute_measurement_properties(self.meas)
        direction = trans_prop["avg_water_dir"][
            self.checked_transects_idx[self.transect_row]
        ]
        self.ed_adv_graph_flow_dir.setText("{:6.2f}".format(direction))

    def available_plot_types(self):
        """Enable / disable plot types"""

        # Mag Error
        if self.meas.transects[
            self.checked_transects_idx[self.transect_row]
        ].sensors.heading_deg.internal.mag_error is not None and np.logical_not(
            np.all(
                np.isnan(
                    self.meas.transects[
                        self.checked_transects_idx[self.transect_row]
                    ].sensors.heading_deg.internal.mag_error
                )
            )
        ):
            self.cb_adv_graph_mag_error.setEnabled(True)
        else:
            self.cb_adv_graph_mag_error.setEnabled(False)
            self.cb_adv_graph_mag_error.setChecked(False)

        # External Compass
        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].sensors.heading_deg.external
            is not None
        ):
            self.cb_adv_graph_ext_heading.setEnabled(True)
        else:
            self.cb_adv_graph_ext_heading.setEnabled(False)
            self.cb_adv_graph_ext_heading.setChecked(False)

        # GGA data
        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].boat_vel.gga_vel
            is not None
            and self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].boat_vel.gga_vel.u_mps
            is not None
        ):
            self.cb_adv_graph_gga_boat_speed.setEnabled(True)
            self.cb_adv_graph_gga_quality.setEnabled(True)
            self.cb_adv_graph_gga_hdop.setEnabled(True)
            self.cb_adv_graph_gga_altitude.setEnabled(True)
            self.cb_adv_graph_gga_satellites.setEnabled(True)
            self.cb_adv_graph_gga_source.setEnabled(True)
        else:
            self.cb_adv_graph_gga_boat_speed.setEnabled(False)
            self.cb_adv_graph_gga_quality.setEnabled(False)
            self.cb_adv_graph_gga_hdop.setEnabled(False)
            self.cb_adv_graph_gga_altitude.setEnabled(False)
            self.cb_adv_graph_gga_satellites.setEnabled(False)
            self.cb_adv_graph_gga_source.setEnabled(False)
            self.cb_adv_graph_gga_boat_speed.setChecked(False)
            self.cb_adv_graph_gga_quality.setChecked(False)
            self.cb_adv_graph_gga_hdop.setChecked(False)
            self.cb_adv_graph_gga_altitude.setChecked(False)
            self.cb_adv_graph_gga_satellites.setChecked(False)
            self.cb_adv_graph_gga_source.setChecked(False)

        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].boat_vel.vtg_vel
            is not None
            and self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].boat_vel.vtg_vel.u_mps
            is not None
        ):
            self.cb_adv_graph_vtg_boat_speed.setEnabled(True)
            self.cb_adv_graph_vtg_source.setEnabled(True)
        else:
            self.cb_adv_graph_vtg_boat_speed.setEnabled(False)
            self.cb_adv_graph_vtg_boat_speed.setChecked(False)
            self.cb_adv_graph_vtg_source.setEnabled(False)
            self.cb_adv_graph_vtg_source.setChecked(False)

        # BT data
        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].boat_vel.bt_vel.corr.size
            > 0
        ):
            self.cb_adv_graph_bt_correlation.setEnabled(True)
        else:
            self.cb_adv_graph_bt_correlation.setEnabled(False)
            self.cb_adv_graph_bt_correlation.setChecked(False)

        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].boat_vel.bt_vel.rssi.size
            > 0
        ):
            self.cb_adv_graph_bt_rssi.setEnabled(True)
        else:
            self.cb_adv_graph_bt_rssi.setEnabled(False)
            self.cb_adv_graph_bt_rssi.setChecked(False)

        # WT Data
        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].adcp.manufacturer
            == "SonTek"
        ):
            self.cb_adv_graph_wt_snr_ts.setEnabled(True)
        else:
            self.cb_adv_graph_wt_snr_ts.setEnabled(False)
            self.cb_adv_graph_wt_snr_ts.setChecked(False)

        # Battery voltage
        if (
            self.meas.transects[
                self.checked_transects_idx[self.transect_row]
            ].sensors.battery_voltage.internal
            is None
        ):
            self.cb_adv_graph_battery_voltage.setEnabled(False)
        else:
            self.cb_adv_graph_battery_voltage.setEnabled(True)

    def adv_graph_plots(self):
        """Creates advanced plots for data in transect."""

        # Determine which plot types the user has selected
        selected_types = []
        for item in self.adv_graph_types:
            if item[1].isChecked():
                selected_types.append(item[0])

        # Get flow direction
        flow_direction = float(self.ed_adv_graph_flow_dir.text())

        # Determine transect to plot
        idx = self.checked_transects_idx[self.combo_adv_graph_transect.currentIndex()]

        # If the canvas has not been previously created, create the canvas and
        # add the widget.
        if self.adv_graph_canvas is None:
            # Create the canvas
            self.adv_graph_canvas = MplCanvas(
                parent=self.graph_adv_graph, width=10, height=8, dpi=80
            )
            # Assign layout to widget to allow auto-scaling
            layout = QtWidgets.QVBoxLayout(self.graph_adv_graph)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(0, 0, 0, 0)
            # Add the canvas
            layout.addWidget(self.adv_graph_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.adv_graph_toolbar = NavigationToolbar(self.adv_graph_canvas, self)
            self.adv_graph_toolbar.hide()

        # Initialize the advanced figure and assign to the canvas
        self.adv_graph_fig = AdvGraphs(canvas=self.adv_graph_canvas)
        # Create the figure with the specified data
        self.adv_graph_fig.create(
            transect=self.meas.transects[idx],
            discharge=self.meas.discharge[idx],
            units=self.units,
            selected_types=selected_types,
            color_map=self.color_map,
            x_axis_type=self.x_axis_type,
            flow_direction=flow_direction,
            show_below_sl=self.show_below_sl,
            show_unmeasured=self.plot_extrapolated,
        )

        # Draw canvas
        self.adv_graph_canvas.draw()

        # Update list of figs
        self.figs = [self.adv_graph_fig]
        self.fig_calls = [self.adv_graph_plots]
        self.toolbars = [self.adv_graph_toolbar]

        # Reset data cursor to work with new figure
        if self.actionData_Cursor.isChecked():
            self.data_cursor()
        self.tab_adv_graph.setFocus()

    def adv_graph_show_hide(self):
        """Controls the visibility of the plot controls and expands and
        contracts the layout holding the plots and plot controls.
        """

        # Hide control and expand plots
        if self.gb_adv_graph_controls.isVisible():
            self.gb_adv_graph_controls.hide()
            self.adv_graph_layout.setStretch(0, 10)
            self.adv_graph_layout.setStretch(1, 0)
            self.pb_adv_graph_controls.setText("Show Plot Controls")

        # Show control and reduce plot area
        else:
            self.gb_adv_graph_controls.show()
            self.adv_graph_layout.setStretch(0, 7)
            self.adv_graph_layout.setStretch(1, 3)
            self.pb_adv_graph_controls.setText("Hide Plot Controls")

    # MAP tab (Multi-transects Average Profile)
    # ==============
    def map_tab(self):
        """Initializes and configures MAP tab."""
        if self.meas.map is None:
            self.meas.compute_map()
            self.map_settings = {
                "cb_map_interpolation": True,
                "ed_map_cell_width": self.meas.map.auto_node_horz,
                "ed_map_cell_height": self.meas.map.auto_node_vert,
                "cb_map_top_bottom": True,
                "cb_map_edges": True,
                "ed_map_secondary_velocity": None,
                "cb_map_bed_profiles": True,
                "combo_map_data": "Primary velocity",
                "rb_map_contour": True,
                "rb_map_bathymetry": False,
                "rb_map_temp": False,
                "rb_map_stickship": False,
            }

            # Initialize tab
            if not self.map_initialized:
                self.map_tab_initialize()

            self.rb_map_contour.setChecked(True)
            self.cb_map_cell_size_auto.setChecked(True)
            self.ed_map_cell_width.blockSignals(True)
            self.ed_map_cell_width.setEnabled(False)
            self.ed_map_cell_width.clear()

            self.ed_map_cell_height.blockSignals(True)
            self.ed_map_cell_height.setEnabled(False)
            self.ed_map_cell_height.clear()

            self.cb_map_interpolation.setChecked(True)
            self.cb_map_top_bottom.setChecked(True)
            self.cb_map_edges.setChecked(True)
            self.cb_map_bed_profiles.setChecked(True)
            min_width = self.meas.map.auto_node_horz
            self.ed_map_cell_width.setText(
                "{:3.2f}".format(min_width * self.units["L"])
            )
            min_height = self.meas.map.auto_node_vert
            self.ed_map_cell_height.setText(
                "{:3.2f}".format(min_height * self.units["L"])
            )
            self.ed_map_secondary_velocity.setText("")
            self.ed_map_secondary_velocity.setEnabled(True)

            self.combo_map_data.blockSignals(True)
            self.combo_map_data.setCurrentIndex(0)
            self.combo_map_data.blockSignals(False)

            self.map_change = False

        if self.map_change:
            # Reset settings if change
            self.cb_map_interpolation.setChecked(True)
            self.cb_map_top_bottom.setChecked(True)
            self.cb_map_edges.setChecked(True)
            self.cb_map_bed_profiles.setChecked(True)
            # self.ed_map_cell_width.setText("")
            # self.ed_map_cell_height.setText("")
            self.ed_map_secondary_velocity.setText("")
            self.combo_map_data.setCurrentIndex(0)
            self.map_current_settings = {
                "cb_map_interpolation": self.cb_map_interpolation.isChecked(),
                "ed_map_cell_width": self.check_numeric_input(self.ed_map_cell_width),
                "ed_map_cell_height": self.check_numeric_input(self.ed_map_cell_height),
                "cb_map_top_bottom": self.cb_map_top_bottom.isChecked(),
                "cb_map_edges": self.cb_map_edges.isChecked(),
                "ed_map_secondary_velocity": self.check_numeric_input(
                    self.ed_map_secondary_velocity
                ),
                "cb_map_bed_profiles": self.cb_map_bed_profiles.isChecked(),
                "combo_map_data": self.combo_map_data.currentText(),
                "rb_map_contour": self.rb_map_contour.isChecked(),
                "rb_map_bathymetry": self.rb_map_bathymetry.isChecked(),
                "rb_map_temp": self.rb_map_temp.isChecked(),
                "rb_map_stickship": self.rb_map_stickship.isChecked(),
            }

        # Disable MAP open Earth button if not GGA
        settings = Measurement.current_settings(self.meas)
        if settings["NavRef"] == "gga_vel":
            self.pb_map_open_earth.setEnabled(True)
        else:
            self.pb_map_open_earth.setEnabled(False)

        # Save MAP parameters as dict
        secondary_velocity_scale = self.check_numeric_input(
            self.ed_map_secondary_velocity
        )
        self.map_settings = {
            "cb_map_interpolation": self.cb_map_interpolation.isChecked(),
            "ed_map_cell_width": self.check_numeric_input(self.ed_map_cell_width),
            "ed_map_cell_height": self.check_numeric_input(self.ed_map_cell_height),
            "cb_map_top_bottom": self.cb_map_top_bottom.isChecked(),
            "cb_map_edges": self.cb_map_edges.isChecked(),
            "ed_map_secondary_velocity": secondary_velocity_scale,
            "cb_map_bed_profiles": self.cb_map_bed_profiles.isChecked(),
            "combo_map_data": self.combo_map_data.currentText(),
            "rb_map_contour": self.rb_map_contour.isChecked(),
            "rb_map_bathymetry": self.rb_map_bathymetry.isChecked(),
            "rb_map_temp": self.rb_map_temp.isChecked(),
            "rb_map_stickship": self.rb_map_stickship.isChecked(),
        }

        # MAP table
        self.map_table()

        # MAP figures
        self.update_map_plot()

        self.canvases = [self.map_canvas]
        self.figs = [self.map_fig]
        self.fig_calls = [self.map_wt_contour]
        self.toolbars = [self.map_toolbar]
        self.ui_parents = [i.parent() for i in self.canvases]
        self.figs_menu_connection()

    def map_tab_initialize(self):
        # Todo add signals for any change to the map properties
        # Configure dictionary of plot options
        self.map_current_settings = self.map_settings

        # radio button signals for plot type
        self.rb_map_contour.clicked.connect(self.update_map)
        self.rb_map_bathymetry.clicked.connect(self.update_map)
        self.rb_map_temp.clicked.connect(self.update_map)
        self.rb_map_stickship.clicked.connect(self.update_map)

        # signals for contour options
        self.combo_map_data.currentTextChanged.connect(self.update_map)
        self.ed_map_secondary_velocity.editingFinished.connect(self.update_map)
        self.cb_map_cell_size_auto.clicked.connect(self.map_cell_auto)
        self.ed_map_cell_width.editingFinished.connect(self.update_map)
        self.ed_map_cell_height.editingFinished.connect(self.update_map)
        self.cb_map_top_bottom.clicked.connect(self.update_map)
        self.cb_map_edges.clicked.connect(self.update_map)
        self.cb_map_interpolation.clicked.connect(self.update_map)
        self.cb_map_bed_profiles.clicked.connect(self.update_map)

        self.pb_map_save.clicked.connect(self.map_save_data)
        self.pb_map_open_earth.clicked.connect(self.plot_map_google_earth)

        # Limit edit to two decimals float
        rx = QtCore.QRegExp("^-?\\d*\\.?\\d{0,2}$")
        validator = QtGui.QRegExpValidator(rx, self)
        self.ed_map_cell_width.setValidator(validator)
        self.ed_map_cell_height.setValidator(validator)

        self.map_initialized = True

    def update_map(self):
        """Updates MAP with user's parameters."""

        # Load MAP parameters and check if there is any change
        with self.wait_cursor():
            if self.map_change:
                change_data = True
                change_plot = True
            else:
                change_data = False
                change_plot = False

            if self.combo_map_data.currentIndex() <= 1:
                self.ed_map_secondary_velocity.setEnabled(True)
                if self.combo_map_data.currentIndex() == 0:
                    self.txt_map_v_scale.setText("Secondary Velocity Scale:")
                else:
                    self.txt_map_v_scale.setText("Transverse Velocity Scale:")
            else:
                self.ed_map_secondary_velocity.setEnabled(False)

            cell_width = self.check_numeric_input(self.ed_map_cell_width)
            min_width = self.meas.map.borders_ens[-1] / 1000
            if cell_width is not None:
                cell_width = cell_width * 1 / self.units["L"]

                if cell_width < min_width:
                    cell_width = min_width
                    self.ed_map_cell_width.setText(
                        "{:3.2f}".format(cell_width * self.units["L"])
                    )
            else:
                self.ed_map_cell_width.setText(
                    "{:3.2f}".format(self.meas.map.auto_node_horz * self.units["L"])
                )

            cell_height = self.check_numeric_input(self.ed_map_cell_height)
            min_height = self.meas.map.main_depth_layers[-1] / 100
            if cell_height is not None:
                cell_height = cell_height * 1 / self.units["L"]
                if cell_height < min_height:
                    cell_height = min_height
                    self.ed_map_cell_height.setText(
                        "{:3.2f}".format(min_height * self.units["L"])
                    )
            else:
                self.ed_map_cell_height.setText(
                    "{:3.2f}".format(self.meas.map.auto_node_vert * self.units["L"])
                )

            self.map_settings = {
                "cb_map_interpolation": self.cb_map_interpolation.isChecked(),
                "ed_map_cell_width": cell_width,
                "ed_map_cell_height": cell_height,
                "cb_map_top_bottom": self.cb_map_top_bottom.isChecked(),
                "cb_map_edges": self.cb_map_edges.isChecked(),
                "ed_map_secondary_velocity": self.check_numeric_input(
                    self.ed_map_secondary_velocity
                ),
                "cb_map_bed_profiles": self.cb_map_bed_profiles.isChecked(),
                "combo_map_data": self.combo_map_data.currentText(),
                "rb_map_contour": self.rb_map_contour.isChecked(),
                "rb_map_bathymetry": self.rb_map_bathymetry.isChecked(),
                "rb_map_temp": self.rb_map_temp.isChecked(),
                "rb_map_stickship": self.rb_map_stickship.isChecked(),
            }

            if self.map_change is False:
                for key in self.map_current_settings:
                    if self.map_settings[key] != self.map_current_settings[key]:
                        if key in [
                            "cb_map_interpolation",
                            "ed_map_cell_width",
                            "ed_map_cell_height",
                            "cb_map_top_bottom",
                            "cb_map_edges",
                        ]:
                            change_data = True
                            change_plot = True
                            break
                        else:
                            change_plot = True
                            change_data = False

            if self.map_canvas is None:
                change_plot = True

            # Save current parameters
            self.map_current_settings = self.map_settings

            # Apply changes
            if change_data:
                self.meas.compute_map(
                    node_horizontal_user=self.map_settings["ed_map_cell_width"],
                    node_vertical_user=self.map_settings["ed_map_cell_height"],
                    extrap_option=self.map_settings["cb_map_top_bottom"],
                    edges_option=self.map_settings["cb_map_edges"],
                    interp_option=self.map_settings["cb_map_interpolation"],
                )
                self.map_table(update=True)
            if change_plot:
                self.update_map_plot()

            self.map_change = False

    def map_table(self, update=False):
        """Create and populate MAP results table."""
        # Setup table
        n_transects = len(self.meas.transects)
        tbl = self.table_map_results
        if not update:
            map_header = [self.tr("MAP"), self.tr("Meas."), self.tr("Delta (%)")]
            map_rows = [
                self.tr("Total Q ") + self.tr(self.units["label_Q"]),
                self.tr("Q/A ") + self.tr(self.units["label_V"]),
                self.tr("Mean depth ") + self.tr(self.units["label_L"]),
                self.tr("Width ") + self.tr(self.units["label_L"]),
            ]
            tbl.setRowCount(0)
            ncols = len(map_header)
            nrows = len(map_rows)
            tbl.setRowCount(nrows)
            tbl.setColumnCount(ncols)

            # tbl.horizontalHeader().hide()
            tbl.setHorizontalHeaderLabels(map_header)
            tbl.horizontalHeader().setFont(self.font_bold)
            tbl.setVerticalHeaderLabels(map_rows)
            tbl.verticalHeader().setFont(self.font_bold)

            header = tbl.horizontalHeader()
            col_header = tbl.verticalHeader()
            header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            col_header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        if (
            len(self.checked_transects_idx) > 0
            and self.meas.map.total_discharge is not None
        ):
            trans_prop = Measurement.compute_measurement_properties(self.meas)

            row = 0
            # MAP Q
            col = 0
            map_q = self.meas.map.total_discharge
            if np.isnan(map_q):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(self.q_digits(map_q * self.units["Q"]))
                    ),
                )
            # Meas Q
            col += 1
            discharge = Measurement.mean_discharges(self.meas)
            tbl.setItem(
                row,
                col,
                QtWidgets.QTableWidgetItem(
                    "{:8}".format(
                        self.q_digits(discharge["total_mean"] * self.units["Q"])
                    )
                ),
            )
            # Delta Q
            col += 1
            if discharge["total_mean"] != 0:
                per_diff = (
                    100 * (map_q - discharge["total_mean"]) / discharge["total_mean"]
                )
            else:
                per_diff = np.nan
            if np.isnan(per_diff):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row, col, QtWidgets.QTableWidgetItem("{:7.1f}".format(per_diff))
                )

            row += 1
            # MAP mean v
            col = 0
            map_area = np.nansum(self.meas.map.cells_area)
            map_v = map_q / map_area * self.units["V"]
            if np.isnan(map_v):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem("{:8}".format(self.q_digits(map_v))),
                )
            # Meas. mean v
            col += 1
            meas_v = trans_prop["avg_water_speed"][n_transects] * self.units["V"]
            if np.isnan(meas_v):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem("{:8}".format(self.q_digits(meas_v))),
                )
            # Delta v
            col += 1
            if meas_v != 0:
                per_diff = 100 * (map_v - meas_v) / meas_v
            else:
                per_diff = np.nan
            if np.isnan(per_diff):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row, col, QtWidgets.QTableWidgetItem("{:7.1f}".format(per_diff))
                )

            row += 1
            # MAP mean depth
            col = 0
            map_d = np.nanmean(self.meas.map.depths)
            if np.isnan(map_d):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(self.q_digits(map_d * self.units["L"]))
                    ),
                )
            # Meas. mean depth
            col += 1
            depth_meas = []
            for id_transect in self.checked_transects_idx:
                transect = self.meas.transects[id_transect]
                depth_meas.append(transect.depths.bt_depths.depth_processed_m)
            every_depth = np.array(
                [item for subarray in depth_meas for item in subarray]
            )
            meas_d = np.nanmean(every_depth)
            if np.isnan(meas_d):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(self.q_digits(meas_d * self.units["L"]))
                    ),
                )
            # Delta mean depth
            col += 1
            if meas_d != 0:
                per_diff = 100 * (map_d - meas_d) / meas_d
            else:
                per_diff = np.nan
            if np.isnan(per_diff):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row, col, QtWidgets.QTableWidgetItem("{:7.1f}".format(per_diff))
                )

            row += 1
            # MAP width
            col = 0
            map_width = self.meas.map.borders_ens[-1]
            if np.isnan(map_width):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(self.q_digits(map_width * self.units["L"]))
                    ),
                )
            # Meas. width
            col += 1
            meas_width = trans_prop["width"][n_transects]
            if np.isnan(meas_width):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(
                        "{:8}".format(self.q_digits(meas_width * self.units["L"]))
                    ),
                )
            # Delta mean depth
            col += 1
            if meas_width != 0:
                per_diff = 100 * (map_width - meas_width) / meas_width
            else:
                per_diff = np.nan
            if np.isnan(per_diff):
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem("N/A"))
            else:
                tbl.setItem(
                    row, col, QtWidgets.QTableWidgetItem("{:7.1f}".format(per_diff))
                )

            tbl.item(0, 0).setFont(self.font_bold)
            tbl.item(1, 0).setFont(self.font_bold)
            tbl.item(2, 0).setFont(self.font_bold)
            tbl.item(3, 0).setFont(self.font_bold)

    def update_map_plot(self):
        """Method to update map plot based on selected radio buttons."""

        # If the canvas has not been previously created, create the canvas and
        # add the widget.

        # Todo fix create of plots. Sometimes they go behind the settings
        #  panel on the right side of the UI.
        if self.map_canvas is None:
            # Create the canvas
            self.map_canvas = MplCanvas(
                parent=self.graphics_map_wt_contour, width=12, height=6, dpi=80
            )
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graphics_map_wt_contour)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.map_canvas)
            # Initialize hidden toolbar for use by graphics controls
            self.map_toolbar = NavigationToolbar(self.map_canvas, self)
            self.map_toolbar.hide()

        if self.rb_map_contour.isChecked():
            self.combo_map_data.blockSignals(False)
            self.ed_map_secondary_velocity.blockSignals(False)
            self.cb_map_top_bottom.blockSignals(False)
            self.map_wt_contour()

        elif self.rb_map_bathymetry.isChecked() or self.rb_map_temp.isChecked():
            self.combo_map_data.blockSignals(True)
            self.ed_map_secondary_velocity.blockSignals(True)
            self.cb_map_top_bottom.blockSignals(True)
            self.plot_map()

        elif self.rb_map_stickship.isChecked():
            self.combo_map_data.blockSignals(True)
            self.ed_map_secondary_velocity.blockSignals(True)
            self.cb_map_top_bottom.blockSignals(True)
            self.map_shiptrack()

        self.figs = [self.map_fig]
        self.fig_calls = [self.update_map_plot]

        # Reset data cursor to work with new figure
        if self.actionData_Cursor.isChecked():
            self.data_cursor()

    def plot_map(self):
        """Creates plot of MAP data."""

        self.map_fig = AdvGraphs(canvas=self.map_canvas)

        self.map_fig.plot_map(
            self.meas.map,
            units=self.units,
            bath=self.rb_map_bathymetry.isChecked(),
            temp=self.rb_map_temp.isChecked(),
            plot_transects=self.cb_map_bed_profiles.isChecked(),
        )

        # Draw canvas
        self.map_canvas.draw()

    def map_wt_contour(self):
        """Creates water track profile on MAP data."""

        # Initialize the boat speed figure and assign to the canvas
        self.map_fig = AdvGraphs(canvas=self.map_canvas)
        self.map_fig.color_map = self.color_map

        # Quiver parameters
        data_quiver = None
        if self.map_settings["ed_map_secondary_velocity"] and self.map_settings[
            "combo_map_data"
        ] in ["Primary velocity", "Streamwise velocity"]:
            if self.map_settings["combo_map_data"] == "Primary velocity":
                vy = self.meas.map.secondary_velocity
                quiver_label = "Secondary velocity"
            elif self.map_settings["combo_map_data"] == "Streamwise velocity":
                vy = self.meas.map.transverse_velocity
                quiver_label = "Transverse velocity"
            data_quiver = {
                "x": self.meas.map.distance_cells_center,
                "z": self.meas.map.depth_cells_center,
                "vy": vy,
                "vz": self.meas.map.vertical_velocity,
                "scale": self.map_settings["ed_map_secondary_velocity"],
                "label": quiver_label,
            }

        # Bed profiles of transects
        bed_profiles = None
        if self.map_settings["cb_map_bed_profiles"]:
            bed_profiles = {
                "x": self.meas.map.acs_distance,
                "depth": self.meas.map.depth_by_transect,
            }

        map_data = self.meas.map
        data_type = self.map_settings["combo_map_data"]
        manufacturer = self.meas.transects[
            self.checked_transects_idx[0]
        ].adcp.manufacturer
        (
            x_plt,
            cell_plt,
            data_plt,
            depths,
            x_data,
            data_units,
        ) = self.map_fig.contour_map_prep(
            map_data, data_type, self.units, manufacturer=manufacturer
        )

        # Plot MAP profile
        self.map_fig.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=x_data,
            depth=depths,
            data_units=data_units,
            data_quiver=data_quiver,
            bed_profiles=bed_profiles,
        )

        self.map_fig.fig.subplots_adjust(
            left=0.08, bottom=0.1, right=0.95, top=0.97, wspace=0.02, hspace=0
        )
        # Draw canvas
        self.map_canvas.draw()

    def map_shiptrack(self):
        """Creates shiptrack plot for MAP cross-section and transects' track."""

        # Initialize the shiptrack figure and assign to the canvas
        self.map_fig = Maptrack(canvas=self.map_canvas)
        # Create the figure with the specified data
        settings = Measurement.current_settings(self.meas)
        self.map_fig.create(
            map_data=self.meas.map,
            units=self.units,
            nav_ref=settings["NavRef"],
            plot_transects=self.cb_map_bed_profiles.isChecked(),
        )

        # Draw canvas
        self.map_canvas.draw()

    def map_save_data(self):
        """Save MAP data as csv or txt."""
        if self.meas.map is not None and self.meas.map.total_discharge is not None:
            # ascii file delimiter
            try:
                ss = self.sticky_settings.get("Delimiter")
                delimiter = ss
            except KeyError:
                self.sticky_settings.new("Delimiter", "comma delimited")
                delimiter = "comma delimited"

            save_map = SaveDialog(parent=self, save_type="MAP", delimiter=delimiter)

            if len(save_map.full_Name) > 0:
                try:
                    try:
                        self.sticky_settings.set("Delimiter", save_map.delimiter)
                    except KeyError:
                        self.sticky_settings.new("Delimiter", save_map.delimiter)

                    manufacturer = self.meas.transects[
                        self.checked_transects_idx[0]
                    ].adcp.manufacturer
                    self.meas.map.export_csv(
                        save_map.full_Name,
                        units=self.units,
                        delimiter=save_map.delimiter,
                        manufacturer=manufacturer,
                    )
                except Exception:
                    self.popup_message(self.tr("Failed to save MAP data."))

    def plot_map_google_earth(self):
        """Creates line plots of transects in Google Earth using GGA
        coordinates and MAP average ship track."""

        fullname = os.path.join(
            self.sticky_settings.get("Folder"),
            datetime.today().strftime("MAP_%Y%m%d_%H%M%S_QRev.kml"),
        )

        self.meas.map.export_kml(self.meas, fullname)

        try:
            os.startfile(fullname)
        except os.error:
            self.popup_message(
                text=self.tr(
                    "Google Earth is not installed or is not associated with "
                    "kml files."
                )
            )

    def map_cell_auto(self):
        """Enable or disable the width and Height line edits."""

        if self.cb_map_cell_size_auto.isChecked():
            self.ed_map_cell_width.blockSignals(True)
            self.ed_map_cell_width.setEnabled(False)
            self.ed_map_cell_width.clear()

            self.ed_map_cell_height.blockSignals(True)
            self.ed_map_cell_height.setEnabled(False)
            self.ed_map_cell_height.clear()

            self.update_map()

        else:
            self.ed_map_cell_width.blockSignals(False)
            self.ed_map_cell_width.setEnabled(True)

            self.ed_map_cell_height.blockSignals(False)
            self.ed_map_cell_height.setEnabled(True)

    # Graphics save
    # =================
    def figs_menu_connection(self):
        """Connect ui to event filter for current figures."""
        for fig in self.figs:
            fig.canvas.parent().installEventFilter(self)

    def eventFilter(self, source, event):
        """Load events."""

        if event.type() == QtCore.QEvent.ContextMenu:
            if source in self.ui_parents:
                self.current_fig = self.figs[self.ui_parents.index(source)]

                # Determine axes of graph in which the click occured and save
                # for use by change axes limits
                extents = []
                for ax in self.current_fig.fig.axes:
                    extents.append(ax.bbox.extents)
                extents = np.array(extents)
                y_max = np.nanmax(extents[:, -1])
                y_adjusted = y_max - event.y()
                ax = np.where(
                    np.logical_and(
                        np.greater(event.x(), extents[:, 0]),
                        np.less(y_adjusted, extents[:, 3]),
                    )
                )[0]
                if len(ax) > 0:
                    self.current_axis = self.current_fig.fig.axes[ax[-1]]

                # Context menu
                self.figsMenu.exec_(event.globalPos())
                return True
        return super().eventFilter(source, event)

    def save_fig(self):
        """Save selected figure."""
        if self.current_fig is not None:
            # Get the current folder setting.
            save_fig = SaveDialog(parent=self, save_type="fig")
            # Save figure in user format
            if len(save_fig.full_Name) > 0:
                self.current_fig.fig.savefig(
                    save_fig.full_Name, dpi=300, bbox_inches="tight"
                )

    # Graphics controls
    # =================
    def clear_zphd(self):
        """Clears the graphics user controls."""

        try:
            self.actionData_Cursor.setChecked(False)
            for fig in self.figs:
                fig.set_hover_connection(False)
            if self.actionPan.isChecked():
                self.actionPan.trigger()
            if self.actionZoom.isChecked():
                self.actionZoom.trigger()
        except (AttributeError, SystemError):
            pass

    def data_cursor(self):
        """Apply the data cursor."""

        if self.actionData_Cursor.isChecked():
            for fig in self.figs:
                if self.actionPan.isChecked():
                    self.actionPan.trigger()
                if self.actionZoom.isChecked():
                    self.actionZoom.trigger()
                self.actionData_Cursor.setChecked(True)
                if fig is not None:
                    fig.set_hover_connection(True)
        else:
            for fig in self.figs:
                fig.set_hover_connection(False)

    def home(self):
        """Reset graphics to default."""

        for tb in self.toolbars:
            tb.home()

    def zoom(self):
        """Zoom graphics using window."""

        for tb in self.toolbars:
            tb.zoom()
        self.actionPan.setChecked(False)
        self.actionData_Cursor.setChecked(False)
        self.data_cursor()

    def pan(self):
        """Pan graph."""

        for tb in self.toolbars:
            tb.pan()
        self.actionZoom.setChecked(False)
        self.actionData_Cursor.setChecked(False)
        self.data_cursor()

    def change_x_axis(self):
        """Manages the changing of the x axis type."""

        with self.wait_cursor():
            # Clear zoom, pan, home, data_cursor
            self.clear_zphd()

            # Determine the selected tab
            tab_idx = self.current_tab

            # Main tab
            if tab_idx == "Main":
                self.contour_shiptrack(self.checked_transects_idx[self.transect_row])

            # Compass/PR tab
            elif tab_idx == "Compass/P/R":
                self.compass_plot()
                self.pr_plot()

            # Moving-bed test tab
            elif tab_idx == "MovBedTst":
                self.mb_plots(idx=self.mb_row)

            # Bottom track tab
            elif tab_idx == "BT":
                self.bt_plots()

            # GPS tab
            elif tab_idx == "GPS":
                self.gps_plots()

            # Depth tab
            elif tab_idx == "Depth":
                self.depth_plots()

            # Water track tab
            elif tab_idx == "WT":
                self.wt_plots()

            # Edges tab
            elif tab_idx == "Edges":
                self.edges_graphics()

            # Adv. Graph
            elif tab_idx == "Adv. Graph":
                self.adv_graph_tab()

    def set_axes(self):
        """Scales the selected graph to either user specifications of automatics
        scaling.
        """

        scale = AxesScale()

        # Get current axes limits
        x_limits = self.current_axis.get_xlim()
        y_limits = self.current_axis.get_ylim()

        # Show limits in dialog
        scale.ed_x_left.setText("%.2f" % x_limits[0])
        scale.ed_x_right.setText("%.2f" % x_limits[1])
        scale.ed_y_bottom.setText("%.2f" % y_limits[0])
        scale.ed_y_top.setText("%.2f" % y_limits[1])

        rsp = scale.exec_()

        with self.wait_cursor():
            # Apply settings from options window
            if rsp == QtWidgets.QDialog.Accepted:
                if scale.cb_axes_auto.isChecked():
                    # If automatic is selected the original method that created the graph
                    # is identified and called. However, if that method cannot be
                    # identified or it requires extra arguments then the plot is
                    # rescaled using the data available from the plot axes. The
                    # reason the original plot method has priority is that for some
                    # graphs the tick scaling is customized.
                    try:
                        self.fig_calls[self.figs.index(self.current_fig)]()
                    except:
                        # Rescale the plot using data from the plot
                        ydata = np.array([])
                        xdata = np.array([])
                        for line in self.current_axis.lines:
                            ydata = np.hstack((ydata, line.get_ydata()))
                            xdata = np.hstack((xdata, line.get_xdata()))
                        ydata_max = np.nanmax(ydata) * 1.02
                        ydata_min = 0 - np.nanmax(ydata) * 0.02
                        xdata_max = np.nanmax(xdata) * 1.02
                        xdata_min = 0 - np.nanmax(xdata) * 0.02

                        if np.isnan(ydata_max):
                            ydata_max = 1
                            ydata_min = 0
                        if np.isnan(xdata_max):
                            xdata_max = 1
                            xdata_min = 0

                        if x_limits[0] < x_limits[1]:
                            new_x_limits = [xdata_min, xdata_max]
                        else:
                            new_x_limits = [xdata_max, xdata_min]

                        if y_limits[0] < y_limits[1]:
                            new_y_limits = [ydata_min, ydata_max]
                        else:
                            new_y_limits = [ydata_max, ydata_min]
                else:
                    x_left = self.check_numeric_input(scale.ed_x_left, block=False)
                    x_right = self.check_numeric_input(scale.ed_x_right, block=False)
                    y_bottom = self.check_numeric_input(scale.ed_y_bottom, block=False)
                    y_top = self.check_numeric_input(scale.ed_y_top, block=False)
                    new_x_limits = [x_left, x_right]
                    new_y_limits = [y_bottom, y_top]

                # Set new limits
                if not any(new_x_limits) is None and not any(new_y_limits) is None:
                    self.current_axis.set_xlim(left=x_left, right=x_right)
                    self.current_axis.set_ylim(bottom=y_bottom, top=y_top)
                    self.current_axis.yaxis.set_major_locator(AutoLocator())
                    self.current_fig.canvas.draw()

    def x_axis_time(self):
        """Changes the x-axis type to time"""
        if self.current_tab == "Edges":
            self.edges_axis_type = "T"
        self.x_axis_type = "T"
        self.change_x_axis()

    def x_axis_ensemble(self):
        """Changes the x-axis type to ensembles"""
        if self.current_tab == "Edges":
            self.edges_axis_type = "E"
        self.x_axis_type = "E"
        self.change_x_axis()

    def x_axis_length(self):
        """Changes the x-axis type to length"""

        if self.current_tab == "Edges":
            self.edges_axis_type = "L"
        self.x_axis_type = "L"
        self.change_x_axis()

    def set_show_below_sl(self):
        """Sets toggle to allow data below the side lobe to be shown."""

        if self.show_below_sl:
            self.show_below_sl = False
        else:
            self.show_below_sl = True

        self.adv_graph_plots()

    def show_extrapolated(self):
        if self.meas is not None:
            if not self.plot_extrapolated:
                self.plot_extrapolated = True
                self.actionShow_Extrapolated.setChecked(True)
            else:
                self.plot_extrapolated = False
                self.actionShow_Extrapolated.setChecked(False)

            with self.wait_cursor():
                # Clear zoom, pan, home, data_cursor
                self.clear_zphd()

                # Determine the selected tab
                tab_idx = self.current_tab

                # Main tab
                if tab_idx == "Main":
                    self.main_wt_contour(
                        transect_id=self.checked_transects_idx[self.transect_row]
                    )
                elif tab_idx == "WT":
                    self.wt_plots()
                elif tab_idx == "Adv. Graph":
                    self.adv_graph_tab()
        else:
            self.actionShow_Extrapolated.setChecked(False)

    # Split functions
    # ==============
    def split_initialization(self, groupings=None, data=None):
        """Sets the GUI components to support semi-automatic processing of pairings
        that split a single measurement into multiple measurements.
        Loads the first pairing.

        Parameters
        ==========
        groupings: list
            This a list of lists of transect indices splitting a single measurement
            into multiple measurements Example groupings = [[0, 1], [2, 3, 4, 5], [8, 9]]
        data: Measurement
            Object of class Measurement which contains all of the transects to be
            grouped into multiple measurements
        """

        if groupings is not None:
            # GUI settings to allow processing to split measurement into
            # multiple measurements
            self.save_all = False
            self.actionOpen.setEnabled(False)
            self.actionCheck.setEnabled(False)
            self.actionSave.setEnabled(True)
            self.actionComment.setEnabled(True)
            self.actionBT.setDisabled(True)
            self.actionGGA.setDisabled(True)
            self.actionVTG.setDisabled(True)
            self.actionOFF.setDisabled(True)
            self.actionON.setDisabled(True)
            self.actionOptions.setDisabled(True)
            self.actionGoogle_Earth.setDisabled(True)
            self.actionShow_Extrapolated.setEnabled(True)

            # Data settings
            self.meas = data
            self.groupings = groupings
            self.checked_transects_idx = Measurement.checked_transects(self.meas)
            self.h_external_valid = Measurement.h_external_valid(self.meas)
            self.transect_row = 0

            # Process first pairing
            self.group_idx = 0
            self.checked_transects_idx = self.groupings[self.group_idx]
            self.split_processing(self.checked_transects_idx)

    def split_processing(self, group):
        """Creates the measurement based on the transect indices defined in
        group and updates the main tab with this new measurement data.

        Parameters
        ==========
        group: list
            List of transect indices that comprise a single measurement.
        """

        Measurement.selected_transects_changed(self.meas, selected_transects_idx=group)

        if self.group_idx > 0:
            # Activate main, Summary, and Messages tabs
            self.tab_all.setCurrentIndex(0)
            self.tab_summary.setCurrentIndex(0)
            self.tab_mc.setCurrentIndex(0)
            self.transect_row = 0

            # Set the change status to True for the main window update
            self.change = True
            self.map_change = True

        self.update_main()

    def split_save(self):
        """Saves the current measurement and automatically loads the next
        measurement based on the pairings. When the last pairing has been completed,
        returns control to the function initiating QRev.
        """

        # Initialize dialog
        rating_dialog = Rating(self)
        rating_dialog.uncertainty_value.setText(
            "{:4.1f}".format(self.meas.uncertainty.total_95_user)
        )
        if self.meas.uncertainty.total_95_user < 3:
            rating_dialog.rb_excellent.setChecked(True)
        elif self.meas.uncertainty.total_95_user < 5.01:
            rating_dialog.rb_good.setChecked(True)
        elif self.meas.uncertainty.total_95_user < 8.01:
            rating_dialog.rb_fair.setChecked(True)
        else:
            rating_dialog.rb_poor.setChecked(True)
        rating_entered = rating_dialog.exec_()

        # If data entered.
        with self.wait_cursor():
            if rating_entered:
                if rating_dialog.rb_excellent.isChecked():
                    rating = "Excellent"
                elif rating_dialog.rb_good.isChecked():
                    rating = "Good"
                elif rating_dialog.rb_fair.isChecked():
                    rating = "Fair"
                else:
                    rating = "Poor"

        # Create default file name
        if rating_entered:
            self.meas.user_rating = rating

            group = str(self.group_idx + 1)

            save_file = SaveDialog(group=group, parent=self)

            if len(save_file.full_Name) > 0:
                # Save data in Matlab format
                if self.save_all:
                    Python2Matlab.save_matlab_file(
                        self.meas, save_file.full_Name, __qrev_version__
                    )
                else:
                    Python2Matlab.save_matlab_file(
                        self.meas,
                        save_file.full_Name,
                        __qrev_version__,
                        checked=self.groupings[self.group_idx],
                    )

                # Save xml file
                self.meas.xml_output(
                    __qrev_version__, save_file.full_Name[:-4] + ".xml"
                )

                # Notify user when save complete
                QtWidgets.QMessageBox.about(
                    self,
                    "Save",
                    "Group "
                    + group
                    + " of "
                    + str(len(self.groupings))
                    + "\n Files (*_QRev.mat and "
                    "*_QRev.xml) have been saved.",
                )

                # Create a summary of the processed discharges
                discharge = Measurement.mean_discharges(self.meas)
                q = {
                    "group": self.groupings[self.group_idx],
                    "start_serial_time": self.meas.transects[
                        self.groupings[self.group_idx][0]
                    ].date_time.start_serial_time,
                    "end_serial_time": self.meas.transects[
                        self.groupings[self.group_idx][-1]
                    ].date_time.end_serial_time,
                    "processed_discharge": discharge["total_mean"],
                    "rating": rating,
                    "xml_file": save_file.full_Name[:-4] + ".xml",
                }
                self.processed_data.append(q)

                # Create summary of all processed transects
                for idx in self.groupings[self.group_idx]:
                    q_trans = {
                        "transect_id": idx,
                        "transect_file": self.meas.transects[idx].file_name[:-4],
                        "start_serial_time": self.meas.transects[
                            idx
                        ].date_time.start_serial_time,
                        "end_serial_time": self.meas.transects[
                            idx
                        ].date_time.end_serial_time,
                        "duration": self.meas.transects[
                            idx
                        ].date_time.transect_duration_sec,
                        "processed_discharge": self.meas.discharge[idx].total,
                    }
                    self.processed_transects.append(q_trans)

                # Load next pairing
                self.group_idx += 1

                # If all pairings have been processed return control to the
                # function initiating QRev.
                if self.group_idx > len(self.groupings) - 1:
                    self.caller.processed_meas = self.processed_data
                    self.caller.processed_transects = self.processed_transects
                    self.caller.Show_RIVRS()
                    self.close()

                else:
                    self.checked_transects_idx = self.groupings[self.group_idx]
                    self.split_processing(self.checked_transects_idx)

    # Support functions
    # =================
    def q_qa_message(
        self,
        qa_data,
        cat_idx,
        transect_id,
        total_threshold_warning,
        total_threshold_caution,
        run_threshold_warning,
        run_threshold_caution,
    ):
        """Creates QA message for tooltips."""

        text = []
        if cat_idx == 0:
            if qa_data["all_invalid"][transect_id]:
                text.append("No valid data. \n")

        try:
            qa_check = qa_data["q_total_warning"][transect_id, cat_idx]
        except IndexError:
            qa_check = qa_data["q_total_warning"][transect_id]

        if qa_check:
            text.append(
                self.tr(
                    "Interpolated Q for invalid cells and ensembles in a transect exceeds "
                )
                + "%3.0f" % total_threshold_warning
                + "%;\n"
            )

        try:
            qa_check = qa_data["q_max_run_warning"][transect_id, cat_idx]
        except IndexError:
            qa_check = qa_data["q_max_run_warning"][transect_id]

        if qa_check:
            text.append(
                self.tr("Interpolated Q for consecutive invalid ensembles exceeds ")
                + "%3.0f" % run_threshold_warning
                + "%;\n"
            )

        try:
            qa_check = qa_data["q_total_caution"][transect_id, cat_idx]
        except IndexError:
            qa_check = qa_data["q_total_caution"][transect_id]

        if qa_check:
            text.append(
                self.tr(
                    "Interpolated Q for invalid cells and ensembles in a transect exceeds "
                )
                + "%3.0f" % total_threshold_caution
                + "%;\n"
            )

        try:
            qa_check = qa_data["q_max_run_caution"][transect_id, cat_idx]
        except IndexError:
            qa_check = qa_data["q_max_run_caution"][transect_id]

        if qa_check:
            text.append(
                self.tr("Interpolated Q for consecutive invalid ensembles exceeds ")
                + "%3.0f" % run_threshold_caution
                + "%;\n"
            )
        return text

    @staticmethod
    def popup_message(text):
        """Display a message box with messages specified in text.

        Parameters
        ----------
        text: str
            Message to be displayed.
        """

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(text)
        msg.setWindowTitle("Error")
        msg.exec_()
        return

    def keyPressEvent(self, e):
        """Implements shortcut keys.

        Parameters
        ----------
        e: event
            Event generated by key pressed by user
        """

        # Help
        if e.key() == QtCore.Qt.Key_F1:
            self.help()

        # Change displayed transect
        if self.current_tab != "MovBedTst" and self.current_tab != "SysTest":
            # Select transect above in table or wrap to bottom
            if e.key() == QtCore.Qt.Key_Up:
                if self.transect_row - 1 < 0:
                    self.transect_row = len(self.checked_transects_idx) - 1
                else:
                    self.transect_row -= 1
                self.change = True
                self.map_change = True
                self.change_selected_transect()

            # Select transect below in table or wrap to top
            elif e.key() == QtCore.Qt.Key_Down:
                if self.transect_row + 1 > len(self.checked_transects_idx) - 1:
                    self.transect_row = 0
                else:
                    self.transect_row += 1
                self.change = True
                self.map_change = True
                self.change_selected_transect()

        # Change displayed moving-bed test
        elif self.current_tab == "MovBedTst":
            # Select transect above in table or wrap to bottom
            if e.key() == QtCore.Qt.Key_Up:
                if self.mb_row - 1 < 0:
                    self.mb_row = len(self.meas.mb_tests) - 1
                else:
                    self.mb_row -= 1

            # Select transect below in table or wrap to top
            elif e.key() == QtCore.Qt.Key_Down:
                if self.mb_row + 1 > len(self.meas.mb_tests) - 1:
                    self.mb_row = 0
                else:
                    self.mb_row += 1

            self.mb_table_clicked(self.mb_row, 3)

        # Turn on or off display of alternate method medians to allow comparison
        if self.current_tab == "Extrap":
            # Turn on comparison medians
            if e.key() == QtCore.Qt.Key_F8:
                self.compare_medians()
            # Turn off comparison medians
            if e.key() == QtCore.Qt.Key_F9:
                self.extrap_plot()

    def change_selected_transect(self):
        """Coordinates changing the displayed transect when changing
        transects with the up/down arrow keys.
        """

        tab_idx = self.tab_all.tabText(self.tab_all.currentIndex())
        col = 0

        # Main tab
        if tab_idx == "Main":
            self.select_transect(self.transect_row + 1, col)

        # Compass/PR tab
        elif tab_idx == "Compass/P/R":
            self.compass_table_clicked(self.transect_row, col)

        # Bottom track tab
        elif tab_idx == "BT":
            self.bt_table_clicked(self.transect_row, col)

        # GPS tab
        elif tab_idx == "GPS":
            self.gps_table_clicked(self.transect_row, col)

        # Depth tab
        elif tab_idx == "Depth":
            self.depth_table_clicked(self.transect_row, col)

        # Water track tab
        elif tab_idx == "WT":
            self.wt_table_clicked(self.transect_row, col)

        # Edges tab
        elif tab_idx == "Edges":
            self.edges_table_clicked(self.transect_row, col)

    @staticmethod
    def check_numeric_input(obj, block=True):
        """Check if input is a numeric object.

        Parameters
        ----------
        obj: QtWidget
            QtWidget user edit box.
        block: bool
            Block signals

        Returns
        -------
        out: float
            obj converted to float if possible

        """
        if block:
            obj.blockSignals(True)
        out = None
        if len(obj.text()) > 0:
            # Try to convert obj to a float
            try:
                text = obj.text()
                out = float(text)
            # If conversion is not successful warn user that the input is
            # invalid.
            except ValueError:
                obj.setText("")
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Error")
                msg.setInformativeText(
                    "You have entered non-numeric text. Enter a numeric " "value."
                )
                msg.setWindowTitle("Error")
                msg.exec_()
        if block:
            obj.blockSignals(False)
        return out

    @contextmanager
    def wait_cursor(self):
        """Provide a busy cursor to the user while the code is processing."""

        try:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            yield
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def tab_manager(self, tab_idx=None, old_discharge=None, subtab_idx=None):
        """Manages the initialization of content for each tab and updates that
         information as necessary.

        Parameters
        ----------
        tab_idx: int
            Index of tab clicked by user
        old_discharge: list
            List of QComp objects contain the discharge prior to most recent
            change
        subtab_idx: int
            Index of subtab of tab_summary, used to force tab_idx to main,
            discharge
        subtab_idx: int
            Index of subtab of tab_summary, used to force tab_idx to main, discharge
        """

        # Clear zoom, pan, home, data_cursor
        self.clear_zphd()

        # Determine the selected tab
        if tab_idx is None:
            tab_idx = self.current_tab
        else:
            tab_idx = self.tab_all.tabText(tab_idx)

        self.current_tab = tab_idx

        # Main tab
        if tab_idx == "Main":
            if subtab_idx is not None:
                self.tab_summary.setCurrentIndex(0)

            if self.change:
                # If data has changed update main tab display
                self.update_main()
            else:
                # Setup list for use by graphics controls
                if self.run_oursin:
                    self.canvases = [
                        self.main_shiptrack_canvas,
                        self.main_wt_contour_canvas,
                        self.main_extrap_canvas,
                        self.main_discharge_canvas,
                        self.uncertainty_lollipop_canvas,
                    ]
                    self.figs = [
                        self.main_shiptrack_fig,
                        self.main_wt_contour_fig,
                        self.main_extrap_fig,
                        self.main_discharge_fig,
                        self.uncertainty_lollipop_fig,
                    ]
                    self.fig_calls = [
                        self.main_shiptrack,
                        self.main_wt_contour,
                        self.main_extrap_plot,
                        self.discharge_plot,
                        self.main_uncertainty_plot,
                    ]
                    self.toolbars = [
                        self.main_shiptrack_toolbar,
                        self.main_wt_contour_toolbar,
                        self.main_extrap_toolbar,
                        self.main_discharge_toolbar,
                        self.uncertainty_lollipop_toolbar,
                    ]
                else:
                    self.canvases = [
                        self.main_shiptrack_canvas,
                        self.main_wt_contour_canvas,
                        self.main_extrap_canvas,
                        self.main_discharge_canvas,
                    ]
                    self.figs = [
                        self.main_shiptrack_fig,
                        self.main_wt_contour_fig,
                        self.main_extrap_fig,
                        self.main_discharge_fig,
                    ]
                    self.fig_calls = [
                        self.main_shiptrack,
                        self.main_wt_contour,
                        self.main_extrap_plot,
                        self.discharge_plot,
                    ]
                    self.toolbars = [
                        self.main_shiptrack_toolbar,
                        self.main_wt_contour_toolbar,
                        self.main_extrap_toolbar,
                        self.main_discharge_toolbar,
                    ]
                self.ui_parents = [i.parent() for i in self.canvases]
                self.tab_main.show()

        # System tab
        elif tab_idx == "SysTest":
            self.system_tab()

        # Compass/PR tab
        elif tab_idx == "Compass/P/R":
            self.compass_tab(old_discharge=old_discharge)

        # Temp/Sal tab
        elif tab_idx == "Temp/Sal":
            self.tempsal_tab(old_discharge=old_discharge)

        # Moving-bed test tab
        elif tab_idx == "MovBedTst":
            self.movbedtst_tab()

        # Bottom track tab
        elif tab_idx == "BT":
            self.bt_tab(old_discharge=old_discharge)

        # GPS tab
        elif tab_idx == "GPS":
            self.gps_tab(old_discharge=old_discharge)

        # Depth tab
        elif tab_idx == "Depth":
            self.depth_tab(old_discharge=old_discharge)

        # Water track tab
        elif tab_idx == "WT":
            self.wt_tab(old_discharge=old_discharge)

        # Extrapolation tab
        elif tab_idx == "Extrap":
            self.extrap_tab()

        # Edges tab
        elif tab_idx == "Edges":
            self.edges_axis_type = "E"
            self.edges_tab()

        # Uncertainty tab
        elif tab_idx == "Uncertainty":
            self.uncertainty_tab()

        # EDI tab
        elif tab_idx == "EDI":
            self.edi_tab()

        # Adv. Graph tab
        elif tab_idx == "Adv. Graph":
            self.adv_graph_tab()

        # MAP tab
        elif tab_idx == "MAP":
            self.map_tab()

        self.set_tab_color()

        # Toggle window to fix sizing when BT or WT tabs are chosen to prevent
        # full screen window from going behind the taskbar.
        # if self.isMaximized() or self.isFullScreen():
        #     self.showNormal()
        #     self.showMaximized()

    def update_comments(self, tab_idx=None):
        """Manages the initialization of content for each tab and updates that
        information as necessary.

        Parameters
        ----------
        tab_idx: int
            Index of tab clicked by user
        """

        # Determine selected tab
        if tab_idx is None:
            tab_idx = self.current_tab
        else:
            self.current_tab = tab_idx

        # Main
        if tab_idx == "Main":
            self.comments_tab()

        # System Test
        elif tab_idx == "SysTest":
            self.systest_comments_messages()

        # Compass/PR
        elif tab_idx == "Compass/P/R":
            self.compass_comments_messages()

        # Temp/Sal
        elif tab_idx == "Temp/Sal":
            self.tempsal_comments_messages()

        # Moving-bed test
        elif tab_idx == "MovBedTst":
            self.mb_comments_messages()

        # Bottom track
        elif tab_idx == "BT":
            self.bt_comments_messages()

        # GPS
        elif tab_idx == "GPS":
            self.gps_comments_messages()

        # Depth
        elif tab_idx == "Depth":
            self.depth_comments_messages()

        # WT
        elif tab_idx == "WT":
            self.wt_comments_messages()

        # Extrapolation
        elif tab_idx == "Extrap":
            self.extrap_comments_messages()

        # Edges
        elif tab_idx == "Edges":
            self.edges_comments_messages()

        # Uncertainty
        elif tab_idx == "Uncertainty":
            self.uncertainty_comments_messages()

    def config_gui(self):
        """Configure the user interface based on the available data."""

        # After data is loaded enable GUI and buttons on toolbar
        self.tab_all.setEnabled(True)
        self.actionSave.setEnabled(True)
        self.actionComment.setEnabled(True)
        self.actionHome.setEnabled(True)
        self.actionZoom.setEnabled(True)
        self.actionPan.setEnabled(True)
        self.actionData_Cursor.setEnabled(True)
        self.actionShow_Extrapolated.setEnabled(True)

        if self.groupings is not None:
            self.actionCheck.setEnabled(False)
        else:
            self.actionCheck.setEnabled(True)
        self.actionBT.setEnabled(True)
        self.actionOptions.setEnabled(True)
        self.actionGGA.setDisabled(True)
        self.actionVTG.setDisabled(True)
        self.actionOFF.setDisabled(True)
        self.actionON.setDisabled(True)

        if self.agency_options["ExtrapolatedSpeed"]["ShowIcon"]:
            self.actionShow_Extrapolated.setVisible(True)
        else:
            self.actionShow_Extrapolated.setVisible(False)

        # Set tab text and icons to default
        for tab_idx in range(self.tab_all.count() - 4):
            self.tab_all.setTabIcon(tab_idx, QtGui.QIcon())
            self.tab_all.tabBar().setTabTextColor(tab_idx, QtGui.QColor(191, 191, 191))

        # Configure tabs and toolbar for the presence or absence of GPS data
        self.tab_all.setTabEnabled(6, False)
        self.actionGGA.setEnabled(False)
        self.actionVTG.setEnabled(False)
        self.actionON.setEnabled(False)
        self.actionOFF.setEnabled(False)
        self.actionGoogle_Earth.setEnabled(False)
        for idx in self.checked_transects_idx:
            if self.meas.transects[idx].boat_vel.gga_vel is not None:
                self.tab_all.setTabEnabled(6, True)
                self.actionGGA.setEnabled(True)
                self.actionON.setEnabled(True)
                self.actionOFF.setEnabled(True)
                self.actionGoogle_Earth.setEnabled(True)
                if not hasattr(self, "sc_gga"):
                    self.sc_gga = QtWidgets.QShortcut(
                        QtGui.QKeySequence("Ctrl+G"), self
                    )
                    self.sc_gga.activated.connect(self.set_ref_gga)
            if self.meas.transects[idx].boat_vel.vtg_vel is not None:
                self.tab_all.setTabEnabled(6, True)
                self.actionVTG.setEnabled(True)
                self.actionON.setEnabled(True)
                self.actionOFF.setEnabled(True)
                if not hasattr(self, "sc_vtg"):
                    self.sc_vtg = QtWidgets.QShortcut(
                        QtGui.QKeySequence("Ctrl+V"), self
                    )
                    self.sc_vtg.activated.connect(self.set_ref_vtg)

            if self.actionVTG.isEnabled() and self.actionGGA.isEnabled():
                break

        if self.actionVTG.isEnabled() and self.actionGGA.isEnabled():
            self.update_toolbar_composite_tracks()

        # Configure tabs for the presence or absence of a compass
        if len(self.checked_transects_idx) > 0:
            heading = np.unique(
                self.meas.transects[
                    self.checked_transects_idx[0]
                ].sensors.heading_deg.internal.data
            )
        else:
            heading = np.array([0])

        if len(heading) > 1 and np.any(np.not_equal(heading, 0)):
            self.tab_all.setTabEnabled(2, True)
            self.tab_all.setTabEnabled(13, True)
        else:
            self.tab_all.setTabEnabled(2, False)
            self.tab_all.setTabEnabled(13, False)

        self.tab_all.setCurrentIndex(0)

    def q_digits(self, q):
        if self.agency_options["QDigits"]["method"] == "sigfig":
            return sfrnd(q, self.agency_options["QDigits"]["digits"])
        else:
            return np.round(q, self.agency_options["QDigits"]["digits"])

    def default_folder(self):
        """Returns default folder.

        Returns the folder stored in settings or if no folder is stored,
        then the current working folder is returned.
        """
        try:
            folder = self.sticky_settings.get("Folder")
            if not folder:
                folder = os.getcwd()
        except KeyError:
            self.sticky_settings.new("Folder", os.getcwd())
            folder = self.sticky_settings.get("Folder")
        return folder

    def closeEvent(self, event):
        """Warns user when closing QRev.

        Parameters
        ----------
        event: QCloseEvent
            Object of QCloseEvent
        """
        if event:
            if self.groupings is None and self.meas is not None:
                close = QtWidgets.QMessageBox()
                close.setIcon(QtWidgets.QMessageBox.Warning)
                close.setWindowTitle("Close")
                close.setText(
                    self.tr(
                        "If you haven't saved your data, "
                        "changes will be lost. \n Are you sure you want to Close? "
                    )
                )
                close.setStandardButtons(
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
                )
                close = close.exec()

                if close == QtWidgets.QMessageBox.Yes:
                    if self.caller is not None:
                        self.caller.Show_RIVRS()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
        else:
            event.accept()


# Adjust scaling based on users resolution.
if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


# Main
# ====
if __name__ == "__main__":
    mp.freeze_support()
    app = QtWidgets.QApplication(sys.argv)
    # splash_pix = QtGui.QPixmap('QRevInt_Splash.png')
    # splash = QtWidgets.QSplashScreen(splash_pix)
    # splash.show
    window = QRev()
    if window.agreement:
        window.show()
        app.exec_()
        # splash.finish(None)
    else:
        app.closeAllWindows()

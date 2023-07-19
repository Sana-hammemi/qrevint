import numpy as np
import copy
from matplotlib import gridspec
import matplotlib.cm as cm
from matplotlib.dates import DateFormatter, num2date
from matplotlib.patches import Polygon
from PyQt5 import QtWidgets, QtCore
from contextlib import contextmanager
from datetime import datetime, timedelta
from MiscLibs.common_functions import sind, cosd
from MiscLibs.compute_edge_cd import compute_edge_cd


class AdvGraphs(object):
    """Class to generate the color contour plot of water speed data.

    Attributes
    ----------
    canvas: MplCanvas
            Object of MplCanvas a FigureCanvas
    fig: Object
        Figure object of the canvas
    units: dict
        Dictionary of units conversions
    hover_connection: int
        Index to data cursor connection
    annot: Annotation
        Annotation object for data cursor
    x_axis_type: str
        Identifies x-axis type (L-lenght, E-ensemble, T-time)
    fig_no: int
        Figure number indicating location within subplots
    color_map: str
        Name of color map for color contour plots
    x: np.ndarray()
        Array of values for the x-axis
    x_timestamp: np.ndarray()
        Array of timestamps used for x-axis if time is selected
    ax: list
        List of subplots
    flow_direction: float
        Flow direction in degrees
    n_subplots: int
        Number of subplots
    transect: TransectData
        Transect for which data are to be plotted
    discharge: QComp
        Discharge data
    data_plotted: list
        List of dictionaries containing the type of plot an values of data
        plotted (x, y, z)
    gs: gridspec
        Grid specification for subplots
    wt_advanced_type_methods: dict
        Dictionary connecting to the plot type to the method to create the plot
    ping_name: dict
        Name of ping type for labeling colorbar and data cursor
    show_below_sl: bool
        Indicates if correlation or intensity data below the side lobe should
        be shown
    ping_type_long_name: dict
        Dictionary linking ping type to long name for labeling
    p_type_color: dict
        Dictionary specifying the plot color for each ping type
    p_type_marker: dict
        Dictionary specifying the plot marker for each ping type
    wt_legend_dict: dict
        Dictionary of legend text for wt ping type
    bt_legend_dict:
        Dictionary of legend text for bt ping type
    freq_color: dict
        Dictionary for bt frequency color
    freq_marker: dict
        Dictionary for bt frequency marker
    expanded_x: np.array(float)
        Values of x-axis for length including edge shape and distance
    show_unmeasured: bool
        Indicates if unmeasured data should be plotted in final wt contour
    """

    def __init__(self, canvas):
        """Initialize object using the specified canvas.

        Parameters
        ----------
        canvas: MplCanvas
            Object of MplCanvas
        """

        # Initialize attributes
        self.canvas = canvas
        self.fig = canvas.fig
        self.units = None
        self.hover_connection = None
        self.annot = None
        self.x_axis_type = "E"
        self.fig_no = 0
        self.color_map = "viridis"
        self.x = None
        self.x_timestamp = None
        self.ax = None
        self.flow_direction = None
        self.n_subplots = 0
        self.transect = None
        self.discharge = None
        self.ax = []
        self.annot = []
        self.data_plotted = []
        self.gs = None
        self.ping_name = None
        self.show_below_sl = False
        self.show_unmeasured = False
        self.expanded_x = None
        self.ping_type_long_name = {
            "I": "Incoherent",
            "C": "Coherent",
            "S": "Surface",
            "1I": "1 MHz Inc",
            "1C": "1 MHz Coh",
            "3I": "3 MHz Inc",
            "3C": "3 MHz Coh",
            "BB": "BB",
            "PC": "PC",
            "PC/BB": "PC/BB",
            "PCBB": "PC/BB",
            "U": "N/A",
            "1": "N/A",
            "Other": "N/A",
        }
        self.p_type_color = {
            "I": "b",
            "C": "#009933",
            "S": "#ffbf00",
            "1I": "b",
            "1C": "#009933",
            "3I": "#ffbf00",
            "3C": "#ff33cc",
            "BB": "b",
            "PC": "#009933",
            "PC/BB": "#ffbf00",
            "PCBB": "#ffbf00",
            "U": "b",
            "1": "b",
            "Other": "b",
        }
        self.p_type_marker = {
            "I": ".",
            "C": "+",
            "S": "x",
            "1I": ".",
            "1C": "*",
            "3I": "+",
            "3C": "x",
            "BB": ".",
            "PC": "+",
            "PC/BB": "x",
            "PCBB": "x",
            "U": ".",
            "1": ".",
            "Other": ".",
        }
        self.wt_legend_dict = {
            "I": "Incoherent",
            "C": "Coherent",
            "S": "Surface Cell",
            "1I": "1MHz Incoherent",
            "1C": "1 MHz HD",
            "3I": "3 MHz Incoherent",
            "3C": "3 MHz HD",
            "BB": "BB",
            "PC": "PC",
            "PC/BB": "PC/BB",
            "PCBB": "PC/BB",
            "U": "N/A",
        }
        self.bt_legend_dict = {
            "600": "600 kHz",
            "1200": "1200 kHz",
            "1000": "1 MHz",
            "2000": "2 MHz",
            "2400": "2.4 MHz",
            "3000": "3 MHz",
            "0": "N/U",
            "BB": "BB",
            "PC": "PC",
            "PC/BB": "PC/BB",
            "U": "U",
            "PCBB": "PC/BB",
            "1": "U",
            "Other": "U",
        }
        self.freq_color = {
            "0": "b",
            "600": "b",
            "1200": "b",
            "1000": "b",
            "2000": "b",
            "2400": "b",
            "3000": "#009933",
        }
        self.freq_marker = {
            "0": ".",
            "600": ".",
            "1200": ".",
            "1000": ".",
            "2000": ".",
            "2400": ".",
            "3000": "+",
        }
        self.wt_advanced_type_methods = {
            "cb_speed_filtered_cc": self.wt_speed_filtered_contour,
            "cb_speed_final_cc": self.wt_speed_final_contour,
            "cb_projected_cc": self.wt_projected_contour,
            "cb_vertical_cc": self.wt_vertical_contour,
            "cb_error_cc": self.wt_error_contour,
            "cb_direction_cc": self.wt_direction_contour,
            "cb_avg_corr_cc": self.wt_avg_corr_contour,
            "cb_corr_beam_cc": self.wt_corr_beam_contour,
            "cb_avg_rssi_cc": self.wt_avg_rssi_contour,
            "cb_rssi_beam_cc": self.wt_rssi_beam_contour,
            "cb_ping_type_cc": self.wt_ping_type,
            "cb_discharge_ts": self.discharge_ts,
            "cb_discharge_percent_ts": self.discharge_percent_ts,
            "cb_avg_speed_ts": self.wt_avg_speed_ts,
            "cb_projected_speed_ts": self.wt_projected_speed_ts,
            "cb_wt_beams_ts": self.wt_3beam_ts,
            "cb_wt_error_ts": self.wt_error_ts,
            "cb_wt_vert_ts": self.wt_vertical_ts,
            "cb_wt_snr_ts": self.wt_snr_ts,
            "cb_bt_boat_speed_ts": self.bt_speed_ts,
            "cb_bt_3beam_ts": self.bt_3beam_ts,
            "cb_bt_error_ts": self.bt_error_ts,
            "cb_bt_vertical_ts": self.bt_vertical_ts,
            "cb_bt_source_ts": self.bt_source_ts,
            "cb_bt_corr_ts": self.bt_corr_ts,
            "cb_bt_rssi_ts": self.bt_rssi_ts,
            "cb_gga_boat_speed_ts": self.gga_speed_ts,
            "cb_vtg_boat_speed_ts": self.vtg_speed_ts,
            "cb_gga_quality_ts": self.gga_quality_ts,
            "cb_gga_hdop_ts": self.gga_hdop_ts,
            "cb_gga_altitude_ts": self.gga_altitude_ts,
            "cb_gga_sats_ts": self.gga_sats_ts,
            "cb_gga_source_ts": self.gga_source_ts,
            "cb_vtg_source_ts": self.vtg_source_ts,
            "cb_adcp_heading_ts": self.heading_adcp_ts,
            "cb_ext_heading_ts": self.heading_external_ts,
            "cb_mag_error_ts": self.heading_mag_error_ts,
            "cb_pitch_ts": self.pitch_ts,
            "cb_roll_ts": self.roll_ts,
            "cb_beam_depths_ts": self.depths_beam_ts,
            "cb_final_depths_ts": self.depths_final_ts,
            "cb_depths_source_ts": self.depths_source_ts,
            "cb_battery_voltage_ts": self.battery_voltage_ts,
        }

    def create(
        self,
        transect,
        discharge,
        units,
        selected_types,
        flow_direction=0,
        color_map="viridis",
        x_axis_type=None,
        show_below_sl=False,
        show_unmeasured=False,
    ):
        """Create selected plots for the specified transect.

        Parameters
        ----------
        transect: TransectData
            Transect for which plots are created
        discharge: QComp
            Discharge data
        units: dict
            Units selected
        selected_types: list
            List of selected plot types
        flow_direction: float
            Flow direction to be used for projected speed plots
        color_map: str
            Name of color map to be used for color contour plots
        show_below_sl: bool
            Indicates if data should be shown below sidelobe cutoff
        x_axis_type: str
            Specifies what variable (ensemble, length or time) to be used for
            the x-axis
        show_unmeasured: bool
            Indicates if unmeasured data should be plotted in final wt contour
        """

        # Make sure a selection was made
        if len(selected_types) > 0:

            with self.wait_cursor():
                # Initialize data sources
                self.flow_direction = flow_direction
                self.transect = transect
                self.discharge = discharge

                self.show_below_sl = show_below_sl
                self.show_unmeasured = show_unmeasured

                # Set default axis
                if x_axis_type is None:
                    x_axis_type = "E"
                self.x_axis_type = x_axis_type

                # Set color map and units
                self.color_map = color_map
                self.units = units

                # Clear the plot
                self.fig.clear()

                # Determine number of subplots
                self.n_subplots = len(selected_types)
                if "cb_corr_beam_cc" in selected_types:
                    self.n_subplots += 3
                if "cb_rssi_beam_cc" in selected_types:
                    self.n_subplots += 3

                # Compute x-axis variable
                self.compute_x_axis()

                # Initialize variable for subplots
                self.ax = []
                self.annot = []
                self.data_plotted = []
                share_y = False

                # Create grid specification
                # Note: the second column of the grid is for the color bar.
                # It is blank but present even for time series
                # plots to allow the sharing of the x-axis between all plots
                self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])

                # Create first subplot
                self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))
                self.wt_advanced_type_methods[selected_types[0]]()
                # Share the y-axis between color contour plots
                if selected_types[0][-3:] == "_cc":
                    share_y = True

                # Create additional subplots as specified, sharing x axis for
                # all plots and  y axis for contour plots
                if len(selected_types) > 1:
                    for n in range(1, len(selected_types)):
                        # Figure number increased by two to account for the
                        # second column in the grid space
                        # for the colorbar
                        self.fig_no += 2
                        if share_y and selected_types[n][-3:] == "_cc":
                            self.ax.append(
                                self.fig.add_subplot(
                                    self.gs[self.fig_no],
                                    sharex=self.ax[0],
                                    sharey=self.ax[0],
                                )
                            )
                        else:
                            self.ax.append(
                                self.fig.add_subplot(
                                    self.gs[self.fig_no], sharex=self.ax[0]
                                )
                            )

                        # Call method based on link in dictionary
                        self.wt_advanced_type_methods[selected_types[n]]()

                # Adjust the spacing of the subplots
                self.fig.subplots_adjust(
                    left=0.05,
                    bottom=0.05,
                    right=0.92,
                    top=0.95,
                    wspace=0.02,
                    hspace=0.08,
                )

                # Apply the x-axis label to the bottom x-axis
                if selected_types[-1][-3:] == "_cc":
                    idx = -2
                else:
                    idx = -1

                self.ax[idx].xaxis.label.set_fontsize(12)

                self.set_x_axis(idx)

        else:
            # Clear the plot
            self.fig.clear()

        self.canvas.draw()

    def create_main_contour(
        self, transect, units, x_axis_type="E", color_map="viridis", discharge=None
    ):

        # Initialize data sources
        self.transect = transect
        self.discharge = discharge

        if discharge is not None:
            self.show_unmeasured = True
        else:
            self.show_unmeasured = False

        # Set axis type and units
        self.x_axis_type = x_axis_type
        self.units = units
        self.color_map = color_map

        # Clear the plot
        self.fig.clear()

        # Determine number of subplots
        self.n_subplots = 1

        # Compute x-axis variable, this applies units
        self.compute_x_axis()

        # Initialize variable for subplots
        self.ax = []
        self.annot = []
        self.data_plotted = []

        # Create grid specification
        # Note: the second column of the grid is for the color bar. It is
        # blank but present even for time series plots to allow the sharing
        # of the x-axis between all plots
        self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])

        self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))
        self.wt_speed_final_contour()

        # Adjust the spacing of the subplots
        self.fig.subplots_adjust(
            left=0.08, bottom=0.2, right=0.92, top=0.97, wspace=0.02, hspace=0
        )

        # Apply the x-axis label to the bottom x-axis
        idx = -2
        self.ax[idx].xaxis.label.set_fontsize(12)
        self.set_x_axis(idx)

        self.canvas.draw()

    def create_depth_tab_graphs(
        self,
        transect,
        units,
        b1=True,
        b2=True,
        b3=True,
        b4=True,
        vb=False,
        ds=False,
        avg4_final=False,
        vb_final=False,
        ds_final=False,
        final=True,
        x_axis_type="E",
    ):
        """Creates the plots for the depth tab. This approach allows zoom and
        pan to work together for both plots.

        Parameters
        ----------
        transect: TransectData
            Transect to plot
        units: dict
            Units selected
        b1: bool
            Indicates if beam 1 is plotted
        b2: bool
            Indicates if beam 2 is plotted
        b3: bool
            Indicates if beam 3 is plotted
        b4: bool
            Indicates if beam 4 is plotted
        vb: bool
            Indicates if the vertical beam is plotted
        ds: bool
            Indicates if the depth sounder is plotted
        avg4_final: bool
            Indicates if the 4-beam average cross section is plotted
        vb_final: bool
            Indicates if the vertical beam cross section is plotted
        ds_final: bool
            Indicates if the depth sounder cross section is plotted
        final: bool
            Indicates if the selected method for determing the cross section
            is plotted
        x_axis_type: str
            Specifies what variable (ensemble, length or time) to be used for
            the x-axis
        """
        with self.wait_cursor():

            # Initialize data sources
            self.transect = transect

            # Set default axis type and units
            self.x_axis_type = x_axis_type
            self.units = units

            # Clear the plot
            self.fig.clear()

            # Determine number of subplots
            self.n_subplots = 2

            # Compute x-axis variable
            self.compute_x_axis()

            # Initialize variable for subplots
            self.ax = []
            self.annot = []
            self.data_plotted = []

            # Create grid specification
            # Note: the second column of the grid is for the color bar. It
            # is blank but present even for time series
            # plots to allow the sharing of the x-axis between all plots
            self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])

            # Create first subplot
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))
            self.depths_beam_ts(b1, b2, b3, b4, vb, ds, leg=False)

            self.fig_no += 2
            # Create additional subplots as specified, sharing x axis y axis
            self.ax.append(
                self.fig.add_subplot(
                    self.gs[self.fig_no], sharex=self.ax[0], sharey=self.ax[0]
                )
            )
            self.depths_final_ts(
                avg4_final=avg4_final, vb_final=vb_final, ds_final=ds_final, final=final
            )

            # Adjust the spacing of the subplots
            self.fig.subplots_adjust(
                left=0.05, bottom=0.07, right=0.99, top=0.95, wspace=0.02, hspace=0.08
            )

            # Apply the x-axis label to the bottom x-axis
            idx = -1
            self.ax[idx].xaxis.label.set_fontsize(12)
            self.set_x_axis(idx)

        self.canvas.draw()

    def create_bt_tab_graphs(
        self,
        transect,
        units,
        beam=True,
        error=False,
        vert=False,
        other=False,
        source=False,
        bt=True,
        gga=False,
        vtg=False,
        x_axis_type="E",
    ):
        """Creates the plots for the bottom track tab.
        This approach allows zoom and pan to work together for both plots.

        Parameters
        ----------
        transect: TransectData
            Transect to plot
        units: dict
            Units selected
        beam: bool
            Indicates if number of beams is plotted
        error: bool
            Indicates if error velocity is plotted
        vert: bool
            Indicates if vertical velocity is plotted
        other: bool
            Indicates if other filter is plotted
        source: bool
            Indicates if the boat speed source is plotted
        bt: bool
            Indicates if the bottom track is plotted in shiptrack
        gga: bool
            Indicates if the gga track is plotted in the shiptrack
        vtg: bool
            Indicates if the vtg track is plotted in the shiptrack
        x_axis_type: str
            Specifies what variable (ensemble, length or time) to be used for
             the x-axis
        """
        with self.wait_cursor():
            # Initialize data sources
            self.transect = transect

            # Set x axis type and units
            self.x_axis_type = x_axis_type
            self.units = units

            # Clear the plot
            self.fig.clear()

            # Determine number of subplots
            self.n_subplots = 2

            # Compute x-axis variable
            self.compute_x_axis()

            # Initialize variable for subplots
            self.ax = []
            self.annot = []
            self.data_plotted = []

            # Create grid specification
            # Note: the second column of the grid is for the color bar.
            # It is blank but present even for time series
            # plots to allow the sharing of the x-axis between all plots
            self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])

            # Create first subplot
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))
            if beam:
                self.bt_3beam_ts()
            elif error:
                self.bt_error_ts()
            elif vert:
                self.bt_vertical_ts()
            elif other:
                self.other_ts(data=self.transect.boat_vel.bt_vel, data_color="r-")
            elif source:
                ref = getattr(self.transect.boat_vel, self.transect.boat_vel.selected)
                self.source_ts(ref, "Boat Source")

            self.fig_no += 2
            # Create boat speed subplots as specified, sharing x axis for
            # all plots
            self.ax.append(
                self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0])
            )
            if bt:
                self.bt_speed_ts(lbl="Boat speed")
            if gga:
                self.gga_speed_ts(lbl="Boat speed")
            if vtg:
                self.vtg_speed_ts(lbl="Boat speed")

            # Adjust the spacing of the subplots
            self.fig.subplots_adjust(
                left=0.05, bottom=0.07, right=0.99, top=0.95, wspace=0.02, hspace=0.08
            )

            # Apply the x-axis label to the bottom x-axis
            idx = -1
            self.ax[idx].xaxis.label.set_fontsize(12)
            self.set_x_axis(idx)

        self.canvas.draw()

    def create_gps_tab_graphs(
        self,
        transect,
        units,
        quality=True,
        altitude=False,
        hdop=False,
        n_sats=False,
        other=False,
        source=False,
        bt=True,
        gga=False,
        vtg=False,
        x_axis_type="E",
    ):
        """Creates the plots for the bottom track tab.
        This approach allows zoom and pan to work together for both plots.

        Parameters
        ----------
        transect: TransectData
            Transect to plot
        units: dict
            Units selected
        quality: bool
            Indicates if gga quality is plotted
        altitude: bool
            Indicates if gga altitude is plotted
        hdop: bool
            Indicates if gga HDOP is plotted
        n_sats: bool
            Indicates if gga number of satellites is plotted
        other: bool
            Indicates if other filter is plotted
        source: bool
            Indicates if the boat speed source is plotted
        bt: bool
            Indicates if the bottom track is plotted in shiptrack
        gga: bool
            Indicates if the gga track is plotted in the shiptrack
        vtg: bool
            Indicates if the vtg track is plotted in the shiptrack
        x_axis_type: str
            Specifies what variable (ensemble, length or time) to be used
            for the x-axis
        """
        with self.wait_cursor():

            # Initialize data sources
            self.transect = transect

            # Set x axis type and units
            self.x_axis_type = x_axis_type
            self.units = units

            # Clear the plot
            self.fig.clear()

            # Determine number of subplots
            self.n_subplots = 2

            # Compute x-axis variable
            self.compute_x_axis()

            # Initialize variable for subplots
            self.ax = []
            self.annot = []
            self.data_plotted = []

            # Create grid specification
            # Note: the second column of the grid is for the color bar. It is
            # blank but present even for time series plots to allow the sharing of
            # the x-axis between all plots
            self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])

            # Create first subplot
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))
            if quality:
                self.gga_quality_ts()
            elif altitude:
                self.gga_altitude_ts()
            elif hdop:
                self.gga_hdop_ts()
            elif n_sats:
                self.gga_sats_ts()
            elif other:
                # Select an object to use for the smooth
                if self.transect.boat_vel.selected == "gga_vel":
                    boat_gps = transect.boat_vel.gga_vel
                    data_color = "b-"
                elif self.transect.boat_vel.selected == "vtg_vel":
                    boat_gps = transect.boat_vel.vtg_vel
                    data_color = "g-"
                elif self.transect.boat_vel.vtg_vel is not None:
                    boat_gps = transect.boat_vel.vtg_vel
                    data_color = "g-"
                else:
                    boat_gps = self.transect.boat_vel.gga_vel
                    data_color = "b-"
                self.other_ts(data=boat_gps, data_color=data_color)
            elif source:
                ref = getattr(self.transect.boat_vel, self.transect.boat_vel.selected)
                self.source_ts(ref, "Boat Source")

            self.fig_no += 2
            # Create boat speed subplot as specified, sharing x axis
            self.ax.append(
                self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0])
            )
            if bt:
                self.bt_speed_ts(lbl="Boat speed")
            if gga:
                self.gga_speed_ts(lbl="Boat speed")
            if vtg:
                self.vtg_speed_ts(lbl="Boat speed")

            # Adjust the spacing of the subplots
            self.fig.subplots_adjust(
                left=0.05, bottom=0.07, right=0.99, top=0.95, wspace=0.02, hspace=0.08
            )

            # Apply the x-axis label to the bottom x-axis
            idx = -1
            self.ax[idx].xaxis.label.set_fontsize(12)
            self.set_x_axis(idx)

        self.canvas.draw()

    def create_wt_tab_graphs(
        self,
        transect,
        units,
        contour=True,
        beam=False,
        error=False,
        vert=False,
        snr=False,
        speed=False,
        x_axis_type="E",
        color_map="viridis",
        discharge=None,
    ):
        """Creates the plots for the bottom track tab.
        This approach allows zoom and pan to work together for both plots.

        Parameters
        ----------
        transect: TransectData
            Transect to plot
        units: dict
            Units selected
        contour: bool
            Indicates if filtered contour is plotted
        beam: bool
            Indicates if number of beams is plotted
        error: bool
            Indicates if error velocity is plotted
        vert: bool
            Indicates if vertical velocity is plotted
        snr: bool
            Indicates if SNR is plotted
        speed: bool
            Indicates if the average water speed source is plotted
        x_axis_type: str
            Specifies what variable (ensemble, length or time) to be used for
            the x-axis
        color_map: str
            Name of color map to be used for color contour plots
        discharge: QComp
            Object of QComp
        """
        with self.wait_cursor():

            # Initialize data sources
            self.transect = transect
            self.discharge = discharge

            if discharge is not None:
                self.show_unmeasured = True
            else:
                self.show_unmeasured = False

            # Set axis type and units
            self.x_axis_type = x_axis_type
            self.units = units
            self.color_map = color_map

            # Clear the plot
            self.fig.clear()

            # Determine number of subplots
            self.n_subplots = 2

            # Compute x-axis variable
            self.compute_x_axis()

            # Initialize variable for subplots
            self.ax = []
            self.annot = []
            self.data_plotted = []

            # Create grid specification
            # Note: the second column of the grid is for the color bar. It is
            # blank but present even for time series plots to allow the sharing
            # of the x-axis between all plots
            self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])

            # Create first subplot
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))
            if contour:
                self.wt_speed_filtered_contour()
            elif beam:
                self.wt_3beam_ts()
            elif error:
                self.wt_error_ts()
            elif vert:
                self.wt_vertical_ts()
            elif snr:
                self.wt_snr_ts()
            elif speed:
                self.wt_avg_speed_ts()

            self.fig_no += 2
            # Create additional subplots as specified, sharing x axis for all
            # plots and also y axis for contour plots
            if contour:
                self.ax.append(
                    self.fig.add_subplot(
                        self.gs[self.fig_no], sharex=self.ax[0], sharey=self.ax[0]
                    )
                )
            else:
                self.ax.append(
                    self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0])
                )
            self.wt_speed_final_contour()

            # Adjust the spacing of the subplots
            self.fig.subplots_adjust(
                left=0.05, bottom=0.07, right=0.92, top=0.95, wspace=0.02, hspace=0.08
            )

            # Apply the x-axis label to the bottom x-axis
            idx = -2
            self.ax[idx].xaxis.label.set_fontsize(12)
            self.set_x_axis(idx)

        self.canvas.draw()

    def create_edge_contour(
        self, transect, units, x_axis_type, color_map, n_ensembles, edge
    ):
        """Create edge contour plots.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        units: dict
            Dictionary of units labels and conversions
        x_axis_type: str
            Indicates type of x-axis (E, L, T)
        color_map: str
            Indicates colormap to use (viridis or jet)
        n_ensembles: int
            Number of ensembles in the edge
        edge: str
            Edge, Left or Right
        """

        with self.wait_cursor():

            # Initialize data sources
            self.transect = transect

            # Set axis type and units
            self.x_axis_type = x_axis_type
            self.units = units
            self.color_map = color_map

            # Clear the plot
            self.fig.clear()

            # Determine number of subplots
            self.n_subplots = 1

            # Compute x-axis variable
            self.compute_x_axis()

            # Initialize variable for subplots
            self.ax = []
            self.annot = []
            self.data_plotted = []

            # Create grid specification
            # Note: the second column of the grid is for the color bar. It is
            # blank but present even for time series plots to allow the sharing
            # of the x-axis between all plots
            self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])

            # Create first subplot
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))

            # Compute water speed for each cell
            water_u = self.transect.w_vel.u_processed_mps[
                :, self.transect.in_transect_idx
            ]
            water_v = self.transect.w_vel.v_processed_mps[
                :, self.transect.in_transect_idx
            ]
            water_speed = np.sqrt(water_u**2 + water_v**2)
            water_speed[
                np.logical_not(self.transect.w_vel.valid_data[0, :, :])
            ] = np.nan

            # Set the 1-dimensional x-axis data based on selected x-axis type.
            # Timestamp must be used for time
            if self.x_axis_type == "T":
                x_1d = np.copy(self.x_timestamp)
            else:
                x_1d = np.copy(self.x)

            # Compute data for contour plot
            (
                x_plt,
                cell_plt,
                data_plt,
                ensembles,
                depth,
                self.x,
            ) = self.contour_data_prep(
                transect=self.transect,
                data=water_speed,
                x_1d=x_1d,
                n_ensembles=n_ensembles,
                edge=edge,
            )

            # Plot data
            self.plt_contour(
                x_plt_in=x_plt,
                cell_plt_in=cell_plt,
                data_plt_in=data_plt,
                x=self.x,
                depth=depth,
                data_units=(
                    self.units["V"],
                    "Filtered \n Speed " + self.units["label_V"],
                ),
                n_ensembles=n_ensembles,
                edge=edge,
            )

            # Apply the x-axis label to the bottom x-axis
            idx = -2
            self.ax[idx].xaxis.label.set_fontsize(12)

            self.set_x_axis(idx)

            self.canvas.draw()

    def set_x_axis(self, idx):
        """Configures the x-axis.

        Parameters
        ----------
        idx = int
            Axis number to apply x-axis configuration to.
        """

        # x-axis is length
        if self.x_axis_type == "L":
            if self.expanded_x is not None:
                x = self.expanded_x
            else:
                x = self.x

            x_max = np.nanmax(x) * self.units["L"]
            x_min = np.nanmin(x) * self.units["L"]

            axis_buffer = x_max - x_min
            if self.transect.start_edge == "Right":
                self.ax[idx].invert_xaxis()
                self.ax[idx].set_xlim(
                    right=x_min - axis_buffer * 0.02,
                    left=x_max + axis_buffer * 0.02,
                )
            else:
                self.ax[idx].set_xlim(
                    left=x_min - axis_buffer * 0.02,
                    right=x_max + axis_buffer * 0.02,
                )
            self.ax[idx].set_xlabel(self.canvas.tr("Length " + self.units["label_L"]))

        # x-axis is ensembles
        elif self.x_axis_type == "E":
            e_rng = np.nanmax(self.x) - np.nanmin(self.x)
            e_max = np.nanmax([np.nanmax(self.x) + 1, np.nanmax(self.x) + e_rng * 0.02])
            e_min = np.nanmin([np.nanmin(self.x) - 1, np.nanmin(self.x) - e_rng * 0.02])
            if self.transect.start_edge == "Right":
                self.ax[idx].invert_xaxis()
                self.ax[idx].set_xlim(right=e_min, left=e_max)
            else:
                self.ax[idx].set_xlim(left=e_min, right=e_max)
            self.ax[idx].set_xlabel(self.canvas.tr("Ensembles"))

        # x-axis is time
        elif self.x_axis_type == "T":
            axis_buffer = (self.x_timestamp[-1] - self.x_timestamp[0]) * 0.02
            if self.transect.start_edge == "Right":
                self.ax[idx].invert_xaxis()
                self.ax[idx].set_xlim(
                    right=datetime.utcfromtimestamp(self.x_timestamp[0] - axis_buffer),
                    left=datetime.utcfromtimestamp(self.x_timestamp[-1] + axis_buffer),
                )
            else:
                self.ax[idx].set_xlim(
                    left=datetime.utcfromtimestamp(self.x_timestamp[0] - axis_buffer),
                    right=datetime.utcfromtimestamp(self.x_timestamp[-1] + axis_buffer),
                )
            date_form = DateFormatter("%H:%M:%S")
            self.ax[idx].xaxis.set_major_formatter(date_form)
            self.ax[idx].set_xlabel(self.canvas.tr("Time"))

    def wt_avg_corr_contour(self):
        """Creates average correlation contour plot."""

        # Compute average of correlation data for each cel
        data = np.nanmean(self.transect.w_vel.corr, axis=0)
        if not self.show_below_sl:
            data[np.logical_not(self.transect.w_vel.cells_above_sl)] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, data, x_1d=x_1d
        )

        # Plot the data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(1, "Correlation \n (counts)"),
        )

    def wt_avg_rssi_contour(self):
        """Creates average return signal strength or SNR contour plot."""

        # Compute mean signal strength for each cell
        data = np.nanmean(self.transect.w_vel.rssi, axis=0)
        if not self.show_below_sl:
            data[np.logical_not(self.transect.w_vel.cells_above_sl)] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, data, x_1d=x_1d
        )

        # Create label based on manufacturer
        if self.transect.adcp.manufacturer == "TRDI":
            data_label = "Intensity \n (counts)"
        elif self.transect.adcp.manufacturer == "SonTek":
            data_label = "SNR (dB)"
        else:
            data_label = "Intensity"

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(1, data_label),
        )

    def wt_avg_speed_ts(self):
        """Create average water speed time series plot."""

        # Compute mean water speed for each ensemble using a weighted
        # average based on depth cell size
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)

        weight = depth_selected.depth_cell_size_m[:, self.transect.in_transect_idx]
        weight[np.isnan(water_u)] = np.nan

        mean_u = np.nansum(water_u * weight, axis=0) / np.nansum(weight, axis=0)
        mean_v = np.nansum(water_v * weight, axis=0) / np.nansum(weight, axis=0)
        avg_speed = np.sqrt(mean_u**2 + mean_v**2)

        # Plot data
        data_units = (self.units["V"], "Water speed " + self.units["label_V"])
        self.plt_timeseries(data=avg_speed, data_units=data_units, ax=self.ax[-1])

    def wt_corr_beam_contour(self):
        """Create contour plots of the correlation in each beam."""

        # Create data to be plotted
        data_all = np.copy(self.transect.w_vel.corr)
        if not self.show_below_sl:
            for n in range(data_all.shape[0]):
                data_all[n, np.logical_not(self.transect.w_vel.cells_above_sl)] = np.nan

        # Compute the minimum and maximum limits based on all the correlations
        # so each beam has the same color scale
        data_limits = [np.nanmin(data_all), np.nanmax(data_all)]

        # Get data for beam 1
        data = data_all[0, :, :]

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, data, x_1d=x_1d
        )

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(1, "Beam 1 Corr. \n (counts)"),
            data_limits=data_limits,
        )

        # Prepare and plot beams 2-4
        for n in range(1, 4):
            # Figure number increases by 2 to account for 2nd column in
            # gridspec used for color bar
            self.fig_no += 2

            # Add subplot
            self.ax.append(
                self.fig.add_subplot(
                    self.gs[self.fig_no], sharex=self.ax[0], sharey=self.ax[0]
                )
            )

            # Get data for beam n+1
            data = data_all[n, :, :]

            # Compute data for contour plot
            (
                x_plt,
                cell_plt,
                data_plt,
                ensembles,
                depth,
                self.x,
            ) = self.contour_data_prep(self.transect, data, x_1d=x_1d)

            # Plot data
            self.plt_contour(
                x_plt_in=x_plt,
                cell_plt_in=cell_plt,
                data_plt_in=data_plt,
                x=self.x,
                depth=depth,
                data_units=(1, "Beam " + str(n + 1) + " Corr. \n (counts)"),
                data_limits=data_limits,
            )

    def wt_direction_contour(self):
        """Create flow direction contour plot."""

        # Compute flow direction using discharge weighting
        u_water = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        v_water = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_dir = np.arctan2(u_water, v_water) * 180 / np.pi
        water_dir[water_dir < 0] = water_dir[water_dir < 0] + 360

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, water_dir, x_1d=x_1d
        )

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(1, "Water Direction \n (deg)"),
        )

    def discharge_ts(self):
        """Create cumulative discharge time series by ensemble."""

        # Prepare data so that data will plot from left bank to right bank
        if self.transect.start_edge == "Right":
            q_ts = (
                self.discharge.top_ens
                + self.discharge.middle_ens
                + self.discharge.bottom_ens
            )
            q_ts = np.nancumsum(q_ts)
            q_ts[0] = q_ts[0] + self.discharge.right
            q_ts[-1] = q_ts[-1] + self.discharge.left
        else:
            q_ts = (
                self.discharge.top_ens
                + self.discharge.middle_ens
                + self.discharge.bottom_ens
            )
            q_ts = np.nancumsum(q_ts)
            q_ts[0] = q_ts[0] + self.discharge.left
            q_ts[-1] = q_ts[-1] + self.discharge.right

        # Plot data
        data_units = (self.units["Q"], "Discharge " + self.units["label_Q"])
        self.plt_timeseries(data=q_ts, data_units=data_units, ax=self.ax[-1])

    def discharge_percent_ts(self):
        """Create plot of cumulative percent discharge by ensemble."""

        # Prepare data so that data will plot from left bank to right bank
        if self.transect.start_edge == "Right":
            q_ts = (
                self.discharge.top_ens
                + self.discharge.middle_ens
                + self.discharge.bottom_ens
            )
            q_ts = np.nancumsum(q_ts)
            q_ts[0] = q_ts[0] + self.discharge.right
            q_ts[-1] = q_ts[-1] + self.discharge.left
        else:
            q_ts = (
                self.discharge.top_ens
                + self.discharge.middle_ens
                + self.discharge.bottom_ens
            )
            q_ts = np.nancumsum(q_ts)
            q_ts[0] = q_ts[0] + self.discharge.left
            q_ts[-1] = q_ts[-1] + self.discharge.right

        # Compute percent of total
        q_ts_per = (q_ts / self.discharge.total) * 100

        # Plot data
        data_units = (1, "Discharge (%)")
        self.plt_timeseries(data=q_ts_per, data_units=data_units, ax=self.ax[-1])

    def wt_error_contour(self):
        """Create contour plot of error velocities."""

        # Get data
        data = self.transect.w_vel.d_mps
        data[np.logical_not(self.transect.w_vel.cells_above_sl)] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, data, x_1d=x_1d
        )

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(self.units["V"], "Error Velocity \n" + self.units["label_V"]),
        )

    def wt_projected_contour(self):
        """Create contour plot of water speed projected in flow direction."""

        # Compute projected water speed
        unit_vector = np.array(
            [[sind(self.flow_direction)], [cosd(self.flow_direction)]]
        )
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        projected_speed = unit_vector[0] * water_u + unit_vector[1] * water_v

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, projected_speed, x_1d=x_1d
        )

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(self.units["V"], "Projected \n Speed" + self.units["label_V"]),
        )

    def wt_projected_speed_ts(self):
        """Create time series plot of projected water speed."""

        # Compute projected water speed for each cell
        unit_vector = np.array(
            [[sind(self.flow_direction)], [cosd(self.flow_direction)]]
        )
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        projected_speed = unit_vector[0] * water_u + unit_vector[1] * water_v

        # Compute the mean projected speed in each ensemble using depth cell
        # size weighting
        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        weight = depth_selected.depth_cell_size_m[:, self.transect.in_transect_idx]
        weight[np.isnan(projected_speed)] = np.nan
        avg_speed = np.nansum(projected_speed * weight, axis=0) / np.nansum(
            weight, axis=0
        )

        # Plot data
        data_units = (self.units["V"], "Projected Speed " + self.units["label_V"])
        self.plt_timeseries(data=avg_speed, data_units=data_units, ax=self.ax[-1])

    def wt_rssi_beam_contour(self):
        """Create contour plot of the signal intensity for each beam."""

        # Set label and units based on data available by manufacturer
        if self.transect.adcp.manufacturer == "TRDI":
            data_label = "\n RSSI (counts)"
        elif self.transect.adcp.manufacturer == "SonTek":
            data_label = "\n SNR (dB)"
        else:
            data_label = "\n Intensity"

        # Create data to be plotted
        data_all = np.copy(self.transect.w_vel.rssi)
        if not self.show_below_sl:
            for n in range(data_all.shape[0]):
                data_all[n, np.logical_not(self.transect.w_vel.cells_above_sl)] = np.nan

        # Determine limits for all data so a common scale can be used for all
        # 4 plots
        data_limits = [np.nanmin(data_all), np.nanmax(data_all)]

        # Get data for beam 1
        data = data_all[0, :, :]

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, data, x_1d=x_1d
        )

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(1, "Beam 1" + data_label),
            data_limits=data_limits,
        )

        # Prepare and plot data for beams 2-4
        for n in range(1, 4):
            self.fig_no += 2
            self.ax.append(
                self.fig.add_subplot(
                    self.gs[self.fig_no], sharex=self.ax[0], sharey=self.ax[0]
                )
            )
            data = data_all[n, :, :]
            (
                x_plt,
                cell_plt,
                data_plt,
                ensembles,
                depth,
                self.x,
            ) = self.contour_data_prep(self.transect, data, x_1d=x_1d)
            self.plt_contour(
                x_plt_in=x_plt,
                cell_plt_in=cell_plt,
                data_plt_in=data_plt,
                x=self.x,
                depth=depth,
                data_units=(1, "Beam " + str(n + 1) + data_label),
                data_limits=data_limits,
            )

    def wt_speed_filtered_contour(self):
        """Create contour of water speed with no interpolation for invalid
        water data.
        """

        # Compute water speed for each cell
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_speed = np.sqrt(water_u**2 + water_v**2)
        water_speed[np.logical_not(self.transect.w_vel.valid_data[0, :, :])] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, water_speed, x_1d=x_1d
        )

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(self.units["V"], "Filtered \n Speed " + self.units["label_V"]),
        )

    def wt_speed_final_contour(self):
        """Contour plot of water speed with interpolation for invalid data."""

        # Compute water speed for each cell
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_speed = np.sqrt(water_u**2 + water_v**2)

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # If discharge data are provided, expanded data with extrapolated values
        if self.show_unmeasured and self.x_axis_type == "L":
            (
                expanded_cell_size,
                expanded_cell_depth,
                expanded_water_speed,
            ) = self.add_extrapolated_topbot(water_speed)
            # Compute data for contour plot
            (
                x_plt,
                cell_plt,
                data_plt,
                ensembles,
                depth,
                self.x,
            ) = self.contour_data_prep(
                self.transect,
                expanded_water_speed,
                x_1d=x_1d,
                cell_depth=expanded_cell_depth,
                cell_size=expanded_cell_size,
            )
        else:
            # Compute data for contour plot
            (
                x_plt,
                cell_plt,
                data_plt,
                ensembles,
                depth,
                self.x,
            ) = self.contour_data_prep(self.transect, water_speed, x_1d=x_1d)

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(
                self.units["V"],
                "Interpolated \n Speed " + self.units["label_V"],
            ),
            show_edge_speed=self.show_unmeasured,
        )

    def wt_vertical_contour(self):
        """Create contour plot of vertical velocities."""

        # Get data
        data = np.copy(self.transect.w_vel.w_mps)
        data[np.logical_not(self.transect.w_vel.cells_above_sl)] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, data, x_1d=x_1d
        )

        # Plot data
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(
                self.units["V"],
                "Vertical \n Velocity" + self.units["label_V"],
            ),
        )

    def wt_ping_type(self):
        """Create plot showing ping type."""

        # Get data
        data = np.copy(self.transect.w_vel.w_mps)
        data[np.logical_not(self.transect.w_vel.cells_above_sl)] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type.
        # Timestamp must be used for time
        if self.x_axis_type == "T":
            x_1d = np.copy(self.x_timestamp)
        else:
            x_1d = np.copy(self.x)

        ping_type = self.transect.w_vel.ping_type
        p_types = np.unique(ping_type)
        ping_name = {}
        n = 0
        for p_type in p_types:
            ping_name[n] = self.ping_type_long_name[p_type]
            data[ping_type == p_type] = n
            n = n + 1

        data[np.logical_not(self.transect.w_vel.cells_above_sl)] = np.nan

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth, self.x = self.contour_data_prep(
            self.transect, data, x_1d=x_1d
        )

        # Plot data
        cmap = self.color_map
        self.ping_name = ping_name
        self.plt_contour(
            x_plt_in=x_plt,
            cell_plt_in=cell_plt,
            data_plt_in=data_plt,
            x=self.x,
            depth=depth,
            data_units=(1, "WT Ping Type"),
            cmap_in=cmap,
            ping_name=ping_name,
            n_names=len(p_types),
        )

        self.data_plotted[-2]["type"] = "ping type"

    def wt_3beam_ts(self):
        """Create time series plot of WT beams used."""

        # Determine number of beams for each ensemble
        wt_temp = copy.deepcopy(self.transect.w_vel)
        wt_temp.filter_beam(4)
        valid_4beam = wt_temp.valid_data[5, :, :].astype(int)
        beam_data = np.copy(valid_4beam).astype(int)
        beam_data[valid_4beam == 1] = 4
        beam_data[wt_temp.valid_data[6, :, :]] = 4
        beam_data[valid_4beam == 0] = 3
        beam_data[np.logical_not(self.transect.w_vel.valid_data[1, :, :])] = -999

        # Configure plot settings
        hold_x = np.copy(self.x)
        self.x = np.tile(self.x, (self.transect.w_vel.valid_data[0, :, :].shape[0], 1))
        invalid = np.logical_and(
            np.logical_not(self.transect.w_vel.valid_data[5, :, :]),
            self.transect.w_vel.cells_above_sl,
        )
        fmt = [
            {"color": "b", "linestyle": "", "marker": "."},
            {"color": "r", "linestyle": "", "marker": "o", "markerfacecolor": "none"},
        ]
        data_units = (1, "WT Number of Beams ")
        data_mask = [[], invalid]

        # Plot data
        self.plt_timeseries(
            data=beam_data,
            data_units=data_units,
            ax=self.ax[-1],
            data_2=beam_data,
            data_mask=data_mask,
            fmt=fmt,
        )
        self.x = hold_x

        # Format axis
        self.ax[-1].set_ylim(top=4.5, bottom=-0.5)

    def wt_error_ts(self):
        """Create time series plot of WT error velocity."""

        # Plot error velocity
        invalid = np.logical_and(
            np.logical_not(self.transect.w_vel.valid_data[2, :, :]),
            self.transect.w_vel.cells_above_sl,
        )

        # Data to plot
        hold_x = np.copy(self.x)
        self.x = np.tile(self.x, (self.transect.w_vel.valid_data[0, :, :].shape[0], 1))
        self.x = self.x[self.transect.w_vel.cells_above_sl]
        y_data = self.transect.w_vel.d_mps[self.transect.w_vel.cells_above_sl]

        data_units = (self.units["V"], "WT Error Vel " + self.units["label_V"])

        # Setup ping type
        if self.transect.w_vel.ping_type.size > 1:
            ping_type = self.transect.w_vel.ping_type[
                self.transect.w_vel.cells_above_sl
            ]
            ping_type_used = np.unique(ping_type)

            p_types = np.unique(ping_type)

            data_mask = []
            fmt = []
            for pt in ping_type_used:
                data_mask.append(ping_type == pt)
                fmt.append(
                    {
                        "marker": self.p_type_marker[pt],
                        "linestyle": "",
                        "mfc": self.p_type_color[pt],
                        "mec": self.p_type_color[pt],
                    }
                )

            data_mask.append(invalid[self.transect.w_vel.cells_above_sl])
            fmt.append(
                {"marker": "o", "color": "r", "ms": 8, "linestyle": "", "mfc": "none"}
            )

            # Plot
            self.plt_timeseries(
                data=None,
                data_units=data_units,
                ax=self.ax[-1],
                data_2=y_data,
                data_mask=data_mask,
                fmt=fmt,
            )

        else:
            fmt = [
                {
                    "marker": ".",
                    "color": "b",
                    "ms": 8,
                    "linestyle": "",
                    "mfc": "b",
                    "mec": "b",
                },
                {"marker": "o", "color": "r", "ms": 8, "linestyle": "", "mfc": "none"},
            ]
            p_types = ["U"]
            data_mask = [[], invalid]

            # Plot first ping type
            self.plt_timeseries(
                data=y_data,
                data_units=data_units,
                ax=self.ax[-1],
                data_2=y_data,
                data_mask=data_mask,
                fmt=fmt,
            )
        self.x = hold_x

        # Create legend
        legend_txt = []
        for p_type in p_types:
            legend_txt.append(self.wt_legend_dict[p_type])

        clean_legend = []
        for item in legend_txt:
            if item not in clean_legend:
                clean_legend.append(item)

        self.ax[-1].legend(clean_legend)

    def wt_vertical_ts(self):
        """Create time series plot of WT vertical velocity."""

        # Plot vertical velocity
        invalid = np.logical_and(
            np.logical_not(self.transect.w_vel.valid_data[3, :, :]),
            self.transect.w_vel.cells_above_sl,
        )

        # Data to plot
        hold_x = np.copy(self.x)
        self.x = np.tile(self.x, (self.transect.w_vel.valid_data[0, :, :].shape[0], 1))
        self.x = self.x[self.transect.w_vel.cells_above_sl]
        y_data = (
            self.transect.w_vel.w_mps[self.transect.w_vel.cells_above_sl]
        )

        data_units = (self.units["V"], "WT Vert. Vel " + self.units["label_V"])

        # Setup ping type
        if self.transect.w_vel.ping_type.size > 1:
            ping_type = self.transect.w_vel.ping_type[
                self.transect.w_vel.cells_above_sl
            ]
            ping_type_used = np.unique(ping_type)

            p_types = np.unique(ping_type)

            data_mask = []
            fmt = []
            for pt in ping_type_used:
                data_mask.append(ping_type == pt)
                fmt.append(
                    {
                        "marker": self.p_type_marker[pt],
                        "linestyle": "",
                        "mfc": self.p_type_color[pt],
                        "mec": self.p_type_color[pt],
                    }
                )

            data_mask.append(invalid[self.transect.w_vel.cells_above_sl])
            fmt.append(
                {"marker": "o", "color": "r", "ms": 8, "linestyle": "", "mfc": "none"}
            )

            # Plot
            self.plt_timeseries(
                data=None,
                data_units=data_units,
                ax=self.ax[-1],
                data_2=y_data,
                data_mask=data_mask,
                fmt=fmt,
            )

        else:
            fmt = [
                {
                    "marker": ".",
                    "color": "b",
                    "ms": 8,
                    "linestyle": "",
                    "mfc": "b",
                    "mec": "b",
                },
                {"marker": "o", "color": "r", "ms": 8, "linestyle": "", "mfc": "none"},
            ]
            p_types = ["U"]
            data_mask = [[], invalid]

            # Plot first ping type
            self.plt_timeseries(
                data=y_data,
                data_units=data_units,
                ax=self.ax[-1],
                data_2=y_data,
                data_mask=data_mask,
                fmt=fmt,
            )
        self.x = hold_x

        # Create legend
        legend_txt = []
        for p_type in p_types:
            legend_txt.append(self.wt_legend_dict[p_type])

        clean_legend = []
        for item in legend_txt:
            if item not in clean_legend:
                clean_legend.append(item)

        self.ax[-1].legend(clean_legend)

    def wt_snr_ts(self):
        """Create time series plot of WT SNR range."""

        # Plot vertical velocity
        invalid = np.logical_and(
            np.logical_not(self.transect.w_vel.valid_data[7, :, :]),
            self.transect.w_vel.cells_above_sl,
        )[0, :]

        # Data to plot
        y_data = self.transect.w_vel.snr_rng
        data_units = (1, "WT SNR Range (dB)")

        # Setup ping type
        if self.transect.w_vel.ping_type.size > 1:
            ping_type = self.transect.w_vel.ping_type[0, :]
            ping_type_used = np.unique(ping_type)

            p_types = np.unique(ping_type)

            data_mask = []
            fmt = []
            for pt in ping_type_used:
                data_mask.append(ping_type == pt)
                fmt.append(
                    {
                        "marker": self.p_type_marker[pt],
                        "linestyle": "",
                        "mfc": self.p_type_color[pt],
                        "mec": self.p_type_color[pt],
                    }
                )

            data_mask.append(invalid)
            fmt.append(
                {"marker": "o", "color": "r", "ms": 8, "linestyle": "", "mfc": "none"}
            )

            # Plot
            self.plt_timeseries(
                data=None,
                data_units=data_units,
                ax=self.ax[-1],
                data_2=y_data,
                data_mask=data_mask,
                fmt=fmt,
            )

        else:
            fmt = [
                {
                    "marker": ".",
                    "color": "b",
                    "ms": 8,
                    "linestyle": "",
                    "mfc": "b",
                    "mec": "b",
                },
                {"marker": "o", "color": "r", "ms": 8, "linestyle": "", "mfc": "none"},
            ]
            p_types = ["U"]
            data_mask = [[], invalid]

            # Plot first ping type
            self.plt_timeseries(
                data=y_data,
                data_units=data_units,
                ax=self.ax[-1],
                data_2=y_data,
                data_mask=data_mask,
                fmt=fmt,
            )

        # Create legend
        legend_txt = []
        for p_type in p_types:
            legend_txt.append(self.wt_legend_dict[p_type])

        clean_legend = []
        for item in legend_txt:
            if item not in clean_legend:
                clean_legend.append(item)

        self.ax[-1].legend(clean_legend)

    def bt_speed_ts(self, lbl="BT Speed"):
        """Create time series plot of BT speed."""

        # Prepare data
        data = np.sqrt(
            self.transect.boat_vel.bt_vel.u_processed_mps**2
            + self.transect.boat_vel.bt_vel.v_processed_mps**2
        )
        invalid = np.logical_not(self.transect.boat_vel.bt_vel.valid_data)
        data_invalid = np.sqrt(
            self.transect.boat_vel.bt_vel.u_mps**2
            + self.transect.boat_vel.bt_vel.v_mps**2
        )
        data_invalid[np.isnan(data_invalid)] = 0

        # Specify format
        fmt = [
            {"color": "r", "linestyle": "-"},
            {"color": "k", "linestyle": "", "marker": "$O$"},
            {"color": "k", "linestyle": "", "marker": "$E$"},
            {"color": "k", "linestyle": "", "marker": "$V$"},
            {"color": "k", "linestyle": "", "marker": "$S$"},
            {"color": "k", "linestyle": "", "marker": "$B$"},
        ]

        data_units = (self.units["V"], lbl + " " + self.units["label_V"])
        self.plt_timeseries(
            data=data,
            data_units=data_units,
            ax=self.ax[-1],
            data_2=data_invalid,
            data_mask=invalid,
            fmt=fmt,
        )

    def bt_3beam_ts(self):
        """Create time series plot of BT number of beams."""

        # Determine number of beams for each ensemble
        bt_temp = copy.deepcopy(self.transect.boat_vel.bt_vel)
        bt_temp.filter_beam(4)
        valid_4beam = bt_temp.valid_data[5, :].astype(int)
        data = np.copy(valid_4beam).astype(int)
        data[valid_4beam == 1] = 4
        data[valid_4beam == 0] = 3
        data[np.logical_not(self.transect.boat_vel.bt_vel.valid_data[1, :])] = 0

        # Configure plot settings
        invalid = np.logical_not(
            self.transect.boat_vel.bt_vel.valid_data[5, :]
        ).tolist()
        fmt = [
            {"color": "b", "linestyle": "", "marker": "."},
            {"color": "r", "linestyle": "", "marker": "o", "markerfacecolor": "none"},
        ]
        data_units = (1, "Number of Beams ")
        data_mask = [[], invalid]

        # Plot data
        self.plt_timeseries(
            data=data,
            data_units=data_units,
            ax=self.ax[-1],
            data_2=data,
            data_mask=data_mask,
            fmt=fmt,
        )
        self.ax[-1].set_ylim(top=4.5, bottom=-0.5)

    def bt_error_ts(self):
        """Create time series plot of BT error velocity."""

        # Plot error velocity
        y_data = self.transect.boat_vel.bt_vel.d_mps
        invalid = np.logical_not(
            self.transect.boat_vel.bt_vel.valid_data[2, :]
        ).tolist()
        data_units = (self.units["V"], "BT Error Vel " + self.units["label_V"])

        # Specify format
        if self.transect.boat_vel.bt_vel.ping_type is None:
            freq_used = (
                np.unique(self.transect.boat_vel.bt_vel.frequency_khz)
                .astype(int)
                .astype(str)
            )
            freq_ensembles = self.transect.boat_vel.bt_vel.frequency_khz.astype(
                int
            ).astype(str)
            marker_dict = self.freq_marker
            color_dict = self.freq_color
        else:
            freq_used = np.unique(self.transect.boat_vel.bt_vel.ping_type)

            freq_ensembles = self.transect.boat_vel.bt_vel.ping_type
            marker_dict = self.p_type_marker
            color_dict = self.p_type_color

        # Create data mask
        data_mask = []
        fmt = []
        for freq in freq_used:

            data_mask.append(freq_ensembles == freq)
            fmt.append(
                {
                    "marker": marker_dict[freq],
                    "linestyle": "",
                    "mfc": color_dict[freq],
                    "mec": color_dict[freq],
                }
            )
        data_mask.append(invalid)
        fmt.append(
            {"marker": "o", "color": "r", "ms": 8, "linestyle": "", "mfc": "none"}
        )

        self.plt_timeseries(
            data=None,
            data_units=data_units,
            ax=self.ax[-1],
            data_2=y_data,
            data_mask=data_mask,
            fmt=fmt,
        )

        # Create legend
        legend_txt = []
        for freq in freq_used:
            legend_txt.append(self.bt_legend_dict[freq])

        clean_legend = []
        for item in legend_txt:
            if item not in clean_legend:
                clean_legend.append(item)

        self.ax[-1].legend(clean_legend)

    def bt_vertical_ts(self):
        """Create time series plot of BT vertical velocity."""

        # Get data
        y_data = self.transect.boat_vel.bt_vel.w_mps
        invalid = np.logical_not(
            self.transect.boat_vel.bt_vel.valid_data[3, :]
        ).tolist()
        data_units = (self.units["V"], "BT Vertical Vel " + self.units["label_V"])

        # Assign ping type if available
        if self.transect.boat_vel.bt_vel.ping_type is None:
            freq_used = (
                np.unique(self.transect.boat_vel.bt_vel.frequency_khz)
                .astype(int)
                .astype(str)
            )
            freq_ensembles = self.transect.boat_vel.bt_vel.frequency_khz.astype(
                int
            ).astype(str)
            marker_dict = self.freq_marker
            color_dict = self.freq_color
        else:
            freq_used = np.unique(self.transect.boat_vel.bt_vel.ping_type)
            freq_ensembles = self.transect.boat_vel.bt_vel.ping_type
            marker_dict = self.p_type_marker
            color_dict = self.p_type_color

        # Construct data formats
        data_mask = []
        fmt = []
        for freq in freq_used:
            data_mask.append(freq_ensembles == freq)
            fmt.append(
                {
                    "marker": marker_dict[freq],
                    "linestyle": "",
                    "mfc": color_dict[freq],
                    "mec": color_dict[freq],
                }
            )
        data_mask.append(invalid)
        fmt.append(
            {"marker": "o", "color": "r", "ms": 8, "linestyle": "", "mfc": "none"}
        )

        # Plot data
        self.plt_timeseries(
            data=None,
            data_units=data_units,
            ax=self.ax[-1],
            data_2=y_data,
            data_mask=data_mask,
            fmt=fmt,
        )

        # Create legend
        legend_txt = []
        for freq in freq_used:
            legend_txt.append(self.bt_legend_dict[freq])
        clean_legend = []
        for item in legend_txt:
            if item not in clean_legend:
                clean_legend.append(item)

        self.ax[-1].legend(clean_legend)

    def bt_source_ts(self):
        """Create time series plot of BT source."""
        self.source_ts(self.transect.boat_vel.bt_vel, "BT Source")

    def bt_corr_ts(self):
        """Plot bottom track correlation."""

        data = self.transect.boat_vel.bt_vel.corr
        data_units = (1, "Corr. (cnts)")

        # Compute max and min
        max_data = np.nanmax(np.nanmax(data))
        if np.isnan(max_data):
            max_data = 255
        min_data = np.nanmin(np.nanmin(data))
        if np.isnan(min_data):
            min_data = 0

        # Plot beam 1 using mask to identify invalid data
        fmt = [
            {
                "color": "k",
                "linestyle": "-",
                "marker": "o",
                "markersize": 4,
                "label": "B1",
            }
        ]
        self.plt_timeseries(
            data=data[0, :],
            data_units=data_units,
            ax=self.ax[-1],
            fmt=fmt,
            set_annot=True,
        )

        # Plot beam 2 using mask to identify invalid data
        fmt = [
            {
                "color": "#005500",
                "linestyle": "-",
                "marker": "o",
                "markersize": 4,
                "label": "B2",
            }
        ]
        self.plt_timeseries(
            data=data[1, :],
            data_units=data_units,
            ax=self.ax[-1],
            fmt=fmt,
            set_annot=False,
        )

        # Plot beam 3 using mask to identify invalid data
        fmt = [
            {
                "color": "b",
                "linestyle": "-",
                "marker": "o",
                "markersize": 4,
                "label": "B3",
            }
        ]
        self.plt_timeseries(
            data=data[2, :],
            data_units=data_units,
            ax=self.ax[-1],
            fmt=fmt,
            set_annot=False,
        )

        # Plot beam 4 using mask to identify invalid data
        fmt = [
            {
                "color": "#aa5500",
                "linestyle": "-",
                "marker": "o",
                "markersize": 4,
                "label": "B4",
            }
        ]
        self.plt_timeseries(
            data=data[3, :],
            data_units=data_units,
            ax=self.ax[-1],
            fmt=fmt,
            set_annot=False,
        )

        # Show legend
        self.ax[-1].legend()

        # Configure y axis
        self.ax[-1].set_ylim(
            top=np.ceil(max_data * 1.02), bottom=np.floor(min_data * 1.02)
        )

    def bt_rssi_ts(self):
        """Plot bottom track intensity."""

        data = self.transect.boat_vel.bt_vel.rssi
        data_units = (1, "RSSI (cnts)")

        # Compute max and min
        max_data = np.nanmax(np.nanmax(data))
        if np.isnan(max_data):
            max_data = 255
        min_data = np.nanmin(np.nanmin(data))
        if np.isnan(min_data):
            min_data = 0

        # Plot beam 1 using mask to identify invalid data
        fmt = [
            {
                "color": "k",
                "linestyle": "-",
                "marker": "o",
                "markersize": 4,
                "label": "B1",
            }
        ]
        self.plt_timeseries(
            data=data[0, :],
            data_units=data_units,
            ax=self.ax[-1],
            fmt=fmt,
            set_annot=True,
        )

        # Plot beam 2 using mask to identify invalid data
        fmt = [
            {
                "color": "#005500",
                "linestyle": "-",
                "marker": "o",
                "markersize": 4,
                "label": "B2",
            }
        ]
        self.plt_timeseries(
            data=data[1, :],
            data_units=data_units,
            ax=self.ax[-1],
            fmt=fmt,
            set_annot=False,
        )

        # Plot beam 3 using mask to identify invalid data
        fmt = [
            {
                "color": "b",
                "linestyle": "-",
                "marker": "o",
                "markersize": 4,
                "label": "B3",
            }
        ]
        self.plt_timeseries(
            data=data[2, :],
            data_units=data_units,
            ax=self.ax[-1],
            fmt=fmt,
            set_annot=False,
        )

        # Plot beam 4 using mask to identify invalid data
        fmt = [
            {
                "color": "#aa5500",
                "linestyle": "-",
                "marker": "o",
                "markersize": 4,
                "label": "B4",
            }
        ]
        self.plt_timeseries(
            data=data[3, :],
            data_units=data_units,
            ax=self.ax[-1],
            fmt=fmt,
            set_annot=False,
        )

        # Show legend
        self.ax[-1].legend()

        # Configure y axis
        self.ax[-1].set_ylim(
            top=np.ceil(max_data * 1.02), bottom=np.floor(min_data * 1.02)
        )

    def other_ts(self, data, data_color="r-"):
        """Create plot of other smooth filter.

        Parameters
        ----------
        data: BoatData
            Object of boat data to be plotted
        data_color: str
            Color of line containing original data
        """

        if data is not None and data.u_mps is not None:
            # Plot smooth
            speed = np.sqrt(data.u_mps**2 + data.v_mps**2)
            invalid_other_vel = np.logical_not(data.valid_data[4, :])
            if data.smooth_filter == "On":
                self.ax[-1].plot(
                    self.x, data.smooth_lower_limit * self.units["V"], color="#d5dce6"
                )
                self.ax[-1].plot(
                    self.x, data.smooth_upper_limit * self.units["V"], color="#d5dce6"
                )
                self.ax[-1].fill_between(
                    self.x,
                    data.smooth_lower_limit * self.units["V"],
                    data.smooth_upper_limit * self.units["V"],
                    facecolor="#d5dce6",
                )

                self.ax[-1].plot(self.x, speed * self.units["V"], data_color)
                self.ax[-1].plot(self.x, data.smooth_speed * self.units["V"])
                self.ax[-1].plot(
                    self.x[invalid_other_vel],
                    speed[invalid_other_vel] * self.units["V"],
                    "ko",
                    linestyle="",
                )
            else:
                self.ax[-1].plot(self.x, speed * self.units["V"], data_color)
            self.ax[-1].set_ylabel(self.canvas.tr("Speed " + self.units["label_V"]))

    def gga_source_ts(self):
        """Plot source for GGA data."""

        self.source_ts(self.transect.boat_vel.gga_vel, "GGA Source")

    def vtg_source_ts(self):
        """Plot source for VTG data."""

        self.source_ts(self.transect.boat_vel.vtg_vel, "VTG Source")

    def source_ts(self, selected, axis_label):
        """Plot source of data.

        Parameters
        ----------
        selected: BoatData
            Boat velocity reference data
        axis_label: str
            Label for y axis
        """

        # Handle situation where transect does not contain the selected source
        if selected is None:
            source = np.tile("INV", len(self.x))
            source = source.astype(object)
        else:
            source = selected.processed_source

        # Plot dummy data to establish consistent order of y axis
        temp_hold = np.copy(self.x)
        if isinstance(temp_hold[0], datetime):
            dummy_time = temp_hold[0] - timedelta(days=1)
            self.x = [dummy_time, dummy_time, dummy_time, dummy_time, dummy_time]
        else:
            self.x = [-10, -10, -10, -10, -10]
        data = ["INV", "INT", "BT", "GGA", "VTG"]
        fmt = [{"color": "w", "linestyle": "-"}]
        data_units = (1, "")
        self.plt_timeseries(data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt)

        # Plot data
        self.x = np.copy(temp_hold)
        data_units = (1, axis_label)
        fmt = [{"color": "b", "linestyle": "", "marker": "."}]
        self.plt_timeseries(data=source, data_units=data_units, ax=self.ax[-1], fmt=fmt)

        # Format y axis
        self.ax[-1].set_yticks(["INV", "INT", "BT", "GGA", "VTG"])

    def gga_quality_ts(self):
        """Plots GPS differential quality reported in GGA sentence."""

        # Check to make sure there is data to plot
        if (
            self.transect.boat_vel.gga_vel is not None
            and self.transect.boat_vel.gga_vel.u_mps is not None
            and np.any(np.logical_not(np.isnan(self.transect.gps.diff_qual_ens)))
        ):

            # Get data
            data = self.transect.gps.diff_qual_ens

            # Set initial format
            fmt = [{"color": "b", "linestyle": "", "marker": "."}]
            data_units = (1, "GGA Quality")

            # Create data mask and formats for invalid data
            invalid = np.logical_not(
                self.transect.boat_vel.gga_vel.valid_data[2, :]
            ).tolist()
            data_mask = [[], invalid]
            fmt.append({"color": "r", "marker": "o", "linestyle": "", "mfc": "none"})

            # Plot data
            self.plt_timeseries(
                data=data,
                data_units=data_units,
                data_mask=data_mask,
                ax=self.ax[-1],
                fmt=fmt,
            )
            # Format y axis
            yint = range(
                0, int(np.ceil(np.nanmax(self.transect.gps.diff_qual_ens)) + 1)
            )
            self.ax[-1].set_ylim(
                top=np.nanmax(yint) + 0.5, bottom=np.nanmin(yint) - 0.5
            )
            self.ax[-1].set_yticks(yint)

    def gga_hdop_ts(self):
        """Plots HDOP reported in GGA sentence."""

        # Check to make sure there is data to plot
        if (
            self.transect.boat_vel.gga_vel is not None
            and self.transect.boat_vel.gga_vel.u_mps is not None
            and np.any(np.logical_not(np.isnan(self.transect.gps.hdop_ens)))
        ):

            # Get data
            data = self.transect.gps.hdop_ens

            # Set initial format
            fmt = [{"color": "b", "linestyle": "", "marker": "."}]
            data_units = (1, "GGA HDOP")

            # Create data mask and formats for invalid data
            invalid = np.logical_not(
                self.transect.boat_vel.gga_vel.valid_data[5, :]
            ).tolist()
            data_mask = [[], invalid]
            fmt.append({"color": "r", "marker": "o", "linestyle": "", "mfc": "none"})

            # Plot data
            self.plt_timeseries(
                data=data,
                data_units=data_units,
                data_mask=data_mask,
                ax=self.ax[-1],
                fmt=fmt,
            )

            # Set y axis properties
            max_y = np.nanmax(self.transect.gps.hdop_ens) + 0.5
            min_y = np.nanmin(self.transect.gps.hdop_ens) - 0.5
            self.ax[-1].set_ylim(top=max_y, bottom=min_y)

    def gga_altitude_ts(self):
        """Plots altitude reported in GGA sentence."""

        # Check to make sure there is data to plot
        if (
            self.transect.boat_vel.gga_vel is not None
            and self.transect.boat_vel.gga_vel.u_mps is not None
            and np.any(np.logical_not(np.isnan(self.transect.gps.altitude_ens_m)))
        ):
            # Get data
            data = self.transect.gps.altitude_ens_m

            # Set initial format
            fmt = [{"color": "b", "linestyle": "", "marker": "."}]
            data_units = (self.units["L"], "GGA Altitude " + self.units["label_L"])

            # Create data mask and formats for invalid data
            invalid = np.logical_not(
                self.transect.boat_vel.gga_vel.valid_data[3, :]
            ).tolist()
            data_mask = [[], invalid]
            fmt.append({"color": "r", "marker": "o", "linestyle": "", "mfc": "none"})

            # Plot data
            self.plt_timeseries(
                data=data,
                data_units=data_units,
                data_mask=data_mask,
                ax=self.ax[-1],
                fmt=fmt,
            )

    def gga_sats_ts(self):
        """Plots number of satellites reported in GGA sentence."""

        # Check to make sure there is data to plot
        if (
            self.transect.boat_vel.gga_vel is not None
            and self.transect.boat_vel.gga_vel.u_mps is not None
            and np.any(np.logical_not(np.isnan(self.transect.gps.num_sats_ens)))
        ):

            # Get data
            data = self.transect.gps.num_sats_ens

            # Set format
            fmt = [{"color": "b", "linestyle": "", "marker": "."}]
            data_units = (1, "No. of Sats")

            # Plot data
            self.plt_timeseries(
                data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt
            )
            try:
                max_y = np.nanmax(self.transect.gps.num_sats_ens) + 0.5
                min_y = np.nanmin(self.transect.gps.num_sats_ens) - 0.5
                self.ax[-1].set_ylim(top=max_y, bottom=min_y)
                yint = range(int(min_y), int(max_y) + 1)
                self.ax[-1].set_yticks(yint)
            except ValueError:
                pass

    def gga_speed_ts(self, lbl="GGA Speed"):
        """Plot boat speed using GGA reference."""

        if (
            self.transect.boat_vel.gga_vel is not None
            and self.transect.boat_vel.gga_vel.u_mps is not None
        ):
            # Compute speed from processed GGA data
            data = np.sqrt(
                self.transect.boat_vel.gga_vel.u_processed_mps**2
                + self.transect.boat_vel.gga_vel.v_processed_mps**2
            )

            # Create data mask for invalid GGA data
            invalid = np.logical_not(self.transect.boat_vel.gga_vel.valid_data)
            data_invalid = np.sqrt(
                self.transect.boat_vel.gga_vel.u_mps**2
                + self.transect.boat_vel.gga_vel.v_mps**2
            )
            data_invalid[np.isnan(data_invalid)] = 0

            # Format for data and invalid identification
            fmt = [
                {"color": "b", "linestyle": "-"},
                {"color": "k", "linestyle": "", "marker": "$O$"},
                {"color": "k", "linestyle": "", "marker": "$Q$"},
                {"color": "k", "linestyle": "", "marker": "$A$"},
                {"color": "k", "linestyle": "", "marker": "$S$"},
                {"color": "k", "linestyle": "", "marker": "$H$"},
            ]

            data_units = (self.units["V"], lbl + " " + self.units["label_V"])

            # Plot data
            self.plt_timeseries(
                data=data,
                data_units=data_units,
                ax=self.ax[-1],
                data_2=data_invalid,
                data_mask=invalid,
                fmt=fmt,
            )

    def vtg_speed_ts(self, lbl="VTG Speed"):
        """Plot boat speed using VTG reference."""

        if (
            self.transect.boat_vel.vtg_vel is not None
            and self.transect.boat_vel.vtg_vel.u_mps is not None
        ):
            # Compute speed from processed VTG data
            data = np.sqrt(
                self.transect.boat_vel.vtg_vel.u_processed_mps**2
                + self.transect.boat_vel.vtg_vel.v_processed_mps**2
            )

            # Create data mask for invalid VTG data
            invalid = np.logical_not(self.transect.boat_vel.vtg_vel.valid_data)
            data_mask = [[], invalid[1], invalid[4], invalid[5]]

            # Use original unprocessed speed to plot invalid symbols
            data_invalid = np.sqrt(
                self.transect.boat_vel.vtg_vel.u_mps**2
                + self.transect.boat_vel.vtg_vel.v_mps**2
            )

            # Format for data and invalid identification
            fmt = [
                {"color": "g", "linestyle": "-"},
                {"color": "k", "linestyle": "", "marker": "$O$"},
                {"color": "k", "linestyle": "", "marker": "$S$"},
                {"color": "k", "linestyle": "", "marker": "$H$"},
            ]
            data_units = (self.units["V"], lbl + " " + self.units["label_V"])

            # Plot data
            self.plt_timeseries(
                data=data,
                data_units=data_units,
                ax=self.ax[-1],
                data_2=data_invalid,
                data_mask=data_mask,
                fmt=fmt,
            )

    def heading_adcp_ts(self):
        """Plot heading from ADCP internal compass."""

        data = self.transect.sensors.heading_deg.internal.data
        fmt = [{"color": "b", "linestyle": "-"}]
        data_units = (1, "ADCP Heading (deg)")
        self.plt_timeseries(data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt)

    def heading_external_ts(self):
        """Plot external heading."""

        data = self.transect.sensors.heading_deg.external.data
        fmt = [{"color": "b", "linestyle": "-"}]
        data_units = (1, "Ext. Heading (deg)")
        self.plt_timeseries(data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt)

    def heading_mag_error_ts(self):
        """Plot magnetic error."""

        data = self.transect.sensors.heading_deg.internal.mag_error
        fmt = [{"color": "b", "linestyle": "-"}]
        data_units = (1, "Mag Error")
        self.plt_timeseries(data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt)

    def pitch_ts(self):
        """Plot pitch data."""

        data = self.transect.sensors.pitch_deg.internal.data
        fmt = [{"color": "b", "linestyle": "-"}]
        data_units = (1, "Pitch (deg)")
        self.plt_timeseries(data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt)

    def roll_ts(self):
        """Plot roll data."""

        data = self.transect.sensors.roll_deg.internal.data
        fmt = [{"color": "b", "linestyle": "-"}]
        data_units = (1, "Roll (deg)")
        self.plt_timeseries(data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt)

    def battery_voltage_ts(self):
        """Plot roll data."""

        data = self.transect.sensors.battery_voltage.internal.data
        fmt = [{"color": "b", "linestyle": "-"}]
        data_units = (1, "Battery (Volts DC)")
        self.plt_timeseries(data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt)

    def depths_beam_ts(
        self, b1=True, b2=True, b3=True, b4=True, vb=True, ds=True, leg=True
    ):
        """Plot available beam depths including depth sounder on single plot.

        Parameters
        ----------
        b1: bool
            Indicates if beam 1 depths are plotted
        b2: bool
            Indicates if beam 2 depths are plotted
        b3: bool
            Indicates if beam 3 depths are plotted
        b4: bool
            Indicates if beam 4 depths are plotted
        vb: bool
            Indicates if vertical beam depths are plotted
        ds: bool
            Indicates if depth sounder depths are plotted
        leg: bool
            Indicates is a legend should be shown
        """

        # Slant beams
        invalid_beams = np.logical_not(
            self.transect.depths.bt_depths.valid_beams
        ).tolist()
        beam_depths = self.transect.depths.bt_depths.depth_beams_m

        # Compute max depth from slant beams
        max_depth = [np.nanmax(np.nanmax(beam_depths))]

        # Plot beam 1 using mask to identify invalid data
        if b1:
            data_mask = [[], invalid_beams[0]]
            data_units = (self.units["L"], "Depth " + self.units["label_L"])
            fmt = [
                {
                    "color": "k",
                    "linestyle": "-",
                    "marker": "o",
                    "markersize": 4,
                    "label": "B1",
                },
                {
                    "color": "r",
                    "linestyle": "",
                    "marker": "o",
                    "markersize": 8,
                    "markerfacecolor": "none",
                    "label": None,
                },
            ]
            self.plt_timeseries(
                data=beam_depths[0, :],
                data_units=data_units,
                data_mask=data_mask,
                ax=self.ax[-1],
                fmt=fmt,
                set_annot=True,
            )

        # Plot beam 2 using mask to identify invalid data
        if b2:
            data_mask = [[], invalid_beams[1]]
            data_units = (self.units["L"], "Depth " + self.units["label_L"])
            fmt = [
                {
                    "color": "#005500",
                    "linestyle": "-",
                    "marker": "o",
                    "markersize": 4,
                    "label": "B2",
                },
                {
                    "color": "r",
                    "linestyle": "",
                    "marker": "o",
                    "markersize": 8,
                    "markerfacecolor": "none",
                    "label": None,
                },
            ]
            self.plt_timeseries(
                data=beam_depths[1, :],
                data_units=data_units,
                data_mask=data_mask,
                ax=self.ax[-1],
                fmt=fmt,
                set_annot=False,
            )

        # Plot beam 3 using mask to identify invalid data
        if b3:
            data_mask = [[], invalid_beams[2]]
            data_units = (self.units["L"], "Depth " + self.units["label_L"])
            fmt = [
                {
                    "color": "b",
                    "linestyle": "-",
                    "marker": "o",
                    "markersize": 4,
                    "label": "B3",
                },
                {
                    "color": "r",
                    "linestyle": "",
                    "marker": "o",
                    "markersize": 8,
                    "markerfacecolor": "none",
                    "label": None,
                },
            ]
            self.plt_timeseries(
                data=beam_depths[2, :],
                data_units=data_units,
                data_mask=data_mask,
                ax=self.ax[-1],
                fmt=fmt,
                set_annot=False,
            )

        # Plot beam 4 using mask to identify invalid data
        if b4:
            data_mask = [[], invalid_beams[3]]
            data_units = (self.units["L"], "Depth " + self.units["label_L"])
            fmt = [
                {
                    "color": "#aa5500",
                    "linestyle": "-",
                    "marker": "o",
                    "markersize": 4,
                    "label": "B4",
                },
                {
                    "color": "r",
                    "linestyle": "",
                    "marker": "o",
                    "markersize": 8,
                    "markerfacecolor": "none",
                    "label": None,
                },
            ]
            self.plt_timeseries(
                data=beam_depths[3, :],
                data_units=data_units,
                data_mask=data_mask,
                ax=self.ax[-1],
                fmt=fmt,
                set_annot=False,
            )

        # Plot vertical beam, if available
        if vb:
            if self.transect.depths.vb_depths is not None:
                invalid_beams = np.logical_not(
                    self.transect.depths.vb_depths.valid_beams[0, :]
                ).tolist()
                beam_depths = self.transect.depths.vb_depths.depth_beams_m[0, :]
                data_mask = [[], invalid_beams]
                data_units = (self.units["L"], "Depth " + self.units["label_L"])
                fmt = [
                    {
                        "color": "#aa00ff",
                        "linestyle": "-",
                        "marker": "o",
                        "markersize": 4,
                        "label": "VB",
                    },
                    {
                        "color": "r",
                        "linestyle": "",
                        "marker": "o",
                        "markersize": 8,
                        "markerfacecolor": "none",
                        "label": None,
                    },
                ]
                self.plt_timeseries(
                    data=beam_depths,
                    data_units=data_units,
                    data_mask=data_mask,
                    ax=self.ax[-1],
                    fmt=fmt,
                    set_annot=False,
                )
                # Add max depth from vertical beam to list
                max_depth.append(np.nanmax(beam_depths))

        # Plot depth sounder data, if available
        if ds:
            if self.transect.depths.ds_depths is not None:
                invalid_beams = np.logical_not(
                    self.transect.depths.ds_depths.valid_beams[0, :]
                )
                beam_depths = self.transect.depths.ds_depths.depth_beams_m[0, :]
                data_mask = [[], invalid_beams]
                data_units = (self.units["L"], "Depth " + self.units["label_L"])
                fmt = [
                    {
                        "color": "#00aaff",
                        "linestyle": "-",
                        "marker": "o",
                        "markersize": 4,
                        "label": "DS",
                    },
                    {
                        "color": "r",
                        "linestyle": "",
                        "marker": "o",
                        "markersize": 8,
                        "markerfacecolor": "none",
                        "label": None,
                    },
                ]
                self.plt_timeseries(
                    data=beam_depths,
                    data_units=data_units,
                    data_mask=data_mask,
                    ax=self.ax[-1],
                    fmt=fmt,
                    set_annot=False,
                )
                # Add max depth from depth sounder to list
                max_depth.append(np.nanmax(beam_depths))

        if leg:
            # Show legend
            self.ax[-1].legend()

        # Configure y axis
        self.ax[-1].invert_yaxis()
        self.ax[-1].set_ylim(
            bottom=np.ceil(np.nanmax(max_depth) * 1.02 * self.units["L"]), top=0
        )

    def depths_final_ts(
        self, avg4_final=False, vb_final=False, ds_final=False, final=True
    ):
        """Plot final cross section used to compute discharge.

        Parameters
        ----------
        avg4_final: bool
            Indicates if 4 beam avg cross section should be plotted
        vb_final: bool
            Indicates if vertical beam cross section should be plotted
        ds_final: bool
            Indicates if depth sounder cross section should be plotted
        final: bool
            Indicates if the selected cross section should be plotted
        """

        beam_depths = np.array([])
        data_units = (self.units["L"], "Depth " + self.units["label_L"])

        # Selected cross section
        if final:
            # Get selected depth
            depth_selected = getattr(
                self.transect.depths, self.transect.depths.selected
            )
            beam_depths = depth_selected.depth_processed_m
            old_x = np.copy(self.x)
            self.x, beam_depths = self.add_edge_bathymetry(self.x, beam_depths)
            # Plot processed depth
            fmt = [{"color": "k", "linestyle": "-", "marker": "o", "markersize": 4}]
            self.plt_timeseries(
                data=beam_depths, data_units=data_units, ax=self.ax[-1], fmt=fmt
            )
            self.x = old_x

        # 4 beam avg cross section
        if avg4_final:
            beam_depths = self.transect.depths.bt_depths.depth_processed_m
            old_x = np.copy(self.x)
            # Include edge bathymetry
            self.x, beam_depths = self.add_edge_bathymetry(self.x, beam_depths)
            fmt = [{"color": "r", "linestyle": "-", "marker": "o", "markersize": 4}]
            self.plt_timeseries(
                data=beam_depths, data_units=data_units, ax=self.ax[-1], fmt=fmt
            )
            self.x = old_x

        # Vertical beam cross section
        if vb_final:
            beam_depths = self.transect.depths.vb_depths.depth_processed_m
            old_x = np.copy(self.x)
            # Include edge bathymetry
            self.x, beam_depths = self.add_edge_bathymetry(self.x, beam_depths)
            fmt = [
                {"color": "#aa00ff", "linestyle": "-", "marker": "o", "markersize": 4}
            ]
            self.plt_timeseries(
                data=beam_depths, data_units=data_units, ax=self.ax[-1], fmt=fmt
            )
            self.x = old_x
        # Depth sounder cross section
        if ds_final:
            beam_depths = self.transect.depths.ds_depths.depth_processed_m
            old_x = np.copy(self.x)
            # Include edge bathymetry
            self.x, beam_depths = self.add_edge_bathymetry(self.x, beam_depths)
            fmt = [
                {"color": "#00aaff", "linestyle": "-", "marker": "o", "markersize": 4}
            ]
            self.plt_timeseries(
                data=beam_depths, data_units=data_units, ax=self.ax[-1], fmt=fmt
            )
            self.x = old_x

        # Format y axis
        self.ax[-1].invert_yaxis()
        try:
            self.ax[-1].set_ylim(
                bottom=np.ceil(np.nanmax(beam_depths) * 1.02 * self.units["L"]), top=0
            )
        except ValueError:
            pass

    def depths_source_ts(self):
        """Plot source of depth for final cross section."""

        # Use selected depth source
        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        source = depth_selected.depth_source_ens

        # Plot dummy data to establish consistent order of y axis
        # self.x is passed through reference to self so it must be temporarily
        # changed for the dummy data
        temp_hold = np.copy(self.x)
        if isinstance(temp_hold[0], datetime):
            dummy_time = temp_hold[0] - timedelta(days=1)
            self.x = [dummy_time, dummy_time, dummy_time, dummy_time, dummy_time]
        else:
            self.x = [-10, -10, -10, -10, -10]
        data = ["INV", "INT", "BT", "VB", "DS"]
        fmt = [{"color": "w", "linestyle": "-"}]
        data_units = (1, "")
        self.plt_timeseries(data=data, data_units=data_units, ax=self.ax[-1], fmt=fmt)

        # Plot source data
        # Restore self.x to original values
        self.x = np.copy(temp_hold)
        data_units = (1, "Depth Source")
        fmt = [{"color": "b", "linestyle": "", "marker": "."}]
        self.plt_timeseries(data=source, data_units=data_units, ax=self.ax[-1], fmt=fmt)
        self.ax[-1].set_yticks(["INV", "INT", "BT", "VB", "DS"])

    def compute_x_axis(self):
        """Compute x axis data."""

        # Initialize x
        x = None

        # x axis is length
        if self.x_axis_type == "L":
            boat_track = self.transect.boat_vel.compute_boat_track(
                transect=self.transect
            )
            if not np.alltrue(np.isnan(boat_track["track_x_m"])):
                x = boat_track["distance_m"]
            self.x = x[self.transect.in_transect_idx]

            # Shift data to account for edge distance
            if self.transect.start_edge == "Left":
                self.x = self.x + self.transect.edges.left.distance_m
            else:
                self.x = self.x + self.transect.edges.right.distance_m

        # x axis is ensembles
        elif self.x_axis_type == "E":
            x = np.arange(1, len(self.transect.depths.bt_depths.depth_processed_m) + 1)
            self.x = x[self.transect.in_transect_idx]

        # x axis is time
        elif self.x_axis_type == "T":
            timestamp = (
                np.nancumsum(self.transect.date_time.ens_duration_sec)
                + self.transect.date_time.start_serial_time
            )
            x = np.copy(timestamp)
            # Timestamp is needed to create contour plots and  setting axis
            # limits
            self.x_timestamp = x[self.transect.in_transect_idx]
            x = []
            # datetime is needed to plot timeseries and x-axis labels
            for stamp in timestamp:
                x.append(datetime.utcfromtimestamp(stamp))
            x = np.array(x)
            self.x = x[self.transect.in_transect_idx]

    @staticmethod
    def contour_data_prep(
        transect,
        data,
        x_1d=None,
        n_ensembles=None,
        edge=None,
        cell_size=None,
        cell_depth=None,
    ):
        """Modifies the selected data from transect into arrays matching the
        meshgrid format for creating contour or color plots.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing data to be plotted
        data: np.ndarray()
            Contour data
        x_1d: np.array
            Array of x-coordinates for each ensemble
        n_ensembles: int
            Used to specify number of ensembles for an edge plot
        edge: str
            Specifies edge (Left or Right)
        cell_size: np.array(float)
            Array of cell sizes, used when extrapolated values are included in plot
        cell_depth: np.array(float)
            Array of cell depths, used when extrapolated values are included in plot

        Returns
        -------
        x_plt: np.array
            Data in meshgrid format used for the contour x variable
        cell_plt: np.array
            Data in meshgrid format used for the contour y variable
        data_plt: np.array
            Data in meshgrid format used to determine colors in plot
        ensembles: np.array
            Ensemble numbers used as the x variable to plot the cross section
             bottom
        depth: np.array
            Depth data used to plot the cross section bottom
        """

        in_transect_idx = transect.in_transect_idx

        # Set x_1d if not specified
        if x_1d is None:
            x_1d = in_transect_idx

        data_2_plot = np.copy(data)

        if n_ensembles is None:
            # Get data from transect
            depth_selected = getattr(transect.depths, transect.depths.selected)
            depth = depth_selected.depth_processed_m[in_transect_idx]
            if cell_depth is None:
                cell_depth = depth_selected.depth_cell_depth_m[:, in_transect_idx]
                cell_size = depth_selected.depth_cell_size_m[:, in_transect_idx]

            x_data = x_1d
            ensembles = in_transect_idx

        else:
            # Use only edge ensembles from transect
            n_ensembles = int(n_ensembles)
            if transect.start_edge == edge:
                # Start on left bank
                depth_selected = getattr(transect.depths, transect.depths.selected)
                depth = depth_selected.depth_processed_m[:n_ensembles]
                if cell_depth is None:
                    cell_depth = depth_selected.depth_cell_depth_m[:, :n_ensembles]
                    cell_size = depth_selected.depth_cell_size_m[:, :n_ensembles]
                data_2_plot = data_2_plot[:, :n_ensembles]
                ensembles = in_transect_idx[:n_ensembles]
                x_data = x_1d[:n_ensembles]

            else:

                depth_selected = getattr(transect.depths, transect.depths.selected)
                depth = depth_selected.depth_processed_m[-n_ensembles:]
                if cell_depth is None:
                    cell_depth = depth_selected.depth_cell_depth_m[:, -n_ensembles:]
                    cell_size = depth_selected.depth_cell_size_m[:, -n_ensembles:]
                data_2_plot = data_2_plot[:, -n_ensembles:]
                ensembles = in_transect_idx[-n_ensembles:]
                x_data = x_1d[-n_ensembles:]

        # Prep water speed to use -999 instead of nans
        data_2_plot[np.isnan(data_2_plot)] = -999

        # Create x for contour plot
        x = np.tile(x_data, (cell_size.shape[0], 1))
        n_ensembles = x.shape[1]

        # Prep data in x direction
        j = -1
        x_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_depth_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_size_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        data_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        depth_xpand = np.array([np.nan] * (2 * cell_size.shape[1]))

        # Center ensembles in grid
        for n in range(n_ensembles):
            if n == 0:
                try:
                    half_back = np.abs(0.5 * (x[:, n + 1] - x[:, n]))
                    half_forward = half_back
                except IndexError:
                    half_back = x[:, 0] - 0.5
                    half_forward = x[:, 0] + 0.5
            elif n == n_ensembles - 1:
                half_forward = np.abs(0.5 * (x[:, n] - x[:, n - 1]))
                half_back = half_forward
            else:
                half_back = np.abs(0.5 * (x[:, n] - x[:, n - 1]))
                half_forward = np.abs(0.5 * (x[:, n + 1] - x[:, n]))
            j += 1
            x_xpand[:, j] = x[:, n] - half_back
            cell_depth_xpand[:, j] = cell_depth[:, n]
            data_xpand[:, j] = data_2_plot[:, n]
            cell_size_xpand[:, j] = cell_size[:, n]
            depth_xpand[j] = depth[n]
            j += 1
            x_xpand[:, j] = x[:, n] + half_forward
            cell_depth_xpand[:, j] = cell_depth[:, n]
            data_xpand[:, j] = data_2_plot[:, n]
            cell_size_xpand[:, j] = cell_size[:, n]
            depth_xpand[j] = depth[n]

        # Create plotting mesh grid
        n_cells = x.shape[0]
        j = -1
        x_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        data_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        for n in range(n_cells):
            j += 1
            x_plt[j, :] = x_xpand[n, :]
            cell_plt[j, :] = cell_depth_xpand[n, :] - 0.5 * cell_size_xpand[n, :]
            data_plt[j, :] = data_xpand[n, :]
            j += 1
            x_plt[j, :] = x_xpand[n, :]
            cell_plt[j, :] = cell_depth_xpand[n, :] + 0.5 * cell_size_xpand[n, :]
            data_plt[j, :] = data_xpand[n, :]

        cell_plt[np.isnan(cell_plt)] = 0
        data_plt[np.isnan(data_plt)] = -999
        x_plt[np.isnan(x_plt)] = 0
        data_plt = data_plt[:-1, :-1]

        return x_plt, cell_plt, data_plt, ensembles, depth, x_data

    def plt_contour(
        self,
        x_plt_in,
        cell_plt_in,
        data_plt_in,
        x,
        depth,
        data_units,
        data_limits=None,
        cmap_in=None,
        ping_name=None,
        n_names=None,
        n_ensembles=None,
        edge=None,
        show_edge_speed=False,
    ):
        """Create contour plot.

        Parameters
        ----------
        x_plt_in: np.ndarray()
            x data used for contour plot
        cell_plt_in: np.ndarray()
            Cell depth data
        data_plt_in: np.ndarray()
            Primary data to plot
        x: np.ndarray()
            x data used for depth plot
        depth: np.ndarray()
            Depth data
        data_units: tuple
            Tuple of data multiplier and label
        data_limits: list
            Optional list of min max data limits
        cmap_in: str
            Name of color map to use
        ping_name: dict
            Dictionary of ping names
        n_names: int
            Number of names
        n_ensembles: int
            Number of ensembles for edge data
        edge: str
            Specifies edge (Left or Right)
        show_edge_speed: bool
            Indicates if edge speed should be plotted
        """

        # Use last subplot
        ax = self.ax[-1]

        # Create plot variables for input
        if self.x_axis_type == "T":
            # If x axis is time, create x_plt
            x_plt = np.zeros(x_plt_in.shape, dtype="object")
            for r in range(x_plt_in.shape[0]):
                for c in range(x_plt_in.shape[1]):
                    x_plt[r, c] = datetime.utcfromtimestamp(x_plt_in[r, c])
        else:
            x_plt = x_plt_in

        if self.x_axis_type == "L":
            x_plt = x_plt * self.units["L"]

        cell_plt = cell_plt_in * self.units["L"]
        data_plt = data_plt_in * data_units[0]

        # Determine limits for color map
        if data_limits is not None:
            max_limit = data_limits[1]
            min_limit = data_limits[0]
        elif np.sum(np.abs(data_plt_in[data_plt_in > -900])) > 0:
            max_limit = np.percentile(
                data_plt_in[data_plt_in > -900] * data_units[0], 99
            )
            min_limit = np.min(data_plt_in[data_plt_in > -900] * data_units[0])
            if 0 < min_limit < 0.1:
                min_limit = 0
        else:
            max_limit = 1
            min_limit = 0

        # Create color map
        if cmap_in is None:
            cmap = cm.get_cmap(self.color_map)
        else:
            cmap = cm.get_cmap(cmap_in)

        cmap.set_under("white")

        # Generate color contour
        c = ax.pcolormesh(
            x_plt, cell_plt, data_plt, cmap=cmap, vmin=min_limit, vmax=max_limit
        )

        # Create data plotted for annotation use
        self.data_plotted.append(
            {"type": "contour", "x": x_plt, "y": cell_plt, "z": data_plt}
        )

        # Initialize annotation for data cursor
        self.annot.append(
            ax.annotate(
                "",
                xy=(0, 0),
                xytext=(-20, 20),
                textcoords="offset points",
                bbox=dict(boxstyle="round", fc="w"),
                arrowprops=dict(arrowstyle="->"),
            )
        )

        self.annot[-1].set_visible(False)

        # Add color bar and axis labels in separate subplot
        self.ax.append(self.fig.add_subplot(self.gs[self.fig_no + 1]))
        self.data_plotted.append({"type": "colorbar"})
        self.annot.append("")
        cb = self.fig.colorbar(c, self.ax[-1])
        cb.ax.set_ylabel(self.canvas.tr(data_units[1]))
        cb.ax.yaxis.label.set_fontsize(12)
        cb.ax.tick_params(labelsize=12)
        cb.ax.set_ylim([min_limit, max_limit])
        ax.invert_yaxis()
        if ping_name is not None:
            tick_list = list(range(n_names))
            label_list = []
            for tick in tick_list:
                label_list.append(ping_name[tick])
            cb.set_ticks(tick_list)
            cb.ax.set_yticklabels(label_list, rotation=90, verticalalignment="center")

        # Plot depth
        if self.x_axis_type == "L":
            # Add edge bathymetry
            self.expanded_x, depth = self.add_edge_bathymetry(x, depth, edge)
            ax.plot(self.expanded_x * self.units["L"], depth * self.units["L"], color="k")
        else:
            self.expanded_x = x
            ax.plot(x, depth * self.units["L"], color="k")

        depth_obj = getattr(self.transect.depths, self.transect.depths.selected)

        # Side lobe cutoff if available
        if self.transect.w_vel.sl_cutoff_m is not None:
            last_valid_cell = np.nansum(self.transect.w_vel.cells_above_sl, axis=0) - 1
            last_depth_cell_size = depth_obj.depth_cell_size_m[
                last_valid_cell, np.arange(depth_obj.depth_cell_size_m.shape[1])
            ]
            y_plt_sl = (
                self.transect.w_vel.sl_cutoff_m + (last_depth_cell_size * 0.5)
            )
            if edge is not None:
                if self.transect.start_edge == edge:
                    y_plt_sl = y_plt_sl[: int(n_ensembles)]
                else:
                    y_plt_sl = y_plt_sl[-int(n_ensembles) :]
            if self.x_axis_type == "L":
                ax.plot(x * self.units["L"], y_plt_sl * self.units["L"], color="r", linewidth=0.5)
            else:
                ax.plot(x, y_plt_sl * self.units["L"], color="r", linewidth=0.5)

        # Upper bound of measured depth cells
        y_plt_top = (
            depth_obj.depth_cell_depth_m[0, :]
            - (depth_obj.depth_cell_size_m[0, :] * 0.5)
        )
        if edge is not None:
            if self.transect.start_edge == edge:
                y_plt_top = y_plt_top[: int(n_ensembles)]
            else:
                y_plt_top = y_plt_top[-int(n_ensembles) :]
        if self.x_axis_type == "L":
            ax.plot(x * self.units["L"], y_plt_top * self.units["L"], color="r", linewidth=0.5)
        else:
            ax.plot(x, y_plt_top * self.units["L"], color="r", linewidth=0.5)

        # Extrapolated data plotting additions
        if show_edge_speed and self.x_axis_type == "L":
            top_valid = []
            bottom_valid = []

            for n in range(data_plt.shape[1]):
                idx = np.where(data_plt[2:-1, n] > -999)[0]
                top_valid.append(cell_plt[idx[0] + 2, n])
                bottom_valid.append(cell_plt[idx[-1] + 2, n])

            top_valid.append(top_valid[-1])
            bottom_valid.append(bottom_valid[-1])
            top_valid = np.array(top_valid)
            bottom_valid = np.array(bottom_valid)
            # Plot extrapolated boundaries
            ax.plot(
                x_plt[-2, :],
                bottom_valid,
                linewidth=3,
                color="w",
                linestyle="dotted",
            )
            ax.plot(
                x_plt[2, :],
                top_valid,
                linewidth=3,
                color="w",
                linestyle="dotted",
            )
            ax.plot(
                [x_plt[-2, 0], x_plt[2, 0]],
                [cell_plt[-2, 0], cell_plt[2, 0]],
                linewidth=3,
                color="w",
                linestyle="dotted",
            )
            ax.plot(
                [x_plt[-2, -1], x_plt[2, -1]],
                [cell_plt[-2, -1], cell_plt[2, -1]],
                linewidth=3,
                color="w",
                linestyle="dotted",
            )
            # Plot edge contours
            self.add_edge_contours(min_limit, max_limit, cmap, ax, depth)

        # Label and limits for y axis
        ax.set_ylabel(self.canvas.tr("Depth ") + self.units["label_L"])
        ax.yaxis.label.set_fontsize(12)
        ax.tick_params(
            axis="both", direction="in", bottom=True, top=True, left=True, right=True
        )
        ax.set_ylim(top=0, bottom=(np.nanmax(depth * self.units["L"]) * 1.02))

    def add_edge_bathymetry(self, x, depth, edge=None):
        """Computes a new cross section profile including edge shapes.
        The edge shape is based on the type of edge.

        Parameters
        ----------
        x: np.array(float)
            Array of lengths along transect in m
        depth: np.array(float)
            Array of depths along transect in m
        edge: strt
            Specifies the edge (Left or Right)

        Returns
        -------
        x: np.array(float)
            Array of lengths along transect with edges in m
        d: np.array(float)
            Array of depths along transect with edge shapes in m
        """

        # Left edge
        if self.transect.start_edge == "Left":
            if self.transect.edges.left.type == "Rectangular":
                start_x = np.array([0, 0])
                start_d = np.array([0, depth[0]])
            elif self.transect.edges.left.type == "Triangular":
                start_x = np.array([0])
                start_d = np.array([0])
            else:
                cd = compute_edge_cd(self.transect.edges.left)
                start_x = np.array([0, 0, self.transect.edges.left.distance_m])
                start_d = np.array([0, depth[0] * cd, depth[0]])
            if self.transect.edges.right.type == "Rectangular":
                end_x = np.array(2 * [x[-1] + self.transect.edges.right.distance_m])
                end_d = np.array([depth[-1], 0])
            elif self.transect.edges.right.type == "Triangular":
                end_x = np.array([x[-1] + self.transect.edges.right.distance_m])
                end_d = np.array([0])
            else:
                cd = compute_edge_cd(self.transect.edges.right)
                end_x = np.array(
                    [
                        x[-1],
                        x[-1] + self.transect.edges.right.distance_m,
                        x[-1] + self.transect.edges.right.distance_m,
                    ]
                )
                end_d = np.array([depth[-1], depth[-1] * cd, 0])

        # Right edge
        else:
            if self.transect.edges.right.type == "Rectangular":
                start_x = np.array([0, 0])
                start_d = np.array([0, depth[0]])
            elif self.transect.edges.right.type == "Triangular":
                start_x = np.array([0])
                start_d = np.array([0])
            else:
                cd = compute_edge_cd(self.transect.edges.right)
                start_x = np.array([0, 0, self.transect.edges.right.distance_m])
                start_d = np.array([0, depth[0] * cd, depth[0]])

            if self.transect.edges.left.type == "Rectangular":
                end_x = np.array(2 * [x[-1] + self.transect.edges.left.distance_m])
                end_d = np.array([depth[-1], 0])
            elif self.transect.edges.left.type == "Triangular":
                end_x = np.array([x[-1] + self.transect.edges.left.distance_m])
                end_d = np.array([0])
            else:
                cd = compute_edge_cd(self.transect.edges.left)
                end_x = np.array(
                    [
                        x[-1],
                        x[-1] + self.transect.edges.left.distance_m,
                        x[-1] + self.transect.edges.left.distance_m,
                    ]
                )
                end_d = np.array([depth[-1], depth[-1] * cd, 0])

        # Combine edges with transect data
        if edge is None:
            x = np.hstack([start_x, x, end_x])
            d = np.hstack([start_d, depth, end_d])
        elif self.transect.start_edge == edge:
            x = np.hstack([start_x, x])
            d = np.hstack([start_d, depth])
        else:
            x = np.hstack([x, end_x])
            d = np.hstack([depth, end_d])

        return x, d

    def add_extrapolated_topbot(self, water_speed):
        """Computes the speed in the top and bottom extrapolated areas and expands
        the water_speed data to include these extrapolated data.

        Parameters
        ----------
        water_speed: np.array(float)
            Water speed from processed u and v components

        Returns
        -------
        expanded_cell_size: np.array(float)
            Cell size data including extrapolated values
        expanded_cell_depth: np.array(float)
            Cell depth data including extrapolated values
        expanded_water_speed: np.array(float)
            Water speed data including extrapolated values
        """

        # Compute extrapolated cell size and depth
        n_ensembles = water_speed.shape[1]
        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        top_cell_size = np.repeat(np.nan, n_ensembles)
        top_cell_depth = np.repeat(np.nan, n_ensembles)
        bottom_cell_size = np.repeat(np.nan, n_ensembles)
        bottom_cell_depth = np.repeat(np.nan, n_ensembles)
        for n in range(n_ensembles):
            # Identify topmost valid cells
            idx_temp = np.where(np.logical_not(np.isnan(water_speed[:, n])))[0]
            if len(idx_temp) > 0:
                # Compute top
                top_cell_size[n] = (
                    depth_selected.depth_cell_depth_m[idx_temp[0], n]
                    - 0.5 * depth_selected.depth_cell_size_m[idx_temp[0], n]
                )
                top_cell_depth[n] = top_cell_size[n] / 2
                # Compute bottom
                bottom_cell_size[n] = depth_selected.depth_processed_m[n] - (
                    depth_selected.depth_cell_depth_m[idx_temp[-1], n]
                    + 0.5 * depth_selected.depth_cell_size_m[idx_temp[-1], n]
                )
                bottom_cell_depth[n] = (
                    depth_selected.depth_processed_m[n] - 0.5 * bottom_cell_size[n]
                )
            else:
                top_cell_size[n] = 0
                top_cell_depth[n] = 0
                bottom_cell_size[n] = 0
                bottom_cell_depth[n] = 0

        # Expanded arrays to include extrapolated cell size and depth
        expanded_cell_size = np.vstack(
            [top_cell_size, depth_selected.depth_cell_size_m, bottom_cell_size]
        )
        expanded_cell_depth = np.vstack(
            [top_cell_depth, depth_selected.depth_cell_depth_m, bottom_cell_depth]
        )

        # Expand array to include extrapolated top and bottom speeds
        expanded_water_speed = np.vstack(
            [self.discharge.top_speed, water_speed, self.discharge.bottom_speed]
        )

        # Fix expanded_water_speed for excluded depth cells
        for n in range(expanded_water_speed.shape[1]):
            idx = np.where(self.transect.w_vel.valid_data[6, :, n])
            if idx[0][0] > 0:
                for row in range(idx[0][0]):
                    expanded_water_speed[row + 1, n] = expanded_water_speed[row, n]

        return expanded_cell_size, expanded_cell_depth, expanded_water_speed

    def add_edge_contours(self, min_limit, max_limit, cmap, ax, depth):
        """Adds color patches representing the average speed in each edge to the
        color contour plot.

        Parameters
        ----------
        min_limit: float
            Minimum limit for colorbar
        max_limit: float
            Maximum limit for colorbar
        cmap: color_map
            Color map
        ax: subplot
            Axis of contour plot
        depth: np.array(float)
            Array of measured transect depths in m
        """

        # Left edge
        if self.transect.start_edge == "Left":
            if self.transect.edges.left.type == "Triangular":
                x_left = np.array(
                    [
                        self.expanded_x[0],
                        self.expanded_x[1],
                        self.expanded_x[1],
                        self.expanded_x[0],
                    ]
                )
                y_left = np.array([depth[0], depth[1], depth[0], depth[0]])

            else:
                x_left = np.array(
                    [
                        self.expanded_x[0],
                        self.expanded_x[1],
                        self.expanded_x[2],
                        self.expanded_x[2],
                        self.expanded_x[0],
                    ]
                )
                y_left = np.array([depth[0], depth[1], depth[2], depth[0], depth[0]])

        else:
            if self.transect.edges.left.type == "Triangular":
                x_left = np.array(
                    [
                        self.expanded_x[-1],
                        self.expanded_x[-2],
                        self.expanded_x[-2],
                        self.expanded_x[-1],
                    ]
                )
                y_left = np.array([depth[-1], depth[-2], depth[-1], depth[-1]])

            else:
                x_left = np.array(
                    [
                        self.expanded_x[-1],
                        self.expanded_x[-2],
                        self.expanded_x[-3],
                        self.expanded_x[-3],
                        self.expanded_x[-1],
                    ]
                )
                y_left = np.array([depth[-1], depth[-2], depth[-3], depth[-1], depth[-1]])

        left_coords = np.vstack([x_left, y_left]).T
        v_left = self.discharge.left_edge_speed
        # Determine color for left edge based on colormap and edge velocity
        left_c = cmap((v_left * self.units['V'] - min_limit) / (max_limit - min_limit))

        # Right edge
        if self.transect.start_edge == "Right":
            if self.transect.edges.right.type == "Triangular":
                x_right = np.array(
                    [
                        self.expanded_x[0],
                        self.expanded_x[1],
                        self.expanded_x[1],
                        self.expanded_x[0],
                    ]
                )
                y_right = np.array([depth[0], depth[1], depth[0], depth[0]])

            else:
                x_right = np.array(
                    [
                        self.expanded_x[0],
                        self.expanded_x[1],
                        self.expanded_x[2],
                        self.expanded_x[2],
                        self.expanded_x[0],
                    ]
                )
                y_right = np.array([depth[0], depth[1], depth[2], depth[0], depth[0]])

        else:
            if self.transect.edges.right.type == "Triangular":
                x_right = np.array(
                    [
                        self.expanded_x[-1],
                        self.expanded_x[-2],
                        self.expanded_x[-2],
                        self.expanded_x[-1],
                    ]
                )
                y_right = np.array([depth[-1], depth[-2], depth[-1], depth[-1]])

            else:
                x_right = np.array(
                    [
                        self.expanded_x[-1],
                        self.expanded_x[-2],
                        self.expanded_x[-3],
                        self.expanded_x[-3],
                        self.expanded_x[-1],
                    ]
                )
                y_right = np.array([depth[-1], depth[-2], depth[-3], depth[-1], depth[-1]])

        right_coords = np.vstack([x_right, y_right]).T
        v_right = self.discharge.right_edge_speed
        # Determine color for right edge based on colormap and edge velocity
        right_c = cmap((v_right * self.units['V'] - min_limit) / (max_limit - min_limit))

        # Plot patches
        ax.add_patch(Polygon(left_coords * self.units["L"], edgecolor=left_c, facecolor=left_c))

        ax.add_patch(Polygon(right_coords * self.units["L"], edgecolor=right_c, facecolor=right_c))

        # Create data plotted for annotation use
        self.data_plotted[-2]["edge_x"] = np.array([x_left, x_right]) * self.units["L"]
        self.data_plotted[-2]["edge_y"] = np.array([y_left, y_right]) * self.units["L"]
        self.data_plotted[-2]["edge_z"] = np.array([v_left, v_right]) * self.units["V"]

    def plt_timeseries(
        self,
        data,
        data_units,
        ax=None,
        data_2=None,
        data_mask=None,
        fmt=None,
        set_annot=True,
            x_override=[],
    ):
        """Create timeseries plot.

        Parameters
        ----------
        data: np.ndarray()
            1-D array of data to be plotted
        data_units: tuple
            Tuple of data multiplier and label
        ax: subplot
            Optional subplot
        data_2: np.ndarray()
            Optional data that can be masked
        data_mask: list
            List of bool indicating what data should be plotted
        fmt: list
            List of dictionary providing plot format properties
        set_annot: bool
            Indicates if annotation should be associated.
        x_override: np.ndarray()
            1-D array of data to be plotted.
        """

        # Use last subplot if not defined
        if ax is None:
            ax = self.ax[-1]

        # Setup plot
        ax.set_ylabel(self.canvas.tr(data_units[1]))
        ax.grid(True)
        ax.yaxis.label.set_fontsize(12)
        ax.tick_params(
            axis="both", direction="in", bottom=True, top=True, left=True, right=True
        )

        # Get format for first call to plot
        if fmt is not None:
            kwargs = fmt[0]
        else:
            kwargs = {"linestyle": "-", "color": "b"}

        # Compute x coordinates in selected units
        if self.x_axis_type == "L":
            if len(x_override) > 0:
                x_coords = x_override * self.units["L"]
            else:
                x_coords = self.x * self.units["L"]
        else:
            if len(x_override) > 0:
                x_coords = x_override
            else:
                x_coords = self.x

        # First call to plot uses masked data if there is no primary data
        if data is not None:
            ax.plot(x_coords, data * data_units[0], **kwargs)
        else:
            ax.plot(
                x_coords[data_mask[0]], data_2[data_mask[0]] * data_units[0], **kwargs
            )

        # Compile all data from primary and masked data sets
        all_data = data
        if data_mask is not None:
            if data_2 is None:
                data_2 = data
                all_data = data
            elif data is None:
                all_data = data_2
            else:
                all_data = np.concatenate([data, data_2])

            # Plot calls for other masked data
            for n in range(1, len(fmt)):
                if fmt is None:
                    kwargs = {
                        "color": "r",
                        "marker": "o",
                        "ms": 8,
                        "markerfacecolor": "none",
                    }
                else:
                    kwargs = fmt[n]

                ax.plot(
                    x_coords[data_mask[n]], data_2[data_mask[n]] * data_units[0], **kwargs
                )

        # Create dictionary of data for use by annotation
        self.data_plotted.append({"type": "ts", "x": x_coords, "y": all_data * data_units[0]})

        # Set axis limits
        try:
            max_y = (
                np.nanmax(all_data) + np.abs(np.nanmax(all_data) * 0.02)
            ) * data_units[0]
            min_y = (
                np.nanmin(all_data) - np.abs(np.nanmin(all_data)) * 0.02
            ) * data_units[0]
            if min_y == 0:
                min_y = max_y * -0.02
            ax.set_ylim(top=max_y, bottom=min_y)
        except (TypeError, ValueError):
            pass

        # Initialize annotation for data cursor. Annotation should only be
        # associated with one call to plt_timeseries if figure makes multiple
        # calls to create multiple lines on the same graph.
        if set_annot:
            self.annot.append(
                ax.annotate(
                    "",
                    xy=(0, 0),
                    xytext=(-20, 20),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops=dict(arrowstyle="->"),
                )
            )

            self.annot[-1].set_visible(False)

        self.canvas.draw()

    def plot_map(self, map_class, units, bath=False,
                 temp=False, plot_transects=False):

        with self.wait_cursor():
            # Initialize data sources
            self.xs = map_class

            # Set x axis type and units
            self.x_axis_type = 'L'
            self.units = units

            self.x = map_class.distance_cells_center[0]
            label = self.canvas.tr("Length ") + self.units["label_L"]

            # Clear the plot
            self.fig.clear()

            # Determine number of subplots
            self.n_subplots = 1

            # Initialize variable for subplots
            self.ax = []
            self.annot = []
            self.data_plotted = []

            # Create grid specification
            # Note: the second column of the grid is for the color bar.
            # It is blank but present even for time series
            # plots to allow the sharing of the x-axis between all plots
            self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50,
                                                                          1])

            # Create first subplot
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))

            if bath:

                data_units = (self.units["L"], self.canvas.tr("Depth") + " " +
                              self.units["label_L"])

                fmt = [{"color": "red", "linewidth": 2}]
                self.plt_timeseries(data=map_class.depths,
                                    data_units=data_units,
                                    fmt=fmt)

                if plot_transects:
                    fmt = [{"color": "grey", "linewidth": 1}]

                    for tran in range(len(map_class.depth_by_transect)):
                        self.plt_timeseries(data=map_class.depth_by_transect[tran],
                                            data_units=data_units,
                                            x_override=map_class.acs_distance[tran],
                                            fmt=fmt)

                self.ax[-1].invert_yaxis()

            if temp:

                y_data = map_class.temperature

                data_units = (1, 'Mean Temp (C)')
                fmt = [{"color": "red", "linewidth": 2}]
                self.plt_timeseries(data=y_data,
                                    data_units=data_units,
                                    ax=self.ax[-1],
                                    fmt=fmt)

                if plot_transects:
                    fmt = [{"color": "grey", "linewidth": 1}]
                    for tran in range(len(map_class.temperature_by_transect)):
                        self.plt_timeseries(data=map_class.temperature_by_transect[tran],
                                            data_units=data_units,
                                            x_override=map_class.acs_distance[tran],
                                            fmt=fmt)

            self.ax[-1].xaxis.label.set_fontsize(12)
            self.ax[-1].set_xlabel(label)

        self.canvas.draw()

    def hover(self, event):
        """Determines if the user has selected a location with data and makes
        annotation visible and calls method to update the text of the
        annotation. If the location is not valid the existing annotation is hidden.

        Parameters
        ----------
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Determine if mouse location references a data point in the plot and
        # update the annotation.
        cont_fig = False
        value = None
        n = 0
        x_plt = np.nan
        y_plt = np.nan
        z_plt = np.nan
        for n, item in enumerate(self.fig.axes):
            if event.inaxes == item:

                # Verify that location is associated with plotted data

                if item is not None:
                    # cont_fig, ind_fig = self.fig.contains(event)
                    # for ax in self.ax:
                    for line in item.lines:
                        cont_fig, ind_fig = line.contains(event)
                        if cont_fig:
                            break
                    if cont_fig:
                        break
                    else:
                        data = self.data_plotted[n]
                        if data["type"] == "contour":
                            if (
                                np.nanmax(data["x"])
                                >= event.xdata
                                >= np.nanmin(data["x"])
                            ):
                                cont_fig = True
                                x_plt = self.data_plotted[n]["x"]
                                y_plt = self.data_plotted[n]["y"]
                                z_plt = self.data_plotted[n]["z"]
                                break
                            # Check for edge speed
                            elif "edge_x" in data:
                                if (
                                    np.nanmax(data["edge_x"][0])
                                    >= event.xdata
                                    >= np.nanmin(data["edge_x"][0])
                                ) and (
                                    np.nanmax(data["edge_y"][0])
                                    >= event.ydata
                                    >= np.nanmin(data["edge_y"][0])
                                ):
                                    cont_fig = True
                                    value = data["edge_z"][0]
                                    break

                                elif (
                                    np.nanmax(data["edge_x"][1])
                                    >= event.xdata
                                    >= np.nanmin(data["edge_x"][1])
                                ) and (
                                    np.nanmax(data["edge_y"][1])
                                    >= event.ydata
                                    >= np.nanmin(data["edge_y"][1])
                                ):
                                    cont_fig = True
                                    value = data["edge_z"][1]
                                    break

                        elif data["type"] == "ping type":
                            if (
                                np.nanmax(data["x"])
                                >= event.xdata
                                >= np.nanmin(data["x"])
                            ):
                                cont_fig = True
                                x_plt = self.data_plotted[n]["x"]
                                y_plt = self.data_plotted[n]["y"]
                                z_plt = self.data_plotted[n]["z"]
                                break

        if cont_fig and self.fig.get_visible():
            # Annotation for contour plot
            if (
                self.data_plotted[n]["type"] == "contour"
                or self.data_plotted[n]["type"] == "ping type"
            ):
                if value is None:
                    # Determine data column index
                    if self.x_axis_type == "T":
                        col_idx = np.where(
                            x_plt[0, :] < num2date(event.xdata).replace(tzinfo=None)
                        )[0][-1]
                    elif self.x_axis_type == "L":
                        # if edge speed x_plt only has 1 dimension
                        if len(x_plt.shape) < 2:
                            col_idx = np.where(x_plt < event.xdata)[0][-1]
                        else:
                            col_idx = np.where(x_plt[0, :] < event.xdata)[0][-1]
                    else:
                        col_idx = (int(round(abs(event.xdata - x_plt[0, 0]))) * 2) - 1

                    # Determine row index. Edge data has no row index
                    if not np.all(np.isnan(y_plt)):
                        row_idx = np.where(y_plt[:, col_idx] > event.ydata)[0]
                        if z_plt[row_idx[0] - 1, col_idx - 1] == -999:
                            row_idx = row_idx[-1] - 1
                        else:
                            row_idx = row_idx[0] - 1
                        value = z_plt[row_idx, col_idx]
                    else:
                        value = z_plt[col_idx]

                if self.data_plotted[n]["type"] == "contour":
                    # Create annotation
                    self.update_annot(
                        ax_idx=n,
                        x=event.xdata,
                        y=event.ydata,
                        v=value,
                    )
                else:
                    # Create annotation
                    self.update_annot(
                        ax_idx=n,
                        x=event.xdata,
                        y=event.ydata,
                        v=value,
                        v_dict=self.ping_name,
                    )

            # Annotation for time series data
            elif self.data_plotted[n]["type"] == "ts":
                self.update_annot(ax_idx=n, x=event.xdata, y=event.ydata, v=value)

            self.annot[n].set_visible(True)
            self.canvas.draw_idle()
        else:
            # If the cursor location is not associated with the plotted
            # data hide the annotation.
            if self.fig.get_visible():
                if type(self.annot[n]) != str:
                    self.annot[n].set_visible(False)
                self.canvas.draw_idle()

    def set_hover_connection(self, setting):
        """Turns the connection to the mouse event on or off.

        Parameters
        ----------
        setting: bool
            Boolean to specify whether the connection for the mouse event is
            active or not.
        """
        if setting and self.hover_connection is None:
            self.hover_connection = self.canvas.mpl_connect(
                "button_press_event", self.hover
            )
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            for item in self.annot:
                if type(item) != str:
                    item.set_visible(False)
            self.canvas.draw_idle()

    def update_annot(self, ax_idx, x, y, v=None, v_dict=None):
        """Updates the location and text and makes visible the previously
        initialized and hidden annotation.

        Parameters
        ----------
        ax_idx: int
            Index of axis
        x: float
            x coordinate for annotation, ensemble
        y: float
            y coordinate for annotation, depth
        v: float or None
            Speed for annotation
        v_dict: dict
            Ping type name for value
        """

        # Set local variables
        pos = [x, y]
        plt_ref = self.fig.axes[ax_idx]
        annot_ref = self.annot[ax_idx]

        # Shift annotation box left or right depending on which half of the
        # axis the pos x is located and the direction of x increasing.
        if plt_ref.viewLim.intervalx[0] < plt_ref.viewLim.intervalx[1]:
            if (
                pos[0]
                < (plt_ref.viewLim.intervalx[0] + plt_ref.viewLim.intervalx[1]) / 2
            ):
                annot_ref._x = -20
            else:
                annot_ref._x = -80
        else:
            if (
                pos[0]
                < (plt_ref.viewLim.intervalx[0] + plt_ref.viewLim.intervalx[1]) / 2
            ):
                annot_ref._x = -80
            else:
                annot_ref._x = -20

        # Shift annotation box up or down depending on which half of the axis
        # the pos y is located and the direction of y increasing.
        if plt_ref.viewLim.intervaly[0] < plt_ref.viewLim.intervaly[1]:
            if (
                pos[1]
                > (plt_ref.viewLim.intervaly[0] + plt_ref.viewLim.intervaly[1]) / 2
            ):
                annot_ref._y = -40
            else:
                annot_ref._y = 20
        else:
            if (
                pos[1]
                > (plt_ref.viewLim.intervaly[0] + plt_ref.viewLim.intervaly[1]) / 2
            ):
                annot_ref._y = 20
            else:
                annot_ref._y = -40
        annot_ref.xy = pos
        text = ""

        # Annotation of contour plot
        if v is not None and v > -999:
            # Format for time axis
            if self.x_axis_type == "T":
                x_label = num2date(pos[0]).strftime("%H:%M:%S.%f")[:-4]
                if v_dict is None:
                    text = "x: {}, y: {:.2f}, \n v: {:.1f}".format(x_label, y, v)
                else:
                    text = "x: {}, y: {:.2f}, \n {}".format(x_label, y, v_dict[v])
            # Format for ensemble axis
            elif self.x_axis_type == "E":
                if v_dict is None:
                    text = "x: {:.2f}, y: {:.2f}, \n v: {:.2f}".format(
                        int(round(x)), y, v
                    )
                else:
                    text = "x: {}, y: {:.2f}, \n {}".format(int(round(x)), y, v_dict[v])
            # Format for length axis
            elif self.x_axis_type == "L":
                if v_dict is None:
                    text = "x: {:.2f}, y: {:.2f}, \n v: {:.2f}".format(x, y, v)
                else:
                    text = "x: {:.2f}, y: {:.2f}, \n {}".format(x, y, v_dict[v])
        # Annotation for time series
        else:
            # Format for time axis
            if self.x_axis_type == "T":
                x_label = num2date(pos[0]).strftime("%H:%M:%S.%f")[:-4]
                text = "x: {}, y: {:.2f}".format(x_label, y)
            # Format for ensemble axis
            elif self.x_axis_type == "E":
                text = "x: {:.0f}, y: {:.2f}".format(int(round(x)), y)
            # Format for length axis
            elif self.x_axis_type == "L":
                text = "x: {:.2f}, y: {:.2f}".format(x, y)

        annot_ref.set_text(text)

    @contextmanager
    def wait_cursor(self):
        """Provide a busy cursor to the user while the code is processing."""
        try:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            yield
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

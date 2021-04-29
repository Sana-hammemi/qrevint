import numpy as np
import copy
from matplotlib import gridspec
import matplotlib.cm as cm
from matplotlib.dates import DateFormatter, num2date
from datetime import datetime
from MiscLibs.common_functions import sind, cosd


class WTAdvanced(object):
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
        List of dictionaries containing the type of plot an values of data plotted (x, y, z)
    gs: gridspec
        Grid specification for subplots
    wt_advanced_type_methods: dict
        Dictionary connecting to the plot type to the method to create the plot
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
        self.x_axis_type = 'E'
        self.fig_no = 0
        self.color_map = 'viridis'
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
        self.wt_advanced_type_methods = {'cb_speed_filtered_cc': self.speed_filtered_contour,
                                         'cb_speed_final_cc': self.speed_final_contour,
                                         'cb_projected_cc': self.projected_contour,
                                         'cb_vertical_cc': self.vertical_contour,
                                         'cb_error_cc': self.error_contour,
                                         'cb_direction_cc': self.direction_contour,
                                         'cb_avg_corr_cc': self.avg_corr_contour,
                                         'cb_corr_beam_cc': self.corr_beam_contour,
                                         'cb_avg_rssi_cc': self.avg_rssi_contour,
                                         'cb_rssi_beam_cc': self.rssi_beam_contour,
                                         'cb_discharge_ts': self.discharge_ts,
                                         'cb_discharge_percent_ts': self.discharge_percent_ts,
                                         'cb_avg_speed_ts': self.avg_speed_ts,
                                         'cb_projected_speed_ts': self.projected_speed_ts,
                                         'cb_bt_boat_speed_ts': self.bt_speed_ts,
                                         'cb_bt_3beam_ts': self.bt_3beam_ts,
                                         'cb_bt_error_ts': self.bt_error_ts,
                                         'cb_bt_vertical_ts': self.bt_vertical_ts,
                                         'cb_bt_source_ts': self.bt_source_ts,
                                         'cb_gga_boat_speed_ts': self.gga_speed_ts,
                                         'cb_vtg_boat_speed_ts': self.vtg_speed_ts,
                                         'cb_gga_quality_ts': self.gga_quality_ts,
                                         'cb_gga_hdop_ts': self.gga_hdop_ts,
                                         'cb_gga_altitude_ts': self.gga_altitude_ts,
                                         'cb_gga_sats_ts': self.gga_sats_ts,
                                         'cb_gga_source_ts': self.gga_source_ts,
                                         'cb_vtg_source_ts': self.vtg_source_ts,
                                         'cb_adcp_heading_ts': self.heading_adcp_ts,
                                         'cb_ext_heading_ts': self.heading_external_ts,
                                         'cb_mag_error_ts': self.mag_error_ts,
                                         'cb_pitch_ts': self.pitch_ts,
                                         'cb_roll_ts': self.roll_ts,
                                         'cb_beam_depths_ts': self.depths_beam_ts,
                                         'cb_final_depths_ts': self.depths_final_ts,
                                         'cb_depths_source_ts': self.depths_source_ts
                                        }

    def create(self, transect, discharge, units, selected_types, flow_direction, color_map='viridis', x_axis_type=None,
               show_below_sl=False):
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
            Specifies what variable (ensemble, length or time) to be used for the x-axis
        """

        # Make sure a selection was made
        if len(selected_types) > 0:

            # Initialize data sources
            self.flow_direction = flow_direction
            self.transect = transect
            self.discharge = discharge

            self.show_below_sl = show_below_sl

            # Set default axis
            if x_axis_type is None:
                x_axis_type = 'E'
            self.x_axis_type = x_axis_type

            # Set color map and units
            self.color_map = color_map
            self.units = units

            # Clear the plot
            self.fig.clear()

            # Determine number of subplots
            self.n_subplots = len(selected_types)
            if 'cb_corr_beam_cc' in selected_types:
                self.n_subplots += 3
            if 'cb_rssi_beam_cc' in selected_types:
                self.n_subplots += 3

            # Compute x-axis variable
            self.compute_x_axis()

            # Initialize variable for subplots
            self.ax = []
            self.annot = []
            self.data_plotted = []
            share_y = False

            # Create grid specification
            # Note: the second column of the grid is for the color bar. It is blank but present even for time series
            # plots to allow the sharing of the x-axis between all plots
            self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])

            # Create first subplot
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))
            self.wt_advanced_type_methods[selected_types[0]]()
            # Share the y-axis between color contour plots
            if selected_types[0][-3:] == '_cc':
                share_y = True

            # Create additional subplots as specified, sharing x axis for all plots and also y axis for contour plots
            if len(selected_types) > 1:
                for n in range(1, len(selected_types)):
                    # Figure number increased by two to account for the second column in the grid space for the colorbar
                    self.fig_no += 2
                    if share_y and selected_types[n][-3:] == '_cc':
                        self.ax.append(self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0], sharey=self.ax[0]))
                    else:
                        self.ax.append(self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0]))
                    # Call method based on link in dictionary
                    self.wt_advanced_type_methods[selected_types[n]]()

            # Adjust the spacing of the subplots
            self.fig.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.02, hspace=0.08)

            # Apply the x-axis label to the bottom x-axis
            if selected_types[-1][-3:] == '_cc':
                idx = -2
            else:
                idx = -1

            self.ax[idx].xaxis.label.set_fontsize(12)

            # x-axis is length
            if self.x_axis_type == 'L':
                if self.transect.start_edge == 'Right':
                    self.ax[idx].invert_xaxis()
                    self.ax[idx].set_xlim(right=-1 * self.x[-1] * 0.02, left=self.x[-1] * 1.02)
                else:
                    self.ax[idx].set_xlim(left=-1 * self.x[-1] * 0.02, right=self.x[-1] * 1.02)
                self.ax[idx].set_xlabel(self.canvas.tr('Length' + self.units['label_L']))

            # x-axis is ensembles
            elif self.x_axis_type == 'E':
                if self.transect.start_edge == 'Right':
                    self.ax[idx].invert_xaxis()
                    self.ax[idx].set_xlim(right=0, left=self.x[-1] + 1)
                else:
                    self.ax[idx].set_xlim(left=0, right=self.x[-1] + 1)
                self.ax[idx].set_xlabel(self.canvas.tr('Ensembles'))

            # x-axis is time
            elif self.x_axis_type == 'T':
                axis_buffer = (self.x_timestamp[-1] - self.x_timestamp[0]) * 0.02
                if self.transect.start_edge == 'Right':
                    self.ax[idx].invert_xaxis()
                    self.ax[idx].set_xlim(right=datetime.utcfromtimestamp(self.x_timestamp[0] - axis_buffer),
                                          left=datetime.utcfromtimestamp(self.x_timestamp[-1] + axis_buffer))
                else:
                    self.ax[idx].set_xlim(left=datetime.utcfromtimestamp(self.x_timestamp[0] - axis_buffer),
                                          right=datetime.utcfromtimestamp(self.x_timestamp[-1] + axis_buffer))
                date_form = DateFormatter('%H:%M:%S')
                self.ax[idx].xaxis.set_major_formatter(date_form)
                self.ax[idx].set_xlabel(self.canvas.tr('Time'))

        else:
            # Clear the plot
            self.fig.clear()

        self.canvas.draw()

    def avg_corr_contour(self):
        """Creates average correlation contour plot.
        """

        # Compute average of correlation data for each cel
        data = np.nanmean(self.transect.w_vel.corr, axis=0)
        if not self.show_below_sl:
            data[self.transect.w_vel.cells_above_sl == False] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)

        # Plot the data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, 'Correlation \n (counts)'))

    def avg_rssi_contour(self):
        """Creates average return signal strength or SNR contour plot.
        """

        # Compute mean signal strength for each cell
        data = np.nanmean(self.transect.w_vel.rssi, axis=0)
        if not self.show_below_sl:
            data[self.transect.w_vel.cells_above_sl == False] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)

        # Create label based on manufacturer
        if self.transect.adcp.manufacturer == 'TRDI':
            data_label = 'Intensity \n (counts)'
        elif self.transect.adcp.manufacturer == 'SonTek':
            data_label = 'SNR (dB)'
        else:
            data_label = 'Intensity'

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, data_label))

    def avg_speed_ts(self):
        """Create average water speed time series plot.
        """

        # Compute mean water speed for each ensemble using a weighted average based on depth cell size
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_speed = np.sqrt(water_u ** 2 + water_v ** 2)
        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        weight = depth_selected.depth_cell_size_m[:, self.transect.in_transect_idx]
        avg_speed = np.nansum(water_speed * weight, axis=0) / np.nansum(weight, axis=0)

        # Plot data
        data_units = (self.units['V'], 'Water speed \n' + self.units['label_V'])
        self.plt_timeseries(data=avg_speed,
                            data_units=data_units,
                            ax=self.ax[-1])

    def corr_beam_contour(self):
        """Create contour plots of the correlation in each beam.
        """

        # Create data to be plotted
        data_all = np.copy(self.transect.w_vel.corr)
        if not self.show_below_sl:
            for n in range(data_all.shape[0]):
                data_all[n, self.transect.w_vel.cells_above_sl == False] = np.nan

        # Compute the minimum and maximum limits based on all the correlations so each beam has the same color scale
        data_limits = [np.nanmin(data_all), np.nanmax(data_all)]

        # Get data for beam 1
        data = data_all[0, :, :]

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, 'Beam 1 Corr. \n (counts)'),
                         data_limits=data_limits)

        # Prepare and plot beams 2-4
        for n in range(1, 4):
            # Figure number increases by 2 to account for 2nd column in gridspec used for color bar
            self.fig_no += 2

            # Add subplot
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0], sharey=self.ax[0]))

            # Get data for beam n+1
            data = data_all[n, :, :]

            # Compute data for contour plot
            x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)

            # Plot data
            self.plt_contour(x_plt_in=x_plt,
                             cell_plt_in=cell_plt,
                             data_plt_in=data_plt,
                             x=self.x,
                             depth=depth,
                             data_units=(1, 'Beam ' + str(n+1) + ' Corr. \n (counts)'),
                             data_limits=data_limits)

    def direction_contour(self):
        """Create flow direction contour plot.
        """

        # Compute flow direction using discharge weighting
        u_water = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        v_water = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_dir = np.arctan2(u_water, v_water) * 180 / np.pi
        water_dir[water_dir < 0] = water_dir[water_dir < 0] + 360

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, water_dir, x_1d=x_1d)

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, 'Water Direction \n (deg)'))

    def discharge_ts(self):
        """Create cumulative discharge time series by ensemble.
        """

        # Prepare data so that data will plot from left bank to right bank
        if self.transect.start_edge == 'Right':
            q_ts = self.discharge.top_ens + self.discharge.middle_ens + self.discharge.bottom_ens
            q_ts = np.nancumsum(q_ts)
            q_ts[0] = q_ts[0] + self.discharge.right
            q_ts[-1] = q_ts[-1] + self.discharge.left
        else:
            q_ts = self.discharge.top_ens + self.discharge.middle_ens + self.discharge.bottom_ens
            q_ts = np.nancumsum(q_ts)
            q_ts[0] = q_ts[0] + self.discharge.left
            q_ts[-1] = q_ts[-1] + self.discharge.right

        # Plot data
        data_units = (self.units['Q'], 'Discharge ' + self.units['label_Q'])
        self.plt_timeseries(data=q_ts,
                            data_units=data_units,
                            ax=self.ax[-1])

    def discharge_percent_ts(self):
        """Create plot of cumulative percent discharge by ensemble.
        """

        # Prepare data so that data will plot from left bank to right bank
        if self.transect.start_edge == 'Right':
            q_ts = self.discharge.top_ens + self.discharge.middle_ens + self.discharge.bottom_ens
            q_ts = np.nancumsum(q_ts)
            q_ts[0] = q_ts[0] + self.discharge.right
            q_ts[-1] = q_ts[-1] + self.discharge.left
        else:
            q_ts = self.discharge.top_ens + self.discharge.middle_ens + self.discharge.bottom_ens
            q_ts = np.nancumsum(q_ts)
            q_ts[0] = q_ts[0] + self.discharge.left
            q_ts[-1] = q_ts[-1] + self.discharge.right

        # Compute percent of total
        q_ts_per = (q_ts / self.discharge.total) * 100

        # Plot data
        data_units = (1, 'Discharge (%)')
        self.plt_timeseries(data=q_ts_per,
                            data_units=data_units,
                            ax=self.ax[-1])

    def error_contour(self):
        """Creat contour plot of error velocities.
        """

        # Get data
        data = self.transect.w_vel.d_mps
        data[self.transect.w_vel.cells_above_sl == False] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Error Velocity \n' + self.units['label_V']))

    def projected_contour(self):
        """Create contour plot of water speed projected in flow direction.
        """

        # Compute projected water speed
        unit_vector = np.array([[sind(self.flow_direction)], [cosd(self.flow_direction)]])
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        projected_speed = unit_vector[0] * water_u + unit_vector[1] * water_v

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, projected_speed, x_1d=x_1d)

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Projected \n Speed' + self.units['label_V']))

    def projected_speed_ts(self):
        """Create time series plot of projected water speed.
        """

        # Compute projected water speed for each cell
        unit_vector = np.array([[sind(self.flow_direction)], [cosd(self.flow_direction)]])
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        projected_speed = unit_vector[0] * water_u + unit_vector[1] * water_v

        # Compute the mean projected speed in each ensemble using depth cell size weighting
        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        weight = depth_selected.depth_cell_size_m[:, self.transect.in_transect_idx]
        avg_speed = np.nansum(projected_speed * weight, axis=0) / np.nansum(weight, axis=0)

        # Plot data
        data_units = (self.units['V'], 'Projected \n Speed ' + self.units['label_V'])
        self.plt_timeseries(data=avg_speed,
                            data_units=data_units,
                            ax=self.ax[-1])

    def rssi_beam_contour(self):
        """Create contour plot of the signal intensity for each beam.
        """

        # Set label and units based on data available by manufacturer
        if self.transect.adcp.manufacturer == 'TRDI':
            data_label = '\n RSSI (counts)'
        elif self.transect.adcp.manufacturer == 'SonTek':
            data_label = '\n SNR (dB)'
        else:
            data_label = '\n Intensity'

        # Create data to be plotted
        data_all = np.copy(self.transect.w_vel.rssi)
        if not self.show_below_sl:
            for n in range(data_all.shape[0]):
                data_all[n, self.transect.w_vel.cells_above_sl == False] = np.nan

        # Determine limits for all data so a common scale can be used for all 4 plots
        data_limits = [np.nanmin(data_all), np.nanmax(data_all)]

        # Get data for beam 1
        data = data_all[0, :, :]

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, 'Beam 1' + data_label),
                         data_limits=data_limits)

        # Prepare and plot data for beams 2-4
        for n in range(1, 4):
            self.fig_no += 2
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0], sharey=self.ax[0]))
            data = data_all[n, :, :]
            x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
            self.plt_contour(x_plt_in=x_plt,
                             cell_plt_in=cell_plt,
                             data_plt_in=data_plt,
                             x=self.x,
                             depth=depth,
                             data_units=(1, 'Beam ' + str(n + 1) + data_label),
                             data_limits=data_limits)

    def speed_filtered_contour(self):
        """Create contour of water speed with no interpolation for invalid water data.
        """

        # Compute water speed for each cell
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_speed = np.sqrt(water_u ** 2 + water_v ** 2)
        water_speed[np.logical_not(self.transect.w_vel.valid_data[0, :, :])] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, water_speed, x_1d=x_1d)

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Filtered \n Speed ' + self.units['label_V']))

    def speed_final_contour(self):
        """Contour plot of water speed with interpolation for invalid data.
        """

        # Compute water speed for each cell
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_speed = np.sqrt(water_u ** 2 + water_v ** 2)

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, water_speed, x_1d=x_1d)

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Interpolated \n Speed ' + self.units['label_V']))

    def vertical_contour(self):
        """Create contour plot of vertical velocities.
        """

        # Get data
        data = np.copy(self.transect.w_vel.w_mps)
        data[self.transect.w_vel.cells_above_sl == False] = np.nan

        # Set the 1-dimensional x-axis data based on selected x-axis type. Timestamp must be used for time
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x

        # Compute data for contour plot
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)

        # Plot data
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Vertical \n Velocity' + self.units['label_V']))

    def bt_speed_ts(self):

        data = np.sqrt(self.transect.boat_vel.bt_vel.u_processed_mps ** 2
                        + self.transect.boat_vel.bt_vel.v_processed_mps ** 2)
        invalid = np.logical_not(self.transect.boat_vel.bt_vel.valid_data)
        data_invalid = np.sqrt(self.transect.boat_vel.bt_vel.u_mps ** 2
                               + self.transect.boat_vel.bt_vel.v_mps ** 2)
        fmt = [{'color': 'b', 'linestyle': '-' },
               {'color': 'r', 'linestyle': '', 'marker': '$O$'},
               {'color': 'r', 'linestyle': '', 'marker': '$E$'},
               {'color': 'r', 'linestyle': '', 'marker': '$V$'},
               {'color': 'r', 'linestyle': '', 'marker': '$S$'},
               {'color': 'r', 'linestyle': '', 'marker': '$B$'}]

        data_units = (self.units['V'], 'BT Speed ' + self.units['label_V'])
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            data_2=data_invalid,
                            data_mask=invalid,
                            fmt=fmt)

    def bt_3beam_ts(self):

        # Determine number of beams for each ensemble
        bt_temp = copy.deepcopy(self.transect.boat_vel.bt_vel)
        bt_temp.filter_beam(4)
        valid_4beam = bt_temp.valid_data[5, :].astype(int)
        data = np.copy(valid_4beam).astype(int)
        data[valid_4beam == 1] = 4
        data[valid_4beam == 0] = 3
        data[np.logical_not(self.transect.boat_vel.bt_vel.valid_data[1, :])] = 0

        # Configure plot settings
        invalid = np.logical_not(self.transect.boat_vel.bt_vel.valid_data[5, :]).tolist()
        fmt = [{'color': 'b', 'linestyle': '', 'marker': '.'},
               {'color': 'r', 'linestyle': '', 'marker': 'o', 'markerfacecolor': 'none'}]
        data_units = (1, 'Number of Beams ')
        data_mask = [[], invalid]

        # Plot data
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            data_mask=data_mask,
                            fmt=fmt)

    def bt_error_ts(self):
        # Plot error velocity
        y_data = self.transect.boat_vel.bt_vel.d_mps
        invalid = np.logical_not(self.transect.boat_vel.bt_vel.valid_data[2, :]).tolist()
        data_units = (self.units['V'], 'BT Error Vel ' + self.units['label_V'])

        if not self.transect.boat_vel.bt_vel.d_meas_thresholds:
            fmt = [{'marker': '.', 'linestyle': '-', 'mfc': 'b', 'mec': 'b'},
                   {'color': 'r', 'ms': 8, 'linestyle': '-', 'mfc': 'none'}]

            self.plt_timeseries(data=y_data,
                                data_units=data_units,
                                ax=self.ax[-1],
                                data_mask=invalid,
                                fmt=fmt)
        else:
            freq_used = np.unique(self.transect.boat_vel.bt_vel.frequency_khz).astype(int).astype(str)
            freq_color = {'0': 'b', '600': 'b', '1200': 'b', '1000': 'b', '2000': 'b', '2400': 'b', '3000': '#009933'}
            freq_marker = {'0': '.', '600': '.', '1200': '.', '1000': '.', '2000': '.', '2400': '.', '3000': '+'}

            freq_ensembles = self.transect.boat_vel.bt_vel.frequency_khz.astype(int).astype(str)

            data_mask = []
            fmt = []
            for freq in freq_used:
                data_mask.append(freq_ensembles == freq)
                fmt.append({'marker': freq_marker[freq], 'linestyle': '', 'mfc': freq_color[freq],
                            'mec': freq_color[freq]})
            data_mask.append(invalid)
            fmt.append({'marker': 'o', 'color': 'r', 'ms': 8, 'linestyle': '', 'mfc': 'none'})

            self.plt_timeseries(data=None,
                                data_units=data_units,
                                ax=self.ax[-1],
                                data_2=y_data,
                                data_mask=data_mask,
                                fmt=fmt)

            # Create legend
            legend_dict = {'600': '600 kHz', '1200': '1200 kHz', '1000': '1 MHz', '2000': '2 MHz',
                           '2400': '2.4 MHz', '3000': '3 MHz', '0': 'N/U'}
            legend_txt = []
            for freq in freq_used:
                legend_txt.append(legend_dict[freq])
            self.ax[-1].legend(legend_txt)

    def bt_vertical_ts(self):
        y_data = self.transect.boat_vel.bt_vel.w_mps
        invalid = np.logical_not(self.transect.boat_vel.bt_vel.valid_data[3, :]).tolist()
        data_units = (self.units['V'], 'BT Vertical Vel ' + self.units['label_V'])

        if not self.transect.boat_vel.bt_vel.w_meas_thresholds:
            fmt = [{'marker': '.', 'linestyle': '-', 'mfc': 'b', 'mec': 'b'},
                   {'color': 'r', 'ms': 8, 'linestyle': '-', 'mfc': 'none'}]

            self.plt_timeseries(data=y_data,
                                data_units=data_units,
                                ax=self.ax[-1],
                                data_mask=invalid,
                                fmt=fmt)
        else:
            freq_used = np.unique(self.transect.boat_vel.bt_vel.frequency_khz).astype(int).astype(str)
            freq_color = {'0': 'b', '600': 'b', '1200': 'b', '1000': 'b', '2000': 'b', '2400': 'b', '3000': '#009933'}
            freq_marker = {'0': '.', '600': '.', '1200': '.', '1000': '.', '2000': '.', '2400': '.', '3000': '+'}

            freq_ensembles = self.transect.boat_vel.bt_vel.frequency_khz.astype(int).astype(str)

            data_mask = []
            fmt = []
            for freq in freq_used:
                data_mask.append(freq_ensembles == freq)
                fmt.append({'marker': freq_marker[freq], 'linestyle': '', 'mfc': freq_color[freq],
                            'mec': freq_color[freq]})
            data_mask.append(invalid)
            fmt.append({'marker': 'o', 'color': 'r', 'ms': 8, 'linestyle': '', 'mfc': 'none'})

            self.plt_timeseries(data=None,
                                data_units=data_units,
                                ax=self.ax[-1],
                                data_2=y_data,
                                data_mask=data_mask,
                                fmt=fmt)

            # Create legend
            legend_dict = {'600': '600 kHz', '1200': '1200 kHz', '1000': '1 MHz', '2000': '2 MHz',
                           '2400': '2.4 MHz', '3000': '3 MHz', '0': 'N/U'}
            legend_txt = []
            for freq in freq_used:
                legend_txt.append(legend_dict[freq])
            self.ax[-1].legend(legend_txt)

    def bt_source_ts(self):

        self.source_ts(self.transect.boat_vel.bt_vel, 'BT Source')

    def gga_source_ts(self):

        self.source_ts(self.transect.boat_vel.gga_vel, 'GGA Source')

    def vtg_source_ts(self):

        self.source_ts(self.transect.boat_vel.vtg_vel, 'VTG Source')

    def source_ts(self, selected, axis_label):
        # Handle situation where transect does not contain the selected source
        if selected is None:
            source = np.tile('INV', len(self.x))
        else:
            source = selected.processed_source

        # Plot dummy data to establish consistent order of y axis
        temp_hold = np.copy(self.x)
        self.x = [-10, -10, -10, -10, -10]
        data = ['INV', 'INT', 'BT', 'GGA', 'VTG']
        fmt = [{'color': 'w', 'linestyle': '-'}]
        data_units = (1, '')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)

        self.x = np.copy(temp_hold)
        data_units = (1, axis_label)
        fmt = [{'color': 'b', 'linestyle': '', 'marker': '.'}]
        self.plt_timeseries(data=source,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)
        self.ax[-1].set_yticks(['INV', 'INT', 'BT', 'GGA', 'VTG'])

    def gga_quality_ts(self):
        # GPS Quality
        data = self.transect.gps.diff_qual_ens
        fmt = [{'color': 'b', 'linestyle': '', 'marker': '.'}]
        invalid = np.logical_not(self.transect.boat_vel.gga_vel.valid_data[2, :]).tolist()
        data_mask = [[], invalid]
        fmt.append({'color': 'r', 'marker': 'o', 'linestyle': '', 'mfc': 'none'})
        data_units = (1, 'GGA Quality')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            data_mask=data_mask,
                            ax=self.ax[-1],
                            fmt=fmt)
        # Format axis
        yint = range(0, int(np.ceil(np.nanmax(self.transect.gps.diff_qual_ens)) + 1))
        self.ax[-1].set_ylim(top=np.nanmax(yint) + 0.5, bottom=np.nanmin(yint) - 0.5)
        self.ax[-1].set_yticks(yint)

    def gga_hdop_ts(self):

        # Plot HDOP
        data = self.transect.gps.hdop_ens
        fmt = [{'color': 'b', 'linestyle': '', 'marker': '.'}]
        invalid = np.logical_not(self.transect.boat_vel.gga_vel.valid_data[5, :]).tolist()
        data_mask = [[], invalid]
        fmt.append({'color': 'r', 'marker': 'o', 'linestyle': '', 'mfc': 'none'})
        data_units = (1, 'GGA HDOP')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            data_mask=data_mask,
                            ax=self.ax[-1],
                            fmt=fmt)

        max_y = np.nanmax(self.transect.gps.hdop_ens) + 0.5
        min_y = np.nanmin(self.transect.gps.hdop_ens) - 0.5
        self.ax[-1].set_ylim(top=max_y, bottom=min_y)

    def gga_altitude_ts(self):
        data = self.transect.gps.altitude_ens_m
        fmt = [{'color': 'b', 'linestyle': '', 'marker': '.'}]
        invalid = np.logical_not(self.transect.boat_vel.gga_vel.valid_data[3, :]).tolist()
        data_mask = [[], invalid]
        fmt.append({'color': 'r', 'marker': 'o', 'linestyle': '', 'mfc': 'none'})
        data_units = (self.units['L'], 'GGA Altitude ' + self.units['label_L'])
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            data_mask=data_mask,
                            ax=self.ax[-1],
                            fmt=fmt)

    def gga_sats_ts(self):

        data = self.transect.gps.num_sats_ens
        fmt = [{'color': 'b', 'linestyle': '', 'marker': '.'}]
        data_units = (1, 'No. of Sats')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)
        try:
            max_y = np.nanmax(self.transect.gps.num_sats_ens) + 0.5
            min_y = np.nanmin(self.transect.gps.num_sats_ens) - 0.5
            self.ax[-1].set_ylim(top=max_y, bottom=min_y)
            yint = range(int(min_y), int(max_y) + 1)
            self.ax[-1].set_yticks(yint)
        except ValueError:
            pass

    def gga_speed_ts(self):

        data = np.sqrt(self.transect.boat_vel.gga_vel.u_processed_mps ** 2
                        + self.transect.boat_vel.gga_vel.v_processed_mps ** 2)
        invalid = np.logical_not(self.transect.boat_vel.gga_vel.valid_data)
        data_invalid = np.sqrt(self.transect.boat_vel.gga_vel.u_mps ** 2
                               + self.transect.boat_vel.gga_vel.v_mps ** 2)
        fmt = [{'color': 'b', 'linestyle': '-' },
               {'color': 'r', 'linestyle': '', 'marker': '$O$'},
               {'color': 'r', 'linestyle': '', 'marker': '$Q$'},
               {'color': 'r', 'linestyle': '', 'marker': '$A$'},
               {'color': 'r', 'linestyle': '', 'marker': '$S$'},
               {'color': 'r', 'linestyle': '', 'marker': '$H$'}]

        data_units = (self.units['V'], 'GGA Speed ' + self.units['label_V'])
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            data_2=data_invalid,
                            data_mask=invalid,
                            fmt=fmt)

    def vtg_speed_ts(self):

        data = np.sqrt(self.transect.boat_vel.vtg_vel.u_processed_mps ** 2
                        + self.transect.boat_vel.vtg_vel.v_processed_mps ** 2)
        invalid = np.logical_not(self.transect.boat_vel.vtg_vel.valid_data)
        data_mask=[[], invalid[1], invalid[4], invalid[5]]
        data_invalid = np.sqrt(self.transect.boat_vel.vtg_vel.u_mps ** 2
                               + self.transect.boat_vel.vtg_vel.v_mps ** 2)
        fmt = [{'color': 'b', 'linestyle': '-' },
               {'color': 'r', 'linestyle': '', 'marker': '$O$'},
               {'color': 'r', 'linestyle': '', 'marker': '$S$'},
               {'color': 'r', 'linestyle': '', 'marker': '$H$'}]

        data_units = (self.units['V'], 'GGA Speed ' + self.units['label_V'])
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            data_2=data_invalid,
                            data_mask=data_mask,
                            fmt=fmt)

    def heading_adcp_ts(self):

        data = self.transect.sensors.heading_deg.internal.data
        fmt = [{'color': 'b', 'linestyle': '-'}]
        data_units = (1, 'ADCP Heading (deg)')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)

    def heading_external_ts(self):

        data = self.transect.sensors.heading_deg.external.data
        fmt = [{'color': 'b', 'linestyle': '-'}]
        data_units = (1, 'Ext. Heading (deg)')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)

    def mag_error_ts(self):

        data = self.transect.sensors.heading_deg.internal.mag_error
        fmt = [{'color': 'b', 'linestyle': '-'}]
        data_units = (1, 'Mag Error')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)

    def pitch_ts(self):

        data = self.transect.sensors.pitch_deg.internal.data
        fmt = [{'color': 'b', 'linestyle': '-'}]
        data_units = (1, 'Pitch (deg)')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)

    def roll_ts(self):

        data = self.transect.sensors.roll_deg.internal.data
        fmt = [{'color': 'b', 'linestyle': '-'}]
        data_units = (1, 'Roll (deg)')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)

    def depths_beam_ts(self):

        invalid_beams = np.logical_not(self.transect.depths.bt_depths.valid_beams).tolist()
        beam_depths = self.transect.depths.bt_depths.depth_beams_m
        # Compute max depth from beams
        max_depth = [np.nanmax(np.nanmax(beam_depths))]
        data_mask = [[], invalid_beams[0]]
        data_units = (self.units['L'], 'Depth ' + self.units['label_L'])
        fmt = [{'color': 'k', 'linestyle': '-', 'marker': 'o',  'markersize': 4, 'label': 'B1'},
               {'color': 'r', 'linestyle': '', 'marker': 'o', 'markersize': 8, 'markerfacecolor': 'none', 'label': None}]
        self.plt_timeseries(data=beam_depths[0, :],
                            data_units=data_units,
                            data_mask=data_mask,
                            ax=self.ax[-1],
                            fmt=fmt,
                            set_annot=True)

        data_mask = [[], invalid_beams[1]]
        data_units = (self.units['L'], '')
        fmt = [{'color': '#005500', 'linestyle': '-', 'marker': 'o', 'markersize': 4, 'label': 'B2'},
               {'color': 'r', 'linestyle': '', 'marker': 'o', 'markersize': 8, 'markerfacecolor': 'none', 'label': None}]
        self.plt_timeseries(data=beam_depths[1, :],
                            data_units=data_units,
                            data_mask=data_mask,
                            ax=self.ax[-1],
                            fmt=fmt,
                            set_annot=False)

        data_mask = [[], invalid_beams[2]]
        data_units = (self.units['L'], '')
        fmt = [{'color': 'b', 'linestyle': '-', 'marker': 'o', 'markersize': 4, 'label': 'B3'},
               {'color': 'r', 'linestyle': '', 'marker': 'o', 'markersize': 8, 'markerfacecolor': 'none', 'label': None}]
        self.plt_timeseries(data=beam_depths[2, :],
                            data_units=data_units,
                            data_mask=data_mask,
                            ax=self.ax[-1],
                            fmt=fmt,
                            set_annot=False)

        data_mask = [[], invalid_beams[3]]
        data_units = (self.units['L'], '')
        fmt = [{'color': '#aa5500', 'linestyle': '-', 'marker': 'o', 'markersize': 4, 'label': 'B4'},
               {'color': 'r', 'linestyle': '', 'marker': 'o', 'markersize': 8, 'markerfacecolor': 'none', 'label': None}]
        self.plt_timeseries(data=beam_depths[3, :],
                            data_units=data_units,
                            data_mask=data_mask,
                            ax=self.ax[-1],
                            fmt=fmt,
                            set_annot=False)

        if self.transect.depths.vb_depths is not None:
            invalid_beams = np.logical_not(self.transect.depths.vb_depths.valid_beams[0, :]).tolist()
            beam_depths = self.transect.depths.vb_depths.depth_beams_m[0, :]
            data_mask = [[], invalid_beams]
            data_units = (self.units['L'], '')
            fmt = [{'color': '#aa00ff', 'linestyle': '-', 'marker': 'o', 'markersize': 4, 'label': 'VB'},
                   {'color': 'r', 'linestyle': '', 'marker': 'o', 'markersize': 8, 'markerfacecolor': 'none', 'label': None}]
            self.plt_timeseries(data=beam_depths,
                                data_units=data_units,
                                data_mask=data_mask,
                                ax=self.ax[-1],
                                fmt=fmt,
                            set_annot=False)

            max_depth.append(np.nanmax(beam_depths))

        if self.transect.depths.ds_depths is not None:
            invalid_beams = np.logical_not(self.transect.depths.ds_depths.valid_beams[0, :])
            beam_depths = self.transect.depths.ds_depths.depth_beams_m[0, :]
            data_mask = [[], invalid_beams]
            data_units = (self.units['L'], '')
            fmt = [{'color': '#00aaff', 'linestyle': '-', 'marker': 'o', 'markersize': 4, 'label': 'DS'},
                   {'color': 'r', 'linestyle': '', 'marker': 'o', 'markersize': 8, 'markerfacecolor': 'none', 'label': None}]
            self.plt_timeseries(data=beam_depths,
                                data_units=data_units,
                                data_mask=data_mask,
                                ax=self.ax[-1],
                                fmt=fmt,
                            set_annot=False)

            max_depth.append(np.nanmax(beam_depths))

        self.ax[-1].legend()
        self.ax[-1].invert_yaxis()
        self.ax[-1].set_ylim(bottom=np.ceil(np.nanmax(max_depth) * 1.1 * self.units['L']), top=0)

    def depths_final_ts(self):

        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        beam_depths = depth_selected.depth_processed_m

        data_units = (self.units['L'], 'Depth ' + self.units['label_L'])
        fmt = [{'color': 'k', 'linestyle': '-', 'marker': 'o', 'markersize': 4}]
        self.plt_timeseries(data=beam_depths,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)
        self.ax[-1].invert_yaxis()
        self.ax[-1].set_ylim(bottom=np.ceil(np.nanmax(beam_depths) * 1.1 * self.units['L']), top=0)

    def depths_source_ts(self):

        # Handle situation where transect does not contain the selected source
        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        source = depth_selected.depth_source_ens

        # Plot dummy data to establish consistent order of y axis
        temp_hold = np.copy(self.x)
        self.x = [-10, -10, -10, -10, -10]
        data = ['INV', 'INT', 'BT', 'VB', 'DS']
        fmt = [{'color': 'w', 'linestyle': '-'}]
        data_units = (1, '')
        self.plt_timeseries(data=data,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)

        self.x = np.copy(temp_hold)
        data_units = (1, 'Depth Source')
        fmt = [{'color': 'b', 'linestyle': '', 'marker': '.'}]
        self.plt_timeseries(data=source,
                            data_units=data_units,
                            ax=self.ax[-1],
                            fmt=fmt)
        self.ax[-1].set_yticks(['INV', 'INT', 'BT', 'VB', 'DS'])

    def compute_x_axis(self):
        """Compute x axis data.
        """

        # Initialize x
        x = None

        # x axis is length
        if self.x_axis_type == 'L':
            boat_track = self.transect.boat_vel.compute_boat_track(transect=self.transect)
            if not np.alltrue(np.isnan(boat_track['track_x_m'])):
                x = boat_track['distance_m'] * self.units['L']
            self.x = x[self.transect.in_transect_idx]

        # x axis is ensembles
        elif self.x_axis_type == 'E':
            x = np.arange(1, len(self.transect.depths.bt_depths.depth_processed_m) + 1)
            self.x = x[self.transect.in_transect_idx]

        # x axis is time
        elif self.x_axis_type == 'T':
            timestamp = np.nancumsum(self.transect.date_time.ens_duration_sec) \
                        + self.transect.date_time.start_serial_time
            x = np.copy(timestamp)
            # Timestamp is needed to create contour plots and  setting axis limits
            self.x_timestamp = x[self.transect.in_transect_idx]
            x = []
            # datetime is needed to plot timeseries and x-axis labels
            for stamp in timestamp:
                x.append(datetime.utcfromtimestamp(stamp))
            x = np.array(x)
            self.x = x[self.transect.in_transect_idx]

    @staticmethod
    def contour_data_prep(transect, data, x_1d=None):
        """Modifies the selected data from transect into arrays matching the meshgrid format for
        creating contour or color plots.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing data to be plotted
        data: np.ndarray()
            Contour data
        x_1d: np.array
            Array of x-coordinates for each ensemble

        Returns
        -------
        x_plt: np.array
            Data in meshgrid format used for the contour x variable
        cell_plt: np.array
            Data in meshgrid format used for the contour y variable
        data_plt: np.array
            Data in meshgrid format used to determine colors in plot
        ensembles: np.array
            Ensemble numbers used as the x variable to plot the cross section bottom
        depth: np.array
            Depth data used to plot the cross section bottom
        """

        in_transect_idx = transect.in_transect_idx

        # Set x_1d if not specified
        if x_1d is None:
            x_1d = in_transect_idx

        # Get data from transect
        depth_selected = getattr(transect.depths, transect.depths.selected)
        depth = depth_selected.depth_processed_m[in_transect_idx]
        cell_depth = depth_selected.depth_cell_depth_m[:, in_transect_idx]
        cell_size = depth_selected.depth_cell_size_m[:, in_transect_idx]
        x_data = x_1d
        ensembles = in_transect_idx

        # Prep water speed to use -999 instead of nans
        data_2_plot = np.copy(data)
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

        return x_plt, cell_plt, data_plt, ensembles, depth

    def plt_contour(self, x_plt_in, cell_plt_in, data_plt_in, x, depth, data_units, data_limits=None):
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
        """

        # Use last subplot
        ax = self.ax[-1]

        # Create plot variables for input
        if self.x_axis_type == 'T':
            # If x axis is time, create x_plt
            x_plt = np.zeros(x_plt_in.shape, dtype='object')
            for r in range(x_plt_in.shape[0]):
                for c in range(x_plt_in.shape[1]):
                    x_plt[r, c] = datetime.utcfromtimestamp(x_plt_in[r, c])
        else:
            x_plt = x_plt_in

        cell_plt = cell_plt_in * self.units['L']
        data_plt = data_plt_in * data_units[0]

        # Determine limits for color map
        if data_limits is not None:
            max_limit = data_limits[1]
            min_limit = data_limits[0]
        elif np.sum(np.abs(data_plt_in[data_plt_in > -900])) > 0:
            max_limit = np.percentile(data_plt_in[data_plt_in > -900] * data_units[0], 99)
            min_limit = np.percentile(data_plt_in[data_plt_in > -900] * data_units[0], 1)
        else:
            max_limit = 1
            min_limit = 0

        # Create color map
        cmap = cm.get_cmap(self.color_map)
        cmap.set_under('white')

        # Generate color contour
        c = ax.pcolormesh(x_plt, cell_plt, data_plt, cmap=cmap, vmin=min_limit, vmax=max_limit)

        # Create data plotted for annotation use
        self.data_plotted.append({'type': 'contour', 'x': x_plt, 'y': cell_plt, 'z': data_plt})

        # Initialize annotation for data cursor
        self.annot.append(ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="w"),
                                      arrowprops=dict(arrowstyle="->")))

        self.annot[-1].set_visible(False)

        # Add color bar and axis labels in separate subplot
        self.ax.append(self.fig.add_subplot(self.gs[self.fig_no + 1]))
        self.data_plotted.append({'type': 'colorbar'})
        self.annot.append('')
        cb = self.fig.colorbar(c, self.ax[-1])
        cb.ax.set_ylabel(self.canvas.tr(data_units[1]))
        cb.ax.yaxis.label.set_fontsize(12)
        cb.ax.tick_params(labelsize=12)
        ax.invert_yaxis()

        # Plot depth
        ax.plot(x, depth * self.units['L'], color='k')

        depth_obj = getattr(self.transect.depths, self.transect.depths.selected)

        # Plot side lobe cutoff if available
        if self.transect.w_vel.sl_cutoff_m is not None:
            last_valid_cell = np.nansum(self.transect.w_vel.cells_above_sl, axis=0) - 1
            last_depth_cell_size = depth_obj.depth_cell_size_m[last_valid_cell,
                                                               np.arange(depth_obj.depth_cell_size_m.shape[1])]
            y_plt_sl = (self.transect.w_vel.sl_cutoff_m + (last_depth_cell_size * 0.5)) * self.units['L']
            ax.plot(x, y_plt_sl, color='r', linewidth=0.5)

        # Plot upper bound of measured depth cells
        y_plt_top = (depth_obj.depth_cell_depth_m[0, :]
                     - (depth_obj.depth_cell_size_m[0, :] * 0.5)) * self.units['L']
        ax.plot(x, y_plt_top, color='r', linewidth=0.5)

        # Label and limits for y axis
        ax.set_ylabel(self.canvas.tr('Depth ') + self.units['label_L'])
        ax.yaxis.label.set_fontsize(12)
        ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        ax.set_ylim(top=0, bottom=(np.nanmax(depth * self.units['L']) * 1.05))

    def plt_timeseries(self, data, data_units, ax=None, data_2=None, data_mask=None, fmt=None, set_annot=True):
        """Create timeseries plot.

        Parameters
        ----------
        data: np.ndarray()
            1-D array of data to be plotted
        data_units: tuple
            Tuple of data multiplier and label
        ax: subplot
            Optional subplot
        """

        # Use last subplot if not defined
        if ax is None:
            ax = self.ax[-1]

        # Setup plot
        ax.set_ylabel(self.canvas.tr(data_units[1]))
        ax.grid()
        ax.yaxis.label.set_fontsize(12)
        ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        # Plot data
        if fmt is not None:
            kwargs = fmt[0]
        else:
            kwargs = {'linestyle':'-', 'color':'b'}

        if data is not None:
            ax.plot(self.x, data * data_units[0], **kwargs)
        else:
            ax.plot(self.x[data_mask[0]], data_2[data_mask[0]], **kwargs)

        all_data = data
        if data_mask is not None:
            if data_2 is None:
                data_2 = data
                all_data = data
            elif data is None:
                all_data = data_2
            else:
                all_data = np.concatenate([data, data_2])

            for n in range(1, len(fmt)):
                if fmt is None:
                    kwargs = {'color':'r', 'marker':'o', 'ms':8, 'markerfacecolor':'none'}
                else:
                    kwargs = fmt[n]

                ax.plot(self.x[data_mask[n]], data_2[data_mask[n]] * data_units[0], **kwargs)

        # Create dictionary of data for use by annotation
        self.data_plotted.append({'type': 'ts', 'x': self.x, 'y': all_data})

        # Set axis limits
        try:
            max_y = (np.nanmax(all_data) + np.abs(np.nanmax(all_data) * 0.1)) * data_units[0]
            min_y = (np.nanmin(all_data) - np.abs(np.nanmin(all_data)) * 0.1) * data_units[0]
            ax.set_ylim(top=max_y, bottom=min_y)
        except TypeError:
            pass

        # Initialize annotation for data cursor
        if set_annot:
            self.annot.append(ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->")))

            self.annot[-1].set_visible(False)

        self.canvas.draw()

    def hover(self, event):
        """Determines if the user has selected a location with data and makes
        annotation visible and calls method to update the text of the annotation. If the
        location is not valid the existing annotation is hidden.

        Parameters
        ----------
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Determine if mouse location references a data point in the plot and update the annotation.
        for n, item in enumerate(self.ax):
            if event.inaxes == item:

                # Verify that location is associated with plotted data
                cont_fig = False
                if item is not None:
                    cont_fig, ind_fig = self.fig.contains(event)

                value = None
                if cont_fig and self.fig.get_visible():
                    # Annotation for contour plot
                    if self.data_plotted[n]['type'] == 'contour':
                        # Get plotted data
                        x_plt = self.data_plotted[n]['x']
                        y_plt = self.data_plotted[n]['y']
                        z_plt = self.data_plotted[n]['z']

                        # Determine data column index
                        if self.x_axis_type == 'T':
                            col_idx = np.where(x_plt[0, :] < num2date(event.xdata).replace(tzinfo=None))[0][-1]
                        elif self.x_axis_type == 'L':
                            col_idx = np.where(x_plt[0, :] < event.xdata)[0][-1]
                        else:
                            col_idx = (int(round(abs(event.xdata - x_plt[0, 0]))) * 2) - 1

                        # Determine plotted value
                        for row_idx, cell in enumerate(y_plt[:, col_idx]):
                            if event.ydata < cell:
                                value = z_plt[row_idx, col_idx]
                                break

                        # Create annotation
                        self.update_annot(ax_idx=n,
                                          x=event.xdata,
                                          y=event.ydata,
                                          v=value)

                    # Annotation for time series data
                    elif self.data_plotted[n]['type'] == 'ts':
                        self.update_annot(ax_idx=n,
                                          x=event.xdata,
                                          y=event.ydata,
                                          v=value)

                    self.annot[n].set_visible(True)
                    self.canvas.draw_idle()
            else:
                # If the cursor location is not associated with the plotted data hide the annotation.
                if self.fig.get_visible():
                    if type(self.annot[n]) != str:
                        self.annot[n].set_visible(False)
                    self.canvas.draw_idle()

    def set_hover_connection(self, setting):
        """Turns the connection to the mouse event on or off.

        Parameters
        ----------
        setting: bool
            Boolean to specify whether the connection for the mouse event is active or not.
        """
        if setting and self.hover_connection is None:
            self.hover_connection = self.canvas.mpl_connect('button_press_event', self.hover)
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            for item in self.annot:
                if type(item) != str:
                    item.set_visible(False)
            self.canvas.draw_idle()

    def update_annot(self, ax_idx, x, y, v=None):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

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
        """

        # Set local variables
        pos = [x, y]
        plt_ref = self.ax[ax_idx]
        annot_ref = self.annot[ax_idx]

        # Shift annotation box left or right depending on which half of the axis the pos x is located and the
        # direction of x increasing.
        if plt_ref.viewLim.intervalx[0] < plt_ref.viewLim.intervalx[1]:
            if pos[0] < (plt_ref.viewLim.intervalx[0] + plt_ref.viewLim.intervalx[1]) / 2:
                annot_ref._x = -20
            else:
                annot_ref._x = -80
        else:
            if pos[0] < (plt_ref.viewLim.intervalx[0] + plt_ref.viewLim.intervalx[1]) / 2:
                annot_ref._x = -80
            else:
                annot_ref._x = -20

        # Shift annotation box up or down depending on which half of the axis the pos y is located and the
        # direction of y increasing.
        if plt_ref.viewLim.intervaly[0] < plt_ref.viewLim.intervaly[1]:
            if pos[1] > (plt_ref.viewLim.intervaly[0] + plt_ref.viewLim.intervaly[1]) / 2:
                annot_ref._y = -40
            else:
                annot_ref._y = 20
        else:
            if pos[1] > (plt_ref.viewLim.intervaly[0] + plt_ref.viewLim.intervaly[1]) / 2:
                annot_ref._y = 20
            else:
                annot_ref._y = -40
        annot_ref.xy = pos
        text = ''

        # Annotation of contour plot
        if v is not None and v > -999:
            # Format for time axis
            if self.x_axis_type == 'T':
                x_label = num2date(pos[0]).strftime('%H:%M:%S.%f')[:-4]
                text = 'x: {}, y: {:.2f}, \n v: {:.1f}'.format(x_label, y, v)
            # Format for ensemble axis
            elif self.x_axis_type == 'E':
                text = 'x: {:.2f}, y: {:.2f}, \n v: {:.1f}'.format(int(round(x)), y, v)
            # Format for length axis
            elif self.x_axis_type == 'L':
                text = 'x: {:.2f}, y: {:.2f}, \n v: {:.1f}'.format(x, y, v)
        # Annotation for time series
        else:
            # Format for time axis
            if self.x_axis_type == 'T':
                x_label = num2date(pos[0]).strftime('%H:%M:%S.%f')[:-4]
                text = 'x: {}, y: {:.2f}'.format(x_label, y)
            # Format for ensemble axis
            elif self.x_axis_type == 'E':
                text = 'x: {:.2f}, y: {:.2f}'.format(int(round(x)), y)
            # Format for length axis
            elif self.x_axis_type == 'L':
                text = 'x: {:.2f}, y: {:.2f}'.format(x, y)

        annot_ref.set_text(text)

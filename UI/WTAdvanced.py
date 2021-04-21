import numpy as np
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
        self.wt_advanced_type_methods = {'cb_avg_corr': self.avg_corr_contour,
                                         'cb_avg_rssi': self.avg_rssi_contour,
                                         'cb_avg_speed': self.avg_speed_ts,
                                         'cb_corr_beam': self.corr_beam_contour,
                                         'cb_direction': self.direction_contour,
                                         'cb_discharge': self.discharge_ts,
                                         'cb_discharge_percent': self.discharge_percent_ts,
                                         'cb_error': self.error_contour,
                                         'cb_projected': self.projected_contour,
                                         'cb_projected_speed_ts': self.projected_speed_ts,
                                         'cb_rssi_beam': self.rssi_beam_contour,
                                         'cb_speed_filtered': self.speed_filtered_contour,
                                         'cb_speed_final': self.speed_final_contour,
                                         'cb_vertical': self.vertical_contour}

    def create(self, transect, discharge, units, selected_types, flow_direction, color_map='viridis', x_axis_type=None):

        if len(selected_types) > 0:
            self.flow_direction = flow_direction
            self.transect = transect
            self.discharge = discharge

            # Set default axis
            if x_axis_type is None:
                x_axis_type = 'E'
            self.x_axis_type = x_axis_type

            self.color_map = color_map

            # Assign and save parameters
            self.units = units

            # Clear the plot
            self.fig.clear()

            # Determine number of subplots
            self.n_subplots = len(selected_types)
            if 'cb_corr_beam' in selected_types:
                self.n_subplots += 3
            if 'cb_rssi_beam' in selected_types:
                self.n_subplots += 3

            # Compute x-axis variable
            self.compute_x_axis()

            # Initialize variable for subplots
            self.ax = []
            self.annot = []
            self.data_plotted = []
            self.gs = gridspec.GridSpec(self.n_subplots, 2, width_ratios=[50, 1])
            # Create first subplot
            # self.ax.append(self.fig.add_subplot(self.n_subplots, 1, self.fig_no))
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no]))
            self.wt_advanced_type_methods[selected_types[0]]()


            # Create additional subplots as specified, sharing x axis
            if len(selected_types) > 1:
                for n in range(1, len(selected_types)):
                    self.fig_no += 2
                    # self.ax.append(self.fig.add_subplot(self.n_subplots, 1, self.fig_no, sharex=self.ax[0]))
                    self.ax.append(self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0]))
                    self.wt_advanced_type_methods[selected_types[n]]()

            self.fig.subplots_adjust(left=0.04, bottom=0.04, right=0.95, top=0.95, wspace=0.02, hspace=0.08)

            if (len(self.ax) % 2) == 0:
                idx = -2
            else:
                idx = -1

            # Set axis limits
            self.ax[idx].xaxis.label.set_fontsize(12)
            if self.x_axis_type == 'L':
                if self.transect.start_edge == 'Right':
                    self.ax[idx].invert_xaxis()
                    self.ax[idx].set_xlim(right=-1 * self.x[-1] * 0.02, left=self.x[-1] * 1.02)
                else:
                    self.ax[idx].set_xlim(left=-1 * self.x[-1] * 0.02, right=self.x[-1] * 1.02)
                self.ax[idx].set_xlabel(self.canvas.tr('Length' + self.units['label_L']))
            elif self.x_axis_type == 'E':
                if self.transect.start_edge == 'Right':
                    self.ax[idx].invert_xaxis()
                    self.ax[idx].set_xlim(right=0, left=self.x[-1] + 1)
                else:
                    self.ax[idx].set_xlim(left=0, right=self.x[-1] + 1)
                self.ax[idx].set_xlabel(self.canvas.tr('Ensembles'))
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

            self.canvas.draw()

    def avg_corr_contour(self):
        data = np.nanmean(self.transect.w_vel.corr, axis=0)
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, 'Correlation \n (counts)'))

    def avg_rssi_contour(self):
        data = np.nanmean(self.transect.w_vel.rssi, axis=0)
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
        if self.transect.adcp.manufacturer == 'TRDI':
            data_label = 'Intensity \n (counts)'
        elif self.transect.adcp.manufacturer == 'SonTek':
            data_label = 'SNR (dB)'
        else:
            data_label = 'Intensity'
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, data_label))

    def avg_speed_ts(self):

        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_speed = np.sqrt(water_u ** 2 + water_v ** 2)
        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        weight = depth_selected.depth_cell_size_m[:, self.transect.in_transect_idx]
        avg_speed = np.nansum(water_speed * weight, axis=0) / np.nansum(weight, axis=0)
        data_units = (self.units['V'], 'Water speed \n' + self.units['label_V'])
        self.plt_timeseries(data=avg_speed,
                            start_edge=self.transect.start_edge,
                            data_units=data_units,
                            ax=self.ax[-1])

    def corr_beam_contour(self):

        data_limits = [np.nanmin(self.transect.w_vel.corr), np.nanmax(self.transect.w_vel.corr)]
        data = self.transect.w_vel.corr[0, :, :]
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, 'Beam 1 Corr. \n (counts)'),
                         data_limits=data_limits)

        for n in range(1, 4):
            self.fig_no += 2
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0]))
            data = self.transect.w_vel.corr[n, :, :]
            if self.x_axis_type == 'T':
                x_1d = self.x_timestamp
            else:
                x_1d = self.x
            x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
            self.plt_contour(x_plt_in=x_plt,
                             cell_plt_in=cell_plt,
                             data_plt_in=data_plt,
                             x=self.x,
                             depth=depth,
                             data_units=(1, 'Beam ' + str(n+1) + ' Corr. \n (counts)'),
                             data_limits=data_limits)

    def direction_contour(self):
        # Compute flow direction using discharge weighting
        u_water = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        v_water = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_dir = np.arctan2(u_water, v_water) * 180 / np.pi
        water_dir[water_dir < 0] = water_dir[water_dir < 0] + 360
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, water_dir, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, 'Water Direction \n (deg)'))

    def discharge_ts(self):

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

        data_units = (self.units['Q'], 'Discharge ' + self.units['label_Q'])
        self.plt_timeseries(data=q_ts,
                            start_edge=self.transect.start_edge,
                            data_units=data_units,
                            ax=self.ax[-1])

    def discharge_percent_ts(self):
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

        q_ts_per = (q_ts / self.discharge.total) * 100

        data_units = (1, 'Discharge (%)')
        self.plt_timeseries(data=q_ts_per,
                            start_edge=self.transect.start_edge,
                            data_units=data_units,
                            ax=self.ax[-1])

    def error_contour(self):
        data = self.transect.w_vel.d_mps
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Error Velocity \n' + self.units['label_V']))

    def projected_contour(self):

        unit_vector = np.array([[sind(self.flow_direction)], [cosd(self.flow_direction)]])
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        projected_speed = unit_vector[0] * water_u + unit_vector[1] * water_v

        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, projected_speed, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Projected \n Speed' + self.units['label_V']))

    def projected_speed_ts(self):
        unit_vector = np.array([[sind(self.flow_direction)], [cosd(self.flow_direction)]])
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        projected_speed = unit_vector[0] * water_u + unit_vector[1] * water_v

        depth_selected = getattr(self.transect.depths, self.transect.depths.selected)
        weight = depth_selected.depth_cell_size_m[:, self.transect.in_transect_idx]
        avg_speed = np.nansum(projected_speed * weight, axis=0) / np.nansum(weight, axis=0)
        data_units = (self.units['V'], 'Projected \n Speed ' + self.units['label_V'])
        self.plt_timeseries(data=avg_speed,
                            start_edge=self.transect.start_edge,
                            data_units=data_units,
                            ax=self.ax[-1])

    def rssi_beam_contour(self):

        if self.transect.adcp.manufacturer == 'TRDI':
            data_label = 'Intensity \n (counts)'
        elif self.transect.adcp.manufacturer == 'SonTek':
            data_label = 'SNR (dB)'
        else:
            data_label = 'Intensity'
        data_limits = [np.nanmin(self.transect.w_vel.rssi), np.nanmax(self.transect.w_vel.rssi)]
        data = self.transect.w_vel.rssi[0, :, :]
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(1, 'Beam 1' + data_label),
                         data_limits=data_limits)

        for n in range(1, 4):
            self.fig_no += 2
            self.ax.append(self.fig.add_subplot(self.gs[self.fig_no], sharex=self.ax[0]))
            data = self.transect.w_vel.rssi[n, :, :]
            if self.x_axis_type == 'T':
                x_1d = self.x_timestamp
            else:
                x_1d = self.x
            x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
            self.plt_contour(x_plt_in=x_plt,
                             cell_plt_in=cell_plt,
                             data_plt_in=data_plt,
                             x=self.x,
                             depth=depth,
                             data_units=(1, 'Beam ' + str(n + 1) + data_label),
                             data_limits=data_limits)

    def speed_filtered_contour(self):
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_speed = np.sqrt(water_u ** 2 + water_v ** 2)
        water_speed[np.logical_not(self.transect.w_vel.valid_data[0, :, :])] = np.nan
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, water_speed, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Filtered \n Speed ' + self.units['label_V']))

    def speed_final_contour(self):
        water_u = self.transect.w_vel.u_processed_mps[:, self.transect.in_transect_idx]
        water_v = self.transect.w_vel.v_processed_mps[:, self.transect.in_transect_idx]
        water_speed = np.sqrt(water_u ** 2 + water_v ** 2)
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, water_speed, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Interpolated \n Speed ' + self.units['label_V']))

    def vertical_contour(self):
        data = self.transect.w_vel.w_mps
        if self.x_axis_type == 'T':
            x_1d = self.x_timestamp
        else:
            x_1d = self.x
        x_plt, cell_plt, data_plt, ensembles, depth = self.contour_data_prep(self.transect, data, x_1d=x_1d)
        self.plt_contour(x_plt_in=x_plt,
                         cell_plt_in=cell_plt,
                         data_plt_in=data_plt,
                         x=self.x,
                         depth=depth,
                         data_units=(self.units['V'], 'Vertical \n Velocity' + self.units['label_V']))

    def compute_x_axis(self):
        # Compute x axis data
        x = None
        if self.x_axis_type == 'L':
            boat_track = self.transect.boat_vel.compute_boat_track(transect=self.transect)
            if not np.alltrue(np.isnan(boat_track['track_x_m'])):
                x = boat_track['distance_m'] * self.units['L']
            self.x = x[self.transect.in_transect_idx]
        elif self.x_axis_type == 'E':
            x = np.arange(1, len(self.transect.depths.bt_depths.depth_processed_m) + 1)
            self.x = x[self.transect.in_transect_idx]
        elif self.x_axis_type == 'T':
            timestamp = np.nancumsum(self.transect.date_time.ens_duration_sec) \
                        + self.transect.date_time.start_serial_time
            x = np.copy(timestamp)
            self.x_timestamp = x[self.transect.in_transect_idx]
            x = []
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

        ax = self.ax[-1]

        if self.x_axis_type == 'T':
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

        self.data_plotted.append({'type':'contour','x':x_plt, 'y':cell_plt, 'z':data_plt})
        # Initialize annotation for data cursor
        self.annot.append(ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="w"),
                                      arrowprops=dict(arrowstyle="->")))

        self.annot[-1].set_visible(False)
        # Add color bar and axis labels
        self.ax.append(self.fig.add_subplot(self.gs[self.fig_no + 1]))
        self.data_plotted.append({'type':'colorbar'})
        self.annot.append('')
        cb = self.fig.colorbar(c, self.ax[-1])
        cb.ax.set_ylabel(self.canvas.tr(data_units[1]))
        cb.ax.yaxis.label.set_fontsize(12)
        cb.ax.tick_params(labelsize=12)
        ax.invert_yaxis()

        # Plot depth
        ax.plot(x, depth * self.units['L'], color='k')

        # Plot side lobe cutoff if available
        if self.transect.w_vel.sl_cutoff_m is not None:
            depth_obj = getattr(self.transect.depths, self.transect.depths.selected)
            last_valid_cell = np.nansum(self.transect.w_vel.cells_above_sl, axis=0) - 1
            last_depth_cell_size = depth_obj.depth_cell_size_m[last_valid_cell,
                                                               np.arange(depth_obj.depth_cell_size_m.shape[1])]
            y_plt_sl = (self.transect.w_vel.sl_cutoff_m + (last_depth_cell_size * 0.5)) * self.units['L']
            y_plt_top = (depth_obj.depth_cell_depth_m[0, :]
                         - (depth_obj.depth_cell_size_m[0, :] * 0.5)) * self.units['L']

            ax.plot(x, y_plt_sl, color='r', linewidth=0.5)
            # Plot upper bound of measured depth cells
            ax.plot(x, y_plt_top, color='r', linewidth=0.5)

        # Label and limits for y axis
        ax.set_ylabel(self.canvas.tr('Depth ') + self.units['label_L'])
        ax.yaxis.label.set_fontsize(12)
        ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        ax.set_ylim(top=0, bottom=np.ceil(np.nanmax(depth * self.units['L'])))

    def plt_timeseries(self, data, start_edge, data_units, ax=None):

        if ax is None:
            ax = self.ax[-1]

        ax.set_ylabel(self.canvas.tr(data_units[1]))
        ax.grid()
        ax.yaxis.label.set_fontsize(12)
        ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        ax.plot(self.x, data * data_units[0], 'b-')
        self.data_plotted.append({'type': 'ts', 'x': self.x, 'y': data})
        # # Set axis limits
        max_y = (np.nanmax(data) + np.nanmax(data) * 0.1) * data_units[0]
        min_y = (np.nanmin(data) - np.nanmin(data) * 0.1) * data_units[0]
        ax.set_ylim(top=max_y, bottom=min_y)

        # Initialize annotation for data cursor
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
                vis = self.annot[n].get_visible()

                cont_fig = False
                if item is not None:
                    cont_fig, ind_fig = self.fig.contains(event)

                if cont_fig and self.fig.get_visible():
                    if self.data_plotted[n]['type'] == 'contour':
                        x_plt = self.data_plotted[n]['x']
                        y_plt = self.data_plotted[n]['y']
                        z_plt = self.data_plotted[n]['z']
                        if self.x_axis_type == 'T':
                            col_idx = np.where(x_plt[0, :] < num2date(event.xdata).replace(tzinfo=None))[0][-1]
                        elif self.x_axis_type == 'L':
                            col_idx = np.where(x_plt[0, :] < event.xdata)[0][-1]
                        else:
                            col_idx = (int(round(abs(event.xdata - x_plt[0, 0]))) * 2) - 1
                        v = None
                        for row_idx, cell in enumerate(y_plt[:, col_idx]):
                            if event.ydata < cell:
                                value = z_plt[row_idx, col_idx]
                                break
                        self.update_annot(ax_idx=n,
                                          x=event.xdata,
                                          y=event.ydata,
                                          v=value)
                    elif self.data_plotted[n]['type'] == 'ts':
                        self.update_annot(ax_idx=n,
                                          x=event.xdata,
                                          y=event.ydata,
                                          v=None)
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
            # self.hover_connection = self.canvas.mpl_connect("motion_notify_event", self.hover)
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
        x: float
            x coordinate for annotation, ensemble
        y: float
            y coordinate for annotation, depth
        v: float
            Speed for annotation
        """
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
        if v is not None and v > -999:
            if self.x_axis_type == 'T':
                x_label = num2date(pos[0]).strftime('%H:%M:%S.%f')[:-4]
                text = 'x: {}, y: {:.2f}, \n v: {:.1f}'.format(x_label, y, v)
            elif self.x_axis_type == 'E':
                text = 'x: {:.2f}, y: {:.2f}, \n v: {:.1f}'.format(int(round(x)), y, v)
            elif self.x_axis_type == 'L':
                text = 'x: {:.2f}, y: {:.2f}, \n v: {:.1f}'.format(x, y, v)
        else:
            if self.x_axis_type == 'T':
                x_label = num2date(pos[0]).strftime('%H:%M:%S.%f')[:-4]
                text = 'x: {}, y: {:.2f}'.format(x_label, y)
            elif self.x_axis_type == 'E':
                text = 'x: {:.2f}, y: {:.2f}'.format(int(round(x)), y)
            elif self.x_axis_type == 'L':
                text = 'x: {:.2f}, y: {:.2f}'.format(x, y)

        annot_ref.set_text(text)
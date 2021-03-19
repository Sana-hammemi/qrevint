import copy
import numpy as np


class BTFilters(object):
    """Class to generate time series plots of the selected filter data.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    fig: Object
        Figure object of the canvas
    units: dict
        Dictionary of units conversions
    beam: object
        Axis of figure for number of beams
    error: object
        Axis of figure for error velocity
    vert: object
        Axis of figure for vertical velocity
    other: object
        Axis of figure for other filters
    source: object
        Axis of figure for navigation reference source
    hover_connection: int
        Index to data cursor connection
    annot: Annotation
        Annotation object for data cursor
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
        self.beam = None
        self.error = None
        self.vert = None
        self.other = None
        self.source = None
        self.hover_connection = None
        self.annot = None

    def create(self, transect, units, selected):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        selected: str
            String identifying the type of plot
        """

        # Assign and save parameters
        self.units = units

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.07, bottom=0.2, right=0.99, top=0.98, wspace=0.1, hspace=0)
        self.fig.ax.set_xlabel(self.canvas.tr('Ensembles'))
        self.fig.ax.grid()
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        ensembles = np.arange(1, len(transect.boat_vel.bt_vel.u_mps) + 1)

        if selected == 'beam':
            # Plot beams
            # Determine number of beams for each ensemble
            bt_temp = copy.deepcopy(transect.boat_vel.bt_vel)
            bt_temp.filter_beam(4)
            valid_4beam = bt_temp.valid_data[5, :].astype(int)
            y_data = np.copy(valid_4beam).astype(int)
            y_data[valid_4beam == 1] = 4
            y_data[valid_4beam == 0] = 3
            y_data[np.logical_not(transect.boat_vel.bt_vel.valid_data[1, :])] = 0

            # Plot all data
            self.beam = self.fig.ax.plot(ensembles, y_data, 'b.')

            # Circle invalid data
            invalid_beam = np.logical_not(transect.boat_vel.bt_vel.valid_data[5, :])
            self.beam.append(self.fig.ax.plot(ensembles[invalid_beam],
                                              y_data[invalid_beam], 'ro', markerfacecolor='none')[0])

            # Format axis
            self.fig.ax.set_ylim(top=4.5, bottom=-0.5)
            self.fig.ax.set_ylabel(self.canvas.tr('Number of Beams'))

        elif selected == 'error':
            # Plot error velocity
            x_data = ensembles
            y_data = transect.boat_vel.bt_vel.d_mps * units['V']
            max_y = np.nanmax(y_data) * 1.1
            min_y = np.nanmin(y_data) * 1.1
            invalid_error_vel = np.logical_not(transect.boat_vel.bt_vel.valid_data[2, :])

            if np.all(np.isnan(transect.boat_vel.bt_vel.d_meas_threshold)):
                self.error = self.fig.ax.plot(x_data, y_data, '.', mfc='b', mec='b')
                # Mark invalid data
                self.error.append(self.fig.ax.plot(x_data[invalid_error_vel],
                                                   y_data[invalid_error_vel],
                                                   'ro', ms=8, markerfacecolor='none')[0])
            else:
                freq_used = np.unique(transect.boat_vel.bt_vel.frequency_khz).astype(int).astype(str)
                freq_color = {'0': 'b', '600': 'b', '1200':'b', '1000':'b', '2000': 'b', '2400': 'b', '3000': '#009933'}
                freq_marker = {'0': '.', '600': '.', '1200':'.', '1000':'.', '2000': '.', '2400': '.', '3000': '+'}

                freq_ensembles = transect.boat_vel.bt_vel.frequency_khz.astype(int).astype(str)
                # Plot first ping type
                self.error = self.fig.ax.plot(x_data[freq_ensembles == freq_used[0]],
                                              y_data[freq_ensembles == freq_used[0]],
                                              freq_marker[freq_used[0]],
                                              mfc=freq_color[freq_used[0]],
                                              mec=freq_color[freq_used[0]])

                # Plot remaining frequencies
                if freq_used.size > 1:
                    for freq in freq_used[1:]:
                        self.error.append(self.fig.ax.plot(x_data[freq_ensembles == freq],
                                                           y_data[freq_ensembles == freq],
                                                           freq_marker[freq],
                                                           mfc=freq_color[freq],
                                                           mec=freq_color[freq])[0])

                # Mark invalid data
                self.error.append(self.fig.ax.plot(x_data[invalid_error_vel],
                                                   y_data[invalid_error_vel],
                                                   'ro', ms=8, markerfacecolor='none')[0])
                # Create legend
                legend_dict = {'600': '600 kHz', '1200':'1200 kHz', '1000':'1 MHz', '2000': '2 MHz',
                               '2400': '2.4 MHz', '3000': '3 MHz', '0': 'N/U'}
                legend_txt = []
                for freq in freq_used:
                    legend_txt.append(legend_dict[freq])
                self.fig.ax.legend(legend_txt)

            self.fig.ax.set_ylim(top=max_y, bottom=min_y)
            self.fig.ax.set_ylabel(self.canvas.tr('Error Velocity' + self.units['label_V']))

        elif selected == 'vert':
            # Plot vertical velocity
            x_data = ensembles
            y_data = transect.boat_vel.bt_vel.w_mps * units['V']
            max_y = np.nanmax(y_data) * 1.1
            min_y = np.nanmin(y_data) * 1.1
            invalid_vert_vel = np.logical_not(transect.boat_vel.bt_vel.valid_data[3, :])
            if np.all(np.isnan(transect.boat_vel.bt_vel.w_meas_threshold)):
                self.error = self.fig.ax.plot(x_data, y_data, '.', mfc='b', mec='b')
                # Mark invalid data
                self.error.append(self.fig.ax.plot(x_data[invalid_vert_vel],
                                                   y_data[invalid_vert_vel],
                                                   'ro', ms=8, markerfacecolor='none')[0])
            else:
                freq_used = np.unique(transect.boat_vel.bt_vel.frequency_khz).astype(int).astype(str)
                freq_color = {'0': 'b', '600': 'b', '1200': 'b', '1000': 'b', '2000': 'b', '2400': 'b', '3000': '#009933'}
                freq_marker = {'0': '.', '600': '.', '1200': '.', '1000': '.', '2000': '.', '2400': '.', '3000': '+'}
                freq_ensembles = transect.boat_vel.bt_vel.frequency_khz.astype(int).astype(str)
                # Plot first ping type
                self.vert = self.fig.ax.plot(x_data[freq_ensembles == freq_used[0]],
                                             y_data[freq_ensembles == freq_used[0]],
                                             freq_marker[freq_used[0]],
                                             mfc=freq_color[freq_used[0]],
                                             mec=freq_color[freq_used[0]])

                # Plot remaining frequencies
                if freq_used.size > 1:
                    for freq in freq_used[1:]:
                        self.vert.append(self.fig.ax.plot(x_data[freq_ensembles == freq],
                                                          y_data[freq_ensembles == freq],
                                                          freq_marker[freq],
                                                          mfc=freq_color[freq],
                                                          mec=freq_color[freq])[0])

                # Mark invalid data
                self.vert.append(self.fig.ax.plot(x_data[invalid_vert_vel],
                                                  y_data[invalid_vert_vel],
                                                  'ro', ms=8, markerfacecolor='none')[0])
                # Create legend
                legend_dict = {'600': '600 kHz', '1200': '1200 kHz', '1000': '1 MHz', '2000': '2 MHz',
                               '2400': '2.4 MHz', '3000': '3 MHz', '0': 'N/U'}
                legend_txt = []
                for freq in freq_used:
                    legend_txt.append(legend_dict[freq])
                self.fig.ax.legend(legend_txt)

            self.fig.ax.set_ylim(top=max_y, bottom=min_y)
            self.fig.ax.set_ylabel(self.canvas.tr('Vert. Velocity' + self.units['label_V']))

        elif selected == 'other':
            # Plot smooth
            speed = np.sqrt(transect.boat_vel.bt_vel.u_mps ** 2
                            + transect.boat_vel.bt_vel.v_mps ** 2)
            invalid_other_vel = np.logical_not(transect.boat_vel.bt_vel.valid_data[4, :])
            if transect.boat_vel.bt_vel.smooth_filter == 'On':
                self.other = self.fig.ax.plot(ensembles,
                                              transect.boat_vel.bt_vel.smooth_lower_limit * self.units['V'],
                                              color='#d5dce6')
                self.other.append(self.fig.ax.plot(ensembles,
                                                   transect.boat_vel.bt_vel.smooth_upper_limit * self.units['V'],
                                                   color='#d5dce6')[0])
                self.other.append(self.fig.ax.fill_between(ensembles,
                                                           transect.boat_vel.bt_vel.smooth_lower_limit
                                                           * self.units['V'],
                                                           transect.boat_vel.bt_vel.smooth_upper_limit
                                                           * self.units['V'],
                                                           facecolor='#d5dce6'))

                self.other.append(self.fig.ax.plot(ensembles, speed * units['V'], 'r-')[0])
                self.other.append(self.fig.ax.plot(ensembles,
                                                   transect.boat_vel.bt_vel.smooth_speed * self.units['V'])[0])
                self.other.append(self.fig.ax.plot(ensembles[invalid_other_vel],
                                                   speed[invalid_other_vel] * units['V'],
                                                   'ko', linestyle='')[0])
            else:
                self.other = self.fig.ax.plot(ensembles, speed * units['V'], 'r-')
            self.fig.ax.set_ylabel(self.canvas.tr('Speed' + self.units['label_V']))

        elif selected == 'source':
            # Plot boat velocity source
            if transect.boat_vel.selected == 'gga_vel':
                boat_selected = transect.boat_vel.gga_vel
            elif transect.boat_vel.selected == 'vtg_vel':
                boat_selected = transect.boat_vel.gga_vel
            else:
                boat_selected = transect.boat_vel.bt_vel

            # Handle situation where transect does not contain the selected source
            if boat_selected is None:
                source = np.tile('INV', len(ensembles))
            else:
                source = boat_selected.processed_source

            # Plot dummy data to establish consistent order of y axis
            self.source = self.fig.ax.plot([-10, -10, -10, -10, -10], ['INV', 'INT', 'BT', 'GGA', 'VTG'], 'w-')
            self.source = self.fig.ax.plot(ensembles, source, 'b.')
            self.fig.ax.set_ylabel(self.canvas.tr('Boat Velocity Source'))
            self.fig.ax.set_yticks(['INV', 'INT', 'BT', 'GGA', 'VTG'])

        self.fig.ax.set_xlim(left=-1 * ensembles[-1] * 0.02, right=ensembles[-1] * 1.02)

        if transect.start_edge == 'Right':
            self.fig.ax.invert_xaxis()
            self.fig.ax.set_xlim(right=-1 * ensembles[-1] * 0.02, left=ensembles[-1] * 1.02)

        # Initialize annotation for data cursor
        self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->"))

        self.annot.set_visible(False)

        self.canvas.draw()

    def update_annot(self, ind, plt_ref):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        ind: dict
            Contains data selected.
        plt_ref: Line2D
            Reference containing plotted data
        """

        pos = plt_ref._xy[ind["ind"][0]]

        # Shift annotation box left or right depending on which half of the axis the pos x is located and the
        # direction of x increasing.
        if plt_ref.axes.viewLim.intervalx[0] < plt_ref.axes.viewLim.intervalx[1]:
            if pos[0] < (plt_ref.axes.viewLim.intervalx[0] + plt_ref.axes.viewLim.intervalx[1]) / 2:
                self.annot._x = -20
            else:
                self.annot._x = -80
        else:
            if pos[0] < (plt_ref.axes.viewLim.intervalx[0] + plt_ref.axes.viewLim.intervalx[1]) / 2:
                self.annot._x = -80
            else:
                self.annot._x = -20

        # Shift annotation box up or down depending on which half of the axis the pos y is located and the
        # direction of y increasing.
        if plt_ref.axes.viewLim.intervaly[0] < plt_ref.axes.viewLim.intervaly[1]:
            if pos[1] > (plt_ref.axes.viewLim.intervaly[0] + plt_ref.axes.viewLim.intervaly[1]) / 2:
                self.annot._y = -40
            else:
                self.annot._y = 20
        else:
            if pos[1] > (plt_ref.axes.viewLim.intervaly[0] + plt_ref.axes.viewLim.intervaly[1]) / 2:
                self.annot._y = 20
            else:
                self.annot._y = -40

        # Format and display text
        self.annot.xy = pos
        text = 'x: {:.2f}, y: {:.2f}'.format(pos[0], pos[1])
        self.annot.set_text(text)

    def hover(self, event):
        """Determines if the user has selected a location with data and makes
        annotation visible and calls method to update the text of the annotation. If the
        location is not valid the existing annotation is hidden.

        Parameters
        ----------
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Set annotation to visible
        vis = self.annot.get_visible()

        # Determine if mouse location references a data point in the plot and update the annotation.
        if event.inaxes == self.fig.ax:
            cont_beam = False
            cont_error = False
            cont_vert = False
            cont_other = False
            ind_beam = None
            ind_error = None
            ind_vert = None
            ind_other = None

            if self.beam is not None:
                cont_beam, ind_beam = self.beam[0].contains(event)
            elif self.error is not None:
                cont_error, ind_error = self.error[0].contains(event)
            elif self.vert is not None:
                cont_vert, ind_vert = self.vert[0].contains(event)
            elif self.other is not None:
                cont_other, ind_other = self.other[0].contains(event)

            if cont_beam:
                self.update_annot(ind_beam, self.beam[0])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_error:
                self.update_annot(ind_error, self.error[0])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_vert:
                self.update_annot(ind_vert, self.vert[0])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_other:
                self.update_annot(ind_other, self.other[0])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                # If the cursor location is not associated with the plotted data hide the annotation.
                if vis:
                    self.annot.set_visible(False)
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
            self.annot.set_visible(False)
            self.canvas.draw_idle()

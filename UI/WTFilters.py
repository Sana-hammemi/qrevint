import copy
import numpy as np
from matplotlib.dates import DateFormatter, num2date
from datetime import datetime


class WTFilters(object):
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
    speed: object
        Axis of figure for speed time series
    snr: object
        Axis of figure for snr filters
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
        self.beam = None
        self.error = None
        self.vert = None
        self.speed = None
        self.snr = None
        self.hover_connection = None
        self.x_axis_type = "E"

    def create(self, transect, units, selected, x_axis_type=None):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        selected: str
            String identifying the type of plot
        x_axis_type: str
            Identifies x-axis type (L-lenght, E-ensemble, T-time)
        """

        # Set default axis
        if x_axis_type is None:
            x_axis_type = "E"
        self.x_axis_type = x_axis_type

        # Assign and save parameters
        self.units = units

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(
            left=0.07, bottom=0.2, right=0.99, top=0.98, wspace=0.1, hspace=0
        )
        self.fig.ax.grid()
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(
            axis="both", direction="in", bottom=True, top=True, left=True, right=True
        )

        # Compute x axis data
        x = None
        if x_axis_type == "L":
            boat_track = transect.boat_vel.compute_boat_track(transect=transect)
            if not np.alltrue(np.isnan(boat_track["track_x_m"])):
                x = boat_track["distance_m"] * units["L"]
        elif x_axis_type == "E":
            x = np.arange(1, len(transect.depths.bt_depths.depth_processed_m) + 1)
        elif x_axis_type == "T":
            timestamp = (
                np.nancumsum(transect.date_time.ens_duration_sec)
                + transect.date_time.start_serial_time
            )
            x = []
            for stamp in timestamp:
                x.append(datetime.utcfromtimestamp(stamp))
            x = np.array(x)

        x = np.tile(x, (transect.w_vel.valid_data[0, :, :].shape[0], 1))

        cas = transect.w_vel.cells_above_sl

        if selected == "beam":
            # Plot beams
            # Determine number of beams for each ensemble
            wt_temp = copy.deepcopy(transect.w_vel)
            wt_temp.filter_beam(4)
            valid_4beam = wt_temp.valid_data[5, :, :].astype(int)
            beam_data = np.copy(valid_4beam).astype(int)
            beam_data[valid_4beam == 1] = 4
            beam_data[wt_temp.valid_data[6, :, :]] = 4
            beam_data[valid_4beam == 0] = 3
            beam_data[np.logical_not(transect.w_vel.valid_data[1, :, :])] = -999

            # Plot all data
            self.beam = self.fig.ax.plot(x, beam_data, "b.")

            # Circle invalid data
            invalid_beam = np.logical_and(
                np.logical_not(transect.w_vel.valid_data[5, :, :]), cas
            )
            self.beam.append(
                self.fig.ax.plot(
                    x[invalid_beam],
                    beam_data[invalid_beam],
                    "ro",
                    ms=8,
                    markerfacecolor="none",
                )[0]
            )

            # Format axis
            self.fig.ax.set_ylim(top=4.5, bottom=-0.5)
            self.fig.ax.set_ylabel(self.canvas.tr("Number of Beams"))

        elif selected == "error":
            # Plot error velocity
            max_y = np.nanmax(transect.w_vel.d_mps[cas]) * 1.1
            min_y = np.nanmin(transect.w_vel.d_mps[cas]) * 1.1
            invalid_error_vel = np.logical_and(
                np.logical_not(transect.w_vel.valid_data[2, :, :]), cas
            )

            if transect.w_vel.ping_type.size > 1:
                # Data to plot
                x_data = x[cas]
                y_data = transect.w_vel.d_mps[cas] * units["V"]

                # Setup ping type
                ping_type = transect.w_vel.ping_type[cas]
                p_type_color = {
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
                    "U": "b",
                }
                p_type_marker = {
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
                    "U": ".",
                }
                p_types = np.unique(ping_type)

                # Plot first ping type
                self.error = self.fig.ax.plot(
                    x_data[ping_type == p_types[0]],
                    y_data[ping_type == p_types[0]],
                    p_type_marker[p_types[0]],
                    mfc=p_type_color[p_types[0]],
                    mec=p_type_color[p_types[0]],
                )

                # Plot remaining ping types
                if len(p_types) > 0:
                    for p_type in p_types[1:]:
                        self.error.append(
                            self.fig.ax.plot(
                                x_data[ping_type == p_type],
                                y_data[ping_type == p_type],
                                p_type_marker[p_type],
                                mfc=p_type_color[p_type],
                                mec=p_type_color[p_type],
                            )[0]
                        )

                # Mark invalid data
                self.error.append(
                    self.fig.ax.plot(
                        x[invalid_error_vel],
                        transect.w_vel.d_mps[invalid_error_vel] * units["V"],
                        "ro",
                        ms=8,
                        markerfacecolor="none",
                    )[0]
                )
                # Create legend
                legend_dict = {
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
                    "U": "N/U",
                }
                legend_txt = []
                for p_type in p_types:
                    legend_txt.append(legend_dict[p_type])
                self.fig.ax.legend(legend_txt)

            else:
                self.error = self.fig.ax.plot(
                    x[cas], transect.w_vel.d_mps[cas] * units["V"], "b."
                )
                self.error.append(
                    self.fig.ax.plot(
                        x[invalid_error_vel],
                        transect.w_vel.d_mps[invalid_error_vel] * units["V"],
                        "ro",
                        markerfacecolor="none",
                    )[0]
                )

            # Scale axes
            self.fig.ax.set_ylim(top=max_y * units["V"], bottom=min_y * units["V"])
            self.fig.ax.set_ylabel(
                self.canvas.tr("Error Velocity" + self.units["label_V"])
            )

        elif selected == "vert":
            # Plot vertical velocity
            max_y = np.nanmax(transect.w_vel.w_mps[cas]) * 1.1
            min_y = np.nanmin(transect.w_vel.w_mps[cas]) * 1.1
            invalid_vert_vel = np.logical_and(
                np.logical_not(transect.w_vel.valid_data[3, :, :]), cas
            )

            if transect.w_vel.ping_type.size > 1:
                # Data to plot
                x_data = x[cas]
                y_data = transect.w_vel.w_mps[cas] * units["V"]

                # Setup ping types for plotting
                ping_type = transect.w_vel.ping_type[cas]
                p_type_color = {
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
                    "U": "b",
                }
                p_type_marker = {
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
                    "U": ".",
                }
                p_types = np.unique(ping_type)

                # Plot first ping type
                self.vert = self.fig.ax.plot(
                    x_data[ping_type == p_types[0]],
                    y_data[ping_type == p_types[0]],
                    p_type_marker[p_types[0]],
                    mfc=p_type_color[p_types[0]],
                    mec=p_type_color[p_types[0]],
                )

                # Plot remaining ping types
                if len(p_types) > 0:
                    for p_type in p_types[1:]:
                        self.vert.append(
                            self.fig.ax.plot(
                                x_data[ping_type == p_type],
                                y_data[ping_type == p_type],
                                p_type_marker[p_type],
                                mfc=p_type_color[p_type],
                                mec=p_type_color[p_type],
                            )[0]
                        )

                # Mark invalid data
                self.vert.append(
                    self.fig.ax.plot(
                        x[invalid_vert_vel],
                        transect.w_vel.w_mps[invalid_vert_vel] * units["V"],
                        "ro",
                        ms=8,
                        markerfacecolor="none",
                    )[0]
                )

                # Create legend
                legend_dict = {
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
                    "U": "N/U",
                }
                legend_txt = []
                for p_type in p_types:
                    legend_txt.append(legend_dict[p_type])
                self.fig.ax.legend(legend_txt)

            else:
                self.vert = self.fig.ax.plot(
                    x[cas], transect.w_vel.w_mps[cas] * units["V"], "b."
                )
                self.vert.append(
                    self.fig.ax.plot(
                        x[invalid_vert_vel],
                        transect.w_vel.w_mps[invalid_vert_vel] * units["V"],
                        "ro",
                        markerfacecolor="none",
                    )[0]
                )

            # Scale axes
            self.fig.ax.set_ylim(top=max_y * units["V"], bottom=min_y * units["V"])
            self.fig.ax.set_ylabel(
                self.canvas.tr("Vert. Velocity" + self.units["label_V"])
            )

        elif selected == "snr":
            # Plot snr
            max_y = np.nanmax(transect.w_vel.snr_rng) * 1.1
            min_y = np.nanmin(transect.w_vel.snr_rng) * 1.1
            invalid_snr = np.logical_and(
                np.logical_not(transect.w_vel.valid_data[7, 0, :]), cas
            )[0, :]

            if transect.w_vel.ping_type.size > 1:
                # Data to plot
                x_data = x[0, cas[0, :]]
                y_data = transect.w_vel.snr_rng[cas[0, :]]

                # Setup ping types for plotting
                ping_type = transect.w_vel.ping_type[0, cas[0, :]]
                p_type_color = {
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
                    "U": "b",
                }
                p_type_marker = {
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
                    "U": ".",
                }
                p_types = np.unique(ping_type)

                # Plot first ping type
                self.snr = self.fig.ax.plot(
                    x_data[ping_type == p_types[0]],
                    y_data[ping_type == p_types[0]],
                    p_type_marker[p_types[0]],
                    mfc=p_type_color[p_types[0]],
                    mec=p_type_color[p_types[0]],
                )

                # Plot remaining ping types
                if len(p_types) > 0:
                    for p_type in p_types[1:]:
                        self.snr.append(
                            self.fig.ax.plot(
                                x_data[ping_type == p_type],
                                y_data[ping_type == p_type],
                                p_type_marker[p_type],
                                mfc=p_type_color[p_type],
                                mec=p_type_color[p_type],
                            )[0]
                        )

                # Mark invalid data
                self.snr.append(
                    self.fig.ax.plot(
                        x[0, invalid_snr],
                        transect.w_vel.snr_rng[invalid_snr],
                        "ro",
                        ms=8,
                        markerfacecolor="none",
                    )[0]
                )

                # Create legend
                legend_dict = {
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
                    "U": "N/U",
                }
                legend_txt = []
                for p_type in p_types:
                    legend_txt.append(legend_dict[p_type])
                self.fig.ax.legend(legend_txt)

            else:
                self.snr = self.fig.ax.plot(x[0, :], transect.w_vel.snr_rng, "b.")
                self.snr.append(
                    self.fig.ax.plot(
                        x[0, invalid_snr],
                        transect.w_vel.snr_rng[invalid_snr],
                        "ro",
                        markerfacecolor="none",
                    )[0]
                )

            # Scale axes
            self.fig.ax.set_ylim(top=max_y, bottom=min_y)
            self.fig.ax.set_ylabel(self.canvas.tr("SNR Range (dB)"))

        elif selected == "speed":
            # Plot speed
            speed = np.nanmean(
                np.sqrt(transect.w_vel.u_mps**2 + transect.w_vel.v_mps**2), 0
            )
            max_y = np.nanmax(speed) * 1.1
            # min_y = np.nanmin(speed) * 0.7
            min_y = 0
            invalid_wt = np.logical_and(np.logical_not(transect.w_vel.valid_data), cas)

            self.speed = self.fig.ax.plot(x[0, :], speed * self.units["V"], "b")
            self.speed.append(
                self.fig.ax.plot(
                    x[0, np.any(invalid_wt[1, :, :], 0)],
                    speed[np.any(invalid_wt[1, :, :], 0)] * units["V"],
                    "k",
                    linestyle="",
                    marker="$O$",
                )[0]
            )
            self.speed.append(
                self.fig.ax.plot(
                    x[0, np.any(invalid_wt[2, :, :], 0)],
                    speed[np.any(invalid_wt[2, :, :], 0)] * units["V"],
                    "k",
                    linestyle="",
                    marker="$E$",
                )[0]
            )
            self.speed.append(
                self.fig.ax.plot(
                    x[0, np.any(invalid_wt[3, :, :], 0)],
                    speed[np.any(invalid_wt[3, :, :], 0)] * units["V"],
                    "k",
                    linestyle="",
                    marker="$V$",
                )[0]
            )
            self.speed.append(
                self.fig.ax.plot(
                    x[0, np.any(invalid_wt[5, :, :], 0)],
                    speed[np.any(invalid_wt[5, :, :], 0)] * units["V"],
                    "k",
                    linestyle="",
                    marker="$B$",
                )[0]
            )
            self.speed.append(
                self.fig.ax.plot(
                    x[0, np.any(invalid_wt[7, :, :], 0)],
                    speed[np.any(invalid_wt[7, :, :], 0)] * units["V"],
                    "k",
                    linestyle="",
                    marker="$R$",
                )[0]
            )

            self.fig.ax.set_ylabel(self.canvas.tr("Speed" + self.units["label_V"]))
            try:
                self.fig.ax.set_ylim(top=max_y * units["V"], bottom=min_y * units["V"])
            except ValueError:
                pass

        if x_axis_type == "L":
            if transect.start_edge == "Right":
                self.fig.ax.invert_xaxis()
                self.fig.ax.set_xlim(
                    right=-1 * x[0, -1] * 0.02 * units["L"],
                    left=x[0, -1] * 1.02 * units["L"],
                )
            else:
                self.fig.ax.set_xlim(
                    left=-1 * x[0, -1] * 0.02 * units["L"],
                    right=x[0, -1] * 1.02 * units["L"],
                )
            self.fig.ax.set_xlabel(self.canvas.tr("Length" + units["label_L"]))
        elif x_axis_type == "E":
            if transect.start_edge == "Right":
                self.fig.ax.invert_xaxis()
                self.fig.ax.set_xlim(right=0, left=x[0, -1] + 1)
            else:
                self.fig.ax.set_xlim(left=0, right=x[0, -1] + 1)
            self.fig.ax.set_xlabel(self.canvas.tr("Ensembles"))
        elif x_axis_type == "T":
            axis_buffer = (timestamp[-1] - timestamp[0]) * 0.02
            if transect.start_edge == "Right":
                self.fig.ax.invert_xaxis()
                self.fig.ax.set_xlim(
                    right=datetime.utcfromtimestamp(timestamp[0] - axis_buffer),
                    left=datetime.utcfromtimestamp(timestamp[-1] + axis_buffer),
                )
            else:
                self.fig.ax.set_xlim(
                    left=datetime.utcfromtimestamp(timestamp[0] - axis_buffer),
                    right=datetime.utcfromtimestamp(timestamp[-1] + axis_buffer),
                )
            date_form = DateFormatter("%H:%M:%S")
            self.fig.ax.xaxis.set_major_formatter(date_form)
            self.fig.ax.set_xlabel(self.canvas.tr("Time"))

        # Initialize annotation for data cursor
        self.annot = self.fig.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(-20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->"),
        )

        self.annot.set_visible(False)

        self.canvas.draw()

    def update_annot(self, ind, plt_ref):

        pos = plt_ref._xy[ind["ind"][0]]
        # Shift annotation box left or right depending on which half of the axis
        # the pos x is located and the direction of x increasing.
        if plt_ref.axes.viewLim.intervalx[0] < plt_ref.axes.viewLim.intervalx[1]:
            if (
                pos[0]
                < (
                    plt_ref.axes.viewLim.intervalx[0]
                    + plt_ref.axes.viewLim.intervalx[1]
                )
                / 2
            ):
                self.annot._x = -20
            else:
                self.annot._x = -80
        else:
            if (
                pos[0]
                < (
                    plt_ref.axes.viewLim.intervalx[0]
                    + plt_ref.axes.viewLim.intervalx[1]
                )
                / 2
            ):
                self.annot._x = -80
            else:
                self.annot._x = -20

        # Shift annotation box up or down depending on which half of the axis
        # the pos y is located and the direction of y increasing.
        if plt_ref.axes.viewLim.intervaly[0] < plt_ref.axes.viewLim.intervaly[1]:
            if (
                pos[1]
                > (
                    plt_ref.axes.viewLim.intervaly[0]
                    + plt_ref.axes.viewLim.intervaly[1]
                )
                / 2
            ):
                self.annot._y = -40
            else:
                self.annot._y = 20
        else:
            if (
                pos[1]
                > (
                    plt_ref.axes.viewLim.intervaly[0]
                    + plt_ref.axes.viewLim.intervaly[1]
                )
                / 2
            ):
                self.annot._y = 20
            else:
                self.annot._y = -40

        self.annot.xy = pos

        # Format and display text
        if self.x_axis_type == "T":
            x_label = num2date(pos[0]).strftime("%H:%M:%S.%f")[:-4]
            text = "x: {}, y: {:.2f}".format(x_label, pos[1])
        else:
            text = "x: {:.2f}, y: {:.2f}".format(pos[0], pos[1])
        self.annot.set_text(text)

    def hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.fig.ax:
            cont_beam = False
            cont_error = False
            cont_vert = False
            cont_speed = False
            cont_snr = False
            if self.beam is not None:
                for n, beam in enumerate(self.beam):
                    cont_beam, ind_beam = beam.contains(event)
                    if cont_beam:
                        break
            elif self.error is not None:
                for n, err in enumerate(self.error):
                    cont_error, ind_error = err.contains(event)
                    if cont_error:
                        break
            elif self.vert is not None:
                for n, vert in enumerate(self.vert):
                    cont_vert, ind_vert = vert.contains(event)
                    if cont_vert:
                        break
            elif self.speed is not None:
                cont_speed, ind_other = self.speed[0].contains(event)
            elif self.snr is not None:
                cont_snr, ind_snr = self.snr[0].contains(event)

            if cont_beam:
                self.update_annot(ind_beam, self.beam[n])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_error:
                self.update_annot(ind_error, self.error[n])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_vert:
                self.update_annot(ind_vert, self.vert[n])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_speed:
                self.update_annot(ind_other, self.speed[0])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_snr:
                self.update_annot(ind_snr, self.snr[0])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()

    def set_hover_connection(self, setting):

        if setting and self.hover_connection is None:
            self.hover_connection = self.canvas.mpl_connect(
                "button_press_event", self.hover
            )
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            self.annot.set_visible(False)
            self.canvas.draw_idle()

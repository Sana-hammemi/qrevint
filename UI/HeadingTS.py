import numpy as np
from PyQt5 import QtCore


class HeadingTS(object):
    """Class to generate at time series of heading data.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    internal: list
        Reference to internal compass time series plot
    external: list
        Reference to internal compass time series plot
    merror: list
        Reference to magnetic error time series plot
    row_index: list
        List of rows from the table that are plotted
    hover_connection: bool
        Switch to allow user to use the data cursor
    annot: Annotation
        Annotation object for heading
    annot2: Annotation
        Annotation object for percent change in magnetic field
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
        self.internal = None
        self.external = None
        self.merror = None
        self.row_index = []
        self.hover_connection = None
        self.annot = None
        self.annot2 = None
        self.x_axis_type = "E"

    def create(
        self,
        meas,
        checked,
        tbl,
        cb_internal,
        cb_external,
        cb_merror,
        units,
        x_axis_type=None,
    ):
        """Creates heading time series graph.

        Parameters
        ----------
        meas: Measurement
            Object of Measurement class
        checked: list
            List of bool indicating which transects are included in the
            discharge computation
        tbl: QTableWidget
            Heading, pitch, and roll table
        cb_internal: QCheckBox
            Indicates if the internal heading data is visible
        cb_external: QCheckBox
            Inidcates if the external heading data is visible
        cb_merror: QCheckBox
            Indicates if the percent change in magnetic field is visible
        units: dict
            Dictionary of units conversions
        x_axis_type: str
            Identifies x-axis type (L-lenght, E-ensemble, T-time)
        """

        # Set default axis
        if x_axis_type is None:
            x_axis_type = "E"
        self.x_axis_type = x_axis_type

        # Clear the plot
        self.fig.clear()
        # No data selected for graphing
        if np.all(
            np.logical_not(
                [
                    cb_merror.isChecked(),
                    cb_internal.isChecked(),
                    cb_external.isChecked(),
                ]
            )
        ):
            return

        self.row_index = []

        # Configure axis
        self.fig.axh = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(
            left=0.1, bottom=0.15, right=0.95, top=0.98, wspace=0.1, hspace=0
        )
        self.fig.axh.set_ylabel(self.canvas.tr("Heading (deg)"))
        self.fig.axh.xaxis.label.set_fontsize(10)
        self.fig.axh.yaxis.label.set_fontsize(10)
        self.fig.axh.tick_params(
            axis="both", direction="in", bottom=True, top=True, left=True, right=True
        )
        self.fig.axh.set_yticks([0, 90, 180, 270, 360])

        if cb_merror.isChecked():
            # Plot magnetic field change
            self.fig.axm = self.fig.axh.twinx()
            self.fig.axm.set_ylabel(self.canvas.tr("Magnetic Change (%)"))
            self.fig.axm.yaxis.label.set_fontsize(10)
            self.fig.axm.tick_params(
                axis="both",
                direction="in",
                bottom=True,
                top=True,
                left=True,
                right=True,
            )

        self.internal = []
        self.external = []
        self.merror = []
        x = np.nan
        for row in range(len(checked)):
            if tbl.item(row, 0).checkState() == QtCore.Qt.Checked:
                self.row_index.append(row)
                if cb_internal.isChecked():
                    # Get ADCP heading
                    if (
                        meas.transects[checked[row]].sensors.heading_deg.selected
                        == "user"
                    ):
                        heading = np.copy(
                            meas.transects[checked[row]].sensors.heading_deg.user.data
                        )
                    else:
                        heading = np.copy(
                            meas.transects[
                                checked[row]
                            ].sensors.heading_deg.internal.data
                        )
                    # Arrange data left to right
                    flip = False
                    if meas.transects[checked[row]].start_edge == "Right":
                        heading = np.flip(heading)
                        flip = True
                    # Compute x-axis
                    x = self.set_x_axis(
                        x_axis_type=x_axis_type,
                        transect=meas.transects[checked[row]],
                        units=units,
                        flip=flip,
                    )
                    self.internal.append(self.fig.axh.plot(x, heading, "r-")[0])
                else:
                    self.internal = None

                if cb_external.isChecked():
                    # Get External Heading
                    heading = np.copy(
                        meas.transects[checked[row]].sensors.heading_deg.external.data
                    )

                    # Arrange data left to right
                    flip = False
                    if meas.transects[checked[row]].start_edge == "Right":
                        heading = np.flip(heading)
                        flip = True
                    # Compute x-axis
                    x = self.set_x_axis(
                        x_axis_type=x_axis_type,
                        transect=meas.transects[checked[row]],
                        units=units,
                        flip=flip,
                    )
                    self.external.append(self.fig.axh.plot(x, heading, "b-")[0])
                else:
                    self.external = None

                if cb_merror.isChecked():
                    # Get magnetic field change
                    mag_chng = np.copy(
                        meas.transects[
                            checked[row]
                        ].sensors.heading_deg.internal.mag_error
                    )

                    # Arrange data left to right
                    flip = False
                    if meas.transects[checked[row]].start_edge == "Right":
                        mag_chng = np.flip(mag_chng)
                        flip = True
                    # Compute x-axis
                    x = self.set_x_axis(
                        x_axis_type=x_axis_type,
                        transect=meas.transects[checked[row]],
                        units=units,
                        flip=flip,
                    )
                    self.merror.append(self.fig.axm.plot(x, mag_chng, "k-")[0])
                    self.merror.append(
                        self.fig.axm.plot([x[0], x[-1]], [2, 2], "k--")[0]
                    )
                else:
                    self.merror = None

        # Label axis
        if x_axis_type == "L":
            self.fig.axh.set_xlim(
                left=-1 * np.nanmax(x) * 0.02,
                right=np.nanmax(x) * 1.02,
            )
            self.fig.axh.set_xlabel(
                self.canvas.tr("Length Left to Right" + units["label_L"])
            )
        elif x_axis_type == "E":
            self.fig.axh.set_xlim(
                left=-1 * np.nanmax(x) * 0.02, right=np.nanmax(x) * 1.02
            )
            self.fig.axh.set_xlabel(self.canvas.tr("Ensembles Left to Right"))
        elif x_axis_type == "T":
            self.fig.axh.set_xlim(
                left=-1 * np.nanmax(x) * 0.02, right=np.nanmax(x) * 1.02
            )
            self.fig.axh.set_xlabel(
                self.canvas.tr("Duration Left to Right " "(seconds)")
            )

        # Configure annotations for magnetic error
        if cb_merror.isChecked():
            self.annot2 = self.fig.axm.annotate(
                "",
                xy=(0, 0),
                xytext=(-20, 20),
                textcoords="offset points",
                bbox=dict(boxstyle="round", fc="w"),
                arrowprops=dict(arrowstyle="->"),
            )

            self.annot2.set_visible(False)

        # Initialize annotation for data cursor
        self.annot = self.fig.axh.annotate(
            "",
            xy=(0, 0),
            xytext=(-20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->"),
        )

        self.annot.set_visible(False)
        self.fig.axh.set_yticks([0, 90, 180, 270, 360])
        self.canvas.draw()

    @staticmethod
    def set_x_axis(x_axis_type, transect, units, flip=False):
        """Computes values for the x-axis based on specified x-axis type.

        Parameters
        ----------
        x_axis_type: str
            Identifies x-axis type (L-lenght, E-ensemble, T-time)
        transect: TransectData
            Object of TransectData
        units: dict
            Dictionary of units conversions
        flip: bool
            Need to flip data so it is left to right
        """

        # Compute x axis data
        x = None
        if x_axis_type == "L":
            boat_track = transect.boat_vel.compute_boat_track(transect=transect)
            if not np.alltrue(np.isnan(boat_track["track_x_m"])):
                x = boat_track["distance_m"] * units["L"]
        elif x_axis_type == "E":
            x = np.arange(1, len(transect.depths.bt_depths.depth_processed_m) + 1)
        elif x_axis_type == "T":
            x = np.nancumsum(transect.date_time.ens_duration_sec)

        if flip:
            x = x[-1] - x

        return x

    def update_annot(self, annot, ind, plt_ref, row):
        """Updates the location and text and makes visible the previously
        initialized and hidden annotation.

        Parameters
        ----------
        annot: Annotation
            Annotation for data cursor
        ind: dict
            Contains data selected.
        plt_ref: Line2D
            Reference containing plotted data
        row: int
            Index of row in table from to which the plotted data are associated
        """

        # Get selected data coordinates
        pos = plt_ref._xy[ind["ind"][0]]

        # Shift annotation box left or right depending on which half of the
        # axis the pos x is located and the direction of x increasing.
        if plt_ref.axes.viewLim.intervalx[0] < plt_ref.axes.viewLim.intervalx[1]:
            if (
                pos[0]
                < (
                    plt_ref.axes.viewLim.intervalx[0]
                    + plt_ref.axes.viewLim.intervalx[1]
                )
                / 2
            ):
                annot._x = -20
            else:
                annot._x = -80
        else:
            if (
                pos[0]
                < (
                    plt_ref.axes.viewLim.intervalx[0]
                    + plt_ref.axes.viewLim.intervalx[1]
                )
                / 2
            ):
                annot._x = -80
            else:
                annot._x = -20

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
                annot._y = -40
            else:
                annot._y = 20
        else:
            if (
                pos[1]
                > (
                    plt_ref.axes.viewLim.intervaly[0]
                    + plt_ref.axes.viewLim.intervaly[1]
                )
                / 2
            ):
                annot._y = 20
            else:
                annot._y = -40

        annot.xy = pos

        # Format and display text
        text = "row: {:.0f}, x: {:.2f}, y: {:.2f}".format(row, pos[0], pos[1])

        annot.set_text(text)

    def hover(self, event):
        """Determines if the user has selected a location with data and makes
        annotation visible and calls method to update the text of the
        annotation. If the location is not valid the existing annotation is hidden.

        Parameters
        ----------
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Set annotation to visible
        vis = self.annot.get_visible()

        cont = False
        ind = None
        item = None
        n = None
        # Determine if mouse location references a data point in the plot and
        # update the annotation.
        if event.inaxes == self.fig.axh or event.inaxes == self.fig.axm:
            if self.internal is not None:
                for n, item in enumerate(self.internal):
                    cont, ind = item.contains(event)
                    if cont:
                        break
            if not cont and self.external is not None:
                for n, item in enumerate(self.external):
                    cont, ind = item.contains(event)
                    if cont:
                        break
            if cont:
                self.update_annot(
                    annot=self.annot, ind=ind, plt_ref=item, row=self.row_index[n] + 1
                )
                self.annot.set_visible(True)
                self.canvas.draw_idle()
                if self.merror is not None:
                    self.annot2.set_visible(False)

            else:
                self.annot.set_visible(False)
                if self.merror is not None:
                    for n, item in enumerate(self.merror):
                        cont, ind = item.contains(event)
                        if cont:
                            break
                if cont:
                    self.update_annot(
                        annot=self.annot2,
                        ind=ind,
                        plt_ref=item,
                        row=self.row_index[n] + 1,
                    )
                    self.annot2.set_visible(True)
                    self.canvas.draw_idle()
                else:
                    self.annot2.set_visible(False)
        else:
            # If the cursor location is not associated with the plotted data
            # hide the annotation.
            if vis:
                self.annot.set_visible(False)
                if self.merror is not None:
                    self.annot2.set_visible(False)
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
            self.annot.set_visible(False)
            self.canvas.draw_idle()

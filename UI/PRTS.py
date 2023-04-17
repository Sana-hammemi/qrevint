import numpy as np
from PyQt5 import QtCore


class PRTS(object):
    """Class to generate at time series of heading data.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    pitch: list
        Reference to pitch time series plot
    roll: list
        Reference to roll time series plot
    row_index: list
        List of rows from the table that are plotted
    hover_connection: bool
        Switch to allow user to use the data cursor
    annot: Annotation
        Annotation for data cursor
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
        self.pitch = None
        self.roll = None
        self.row_index = []
        self.hover_connection = None
        self.annot = None
        self.x_axis_type = "E"

    def create(self, meas, checked, tbl, cb_pitch, cb_roll, units, x_axis_type=None):
        """Generates the pitch and roll plot.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        checked: list
            List of transect indices to be included in discharge computation
        tbl: QTableWidget
            Table containing heading, pitch, and roll information
        cb_pitch: QCheckBox
            Checkbox indicating if the pitch is displayed
        cb_roll: QCheckBox
            Checkbox indication if the roll is displayed
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

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(
            left=0.1, bottom=0.15, right=0.95, top=0.98, wspace=0.1, hspace=0
        )
        self.fig.ax.set_ylabel(self.canvas.tr("Pitch or Roll (deg)"))
        self.fig.ax.xaxis.label.set_fontsize(10)
        self.fig.ax.yaxis.label.set_fontsize(10)
        self.fig.ax.tick_params(
            axis="both", direction="in", bottom=True, top=True, left=True, right=True
        )
        self.pitch = []
        self.roll = []
        self.row_index = []

        # Plot all selected transects
        for row in range(len(checked)):
            if tbl.item(row, 0).checkState() == QtCore.Qt.Checked:
                self.row_index.append(row)
                if cb_pitch.isChecked():
                    # Get pitch data
                    pitch = np.copy(
                        meas.transects[checked[row]].sensors.pitch_deg.internal.data
                    )
                    # Arrange data from left to right
                    flip = False
                    if meas.transects[checked[row]].start_edge == "Right":
                        pitch = np.flip(pitch)
                        flip = True
                    # Compute x-axis
                    x = self.set_x_axis(
                        x_axis_type=x_axis_type,
                        transect=meas.transects[checked[row]],
                        units=units,
                        flip=flip,
                    )
                    if pitch.shape[0] > 0:
                        self.pitch.append(self.fig.ax.plot(x, pitch, "r-")[0])

                else:
                    self.pitch = None

                if cb_roll.isChecked():
                    # Get roll data
                    roll = np.copy(
                        meas.transects[checked[row]].sensors.roll_deg.internal.data
                    )
                    # Arrange data from left to right
                    flip = False
                    if meas.transects[checked[row]].start_edge == "Right":
                        roll = np.flip(roll)
                    # Compute x-axis
                    x = self.set_x_axis(
                        x_axis_type=x_axis_type,
                        transect=meas.transects[checked[row]],
                        units=units,
                        flip=flip,
                    )
                    if roll.shape[0] > 0:
                        self.roll.append(self.fig.ax.plot(x, roll, "b-")[0])
                else:
                    self.roll = None

        # Label axis
        if x_axis_type == "L":
            self.fig.ax.set_xlim(
                left=-1 * np.nanmax(x) * 0.02 * units["L"],
                right=np.nanmax(x) * 1.02 * units["L"],
            )
            self.fig.ax.set_xlabel(
                self.canvas.tr("Length Left to Right" + units["label_L"])
            )
        elif x_axis_type == "E":
            self.fig.ax.set_xlim(
                left=-1 * np.nanmax(x) * 0.02, right=np.nanmax(x) * 1.02
            )
            self.fig.ax.set_xlabel(self.canvas.tr("Ensembles Left to Right"))
        elif x_axis_type == "T":
            self.fig.ax.set_xlim(
                left=-1 * np.nanmax(x) * 0.02, right=np.nanmax(x) * 1.02
            )
            self.fig.ax.set_xlabel(self.canvas.tr("Duration Left to Right (seconds)"))

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

    def update_annot(self, ind, plt_ref, row):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        ind: dict
            Contains data selected.
        plt_ref: Line2D
            Reference containing plotted data
        row: int
            Index to row from which the data selected by the data cursor is associated
        """

        # Get selected data coordinates
        pos = plt_ref._xy[ind["ind"][0]]

        # Shift annotation box left or right depending on which half of the axis the pos x is located and the
        # direction of x increasing.
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

        # Shift annotation box up or down depending on which half of the axis the pos y is located and the
        # direction of y increasing.
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
        text = "row: {:.0f}, x: {:.2f}, y: {:.2f}".format(row, pos[0], pos[1])
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
            cont = False
            ind = None
            item = None
            n = None
            if self.pitch is not None:
                for n, item in enumerate(self.pitch):
                    cont, ind = item.contains(event)
                    if cont:
                        break
            if not cont and self.roll is not None:
                for n, item in enumerate(self.roll):
                    cont, ind = item.contains(event)
                    if cont:
                        break
            if cont:
                self.update_annot(ind, plt_ref=item, row=self.row_index[n] + 1)
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
            # self.hover_connection = self.canvas.mpl_connect("motion_notify_event", self.hover)
            self.hover_connection = self.canvas.mpl_connect(
                "button_press_event", self.hover
            )
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            self.annot.set_visible(False)
            self.canvas.draw_idle()

import numpy as np
import matplotlib.cm as cm
from matplotlib.dates import DateFormatter, num2date
from datetime import datetime


class WTContour(object):
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
    x_plt: np.ndarray()
        Array of values used for x-axis
    cell_plt: np.ndarray(float)
        Cell depths to plot in user specified units
    speed_plt: np.ndarray(float)
        Water speeds to plot in user specified units
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
        self.x_plt = None
        self.cell_plt = None
        self.speed_plt = None
        self.x_axis_type = "E"

    def create(
        self,
        transect,
        units,
        invalid_data=None,
        n_ensembles=None,
        edge_start=None,
        max_limit=0,
        color_map="viridis",
        x_axis_type=None,
    ):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        invalid_data: np.array(bool)
            Array indicating which depth cells contain invalid data
        n_ensembles: int
            Number of ensembles in edge for edge graph
        edge_start: bool, None
            Transect started on left bank
        max_limit: float
            Maximum limit for colorbar. Used to keep scale consistent when
             multiple contours on same page.
        color_map: str
            Defines the color map to be used in the color contour plot
        x_axis_type: str
            Identifies x-axis type (L-lenght, E-ensemble, T-time)
        color_map: str
            Defines the color map to be used in the color contour plot
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
            left=0.08, bottom=0.2, right=1, top=0.97, wspace=0.1, hspace=0
        )

        # Compute x axis data
        x = None
        if x_axis_type == "L":
            boat_track = transect.boat_vel.compute_boat_track(transect=transect)
            if not np.alltrue(np.isnan(boat_track["track_x_m"])):
                x = boat_track["distance_m"] * units["L"]
            else:
                x = np.arange(1, len(transect.depths.bt_depths.depth_processed_m) + 1)
        elif x_axis_type == "E":
            x = np.arange(1, len(transect.depths.bt_depths.depth_processed_m) + 1)
        elif x_axis_type == "T":
            timestamp = (
                np.nancumsum(transect.date_time.ens_duration_sec)
                + transect.date_time.start_serial_time
            )
            x = np.copy(timestamp)

        if n_ensembles is None or n_ensembles > 0:
            if edge_start is None:
                (
                    x_plt,
                    cell_plt,
                    speed_plt,
                    ensembles,
                    depth,
                ) = self.color_contour_data_prep(
                    transect=transect,
                    data_type="Processed",
                    invalid_data=invalid_data,
                    n_ensembles=n_ensembles,
                    x_1d=x,
                )

            else:
                (
                    x_plt,
                    cell_plt,
                    speed_plt,
                    ensembles,
                    depth,
                ) = self.color_contour_data_prep(
                    transect=transect,
                    data_type="Raw",
                    invalid_data=invalid_data,
                    n_ensembles=n_ensembles,
                    edge_start=edge_start,
                    x_1d=x,
                )

            if x_axis_type == "T":
                self.x_plt = np.zeros(x_plt.shape, dtype="object")
                for r in range(x_plt.shape[0]):
                    for c in range(x_plt.shape[1]):
                        self.x_plt[r, c] = datetime.utcfromtimestamp(x_plt[r, c])
                x = []
                for stamp in timestamp:
                    x.append(datetime.utcfromtimestamp(stamp))
                x = np.array(x)

            else:
                self.x_plt = x_plt

            # Use only specified ensembles, required for edges
            x = x[ensembles]

            self.cell_plt = cell_plt * self.units["L"]
            self.speed_plt = speed_plt * self.units["V"]

            # Determine limits for color map
            min_limit = 0
            if max_limit == 0:
                if np.sum(speed_plt[speed_plt > -900]) > 0:
                    max_limit = np.percentile(
                        speed_plt[speed_plt > -900] * units["V"], 99
                    )
                else:
                    max_limit = 1

            # Create color map
            cmap = cm.get_cmap(color_map)
            cmap.set_under("white")

            # Generate color contour
            c = self.fig.ax.pcolormesh(
                self.x_plt,
                self.cell_plt,
                self.speed_plt,
                cmap=cmap,
                vmin=min_limit,
                vmax=max_limit,
            )

            # Add color bar and axis labels
            cb = self.fig.colorbar(c, pad=0.02)
            cb.ax.set_ylabel(self.canvas.tr("Water Speed ") + units["label_V"])
            cb.ax.yaxis.label.set_fontsize(12)
            cb.ax.tick_params(labelsize=12)
            self.fig.ax.invert_yaxis()

            # Plot depth
            self.fig.ax.plot(x, depth * units["L"], color="k")

            # Plot side lobe cutoff if available
            if transect.w_vel.sl_cutoff_m is not None:
                depth_obj = getattr(transect.depths, transect.depths.selected)
                last_valid_cell = np.nansum(transect.w_vel.cells_above_sl, axis=0) - 1
                last_depth_cell_size = depth_obj.depth_cell_size_m[
                    last_valid_cell, np.arange(depth_obj.depth_cell_size_m.shape[1])
                ]
                y_plt_sl = (
                    transect.w_vel.sl_cutoff_m + (last_depth_cell_size * 0.5)
                ) * units["L"]
                y_plt_top = (
                    depth_obj.depth_cell_depth_m[0, :]
                    - (depth_obj.depth_cell_size_m[0, :] * 0.5)
                ) * units["L"]

                if edge_start is True:
                    y_plt_sl = y_plt_sl[: int(n_ensembles)]
                    y_plt_top = y_plt_top[: int(n_ensembles)]
                elif edge_start is False:
                    y_plt_sl = y_plt_sl[-int(n_ensembles) :]
                    y_plt_top = y_plt_top[-int(n_ensembles) :]

                self.fig.ax.plot(x, y_plt_sl, color="r", linewidth=0.5)
                # Plot upper bound of measured depth cells
                self.fig.ax.plot(x, y_plt_top, color="r", linewidth=0.5)

            # Label and limits for y axis
            self.fig.ax.set_ylabel(self.canvas.tr("Depth ") + units["label_L"])
            self.fig.ax.xaxis.label.set_fontsize(12)
            self.fig.ax.yaxis.label.set_fontsize(12)
            self.fig.ax.tick_params(
                axis="both",
                direction="in",
                bottom=True,
                top=True,
                left=True,
                right=True,
            )
            self.fig.ax.set_ylim(top=0, bottom=np.ceil(np.nanmax(depth * units["L"])))

            # Label and limits for x axis
            if x_axis_type == "L":
                axis_buffer = np.nanmax(x_plt[0, :]) - np.nanmin(x_plt[0, :])
                if transect.start_edge == "Right":
                    self.fig.ax.invert_xaxis()
                    self.fig.ax.set_xlim(
                        right=np.nanmin(x_plt[0, :]) - axis_buffer * 0.02,
                        left=np.nanmax(x_plt[0, :]) + axis_buffer * 0.02,
                    )
                else:
                    self.fig.ax.set_xlim(
                        left=np.nanmin(x_plt[0, :]) - axis_buffer * 0.02,
                        right=np.nanmax(x_plt[0, :]) + axis_buffer * 0.02,
                    )
                self.fig.ax.set_xlabel(self.canvas.tr("Length" + units["label_L"]))
            elif x_axis_type == "E":
                if transect.start_edge == "Right":
                    self.fig.ax.invert_xaxis()
                    self.fig.ax.set_xlim(right=np.nanmin(x) - 1, left=np.nanmax(x) + 1)
                else:
                    self.fig.ax.set_xlim(left=np.nanmin(x) - 1, right=np.nanmax(x) + 1)
                self.fig.ax.set_xlabel(self.canvas.tr("Ensembles"))
            elif x_axis_type == "T":
                axis_buffer = (x_plt[0, -1] - x_plt[0, 0]) * 0.02
                if transect.start_edge == "Right":
                    self.fig.ax.invert_xaxis()
                    self.fig.ax.set_xlim(
                        right=datetime.utcfromtimestamp(x_plt[0, 0] - axis_buffer),
                        left=datetime.utcfromtimestamp(x_plt[0, -1] + axis_buffer),
                    )
                else:
                    self.fig.ax.set_xlim(
                        left=datetime.utcfromtimestamp(x_plt[0, 0] - axis_buffer),
                        right=datetime.utcfromtimestamp(x_plt[0, -1] + axis_buffer),
                    )
                date_form = DateFormatter("%H:%M:%S")
                self.fig.ax.xaxis.set_major_formatter(date_form)
                self.fig.autofmt_xdate()
                self.fig.subplots_adjust(
                    left=0.08, bottom=0.3, right=1, top=0.97, wspace=0.1, hspace=0
                )
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
        else:
            max_limit = 0
        return max_limit

    @staticmethod
    def color_contour_data_prep(
        transect,
        data_type="Processed",
        invalid_data=None,
        n_ensembles=None,
        edge_start=None,
        x_1d=None,
    ):
        """Modifies the selected data from transect into arrays matching the
         meshgrid format for
        creating contour or color plots.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing data to be plotted
        data_type: str
            Specifies Processed or Filtered data type to be be plotted
        invalid_data: np.ndarray(bool)
            Array indicating what data are invalid
        n_ensembles: int
            Number of ensembles to plot. Used for edge contour plot.
        edge_start: bool
            Indicates if transect starts on left edge
        x_1d: np.array
            Array of x-coordinates for each ensemble

        Returns
        -------
        x_plt: np.array
            Data in meshgrid format used for the contour x variable
        cell_plt: np.array
            Data in meshgrid format used for the contour y variable
        speed_plt: np.array
            Data in meshgrid format used to determine colors in plot
        ensembles: np.array
            Ensemble numbers used as the x variable to plot the cross section
            bottom
        depth: np.array
            Depth data used to plot the cross section bottom
        """
        in_transect_idx = transect.in_transect_idx

        if x_1d is None:
            x_1d = in_transect_idx

        # Get data from transect
        if n_ensembles is None:
            # Use whole transect
            if data_type == "Processed":
                water_u = transect.w_vel.u_processed_mps[:, in_transect_idx]
                water_v = transect.w_vel.v_processed_mps[:, in_transect_idx]
            else:
                water_u = transect.w_vel.u_mps[:, in_transect_idx]
                water_v = transect.w_vel.v_mps[:, in_transect_idx]

            depth_selected = getattr(transect.depths, transect.depths.selected)
            depth = depth_selected.depth_processed_m[in_transect_idx]
            cell_depth = depth_selected.depth_cell_depth_m[:, in_transect_idx]
            cell_size = depth_selected.depth_cell_size_m[:, in_transect_idx]
            x_data = x_1d
            ensembles = in_transect_idx
        else:
            # Use only edge ensembles from transect
            n_ensembles = int(n_ensembles)
            if edge_start:
                # Start on left bank
                if data_type == "Processed":
                    water_u = transect.w_vel.u_processed_mps[:, :n_ensembles]
                    water_v = transect.w_vel.v_processed_mps[:, :n_ensembles]
                else:
                    water_u = transect.w_vel.u_mps[:, :n_ensembles]
                    water_v = transect.w_vel.v_mps[:, :n_ensembles]

                depth_selected = getattr(transect.depths, transect.depths.selected)
                depth = depth_selected.depth_processed_m[:n_ensembles]
                cell_depth = depth_selected.depth_cell_depth_m[:, :n_ensembles]
                cell_size = depth_selected.depth_cell_size_m[:, :n_ensembles]
                ensembles = in_transect_idx[:n_ensembles]
                x_data = x_1d[:n_ensembles]
                if invalid_data is not None:
                    invalid_data = invalid_data[:, :n_ensembles]
            else:
                # Start on right bank
                if data_type == "Processed":
                    water_u = transect.w_vel.u_processed_mps[:, -n_ensembles:]
                    water_v = transect.w_vel.v_processed_mps[:, -n_ensembles:]
                else:
                    water_u = transect.w_vel.u_mps[:, -n_ensembles:]
                    water_v = transect.w_vel.v_mps[:, -n_ensembles:]

                depth_selected = getattr(transect.depths, transect.depths.selected)
                depth = depth_selected.depth_processed_m[-n_ensembles:]
                cell_depth = depth_selected.depth_cell_depth_m[:, -n_ensembles:]
                cell_size = depth_selected.depth_cell_size_m[:, -n_ensembles:]
                ensembles = in_transect_idx[-n_ensembles:]
                x_data = x_1d[-n_ensembles:]
                if invalid_data is not None:
                    invalid_data = invalid_data[:, -n_ensembles:]

        # Prep water speed to use -999 instead of nans
        water_speed = np.sqrt(water_u**2 + water_v**2)
        speed = np.copy(water_speed)
        speed[np.isnan(speed)] = -999
        if invalid_data is not None:
            speed[invalid_data] = -999

        # Set x variable to ensembles
        x = np.tile(x_data, (cell_size.shape[0], 1))
        n_ensembles = x.shape[1]

        # Prep data in x direction
        j = -1
        x_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_depth_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_size_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        speed_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
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
            speed_xpand[:, j] = speed[:, n]
            cell_size_xpand[:, j] = cell_size[:, n]
            depth_xpand[j] = depth[n]
            j += 1
            x_xpand[:, j] = x[:, n] + half_forward
            cell_depth_xpand[:, j] = cell_depth[:, n]
            speed_xpand[:, j] = speed[:, n]
            cell_size_xpand[:, j] = cell_size[:, n]
            depth_xpand[j] = depth[n]

        # Create plotting mesh grid
        n_cells = x.shape[0]
        j = -1
        x_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        speed_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        for n in range(n_cells):
            j += 1
            x_plt[j, :] = x_xpand[n, :]
            cell_plt[j, :] = cell_depth_xpand[n, :] - 0.5 * cell_size_xpand[n, :]
            speed_plt[j, :] = speed_xpand[n, :]
            j += 1
            x_plt[j, :] = x_xpand[n, :]
            cell_plt[j, :] = cell_depth_xpand[n, :] + 0.5 * cell_size_xpand[n, :]
            speed_plt[j, :] = speed_xpand[n, :]

        cell_plt[np.isnan(cell_plt)] = 0
        speed_plt[np.isnan(speed_plt)] = -999
        x_plt[np.isnan(x_plt)] = 0

        return x_plt, cell_plt, speed_plt, ensembles, depth

    def hover(self, event):
        """Determines if the user has selected a location with data and makes
        annotation visible and calls method to update the text of the
        annotation. If the
        location is not valid the existing annotation is hidden.

        Parameters
        ----------
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Set annotation to visible
        vis = self.annot.get_visible()

        # Determine if mouse location references a data point in the plot and
        # update the annotation.
        if event.inaxes == self.fig.ax:
            cont_fig = False
            if self.fig is not None:
                cont_fig, ind_fig = self.fig.contains(event)

            if cont_fig and self.fig.get_visible():
                if self.x_axis_type == "T":
                    col_idx = np.where(
                        self.x_plt[0, :] < num2date(event.xdata).replace(tzinfo=None)
                    )[0][-1]
                elif self.x_axis_type == "L":
                    col_idx = np.where(self.x_plt[0, :] < event.xdata)[0][-1]
                else:
                    col_idx = (int(round(abs(event.xdata - self.x_plt[0, 0]))) * 2) - 1
                vel = None
                for n, cell in enumerate(self.cell_plt[:, col_idx]):
                    if event.ydata < cell:
                        vel = self.speed_plt[n, col_idx]
                        break

                self.update_annot(event.xdata, event.ydata, vel)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                # If the cursor location is not associated with the plotted
                # data hide the annotation.
                if vis:
                    self.annot.set_visible(False)
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
            # self.hover_connection =
            # self.canvas.mpl_connect("motion_notify_event", self.hover)
            self.hover_connection = self.canvas.mpl_connect(
                "button_press_event", self.hover
            )
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            self.annot.set_visible(False)
            self.canvas.draw_idle()

    def update_annot(self, x, y, v):
        """Updates the location and text and makes visible the previously
        initialized and hidden annotation.

        Parameters
        ----------
        x: float
            x coordinate for annotation, ensemble
        y: float
            y coordinate for annotation, depth
        v: float
            Speed for annotation
        """
        plt_ref = self.fig
        pos = [x, y]

        # Shift annotation box left or right depending on which half of the
        # axis the pos x is located and the
        # direction of x increasing.
        if plt_ref.ax.viewLim.intervalx[0] < plt_ref.ax.viewLim.intervalx[1]:
            if (
                pos[0]
                < (plt_ref.ax.viewLim.intervalx[0] + plt_ref.ax.viewLim.intervalx[1])
                / 2
            ):
                self.annot._x = -20
            else:
                self.annot._x = -80
        else:
            if (
                pos[0]
                < (plt_ref.ax.viewLim.intervalx[0] + plt_ref.ax.viewLim.intervalx[1])
                / 2
            ):
                self.annot._x = -80
            else:
                self.annot._x = -20

        # Shift annotation box up or down depending on which half of the
        # axis the pos y is located and the
        # direction of y increasing.
        if plt_ref.ax.viewLim.intervaly[0] < plt_ref.ax.viewLim.intervaly[1]:
            if (
                pos[1]
                > (plt_ref.ax.viewLim.intervaly[0] + plt_ref.ax.viewLim.intervaly[1])
                / 2
            ):
                self.annot._y = -40
            else:
                self.annot._y = 20
        else:
            if (
                pos[1]
                > (plt_ref.ax.viewLim.intervaly[0] + plt_ref.ax.viewLim.intervaly[1])
                / 2
            ):
                self.annot._y = 20
            else:
                self.annot._y = -40
        self.annot.xy = pos
        if v is not None and v > -999:
            if self.x_axis_type == "T":
                x_label = num2date(pos[0]).strftime("%H:%M:%S.%f")[:-4]
                text = "x: {}, y: {:.2f}, \n v: {:.1f}".format(x_label, y, v)
            elif self.x_axis_type == "E":
                text = "x: {:.2f}, y: {:.2f}, \n v: {:.1f}".format(int(round(x)), y, v)
            elif self.x_axis_type == "L":
                text = "x: {:.2f}, y: {:.2f}, \n v: {:.1f}".format(x, y, v)
        else:
            if self.x_axis_type == "T":
                x_label = num2date(pos[0]).strftime("%H:%M:%S.%f")[:-4]
                text = "x: {}, y: {:.2f}".format(x_label, y)
            elif self.x_axis_type == "E":
                text = "x: {:.2f}, y: {:.2f}".format(int(round(x)), y)
            elif self.x_axis_type == "L":
                text = "x: {:.2f}, y: {:.2f}".format(x, y)

        self.annot.set_text(text)

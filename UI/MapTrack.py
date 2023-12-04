import numpy as np
import copy


class Maptrack(object):
    """Class to generate shiptrack plot from MAP profile.

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
        self.acs = None
        self.hover_connection = None
        self.annot = None
        self.vectors = None

    def create(self, map_data, units, nav_ref, plot_transects=True):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        map_data: MAP
            Object of MAP from Measurement
        units: dict
            Dictionary of units conversions.
        nav_ref: str
            Navigation reference (bt_vel, gga_vel, vtg_vel)
        plot_transects: bool
        """

        # Assign and save parameters
        self.units = units
        self.acs = None

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(
            left=0.15, bottom=0.1, right=0.98, top=0.95, wspace=0.1, hspace=0
        )
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)

        direction_section = np.arctan2(map_data.slope, 1)

        if map_data.streamwise_velocity is not None:
            u = map_data.streamwise_velocity * np.sin(
                direction_section
            ) + map_data.transverse_velocity * np.cos(direction_section)
            v = map_data.transverse_velocity * np.sin(
                direction_section
            ) - map_data.streamwise_velocity * np.cos(direction_section)

            u = u * -1 * map_data._unit
            v = v * -1 * map_data._unit

            u_mean = np.nanmean(u, axis=0)
            v_mean = np.nanmean(v, axis=0)

            x_plt = (map_data.x[1:] + map_data.x[:-1]) / 2
            y_plt = (map_data.y[1:] + map_data.y[:-1]) / 2

            speed = np.sqrt(u_mean**2 + v_mean**2) * units["V"]
            if len(speed) > 0:
                max_speed = np.nanmax(speed)
            else:
                max_speed = 0

            self.vectors = self.fig.ax.quiver(
                x_plt,
                y_plt,
                u_mean * units["V"],
                v_mean * units["V"],
                units="dots",
                width=1,
                scale_units="width",
                scale=4 * max_speed,
            )

            self.acs = self.fig.ax.plot(
                map_data.x,
                map_data.y,
                color="firebrick",
                linewidth=2,
                label="MAP Average course",
                zorder=1,
            )
        if plot_transects:
            for i in range(len(map_data.x_raw_coordinates)):
                self.fig.ax.plot(
                    map_data.x_raw_coordinates[i],
                    map_data.y_raw_coordinates[i],
                    color="grey",
                    linewidth=1,
                    zorder=0,
                )

        # Customize axes
        if nav_ref == "gga_vel":
            self.fig.ax.set_xlabel(
                self.canvas.tr("UTM East coordinates ") + units["label_L"]
            )
            self.fig.ax.set_ylabel(
                self.canvas.tr("UTM North coordinates ") + units["label_L"]
            )
        else:
            self.fig.ax.set_xlabel(self.canvas.tr("Distance East ") + units["label_L"])
            self.fig.ax.set_ylabel(self.canvas.tr("Distance North ") + units["label_L"])

        self.fig.ax.tick_params(
            axis="both", direction="in", bottom=True, top=True, left=True, right=True
        )
        self.fig.ax.grid()
        self.fig.ax.axis("equal")
        for label in self.fig.ax.get_xticklabels() + self.fig.ax.get_yticklabels():
            label.set_fontsize(10)

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

    def hover(self, event):
        """Determines if the user has selected a location with temperature data and makes
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
        if event.inaxes == self.fig.ax and event.button != 3:
            cont = False
            ind = None
            plotted_line = None

            # Find the transect(line) that contains the mouse click
            for plotted_line in self.fig.ax.lines:
                cont, ind = plotted_line.contains(event)
                if cont:
                    break
            if cont:
                self.update_annot(ind, plotted_line)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                # If the cursor location is not associated with the plotted data hide the annotation.
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()

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

        text = "x: {:.2f}, y: {:.2f}".format(pos[0], pos[1])
        self.annot.set_text(text)

    def set_hover_connection(self, setting):
        """Turns the connection to the mouse event on or off.

        Parameters
        ----------
        setting: bool
            Boolean to specify whether the connection for the mouse event is active or not.
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

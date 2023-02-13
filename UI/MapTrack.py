import warnings
import numpy as np
from PyQt5.QtWidgets import QMenu


class Maptrack(object):
    """Class to generate shiptrack plot. If checkboxes for the boat reference
        (BT, GGA, VTG) are available they can be used to control what references are plotted.

        Attributes
        ----------
        canvas: MplCanvas
            Object of MplCanvas a FigureCanvas
        fig: Object
            Figure object of the canvas
        units: dict
            Dictionary of units conversions
        cb: bool
            Boolean to determine if checkboxes to control the boat speed reference are to be used
        cb_bt: QCheckBox
            Name of QCheckBox for bottom track
        cb_gga: QCheckBox
            Name of QCheckBox for GGA
        cb_vtg: QCheckBox
            Name of QCheckBox for VTG
        cb_vectors: QCheckBox
            Name of QCheckBox for vectors
        bt: list
            Plot reference for bottom track
        gga: list
            Plot reference for GGA
        vtg: list
            Plot reference for VTG
        vectors: list
            Plot reference for vectors
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
        self.cb = None
        self.cb_bt = None
        self.cb_gga = None
        self.cb_vtg = None
        self.cb_vectors = None
        self.bt = None
        self.gga = None
        self.vtg = None
        self.vectors = None
        self.vector_ref = None
        self.hover_connection = None
        self.annot = None

        self.clicked_connection = None

    def create(self, map_data, units):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        cb: bool
            Boolean to determine if checkboxes to control the boat speed reference are to be used
        cb_bt: QCheckBox
            Name of QCheckBox for bottom track
        cb_gga: QCheckBox
            Name of QCheckBox for GGA
        cb_vtg: QCheckBox
            Name of QCheckBox for VTG
        cb_vectors: QCheckBox
            Name of QCheckBox for vectors
        n_ensembles: int
            Number of ensembles to plot. Used in edges tab.
        edge_start: int
            Ensemble to start plotting. Used in edges tab.
        """

        # Assign and save parameters
        self.units = units
        self.acs = None

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.18, bottom=0.18, right=0.98, top=0.98, wspace=0.1, hspace=0)
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)

        x_boundaries0 = [min([min(l) for l in map_data.x_projected]), max([max(l) for l in map_data.x_projected])]
        x_boundaries1 = [min([min(l) for l in map_data.x_raw_coordinates]), max([max(l) for l in map_data.x_raw_coordinates])]
        x_boundaries = [min([x_boundaries0[0], x_boundaries1[0]]), max([x_boundaries0[1], x_boundaries1[1]])]
        y_boundaries0 = [min([min(l) for l in map_data.y_projected]), max([max(l) for l in map_data.y_projected])]
        y_boundaries1 = [min([min(l) for l in map_data.y_raw_coordinates]), max([max(l) for l in map_data.y_raw_coordinates])]
        y_boundaries = [min([y_boundaries0[0], y_boundaries1[0]]), max([y_boundaries0[1], y_boundaries1[1]])]
        x_mean = np.nanmean(x_boundaries)
        y_mean = np.nanmean(y_boundaries)
        x2 = abs(x_boundaries[1] - x_boundaries[0]) / 2
        y2 = abs(y_boundaries[1] - y_boundaries[0]) / 2
        dist = np.nanmax([x2, y2])


        self.acs = self.fig.ax.plot(x_boundaries, [map_data.slope * l + map_data.intercept for l in x_boundaries],
                                    color='firebrick', linewidth=2, label='MAP Average course', zorder=2)
        for i in range(len(map_data.x_raw_coordinates)):
            self.fig.ax.plot(map_data.x_raw_coordinates[i], map_data.y_raw_coordinates[i], color='grey', linewidth=1)
        self.fig.ax.plot(np.nan, np.nan, color='grey', linewidth=1, label='Transect boat track')

        # Customize axes
        self.fig.ax.set_xlabel(self.canvas.tr('Distance East ') + units['label_L'])
        self.fig.ax.set_ylabel(self.canvas.tr('Distance North ') + units['label_L'])

        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.ax.grid()
        self.fig.ax.axis('equal')
        for label in (self.fig.ax.get_xticklabels() + self.fig.ax.get_yticklabels()):
            label.set_fontsize(10)


        self.fig.ax.set_ylim(y_mean - dist, y_mean + dist)
        self.fig.ax.set_xlim(x_mean - dist, x_mean + dist)
        # self.fig.ax.gca().set_aspect('equal', adjustable='box')
        # self.fig.ax.legend(loc='best')

        # Initialize annotation for data cursor
        self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->"))

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
        vector_ref: Quiver
            Refernece containing plotted data
        ref_label: str
            Label used to ID data type in annotation
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
        self.annot.xy = pos

        text = 'x: {:.2f}, y: {:.2f}'.format(pos[0], pos[1])
        self.annot.set_text(text)

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


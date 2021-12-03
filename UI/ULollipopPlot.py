class ULollipopPlot(object):
    """Class to generate lollipop plot of Oursin uncertainty results.
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
        self.plot_df = None

    def create(self, meas):
        """Generates the lollipop plot.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        """

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        self.fig.ax.clear()

        if meas.run_oursin:
            # Set margins and padding for figure
            self.fig.subplots_adjust(left=0.2, bottom=0.15, right=0.98, top=0.95, wspace=0.1, hspace=0)

            # Configure plot dataframe
            self.plot_df = meas.oursin.u_contribution_measurement_user.drop(['total'], axis=1)
            self.plot_df = self.plot_df.mul(100)
            self.plot_df.index = ['Percent']
            self.plot_df.columns = ['System', 'Compass', 'Moving-bed', '# Ensembles', 'Meas. Q', 'Top Q', 'Bottom Q',
                                    'Left Q', 'Right Q', 'Inv. Boat', 'Inv. Depth', 'Inv. Water', 'COV']
            self.plot_df = self.plot_df.transpose()
            self.plot_df = self.plot_df.sort_values(by='Percent')

            # Generate plot
            self.fig.ax.hlines(y=self.plot_df.index, xmin=0, xmax=self.plot_df['Percent'])
            self.fig.ax.plot(self.plot_df['Percent'], self.plot_df.index, 'o', markersize=11)
            self.fig.ax.set_xlabel(self.canvas.tr("Percent of Total"))
            self.fig.ax.xaxis.label.set_fontsize(12)
            self.fig.ax.tick_params(axis='both', which='major', labelsize=10)
            self.fig.ax.set_title(self.canvas.tr('95% Total Uncertainty: ') +
                                  '%5.1f' % meas.oursin.u_measurement_user['total_95'][0], fontweight="bold")

            # Setup annotation features
            self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                              bbox=dict(boxstyle="round", fc="w"),
                                              arrowprops=dict(arrowstyle="->"))

            self.annot.set_visible(False)

            self.canvas.draw()

    def update_annot(self, name, u_value, event):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        name: str
            Name of uncertainty type
        u_value: float
            Uncertainty percent
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Get selected data coordinates
        pos = [event.xdata, event.ydata]

        # Shift annotation box left or right depending on which half of the axis the pos x is located and the
        # direction of x increasing.
        if self.fig.ax.viewLim.intervalx[0] < self.fig.ax.viewLim.intervalx[1]:
            if pos[0] < (self.fig.ax.viewLim.intervalx[0] + self.fig.ax.viewLim.intervalx[1]) / 2:
                self.annot._x = -20
            else:
                self.annot._x = -80
        else:
            if pos[0] < (self.fig.ax.axes.viewLim.intervalx[0] + self.fig.ax.viewLim.intervalx[1]) / 2:
                self.annot._x = -80
            else:
                self.annot._x = -20

        # Shift annotation box up or down depending on which half of the axis the pos y is located and the
        # direction of y increasing.
        if self.fig.ax.viewLim.intervaly[0] < self.fig.ax.viewLim.intervaly[1]:
            if pos[1] > (self.fig.ax.viewLim.intervaly[0] + self.fig.ax.viewLim.intervaly[1]) / 2:
                self.annot._y = -40
            else:
                self.annot._y = 20
        else:
            if pos[1] > (self.fig.ax.viewLim.intervaly[0] + self.fig.ax.viewLim.intervaly[1]) / 2:
                self.annot._y = 20
            else:
                self.annot._y = -40

        self.annot.xy = pos

        # Format and display text
        text = '{}: {:2.2f}%'.format(name, u_value)
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
            row = int(round(event.ydata))
            name = list(self.plot_df.index)[row]
            u_value = self.plot_df.loc[name, 'Percent']

            self.update_annot(name, u_value, event)
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
            Boolean to specify whether the connection for the mouse event is
            active or not.
        """

        if setting and self.hover_connection is None:
            self.hover_connection = self.canvas.mpl_connect('button_press_event', self.hover)
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            if self.annot is not None:
                self.annot.set_visible(False)
            self.canvas.draw_idle()

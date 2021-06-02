import pandas as pd

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

            self.plot_df = meas.oursin.u_contribution_measurement_user.drop(['total'], axis=1)
            self.plot_df = self.plot_df.mul(100)
            self.plot_df.index = ['Percent']
            self.plot_df.columns = ['System', 'Compass', 'Moving-bed', '# Ensembles', 'Meas. Q', 'Top Q', 'Bottom Q',
                      'Left Q', 'Right Q', 'Inv. Boat', 'Inv. Depth', 'Inv. Water', 'COV']
            self.plot_df = self.plot_df.transpose()
            self.plot_df = self.plot_df.sort_values(by='Percent')

            self.fig.ax.hlines(y=self.plot_df.index, xmin=0, xmax=self.plot_df['Percent'])
            self.fig.ax.plot(self.plot_df['Percent'], self.plot_df.index, 'o', markersize=11)
            self.fig.ax.set_xlabel(self.canvas.tr("Percent of Total"))
            self.fig.ax.xaxis.label.set_fontsize(12)
            self.fig.ax.tick_params(axis='both', which='major', labelsize=10)
            self.fig.ax.set_title(self.canvas.tr('95% Total Uncertainty: ') +
                              '%5.1f' % meas.oursin.u_measurement_user['total_95'][0], fontweight="bold")
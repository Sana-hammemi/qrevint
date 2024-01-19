from PyQt5 import QtWidgets
from UI import Arrows_Scale
from UI.MplCanvas import MplCanvas
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class ArrowsScale(QtWidgets.QDialog, Arrows_Scale.Ui_ArrowsScaling):
    """Dialog to allow users to change heading offset.

    Parameters
    ----------
    Axes_Scale.Ui_Axes_Scale : QDialog
        Dialog window to allow users to change axes scaline
    """

    def __init__(self, parent=None):
        super(ArrowsScale, self).__init__(parent)
        self.setupUi(self)
        self.canvas = MplCanvas(
            parent=self.graphics_color_bar, width=1, height=3, dpi=80
        )
        # Assign layout to widget to allow auto scaling
        layout = QtWidgets.QVBoxLayout(self.graphics_color_bar)
        # Adjust margins of layout to maximize graphic area
        layout.setContentsMargins(1, 1, 1, 1)
        # Add the canvas
        layout.addWidget(self.canvas)
        self.fig = self.canvas.fig

        self.plot_colorbar()

    def plot_colorbar(self, palette='jet'):
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot()

        # Create colorbar
        cbar = plt.colorbar(cm.ScalarMappable(cmap=palette), cax=self.fig.ax, orientation='vertical')
        cbar.ax.set_facecolor('none')
        self.fig.ax.set_axis_off()
        self.fig.subplots_adjust(
            left=0.0, bottom=0.0, right=1, top=1, wspace=0.02, hspace=0
        )

        self.canvas.draw()

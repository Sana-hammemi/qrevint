from PyQt5 import QtWidgets, QtGui, QtCore
from qrev.UI import Arrows_Scale
from qrev.UI.MplCanvas import MplCanvas
from matplotlib import cm


class ArrowsScale(QtWidgets.QDialog, Arrows_Scale.Ui_ArrowsScaling):
    """Dialog to allow users to change heading offset.

    Parameters
    ----------
    Axes_Scale.Ui_Axes_Scale : QDialog
        Dialog window to allow users to change axes scaline
    """

    def __init__(self, parent):
        super(ArrowsScale, self).__init__(parent)
        self.setupUi(self)

        # Enter numerical values
        validator = QtGui.QDoubleValidator(self)
        validator.setBottom(
            -float('inf'))  # or set a specific range like -100.0
        validator.setTop(float('inf'))
        validator.setDecimals(2)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)

        self.ed_arrow_scale.setValidator(validator)
        self.ed_v_max.setValidator(validator)
        self.ed_v_min.setValidator(validator)

        # Canvas for ColorBar
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

        self.plot_colorbar(palette=parent.color_map)

    def plot_colorbar(self, palette='jet'):
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot()
        self.fig.colorbar(cm.ScalarMappable(cmap=palette), cax=self.fig.ax, orientation='vertical')

        # Create colorbar
        self.fig.ax.set_axis_off()
        self.fig.subplots_adjust(
            left=0.0, bottom=0.0, right=1, top=1, wspace=0.02, hspace=0
        )

        self.canvas.draw()

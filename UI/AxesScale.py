from PyQt5 import QtWidgets
from UI import Axes_Scale


class AxesScale(QtWidgets.QDialog, Axes_Scale.Ui_Axes_Scale):
    """Dialog to allow users to change heading offset.

    Parameters
    ----------
    Axes_Scale.Ui_Axes_Scale : QDialog
        Dialog window to allow users to change axes scaline
    """

    def __init__(self, parent=None):
        super(AxesScale, self).__init__(parent)
        self.setupUi(self)

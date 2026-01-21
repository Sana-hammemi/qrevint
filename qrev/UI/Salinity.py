from PyQt5 import QtWidgets, QtGui
from qrev.UI import wSalinity


class Salinity(QtWidgets.QDialog, wSalinity.Ui_salinity):
    """Dialog to allow users to change salinity.

    Parameters
    ----------
    wSalinity.Ui_salinity : QDialog
        Dialog window to allow users to change salinity
    """

    def __init__(self, parent=None):
        super(Salinity, self).__init__(parent)
        self.setupUi(self)

        # set to numbers only, 2 decimals, and 0 to 69.99 ppt
        validator = QtGui.QDoubleValidator(0.0, 69.99, 2, self)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.ed_salinity.setValidator(validator)


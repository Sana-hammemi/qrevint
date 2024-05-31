from PyQt5 import QtWidgets
from qrev.UI import wThreshold


class Threshold(QtWidgets.QDialog, wThreshold.Ui_threshold):
    """Dialog to allow users to change the point threshold in extrap.

    Parameters
    ----------
    wThreshold.Ui_threshold : QDialog
        Dialog window to allow users to change the point threshold in extrap
    """

    def __init__(self, parent=None):
        """Initialize dialog"""

        super(Threshold, self).__init__(parent)
        self.setupUi(self)

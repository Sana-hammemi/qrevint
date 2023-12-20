from PyQt5 import QtWidgets
from UI import wDisclaimer


class Disclaimer(QtWidgets.QDialog, wDisclaimer.Ui_Disclaimer):
    """Dialog to force users to accept the disclaimer and license the
    first time the run the code."""

    def __init__(self, parent=None):
        super(Disclaimer, self).__init__(parent)
        self.setupUi(self)
